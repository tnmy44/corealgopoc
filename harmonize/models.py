from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Column:
    """A column in a source or target table."""

    name: str
    dtype: str  # "string", "numeric", "date", "boolean"
    description: str | None = None
    examples: list[str] | None = None


@dataclass
class Table:
    """A table with schema and sampled data."""

    name: str
    columns: list[Column]
    data: dict[str, list[Any]] = field(default_factory=dict)  # col_name -> values


@dataclass
class NumericStats:
    min_val: float
    max_val: float
    mean: float
    histogram: list[tuple[float, float, int]] = field(
        default_factory=list
    )  # (lower, upper, count)
    std: float = 0.0
    median: float = 0.0
    q25: float = 0.0
    q75: float = 0.0


@dataclass
class StringStats:
    min_length: int
    max_length: int
    avg_length: float
    most_common: list[tuple[str, int]] = field(
        default_factory=list
    )  # (value, count)
    pattern_distribution: list[tuple[str, int]] = field(
        default_factory=list
    )  # (pattern, count)


@dataclass
class BooleanStats:
    true_count: int
    false_count: int


@dataclass
class DataProfile:
    """Statistical profile of a column's data."""

    column_name: str
    dtype: str
    total_count: int
    null_count: int
    unique_count: int
    numeric_stats: NumericStats | None = None
    string_stats: StringStats | None = None
    boolean_stats: BooleanStats | None = None


@dataclass
class PastMapping:
    """A previously approved mapping retrieved from memory."""

    target_column: str
    expression: str
    source_columns: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    source_profiles: dict[str, DataProfile] = field(default_factory=dict)


@dataclass
class MappingResult:
    """A generated mapping for one target column."""

    target_column: str
    expression: str
    source_columns: list[str]
    confidence: float
    method: str  # "deterministic" or "llm"


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class HarmonisationInput:
    source_tables: list[Table]
    target_tables: list[Table]


@dataclass
class HarmonisationOutput:
    mappings: list[MappingResult]
    unmapped_columns: list[str] = field(default_factory=list)
