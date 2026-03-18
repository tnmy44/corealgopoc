"""Evaluation of string matching algorithms on real column-name synonym data.

Methodology:
    For each synonym group and each pair (query, expected_match):
      - Determine which dataset pool the expected_match belongs to (gsmbs or mfa)
      - Score the query against ALL columns in that pool
      - Record the rank and scores of expected_match vs non-synonyms

Cost model (asymmetric):
    False positives (non-synonym gets high score → wrong mapping) are **5x** more
    costly than false negatives (synonym gets low score → fall back to LLM).

    At a score threshold t, for each query the engine would:
      - Accept top-1 if its score >= t  →  cost 0 if correct, cost 5 if wrong (FP)
      - Abstain if top score < t        →  cost 1 (FN, falls back to LLM)

    We sweep thresholds to find each algorithm's optimal operating point.

Metrics:
    - FP Rate:   % of queries where top-1 is NOT the synonym
    - Margin:    mean(synonym_score - max_non_synonym_score), positive = good separation
    - OptCost:   minimum weighted cost (5·FP + 1·FN) at the optimal threshold, per query
    - OptThresh: the threshold that achieves OptCost
    - Hit@1/3/5: rank-based recall metrics
    - MRR:       Mean Reciprocal Rank
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Optional

import pytest

from harmonize.interfaces import StringMatcher
from harmonize.string_matching import (
    ExactStringMatcher,
    JaroWinklerMatcher,
    LevenshteinStringMatcher,
    SemanticMatcher,
    SubsequenceMatcher,
    TokenSetMatcher,
    WeightedCombinationMatcher,
)
from tests.stringmatching.column_names import gsmbs_input_cols, mfa_input_cols

# ---------------------------------------------------------------------------
# Load synonym groups
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.dirname(__file__)


def _load_synonyms() -> list[list[str]]:
    with open(os.path.join(_DATA_DIR, "synonyms.json")) as f:
        groups = json.load(f)
    # Deduplicate within each group
    deduped = []
    for group in groups:
        seen = set()
        unique = []
        for term in group:
            key = term.strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(term.strip())
        if len(unique) >= 2:
            deduped.append(unique)
    return deduped


# ---------------------------------------------------------------------------
# Build dataset lookup: which pool does a term belong to?
# ---------------------------------------------------------------------------

_gsmbs_set = {c.lower(): c for c in gsmbs_input_cols}
_mfa_set = {c.lower(): c for c in mfa_input_cols}


def _find_pool(term: str) -> Optional[tuple[str, list[str]]]:
    """Return (pool_name, pool_columns) if term belongs to a known dataset."""
    key = term.strip().lower()
    if key in _gsmbs_set:
        return ("gsmbs", gsmbs_input_cols)
    if key in _mfa_set:
        return ("mfa", mfa_input_cols)
    return None


# ---------------------------------------------------------------------------
# Build evaluation pairs from synonym groups
# ---------------------------------------------------------------------------

@dataclass
class EvalPair:
    query: str  # term used as the lookup key
    expected: str  # the synonym that should rank highest in the pool
    pool_name: str  # "gsmbs" or "mfa"
    pool: list[str]  # all columns in that dataset


def _build_eval_pairs() -> list[EvalPair]:
    """For each synonym group, generate (query, expected, pool) pairs.

    For each term in a group that belongs to a known dataset, pair it with
    every other term in the group as a query (cross-dataset lookups).
    """
    synonyms = _load_synonyms()
    pairs: list[EvalPair] = []

    for group in synonyms:
        for i, target_term in enumerate(group):
            pool_info = _find_pool(target_term)
            if pool_info is None:
                continue
            pool_name, pool = pool_info
            # Every other term in the group becomes a query
            for j, query_term in enumerate(group):
                if i == j:
                    continue
                # Skip if query is in the same pool (we want cross-dataset)
                query_pool = _find_pool(query_term)
                if query_pool is not None and query_pool[0] == pool_name:
                    continue
                pairs.append(EvalPair(
                    query=query_term,
                    expected=target_term,
                    pool_name=pool_name,
                    pool=pool,
                ))

    return pairs


# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------

FP_COST = 5
FN_COST = 1


@dataclass
class QueryResult:
    """Per-query raw data for downstream metric computation."""

    rank: int  # 1-indexed rank of the synonym in the pool
    synonym_score: float  # score of the true synonym
    top1_score: float  # score of the top-ranked candidate
    top1_is_synonym: bool  # whether top-1 is the correct synonym
    best_distractor_score: float  # highest score among non-synonyms


@dataclass
class EvalResult:
    algorithm: str
    # Asymmetric cost metrics (primary)
    fp_rate: float  # fraction of queries where top-1 is wrong
    tp_rate: float  # fraction of queries correctly accepted at optimal threshold
    abstain_rate: float  # fraction of queries where algorithm abstains (falls back to LLM)
    avg_margin: float  # mean(synonym_score - max_non_synonym_score)
    optimal_cost: float  # min weighted cost per query at best threshold
    optimal_threshold: float  # threshold achieving optimal_cost
    # Rank-based metrics (secondary)
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    mean_rank: float
    # Performance
    avg_time_us: float  # average time per score() call in microseconds
    num_pairs: int


def _collect_query_results(
    matcher: StringMatcher, pairs: list[EvalPair]
) -> tuple[list[QueryResult], float]:
    """Returns (query_results, avg_time_per_score_call_in_microseconds)."""
    results: list[QueryResult] = []
    total_score_calls = 0
    total_time = 0.0

    for pair in pairs:
        t0 = time.perf_counter()
        scored = [
            (col, matcher.score(pair.query, col)) for col in pair.pool
        ]
        total_time += time.perf_counter() - t0
        total_score_calls += len(pair.pool)
        scored.sort(key=lambda x: (-x[1], x[0]))

        expected_lower = pair.expected.lower()
        rank = None
        synonym_score = 0.0
        for idx, (col, sc) in enumerate(scored, 1):
            if col.lower() == expected_lower:
                rank = idx
                synonym_score = sc
                break

        if rank is not None:
            top1_col, top1_score = scored[0]
            is_top1 = top1_col.lower() == expected_lower
            # Best distractor = highest-scoring non-synonym
            best_dist = 0.0
            for col, sc in scored:
                if col.lower() != expected_lower:
                    best_dist = sc  # scored is sorted descending
                    break
            results.append(QueryResult(
                rank=rank,
                synonym_score=synonym_score,
                top1_score=top1_score,
                top1_is_synonym=is_top1,
                best_distractor_score=best_dist,
            ))

    avg_us = (total_time / total_score_calls * 1e6) if total_score_calls else 0.0
    return results, avg_us


def _compute_optimal_threshold(
    query_results: list[QueryResult],
) -> tuple[float, float]:
    """Sweep thresholds to find the one minimising weighted cost.

    At threshold t, for each query:
      - If top1_score >= t and top1 is synonym:     cost = 0  (TP)
      - If top1_score >= t and top1 is NOT synonym: cost = FP_COST  (FP)
      - If top1_score < t:                          cost = FN_COST  (abstain → FN)

    Returns (optimal_threshold, avg_cost_at_optimum).
    """
    # Collect all unique scores as candidate thresholds, plus 0 and 1
    all_scores: set[float] = {0.0, 1.0}
    for qr in query_results:
        all_scores.add(qr.top1_score)
        all_scores.add(qr.synonym_score)
        # Add midpoints around top1 for finer resolution
        all_scores.add(qr.top1_score + 1e-9)
        all_scores.add(qr.top1_score - 1e-9)

    thresholds = sorted(all_scores)
    n = len(query_results)
    if n == 0:
        return 0.0, 0.0

    best_cost = float("inf")
    best_t = 0.0

    for t in thresholds:
        total_cost = 0.0
        for qr in query_results:
            if qr.top1_score >= t:
                # Algorithm accepts top-1
                if qr.top1_is_synonym:
                    total_cost += 0  # TP
                else:
                    total_cost += FP_COST  # FP: wrong match selected
            else:
                # Algorithm abstains → falls back to LLM
                total_cost += FN_COST  # FN

        avg_cost = total_cost / n
        if avg_cost < best_cost:
            best_cost = avg_cost
            best_t = t

    return best_t, best_cost


def _evaluate_algorithm(
    name: str, matcher: StringMatcher, pairs: list[EvalPair]
) -> EvalResult:
    query_results, avg_time_us = _collect_query_results(matcher, pairs)
    n = len(query_results)
    if n == 0:
        return EvalResult(name, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    ranks = [qr.rank for qr in query_results]

    # Score margin: synonym_score - best_distractor_score
    # Positive = clean separation, negative = non-synonym outscores synonym (FP-prone)
    margins = [qr.synonym_score - qr.best_distractor_score for qr in query_results]

    optimal_t, optimal_cost = _compute_optimal_threshold(query_results)

    # Calculate false positives, true positives, abstains
    false_positives = 0
    true_positives = 0
    abstains = 0
    for qr in query_results:
        if qr.top1_score >= optimal_t:
            # Algorithm accepts top-1
            if qr.top1_is_synonym:
                true_positives += 1
            else:
                false_positives += 1
        else:
            abstains += 1

    return EvalResult(
        algorithm=name,
        fp_rate=false_positives / n,
        tp_rate=true_positives / n,
        abstain_rate=abstains / n,
        avg_margin=sum(margins) / n,
        optimal_cost=optimal_cost,
        optimal_threshold=optimal_t,
        hit_at_1=sum(1 for r in ranks if r == 1) / n,
        hit_at_3=sum(1 for r in ranks if r <= 3) / n,
        hit_at_5=sum(1 for r in ranks if r <= 5) / n,
        mrr=sum(1.0 / r for r in ranks) / n,
        mean_rank=sum(ranks) / n,
        avg_time_us=avg_time_us,
        num_pairs=n,
    )


# ---------------------------------------------------------------------------
# Define algorithms to evaluate
# ---------------------------------------------------------------------------

def _get_algorithms() -> list[tuple[str, StringMatcher]]:
    levenshtein = LevenshteinStringMatcher()
    jaro_winkler = JaroWinklerMatcher()
    token_set = TokenSetMatcher()
    subsequence = SubsequenceMatcher()
    semantic = SemanticMatcher()

    return [
        ("Exact", ExactStringMatcher()),
        ("Levenshtein", levenshtein),
        ("JaroWinkler", jaro_winkler),
        ("TokenSet", token_set),
        ("Subsequence", subsequence),
        ("Semantic", semantic),
        (
            "Levenshtein+TokenSet",
            WeightedCombinationMatcher([(levenshtein, 0.5), (token_set, 0.5)]),
        ),
        (
            "JaroWinkler+TokenSet",
            WeightedCombinationMatcher([(jaro_winkler, 0.5), (token_set, 0.5)]),
        ),
        (
            "Semantic+TokenSet",
            WeightedCombinationMatcher([(semantic, 0.5), (token_set, 0.5)]),
        ),
        (
            "Semantic+Levenshtein",
            WeightedCombinationMatcher([(semantic, 0.5), (levenshtein, 0.5)]),
        ),
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStringMatchingEvaluation:
    """Run all algorithms and print a comparison table."""

    @pytest.fixture(scope="class")
    def eval_pairs(self) -> list[EvalPair]:
        pairs = _build_eval_pairs()
        assert len(pairs) > 0, "No evaluation pairs generated — check synonyms.json and column_names.py"
        return pairs

    @pytest.fixture(scope="class")
    def results(self, eval_pairs: list[EvalPair]) -> list[EvalResult]:
        algorithms = _get_algorithms()
        return [_evaluate_algorithm(name, matcher, eval_pairs) for name, matcher in algorithms]

    def test_eval_pairs_generated(self, eval_pairs: list[EvalPair]):
        """Sanity check: we have a meaningful number of eval pairs."""
        assert len(eval_pairs) >= 20

    def test_comparison_table(self, results: list[EvalResult]):
        """Print the comparison table sorted by optimal weighted cost (lower = better)."""
        ranked = sorted(results, key=lambda r: r.optimal_cost)

        header = (
            f"{'Algorithm':<25} {'OptCost':>8} {'Thresh':>7} {'TP%':>7} {'FP%':>7} {'Abst%':>7} "
            f"{'Margin':>7} {'Hit@1':>7} {'Hit@3':>7} {'MRR':>7} {'Avg Time':>10}"
        )
        sep = "-" * len(header)
        lines = [
            "\n" + sep,
            f"STRING MATCHING EVALUATION  (FP cost={FP_COST}, FN cost={FN_COST})",
            sep,
            header,
            sep,
        ]

        for r in ranked:
            if r.avg_time_us >= 1000:
                time_str = f"{r.avg_time_us / 1000:.1f} ms"
            else:
                time_str = f"{r.avg_time_us:.0f} us"
            lines.append(
                f"{r.algorithm:<25} {r.optimal_cost:>8.3f} {r.optimal_threshold:>7.3f} "
                f"{r.tp_rate:>7.1%} {r.fp_rate:>7.1%} {r.abstain_rate:>7.1%} "
                f"{r.avg_margin:>+7.3f} "
                f"{r.hit_at_1:>7.1%} {r.hit_at_3:>7.1%} {r.mrr:>7.3f} {time_str:>10}"
            )
        lines.append(sep)
        lines.append(
            f"Best by weighted cost: {ranked[0].algorithm} "
            f"(cost={ranked[0].optimal_cost:.3f} @ threshold={ranked[0].optimal_threshold:.3f})"
        )
        lines.append(sep)

        print("\n".join(lines))

    def test_best_algorithm_beats_exact(self, results: list[EvalResult]):
        """The best fuzzy algorithm should have lower weighted cost than exact matching."""
        exact = next(r for r in results if r.algorithm == "Exact")
        best_fuzzy = min(
            (r for r in results if r.algorithm != "Exact"),
            key=lambda r: r.optimal_cost,
        )
        assert best_fuzzy.optimal_cost < exact.optimal_cost, (
            f"Best fuzzy ({best_fuzzy.algorithm}, cost={best_fuzzy.optimal_cost:.3f}) "
            f"should beat Exact (cost={exact.optimal_cost:.3f})"
        )

    def test_best_algorithm_cost_below_baseline(self, results: list[EvalResult]):
        """The best algorithm should beat the 'always abstain' baseline (cost=FN_COST)."""
        best = min(results, key=lambda r: r.optimal_cost)
        assert best.optimal_cost < FN_COST, (
            f"Best algorithm ({best.algorithm}) cost={best.optimal_cost:.3f} "
            f"should be below always-abstain baseline ({FN_COST})"
        )

    def test_individual_algorithm_results(self, results: list[EvalResult]):
        """Each algorithm should produce results for all pairs."""
        for r in results:
            assert r.num_pairs > 0, f"{r.algorithm} produced no results"
