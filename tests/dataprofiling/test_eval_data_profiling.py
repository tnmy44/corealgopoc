"""Evaluation of data profile matching: format discrimination.

The real question data profile matching answers is:
"Is this new data in the same format as the past data, so I can safely reuse
the SQL expression?"

We test discrimination between:
  - Positive pairs: same column, same format (GSMBS vs MFA original) → should match
  - Negative pairs: same column, different format (GSMBS vs MFA transformed) → should NOT match

Transformations simulate real-world format mismatches (date formats, unit
scaling, boolean encoding, case changes).
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass

import pandas as pd
import pytest

from harmonize.data_profiling import (
    DistributionProfileMatcher,
    EnhancedProfileMatcher,
    PandasProfiler,
    SimpleDataProfileMatcher,
    WassersteinProfileMatcher,
    WeightedCombinationProfileMatcher,
)
from harmonize.interfaces import DataProfileMatcher
from harmonize.models import DataProfile

_DATA_DIR = os.path.dirname(__file__)


# ---------------------------------------------------------------------------
# Transformation functions
# ---------------------------------------------------------------------------

def _transform_date_format(values: list) -> list:
    """'9/30/2025' → '2025-09-30' (ISO format)."""
    out: list = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", str(v).strip())
        if m:
            out.append(f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}")
        else:
            out.append(v)
    return out


def _transform_fraction_to_pct(values: list) -> list:
    """0.05 → 5.0 (multiply by 100)."""
    out: list = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        try:
            out.append(str(float(str(v).replace(",", "")) * 100))
        except (ValueError, TypeError):
            out.append(v)
    return out


def _transform_scale_thousands(values: list) -> list:
    """50000 → 50.0 (divide by 1000)."""
    out: list = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        try:
            out.append(str(float(str(v).replace(",", "")) / 1000))
        except (ValueError, TypeError):
            out.append(v)
    return out


def _transform_bool_format(values: list) -> list:
    """'0'/'1' → 'N'/'Y'."""
    mapping = {"0": "N", "1": "Y", "n": "N", "y": "Y",
               "no": "N", "yes": "Y", "false": "N", "true": "Y"}
    out: list = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        out.append(mapping.get(str(v).strip().lower(), v))
    return out


def _transform_uppercase(values: list) -> list:
    """'Cash Out' → 'CASH OUT'."""
    out: list = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        out.append(str(v).upper())
    return out


def _transform_scale_10x(values: list) -> list:
    """Generic ×10 for numeric columns."""
    out: list = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        try:
            out.append(str(float(str(v).replace(",", "")) * 10))
        except (ValueError, TypeError):
            out.append(v)
    return out


# ---------------------------------------------------------------------------
# Auto-assign transformation based on profile
# ---------------------------------------------------------------------------

def _assign_transformation(profile: DataProfile):
    """Pick the most appropriate transformation for a column."""
    if profile.dtype == "boolean":
        return _transform_bool_format

    if profile.dtype == "numeric" and profile.numeric_stats:
        max_val = profile.numeric_stats.max_val
        if max_val <= 1.5:
            return _transform_fraction_to_pct  # rates, ratios
        if max_val > 1000:
            return _transform_scale_thousands  # dollar amounts, scores
        return _transform_scale_10x

    if profile.dtype == "string" and profile.string_stats:
        # Check if dominant pattern looks like a date  (N/N/N)
        for pattern, _ in profile.string_stats.pattern_distribution:
            if "N/N/N" in pattern:
                return _transform_date_format
        return _transform_uppercase

    # Fallback
    return _transform_uppercase


# ---------------------------------------------------------------------------
# Load and profile
# ---------------------------------------------------------------------------

def _load_raw(csv_path: str) -> dict[str, list]:
    """Load CSV, return column_name → list of values (None for NaN)."""
    df = pd.read_csv(csv_path, dtype=str)
    result: dict[str, list] = {}
    for col in df.columns:
        result[col] = [None if pd.isna(v) else v for v in df[col].tolist()]
    return result


def _profile_column(col_name: str, values: list) -> DataProfile:
    profiler = PandasProfiler()
    return profiler.profile(col_name, values, "auto")


# ---------------------------------------------------------------------------
# Evaluation dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PairResult:
    column: str
    positive_score: float
    negative_score: float
    discriminated: bool  # positive_score > negative_score


@dataclass
class EvalResult:
    algorithm: str
    discrimination_rate: float
    avg_positive_score: float
    avg_negative_score: float
    margin: float
    optimal_accuracy: float
    optimal_threshold: float
    num_columns: int
    avg_time_us: float


# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------

def _evaluate_matcher(
    name: str,
    matcher: DataProfileMatcher,
    gsmbs_profiles: dict[str, DataProfile],
    mfa_orig_profiles: dict[str, DataProfile],
    mfa_transformed_profiles: dict[str, DataProfile],
) -> EvalResult:
    """Evaluate a matcher on positive/negative pairs."""
    common_cols = sorted(
        set(gsmbs_profiles.keys())
        & set(mfa_orig_profiles.keys())
        & set(mfa_transformed_profiles.keys())
    )

    pair_results: list[PairResult] = []
    total_time = 0.0
    total_calls = 0

    for col in common_cols:
        gp = gsmbs_profiles[col]
        mp_orig = mfa_orig_profiles[col]
        mp_trans = mfa_transformed_profiles[col]

        t0 = time.perf_counter()
        pos_score = matcher.score(gp, mp_orig)
        neg_score = matcher.score(gp, mp_trans)
        total_time += time.perf_counter() - t0
        total_calls += 2

        pair_results.append(PairResult(
            column=col,
            positive_score=pos_score,
            negative_score=neg_score,
            discriminated=pos_score > neg_score,
        ))

    n = len(pair_results)
    if n == 0:
        return EvalResult(name, 0, 0, 0, 0, 0, 0, 0, 0)

    disc_rate = sum(1 for pr in pair_results if pr.discriminated) / n
    avg_pos = sum(pr.positive_score for pr in pair_results) / n
    avg_neg = sum(pr.negative_score for pr in pair_results) / n
    margin = sum(pr.positive_score - pr.negative_score for pr in pair_results) / n
    opt_acc, opt_t = _compute_optimal_accuracy(pair_results)
    avg_us = (total_time / total_calls * 1e6) if total_calls else 0.0

    return EvalResult(
        algorithm=name,
        discrimination_rate=disc_rate,
        avg_positive_score=avg_pos,
        avg_negative_score=avg_neg,
        margin=margin,
        optimal_accuracy=opt_acc,
        optimal_threshold=opt_t,
        num_columns=n,
        avg_time_us=avg_us,
    )


def _compute_optimal_accuracy(
    pair_results: list[PairResult],
) -> tuple[float, float]:
    """Sweep thresholds, classify each pair as accept/reject, find best accuracy."""
    all_scores: set[float] = {0.0, 1.0}
    for pr in pair_results:
        all_scores.add(pr.positive_score)
        all_scores.add(pr.negative_score)
        all_scores.add(pr.positive_score + 1e-9)
        all_scores.add(pr.positive_score - 1e-9)
        all_scores.add(pr.negative_score + 1e-9)
        all_scores.add(pr.negative_score - 1e-9)

    thresholds = sorted(all_scores)
    n = len(pair_results)
    total_pairs = 2 * n  # n positive + n negative

    best_acc = 0.0
    best_t = 0.0

    for t in thresholds:
        correct = 0
        for pr in pair_results:
            # Positive pair: should accept (score >= t)
            if pr.positive_score >= t:
                correct += 1
            # Negative pair: should reject (score < t)
            if pr.negative_score < t:
                correct += 1
        acc = correct / total_pairs
        if acc > best_acc:
            best_acc = acc
            best_t = t

    return best_acc, best_t


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDataProfilingEvaluation:
    """Evaluate matchers on positive/negative pair discrimination."""

    @pytest.fixture(scope="class")
    def raw_data(self) -> tuple[dict[str, list], dict[str, list]]:
        """Load raw values from both CSVs."""
        gsmbs = _load_raw(os.path.join(_DATA_DIR, "gsmbs.csv"))
        mfa = _load_raw(os.path.join(_DATA_DIR, "mfa.csv"))
        return gsmbs, mfa

    @pytest.fixture(scope="class")
    def evaluation_data(
        self, raw_data: tuple[dict[str, list], dict[str, list]]
    ) -> tuple[
        dict[str, DataProfile],
        dict[str, DataProfile],
        dict[str, DataProfile],
        list[str],
    ]:
        """Build profiles: GSMBS, MFA original, MFA transformed.

        Returns (gsmbs_profiles, mfa_orig_profiles, mfa_trans_profiles, included_cols).
        """
        gsmbs_raw, mfa_raw = raw_data
        common_cols = sorted(set(gsmbs_raw.keys()) & set(mfa_raw.keys()))

        gsmbs_profiles: dict[str, DataProfile] = {}
        mfa_orig_profiles: dict[str, DataProfile] = {}
        mfa_trans_profiles: dict[str, DataProfile] = {}
        included_cols: list[str] = []

        for col in common_cols:
            g_vals = gsmbs_raw[col]
            m_vals = mfa_raw[col]

            # Skip columns that are entirely null in either dataset
            g_non_null = [v for v in g_vals if v is not None]
            m_non_null = [v for v in m_vals if v is not None]
            if not g_non_null or not m_non_null:
                continue

            gp = _profile_column(col, g_vals)
            mp = _profile_column(col, m_vals)

            # Pick transformation based on the GSMBS profile
            transform = _assign_transformation(gp)
            m_transformed = transform(m_vals)

            # Check the transformation actually changed something
            m_trans_non_null = [v for v in m_transformed if v is not None]
            if m_trans_non_null == m_non_null:
                continue  # transformation was no-op, skip

            mp_trans = _profile_column(col, m_transformed)

            gsmbs_profiles[col] = gp
            mfa_orig_profiles[col] = mp
            mfa_trans_profiles[col] = mp_trans
            included_cols.append(col)

        return gsmbs_profiles, mfa_orig_profiles, mfa_trans_profiles, included_cols

    @pytest.fixture(scope="class")
    def results(
        self,
        evaluation_data: tuple[
            dict[str, DataProfile],
            dict[str, DataProfile],
            dict[str, DataProfile],
            list[str],
        ],
    ) -> list[EvalResult]:
        gsmbs_p, mfa_orig_p, mfa_trans_p, _ = evaluation_data

        algorithms: list[tuple[str, DataProfileMatcher]] = [
            ("Simple", SimpleDataProfileMatcher()),
            ("Distribution", DistributionProfileMatcher()),
            ("Wasserstein", WassersteinProfileMatcher()),
            ("Enhanced", EnhancedProfileMatcher()),
            (
                "Dist+Wasserstein",
                WeightedCombinationProfileMatcher([
                    (DistributionProfileMatcher(), 0.5),
                    (WassersteinProfileMatcher(), 0.5),
                ]),
            ),
        ]

        return [
            _evaluate_matcher(name, matcher, gsmbs_p, mfa_orig_p, mfa_trans_p)
            for name, matcher in algorithms
        ]

    # -- sanity checks --

    def test_profiles_generated(
        self,
        evaluation_data: tuple[
            dict[str, DataProfile],
            dict[str, DataProfile],
            dict[str, DataProfile],
            list[str],
        ],
    ):
        """Both datasets produce profiles, and we have enough testable columns."""
        gsmbs_p, mfa_orig_p, mfa_trans_p, cols = evaluation_data
        assert len(cols) >= 20, f"Only {len(cols)} testable columns"
        assert set(gsmbs_p.keys()) == set(mfa_orig_p.keys()) == set(mfa_trans_p.keys())

    def test_column_summary(
        self,
        raw_data: tuple[dict[str, list], dict[str, list]],
        evaluation_data: tuple[
            dict[str, DataProfile],
            dict[str, DataProfile],
            dict[str, DataProfile],
            list[str],
        ],
    ):
        """Report column counts."""
        gsmbs_raw, _ = raw_data
        _, _, _, cols = evaluation_data
        total = len(gsmbs_raw)
        print(f"\nTotal columns: {total}, Testable (non-null, transform applied): {len(cols)}")

    def test_type_detection(
        self,
        evaluation_data: tuple[
            dict[str, DataProfile],
            dict[str, DataProfile],
            dict[str, DataProfile],
            list[str],
        ],
    ):
        """Spot-check auto-detected types."""
        gsmbs_p, _, _, _ = evaluation_data
        if "Orig Loan Amount" in gsmbs_p:
            assert gsmbs_p["Orig Loan Amount"].dtype == "numeric"
        if "Property City" in gsmbs_p:
            assert gsmbs_p["Property City"].dtype == "string"

    # -- main evaluation --

    def test_comparison_table(self, results: list[EvalResult]):
        """Print the comparison table sorted by discrimination rate."""
        ranked = sorted(results, key=lambda r: -r.discrimination_rate)

        header = (
            f"{'Algorithm':<22} {'Disc%':>7} {'AvgPos':>7} {'AvgNeg':>7} "
            f"{'Margin':>7} {'OptAcc':>7} {'Thresh':>7} {'#Cols':>6} {'AvgTime':>10}"
        )
        sep = "-" * len(header)
        lines = [
            "\n" + sep,
            "DATA PROFILE MATCHING — FORMAT DISCRIMINATION EVALUATION",
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
                f"{r.algorithm:<22} {r.discrimination_rate:>7.1%} "
                f"{r.avg_positive_score:>7.3f} {r.avg_negative_score:>7.3f} "
                f"{r.margin:>+7.3f} {r.optimal_accuracy:>7.1%} "
                f"{r.optimal_threshold:>7.3f} {r.num_columns:>6} {time_str:>10}"
            )

        lines.append(sep)
        best = ranked[0]
        lines.append(
            f"Best: {best.algorithm} "
            f"(disc={best.discrimination_rate:.1%}, "
            f"margin={best.margin:+.3f}, "
            f"acc={best.optimal_accuracy:.1%} @ t={best.optimal_threshold:.3f})"
        )
        lines.append(sep)

        print("\n".join(lines))

    def test_best_beats_random(self, results: list[EvalResult]):
        """Best algorithm should discriminate well above 50% (random baseline)."""
        best = max(results, key=lambda r: r.discrimination_rate)
        assert best.discrimination_rate > 0.5, (
            f"Best algorithm ({best.algorithm}) disc={best.discrimination_rate:.1%} "
            f"should be above 50% random baseline"
        )

    def test_all_algorithms_produce_results(self, results: list[EvalResult]):
        """Each algorithm should produce results."""
        for r in results:
            assert r.num_columns > 0, f"{r.algorithm} produced no results"

    def test_positive_scores_above_negative(self, results: list[EvalResult]):
        """On average, positive scores should be higher than negative scores."""
        for r in results:
            assert r.avg_positive_score >= r.avg_negative_score, (
                f"{r.algorithm}: avg positive ({r.avg_positive_score:.3f}) "
                f"< avg negative ({r.avg_negative_score:.3f})"
            )
