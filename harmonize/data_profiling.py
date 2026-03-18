from __future__ import annotations

import math
from collections import Counter
from typing import Any


import numpy as np
from scipy.stats import wasserstein_distance as _scipy_wasserstein

from harmonize.interfaces import DataProfileMatcher, DataProfiler
from harmonize.models import (
    BooleanStats,
    DataProfile,
    NumericStats,
    StringStats,
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

_BOOLEAN_TRUE = frozenset({"1", "y", "yes", "true"})
_BOOLEAN_FALSE = frozenset({"0", "n", "no", "false"})
_BOOLEAN_ALL = _BOOLEAN_TRUE | _BOOLEAN_FALSE


def _extract_pattern(s: str) -> str:
    """Collapse consecutive digits -> 'N', consecutive letters -> 'A', keep rest.

    Examples:
        "9/30/2025"  -> "N/N/N"
        "Cash Out"   -> "A A"
        "1000250495" -> "N"
        "0.1"        -> "N.N"
    """
    result: list[str] = []
    prev_type: str | None = None
    for ch in s:
        if ch.isdigit():
            if prev_type != "d":
                result.append("N")
                prev_type = "d"
        elif ch.isalpha():
            if prev_type != "a":
                result.append("A")
                prev_type = "a"
        else:
            result.append(ch)
            prev_type = None
    return "".join(result)


def _detect_dtype(values: list[Any]) -> str:
    """Auto-detect column dtype from raw (string) values."""
    if not values:
        return "string"
    strs = [str(v).strip().lower() for v in values]
    unique_vals = set(strs)
    if unique_vals.issubset(_BOOLEAN_ALL):
        return "boolean"
    numeric_count = 0
    for s in strs:
        try:
            float(s.replace(",", ""))
            numeric_count += 1
        except (ValueError, TypeError):
            pass
    if numeric_count / len(strs) > 0.8:
        return "numeric"
    return "string"


def _clean_values(values: list[Any]) -> tuple[list[Any | None], int, int]:
    """Treat empty/whitespace strings as None. Returns (cleaned, total, null_count)."""
    cleaned: list[Any | None] = []
    null_count = 0
    for v in values:
        if v is None or (isinstance(v, str) and v.strip() == ""):
            cleaned.append(None)
            null_count += 1
        else:
            cleaned.append(v)
    return cleaned, len(cleaned), null_count


def _value_cosine(
    mc1: list[tuple[str, int]], mc2: list[tuple[str, int]]
) -> float:
    """Cosine similarity between two value-frequency vectors."""
    all_vals = sorted({v for v, _ in mc1} | {v for v, _ in mc2})
    if not all_vals:
        return 0.0
    d1, d2 = dict(mc1), dict(mc2)
    v1 = np.array([d1.get(v, 0) for v in all_vals], dtype=float)
    v2 = np.array([d2.get(v, 0) for v in all_vals], dtype=float)
    dot = float(np.dot(v1, v2))
    n1, n2 = float(np.linalg.norm(v1)), float(np.linalg.norm(v2))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


def _jaccard(s1: set, s2: set) -> float:
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def _histogram_intersection(
    h1: list[tuple[float, float, int]], h2: list[tuple[float, float, int]]
) -> float:
    """Intersection of two histograms with potentially different bin edges."""
    if not h1 or not h2:
        return 0.0

    # Gather all unique bin edges and create common bins
    edges: set[float] = set()
    for lo, hi, _ in h1:
        edges.add(lo)
        edges.add(hi)
    for lo, hi, _ in h2:
        edges.add(lo)
        edges.add(hi)
    sorted_edges = sorted(edges)

    if len(sorted_edges) < 2:
        return 1.0

    def _redistribute(
        hist: list[tuple[float, float, int]], common_edges: list[float]
    ) -> list[float]:
        densities: list[float] = []
        for i in range(len(common_edges) - 1):
            ce_lo, ce_hi = common_edges[i], common_edges[i + 1]
            if ce_hi <= ce_lo:
                densities.append(0.0)
                continue
            total = 0.0
            for h_lo, h_hi, h_count in hist:
                h_width = h_hi - h_lo
                if h_width <= 0:
                    continue
                ov_lo = max(ce_lo, h_lo)
                ov_hi = min(ce_hi, h_hi)
                if ov_hi > ov_lo:
                    total += h_count * (ov_hi - ov_lo) / h_width
            densities.append(total)
        return densities

    d1 = _redistribute(h1, sorted_edges)
    d2 = _redistribute(h2, sorted_edges)

    s1 = sum(d1) or 1.0
    s2 = sum(d2) or 1.0
    p1 = [d / s1 for d in d1]
    p2 = [d / s2 for d in d2]

    return sum(min(a, b) for a, b in zip(p1, p2))


# ---------------------------------------------------------------------------
# SimpleDataProfiler (original)
# ---------------------------------------------------------------------------

class SimpleDataProfiler(DataProfiler):
    """Single-pass profiler that computes basic statistics per column."""

    def __init__(self, top_k: int = 10, num_buckets: int = 10):
        self._top_k = top_k
        self._num_buckets = num_buckets

    def profile(
        self, column_name: str, values: list[Any], dtype: str
    ) -> DataProfile:
        total = len(values)
        nulls = sum(1 for v in values if v is None)
        non_null = [v for v in values if v is not None]
        unique = len(set(non_null))

        numeric_stats = None
        string_stats = None
        boolean_stats = None

        if dtype == "numeric":
            numeric_stats = self._profile_numeric(non_null)
        elif dtype == "string":
            string_stats = self._profile_string(non_null)
        elif dtype == "boolean":
            boolean_stats = self._profile_boolean(non_null)

        return DataProfile(
            column_name=column_name,
            dtype=dtype,
            total_count=total,
            null_count=nulls,
            unique_count=unique,
            numeric_stats=numeric_stats,
            string_stats=string_stats,
            boolean_stats=boolean_stats,
        )

    def _profile_numeric(self, values: list[Any]) -> NumericStats | None:
        if not values:
            return None
        nums = [float(v) for v in values]
        min_val = min(nums)
        max_val = max(nums)
        mean = sum(nums) / len(nums)
        histogram = self._build_histogram(nums, min_val, max_val)
        return NumericStats(
            min_val=min_val, max_val=max_val, mean=mean, histogram=histogram
        )

    def _build_histogram(
        self, values: list[float], min_val: float, max_val: float
    ) -> list[tuple[float, float, int]]:
        if min_val == max_val:
            return [(min_val, max_val, len(values))]
        bucket_width = (max_val - min_val) / self._num_buckets
        buckets: list[tuple[float, float, int]] = []
        for i in range(self._num_buckets):
            lower = min_val + i * bucket_width
            upper = lower + bucket_width
            count = sum(1 for v in values if lower <= v < upper)
            # Last bucket includes the upper bound
            if i == self._num_buckets - 1:
                count = sum(1 for v in values if lower <= v <= upper)
            buckets.append((lower, upper, count))
        return buckets

    def _profile_string(self, values: list[Any]) -> StringStats | None:
        if not values:
            return None
        strs = [str(v) for v in values]
        lengths = [len(s) for s in strs]
        counter = Counter(strs)
        most_common = counter.most_common(self._top_k)
        return StringStats(
            min_length=min(lengths),
            max_length=max(lengths),
            avg_length=sum(lengths) / len(lengths),
            most_common=most_common,
        )

    def _profile_boolean(self, values: list[Any]) -> BooleanStats | None:
        if not values:
            return None
        true_count = sum(1 for v in values if v is True)
        false_count = sum(1 for v in values if v is False)
        return BooleanStats(true_count=true_count, false_count=false_count)


# ---------------------------------------------------------------------------
# PandasProfiler — rich profiling with auto-type detection
# ---------------------------------------------------------------------------

class PandasProfiler(DataProfiler):
    """Rich profiler using numpy with auto-type detection.

    Pass dtype="auto" for automatic type detection from raw values.
    """

    def __init__(self, top_k: int = 20, num_buckets: int = 20):
        self._top_k = top_k
        self._num_buckets = num_buckets

    def profile(
        self, column_name: str, values: list[Any], dtype: str
    ) -> DataProfile:
        cleaned, total, null_count = _clean_values(values)
        non_null = [v for v in cleaned if v is not None]
        unique = len(set(str(v) for v in non_null))

        if dtype == "auto":
            dtype = _detect_dtype(non_null) if non_null else "string"

        numeric_stats = None
        string_stats = None
        boolean_stats = None

        if dtype == "numeric":
            numeric_stats = self._profile_numeric(non_null)
        elif dtype == "boolean":
            boolean_stats = self._profile_boolean(non_null)
        elif dtype == "string":
            string_stats = self._profile_string(non_null)

        return DataProfile(
            column_name=column_name,
            dtype=dtype,
            total_count=total,
            null_count=null_count,
            unique_count=unique,
            numeric_stats=numeric_stats,
            string_stats=string_stats,
            boolean_stats=boolean_stats,
        )

    def _profile_numeric(self, values: list[Any]) -> NumericStats | None:
        nums: list[float] = []
        for v in values:
            try:
                nums.append(float(str(v).replace(",", "")))
            except (ValueError, TypeError):
                pass
        if not nums:
            return None
        arr = np.array(nums)
        counts, edges = np.histogram(arr, bins=self._num_buckets)
        hist_tuples = [
            (float(edges[i]), float(edges[i + 1]), int(counts[i]))
            for i in range(len(counts))
        ]
        return NumericStats(
            min_val=float(arr.min()),
            max_val=float(arr.max()),
            mean=float(arr.mean()),
            histogram=hist_tuples,
            std=float(arr.std()),
            median=float(np.median(arr)),
            q25=float(np.percentile(arr, 25)),
            q75=float(np.percentile(arr, 75)),
        )

    def _profile_string(self, values: list[Any]) -> StringStats | None:
        if not values:
            return None
        strs = [str(v) for v in values]
        lengths = [len(s) for s in strs]
        counter = Counter(strs)
        most_common = counter.most_common(self._top_k)
        patterns = [_extract_pattern(s) for s in strs]
        pattern_counter = Counter(patterns)
        pattern_dist = pattern_counter.most_common(self._top_k)
        return StringStats(
            min_length=min(lengths),
            max_length=max(lengths),
            avg_length=sum(lengths) / len(lengths),
            most_common=most_common,
            pattern_distribution=pattern_dist,
        )

    def _profile_boolean(self, values: list[Any]) -> BooleanStats | None:
        if not values:
            return None
        true_count = sum(
            1 for v in values if str(v).strip().lower() in _BOOLEAN_TRUE
        )
        false_count = len(values) - true_count
        return BooleanStats(true_count=true_count, false_count=false_count)


# ---------------------------------------------------------------------------
# SimpleDataProfileMatcher (original)
# ---------------------------------------------------------------------------

class SimpleDataProfileMatcher(DataProfileMatcher):
    """Compares two profiles using null-rate, unique-rate, and type-specific stats."""

    def score(self, profile1: DataProfile, profile2: DataProfile) -> float:
        if profile1.dtype != profile2.dtype:
            return 0.0

        scores: list[float] = []

        # Null rate similarity
        nr1 = profile1.null_count / max(profile1.total_count, 1)
        nr2 = profile2.null_count / max(profile2.total_count, 1)
        scores.append(1.0 - abs(nr1 - nr2))

        # Unique rate similarity
        ur1 = profile1.unique_count / max(profile1.total_count - profile1.null_count, 1)
        ur2 = profile2.unique_count / max(profile2.total_count - profile2.null_count, 1)
        scores.append(1.0 - abs(ur1 - ur2))

        # Type-specific comparison
        if profile1.dtype == "numeric" and profile1.numeric_stats and profile2.numeric_stats:
            scores.append(self._compare_numeric(profile1.numeric_stats, profile2.numeric_stats))
        elif profile1.dtype == "string" and profile1.string_stats and profile2.string_stats:
            scores.append(self._compare_string(profile1.string_stats, profile2.string_stats))
        elif profile1.dtype == "boolean" and profile1.boolean_stats and profile2.boolean_stats:
            scores.append(self._compare_boolean(profile1.boolean_stats, profile2.boolean_stats))

        return sum(scores) / len(scores) if scores else 0.0

    def _compare_numeric(self, s1: NumericStats, s2: NumericStats) -> float:
        # Compare means relative to the combined range
        combined_range = max(s1.max_val, s2.max_val) - min(s1.min_val, s2.min_val)
        if combined_range == 0:
            return 1.0
        mean_diff = abs(s1.mean - s2.mean) / combined_range
        return max(0.0, 1.0 - mean_diff)

    def _compare_string(self, s1: StringStats, s2: StringStats) -> float:
        # Compare average lengths
        max_avg = max(s1.avg_length, s2.avg_length, 1.0)
        return 1.0 - abs(s1.avg_length - s2.avg_length) / max_avg

    def _compare_boolean(self, s1: BooleanStats, s2: BooleanStats) -> float:
        total1 = s1.true_count + s1.false_count
        total2 = s2.true_count + s2.false_count
        if total1 == 0 or total2 == 0:
            return 0.0
        rate1 = s1.true_count / total1
        rate2 = s2.true_count / total2
        return 1.0 - abs(rate1 - rate2)


# ---------------------------------------------------------------------------
# DistributionProfileMatcher — histogram intersection + value/pattern overlap
# ---------------------------------------------------------------------------

class DistributionProfileMatcher(DataProfileMatcher):
    """Compares profiles using histogram intersection and value/pattern overlap."""

    def score(self, profile1: DataProfile, profile2: DataProfile) -> float:
        if profile1.dtype != profile2.dtype:
            return 0.0

        scores: list[float] = []
        weights: list[float] = []

        # Null rate similarity
        nr1 = profile1.null_count / max(profile1.total_count, 1)
        nr2 = profile2.null_count / max(profile2.total_count, 1)
        scores.append(1.0 - abs(nr1 - nr2))
        weights.append(1.0)

        # Unique rate similarity
        nn1 = max(profile1.total_count - profile1.null_count, 1)
        nn2 = max(profile2.total_count - profile2.null_count, 1)
        ur1 = profile1.unique_count / nn1
        ur2 = profile2.unique_count / nn2
        scores.append(1.0 - abs(ur1 - ur2))
        weights.append(1.0)

        if profile1.dtype == "numeric":
            ns1, ns2 = profile1.numeric_stats, profile2.numeric_stats
            if ns1 and ns2:
                # Range overlap
                ov_lo = max(ns1.min_val, ns2.min_val)
                ov_hi = min(ns1.max_val, ns2.max_val)
                un_lo = min(ns1.min_val, ns2.min_val)
                un_hi = max(ns1.max_val, ns2.max_val)
                un_range = un_hi - un_lo
                if un_range > 0:
                    scores.append(max(0.0, (ov_hi - ov_lo) / un_range))
                else:
                    scores.append(1.0)
                weights.append(2.0)

                # Histogram intersection
                scores.append(_histogram_intersection(ns1.histogram, ns2.histogram))
                weights.append(3.0)

                # Mean similarity
                if un_range > 0:
                    scores.append(max(0.0, 1.0 - abs(ns1.mean - ns2.mean) / un_range))
                    weights.append(1.0)

        elif profile1.dtype == "string":
            ss1, ss2 = profile1.string_stats, profile2.string_stats
            if ss1 and ss2:
                # Value cosine similarity
                scores.append(_value_cosine(ss1.most_common, ss2.most_common))
                weights.append(3.0)

                # Pattern Jaccard
                pats1 = {p for p, _ in ss1.pattern_distribution}
                pats2 = {p for p, _ in ss2.pattern_distribution}
                scores.append(_jaccard(pats1, pats2))
                weights.append(2.0)

                # Length similarity
                max_avg = max(ss1.avg_length, ss2.avg_length, 1.0)
                scores.append(1.0 - abs(ss1.avg_length - ss2.avg_length) / max_avg)
                weights.append(1.0)

        elif profile1.dtype == "boolean":
            bs1, bs2 = profile1.boolean_stats, profile2.boolean_stats
            if bs1 and bs2:
                t1 = bs1.true_count + bs1.false_count
                t2 = bs2.true_count + bs2.false_count
                if t1 > 0 and t2 > 0:
                    scores.append(1.0 - abs(bs1.true_count / t1 - bs2.true_count / t2))
                    weights.append(2.0)

        if not weights:
            return 0.0
        return sum(s * w for s, w in zip(scores, weights)) / sum(weights)


# ---------------------------------------------------------------------------
# WassersteinProfileMatcher — earth-mover distance for numeric distributions
# ---------------------------------------------------------------------------

class WassersteinProfileMatcher(DataProfileMatcher):
    """Uses Wasserstein distance for numeric profiles, value/pattern overlap for strings."""

    def score(self, profile1: DataProfile, profile2: DataProfile) -> float:
        if profile1.dtype != profile2.dtype:
            return 0.0

        scores: list[float] = []
        weights: list[float] = []

        # Null rate
        nr1 = profile1.null_count / max(profile1.total_count, 1)
        nr2 = profile2.null_count / max(profile2.total_count, 1)
        scores.append(1.0 - abs(nr1 - nr2))
        weights.append(1.0)

        # Unique rate
        nn1 = max(profile1.total_count - profile1.null_count, 1)
        nn2 = max(profile2.total_count - profile2.null_count, 1)
        ur1 = profile1.unique_count / nn1
        ur2 = profile2.unique_count / nn2
        scores.append(1.0 - abs(ur1 - ur2))
        weights.append(1.0)

        if profile1.dtype == "numeric":
            ns1, ns2 = profile1.numeric_stats, profile2.numeric_stats
            if ns1 and ns2 and ns1.histogram and ns2.histogram:
                mid1 = [(lo + hi) / 2 for lo, hi, _ in ns1.histogram]
                w1 = [float(c) for _, _, c in ns1.histogram]
                mid2 = [(lo + hi) / 2 for lo, hi, _ in ns2.histogram]
                w2 = [float(c) for _, _, c in ns2.histogram]

                if sum(w1) > 0 and sum(w2) > 0:
                    dist = _scipy_wasserstein(mid1, mid2, w1, w2)
                    combined_range = (
                        max(ns1.max_val, ns2.max_val) - min(ns1.min_val, ns2.min_val)
                    )
                    if combined_range > 0:
                        scores.append(max(0.0, 1.0 - dist / combined_range))
                    else:
                        scores.append(1.0)
                    weights.append(4.0)

        elif profile1.dtype == "string":
            ss1, ss2 = profile1.string_stats, profile2.string_stats
            if ss1 and ss2:
                # Value cosine
                scores.append(_value_cosine(ss1.most_common, ss2.most_common))
                weights.append(3.0)

                # Pattern cosine (weighted by frequency, not just set overlap)
                scores.append(_value_cosine(ss1.pattern_distribution, ss2.pattern_distribution))
                weights.append(2.0)

                # Length similarity
                max_avg = max(ss1.avg_length, ss2.avg_length, 1.0)
                scores.append(1.0 - abs(ss1.avg_length - ss2.avg_length) / max_avg)
                weights.append(1.0)

        elif profile1.dtype == "boolean":
            bs1, bs2 = profile1.boolean_stats, profile2.boolean_stats
            if bs1 and bs2:
                t1 = bs1.true_count + bs1.false_count
                t2 = bs2.true_count + bs2.false_count
                if t1 > 0 and t2 > 0:
                    scores.append(1.0 - abs(bs1.true_count / t1 - bs2.true_count / t2))
                    weights.append(2.0)

        if not weights:
            return 0.0
        return sum(s * w for s, w in zip(scores, weights)) / sum(weights)


# ---------------------------------------------------------------------------
# EnhancedProfileMatcher — best combination of all signals
# ---------------------------------------------------------------------------

class EnhancedProfileMatcher(DataProfileMatcher):
    """Combines histogram intersection, wasserstein distance, value overlap,
    pattern comparison, cardinality, and std comparison for maximum discrimination."""

    def score(self, profile1: DataProfile, profile2: DataProfile) -> float:
        if profile1.dtype != profile2.dtype:
            return 0.0

        scores: list[float] = []
        weights: list[float] = []

        # Null rate similarity
        nr1 = profile1.null_count / max(profile1.total_count, 1)
        nr2 = profile2.null_count / max(profile2.total_count, 1)
        scores.append(1.0 - abs(nr1 - nr2))
        weights.append(1.0)

        # Cardinality similarity (log-scale comparison)
        u1 = max(profile1.unique_count, 1)
        u2 = max(profile2.unique_count, 1)
        log_ratio = abs(math.log(u1) - math.log(u2))
        card_sim = max(0.0, 1.0 - log_ratio / 3.0)  # 3.0 = ~20x ratio -> 0
        scores.append(card_sim)
        weights.append(2.0)

        if profile1.dtype == "numeric":
            ns1, ns2 = profile1.numeric_stats, profile2.numeric_stats
            if ns1 and ns2:
                un_lo = min(ns1.min_val, ns2.min_val)
                un_hi = max(ns1.max_val, ns2.max_val)
                un_range = un_hi - un_lo

                # Histogram intersection
                scores.append(_histogram_intersection(ns1.histogram, ns2.histogram))
                weights.append(3.0)

                # Wasserstein distance
                if ns1.histogram and ns2.histogram:
                    mid1 = [(lo + hi) / 2 for lo, hi, _ in ns1.histogram]
                    w1 = [float(c) for _, _, c in ns1.histogram]
                    mid2 = [(lo + hi) / 2 for lo, hi, _ in ns2.histogram]
                    w2 = [float(c) for _, _, c in ns2.histogram]
                    if sum(w1) > 0 and sum(w2) > 0:
                        dist = _scipy_wasserstein(mid1, mid2, w1, w2)
                        if un_range > 0:
                            scores.append(max(0.0, 1.0 - dist / un_range))
                        else:
                            scores.append(1.0)
                        weights.append(3.0)

                # Std comparison
                max_std = max(ns1.std, ns2.std, 1e-9)
                std_sim = 1.0 - abs(ns1.std - ns2.std) / max_std
                scores.append(max(0.0, std_sim))
                weights.append(2.0)

                # Quartile comparison
                if un_range > 0:
                    q_sims = [
                        1.0 - abs(ns1.q25 - ns2.q25) / un_range,
                        1.0 - abs(ns1.median - ns2.median) / un_range,
                        1.0 - abs(ns1.q75 - ns2.q75) / un_range,
                    ]
                    scores.append(max(0.0, sum(q_sims) / 3))
                    weights.append(2.0)

        elif profile1.dtype == "string":
            ss1, ss2 = profile1.string_stats, profile2.string_stats
            if ss1 and ss2:
                # Value cosine similarity (strongest signal for strings)
                scores.append(_value_cosine(ss1.most_common, ss2.most_common))
                weights.append(4.0)

                # Pattern cosine (frequency-weighted)
                scores.append(
                    _value_cosine(ss1.pattern_distribution, ss2.pattern_distribution)
                )
                weights.append(2.0)

                # Length similarity
                max_avg = max(ss1.avg_length, ss2.avg_length, 1.0)
                scores.append(1.0 - abs(ss1.avg_length - ss2.avg_length) / max_avg)
                weights.append(1.0)

        elif profile1.dtype == "boolean":
            bs1, bs2 = profile1.boolean_stats, profile2.boolean_stats
            if bs1 and bs2:
                t1 = bs1.true_count + bs1.false_count
                t2 = bs2.true_count + bs2.false_count
                if t1 > 0 and t2 > 0:
                    scores.append(1.0 - abs(bs1.true_count / t1 - bs2.true_count / t2))
                    weights.append(2.0)

        if not weights:
            return 0.0
        return sum(s * w for s, w in zip(scores, weights)) / sum(weights)


# ---------------------------------------------------------------------------
# WeightedCombinationProfileMatcher
# ---------------------------------------------------------------------------

class WeightedCombinationProfileMatcher(DataProfileMatcher):
    """Combines multiple profile matchers with configurable weights."""

    def __init__(self, matchers: list[tuple[DataProfileMatcher, float]]) -> None:
        self._matchers = matchers

    def score(self, profile1: DataProfile, profile2: DataProfile) -> float:
        total = 0.0
        weight_sum = 0.0
        for matcher, weight in self._matchers:
            total += matcher.score(profile1, profile2) * weight
            weight_sum += weight
        return total / weight_sum if weight_sum > 0 else 0.0
