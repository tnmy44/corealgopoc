from __future__ import annotations

import re
from typing import Any

import numpy as np
from rapidfuzz.distance import JaroWinkler, LCSseq, Levenshtein
from sentence_transformers import SentenceTransformer

from harmonize.interfaces import StringMatcher


def _normalize(s: str) -> str:
    """Lowercase, strip, collapse whitespace and common separators."""
    s = s.lower().strip()
    for ch in ("_", "-", ".", " "):
        s = s.replace(ch, "")
    return s


def _tokenize(s: str) -> list[str]:
    """Split into lowercase tokens on whitespace and common separators."""
    return [t for t in re.split(r"[\s_\-./(),%:]+", s.lower()) if t]


class ExactStringMatcher(StringMatcher):
    """Returns 1.0 if normalized strings are equal, else 0.0."""

    def score(self, s1: str, s2: str) -> float:
        return 1.0 if _normalize(s1) == _normalize(s2) else 0.0


class LevenshteinStringMatcher(StringMatcher):
    """Similarity based on normalised Levenshtein edit distance."""

    def score(self, s1: str, s2: str) -> float:
        return Levenshtein.normalized_similarity(_normalize(s1), _normalize(s2))


class JaroWinklerMatcher(StringMatcher):
    """Jaro-Winkler similarity on normalised strings. Good for short identifiers."""

    def __init__(self, prefix_weight: float = 0.1) -> None:
        self._prefix_weight = prefix_weight

    def score(self, s1: str, s2: str) -> float:
        return JaroWinkler.similarity(
            _normalize(s1), _normalize(s2), prefix_weight=self._prefix_weight
        )


class TokenSetMatcher(StringMatcher):
    """Jaccard similarity on token sets. Handles word reordering well."""

    def score(self, s1: str, s2: str) -> float:
        t1 = set(_tokenize(s1))
        t2 = set(_tokenize(s2))
        if not t1 and not t2:
            return 1.0
        if not t1 or not t2:
            return 0.0
        return len(t1 & t2) / len(t1 | t2)


class SubsequenceMatcher(StringMatcher):
    """Longest common subsequence ratio on normalised strings."""

    def score(self, s1: str, s2: str) -> float:
        return LCSseq.normalized_similarity(_normalize(s1), _normalize(s2))


class SemanticMatcher(StringMatcher):
    """Cosine similarity on sentence-transformer embeddings.

    Uses all-MiniLM-L6-v2 by default — a 33M-param model that runs fast on CPU
    and captures semantic equivalences (e.g. "Purchase Price" ↔ "Sales Price").
    Embeddings are cached so repeated lookups are free.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model = SentenceTransformer(model_name)
        self._cache: dict[str, Any] = {}

    def _embed(self, text: str) -> Any:
        key = text.lower().strip()
        if key not in self._cache:
            self._cache[key] = self._model.encode(
                key, normalize_embeddings=True
            )
        return self._cache[key]

    def score(self, s1: str, s2: str) -> float:
        e1 = self._embed(s1)
        e2 = self._embed(s2)
        return float(np.dot(e1, e2))


class WeightedCombinationMatcher(StringMatcher):
    """Combines multiple matchers with configurable weights."""

    def __init__(self, matchers: list[tuple[StringMatcher, float]]) -> None:
        self._matchers = matchers

    def score(self, s1: str, s2: str) -> float:
        total = 0.0
        weight_sum = 0.0
        for matcher, weight in self._matchers:
            total += matcher.score(s1, s2) * weight
            weight_sum += weight
        return total / weight_sum if weight_sum > 0 else 0.0
