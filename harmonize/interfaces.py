from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from harmonize.models import (
    Column,
    DataProfile,
    MappingResult,
    PastMapping,
    ValidationResult,
)


class StringMatcher(ABC):
    """Scores similarity between two strings (e.g. column names).

    Returns 0.0 for totally different strings, 1.0 for exact match.
    """

    @abstractmethod
    def score(self, s1: str, s2: str) -> float: ...


class DataProfiler(ABC):
    """Generates a statistical profile from column data."""

    @abstractmethod
    def profile(
        self, column_name: str, values: list[Any], dtype: str
    ) -> DataProfile: ...


class DataProfileMatcher(ABC):
    """Scores similarity between two data profiles.

    Returns 0.0 for completely different profiles, 1.0 for identical.
    """

    @abstractmethod
    def score(self, profile1: DataProfile, profile2: DataProfile) -> float: ...


class MemoryStore(ABC):
    """Stores and retrieves past approved mappings."""

    @abstractmethod
    def retrieve_mappings(
        self,
        target_columns: list[str],
        source_columns: list[str],
        industry: str | None = None,
    ) -> dict[str, list[PastMapping]]:
        """Retrieve past mappings keyed by target column name."""
        ...

    @abstractmethod
    def store_mapping(self, mapping: PastMapping) -> None: ...


class MappingValidator(ABC):
    """Validates a generated mapping against source data and target expectations."""

    @abstractmethod
    def validate(
        self,
        mapping: MappingResult,
        source_data: dict[str, list[Any]],
        target_profile: DataProfile | None = None,
    ) -> ValidationResult: ...


class LLMProvider(ABC):
    """Generates SQL mapping expressions using an LLM."""

    @abstractmethod
    def generate_mapping(
        self,
        target_column: Column,
        source_columns: list[Column],
        source_data: dict[str, list[Any]],
        past_mappings: list[PastMapping] | None = None,
    ) -> MappingResult: ...
