from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from harmonize.interfaces import (
    DataProfileMatcher,
    DataProfiler,
    LLMProvider,
    MappingValidator,
    MemoryStore,
    StringMatcher,
)
from harmonize.models import (
    Column,
    DataProfile,
    HarmonisationInput,
    HarmonisationOutput,
    MappingResult,
    PastMapping,
    Table,
)

logger = logging.getLogger(__name__)

MappingCallback = Callable[[MappingResult], None]


@dataclass
class EngineConfig:
    """Tunable thresholds for the harmonisation engine."""

    deterministic_threshold: float = 0.9
    string_match_weight: float = 0.5
    profile_match_weight: float = 0.5


class HarmonisationEngine:
    """Orchestrates the full harmonisation algorithm.

    Pipeline for each target column:
      1. Retrieve past mappings from memory
      2. Score each past mapping (string similarity + profile similarity)
      3. If best score >= threshold → use deterministic mapping, validate it
      4. Otherwise → fall back to LLM
      5. Emit mapping result via callback (for streaming)
    """

    def __init__(
        self,
        string_matcher: StringMatcher,
        data_profiler: DataProfiler,
        profile_matcher: DataProfileMatcher,
        memory_store: MemoryStore,
        validator: MappingValidator,
        llm_provider: LLMProvider,
        config: EngineConfig | None = None,
    ) -> None:
        self._string_matcher = string_matcher
        self._data_profiler = data_profiler
        self._profile_matcher = profile_matcher
        self._memory = memory_store
        self._validator = validator
        self._llm = llm_provider
        self._config = config or EngineConfig()

    def run(
        self,
        input: HarmonisationInput,
        on_mapping: MappingCallback | None = None,
    ) -> HarmonisationOutput:
        """Run the full harmonisation pipeline."""
        # Flatten source columns and data across all source tables
        all_source_columns, all_source_data = self._flatten_sources(
            input.source_tables
        )

        # Profile all source columns
        source_profiles = self._profile_sources(all_source_columns, all_source_data)

        # Collect all target columns
        all_target_columns = self._flatten_target_columns(input.target_tables)
        target_col_names = [c.name for c in all_target_columns]
        source_col_names = [c.name for c in all_source_columns]

        # Retrieve past mappings from memory
        past_mappings = self._memory.retrieve_mappings(
            target_columns=target_col_names,
            source_columns=source_col_names,
        )

        mappings: list[MappingResult] = []
        unmapped: list[str] = []

        for target_col in all_target_columns:
            result = self._harmonise_column(
                target_col=target_col,
                source_columns=all_source_columns,
                source_data=all_source_data,
                source_profiles=source_profiles,
                past_mappings=past_mappings.get(target_col.name.lower(), []),
            )

            if result is not None:
                mappings.append(result)
                if on_mapping:
                    on_mapping(result)
            else:
                unmapped.append(target_col.name)

        return HarmonisationOutput(mappings=mappings, unmapped_columns=unmapped)

    def _harmonise_column(
        self,
        target_col: Column,
        source_columns: list[Column],
        source_data: dict[str, list[Any]],
        source_profiles: dict[str, DataProfile],
        past_mappings: list[PastMapping],
    ) -> MappingResult | None:
        """Try deterministic matching first, then fall back to LLM."""
        # --- Deterministic path ---
        best_mapping, best_score = self._find_best_past_mapping(
            target_col, source_columns, source_data, source_profiles, past_mappings
        )

        if best_mapping and best_score >= self._config.deterministic_threshold:
            result = self._apply_past_mapping(best_mapping, source_columns, best_score)
            validation = self._validator.validate(result, source_data)
            if validation.is_valid:
                logger.info(
                    "Deterministic match for '%s' (score=%.2f)",
                    target_col.name,
                    best_score,
                )
                return result
            else:
                logger.info(
                    "Deterministic match for '%s' failed validation: %s",
                    target_col.name,
                    validation.errors,
                )

        # --- LLM fallback ---
        logger.info("Falling back to LLM for '%s'", target_col.name)
        result = self._llm.generate_mapping(
            target_column=target_col,
            source_columns=source_columns,
            source_data=source_data,
            past_mappings=past_mappings or None,
        )
        return result

    def _find_best_past_mapping(
        self,
        target_col: Column,
        source_columns: list[Column],
        source_data: dict[str, list[Any]],
        source_profiles: dict[str, DataProfile],
        past_mappings: list[PastMapping],
    ) -> tuple[PastMapping | None, float]:
        """Score all past mappings and return the best one with its score."""
        best: PastMapping | None = None
        best_score = 0.0
        source_col_names = {c.name.lower() for c in source_columns}

        for pm in past_mappings:
            score = self._score_past_mapping(
                pm, source_col_names, source_profiles
            )
            if score > best_score:
                best_score = score
                best = pm

        return best, best_score

    def _score_past_mapping(
        self,
        pm: PastMapping,
        source_col_names: set[str],
        source_profiles: dict[str, DataProfile],
    ) -> float:
        """Score a past mapping based on column name matching and profile similarity."""
        cfg = self._config

        # --- String match: do all past source columns have a match in current sources? ---
        if not pm.source_columns:
            return 0.0

        col_scores: list[float] = []
        for past_col in pm.source_columns:
            best_col_score = max(
                (
                    self._string_matcher.score(past_col, current_col)
                    for current_col in source_col_names
                ),
                default=0.0,
            )
            col_scores.append(best_col_score)
        string_score = sum(col_scores) / len(col_scores)

        # --- Profile match ---
        profile_score = self._compute_profile_score(pm, source_profiles)

        # Weighted combination
        total = (
            cfg.string_match_weight * string_score
            + cfg.profile_match_weight * profile_score
        )
        weight_sum = cfg.string_match_weight + cfg.profile_match_weight
        return total / weight_sum if weight_sum > 0 else 0.0

    def _compute_profile_score(
        self,
        pm: PastMapping,
        source_profiles: dict[str, DataProfile],
    ) -> float:
        """Compare profiles of past mapping's source columns against current source profiles."""
        if not pm.source_profiles:
            # No past profiles available — rely solely on string matching
            return 0.5  # neutral score

        scores: list[float] = []
        for past_col, past_profile in pm.source_profiles.items():
            # Find the best-matching current source profile
            best = 0.0
            for current_name, current_profile in source_profiles.items():
                name_sim = self._string_matcher.score(past_col, current_name)
                if name_sim > 0.5:
                    profile_sim = self._profile_matcher.score(
                        past_profile, current_profile
                    )
                    best = max(best, profile_sim)
            scores.append(best)

        return sum(scores) / len(scores) if scores else 0.5

    def _apply_past_mapping(
        self,
        pm: PastMapping,
        source_columns: list[Column],
        score: float,
    ) -> MappingResult:
        """Convert a PastMapping into a MappingResult, remapping column names."""
        source_col_names = [c.name for c in source_columns]

        # Remap: for each past source column, find the closest current source column
        remapped_cols: list[str] = []
        name_map: dict[str, str] = {}
        for past_col in pm.source_columns:
            best_match = max(
                source_col_names,
                key=lambda sc: self._string_matcher.score(past_col, sc),
            )
            remapped_cols.append(best_match)
            name_map[past_col] = best_match

        # Rewrite the expression with remapped column names
        expression = pm.expression
        for old_name, new_name in name_map.items():
            expression = expression.replace(old_name, new_name)

        return MappingResult(
            target_column=pm.target_column,
            expression=expression,
            source_columns=remapped_cols,
            confidence=score,
            method="deterministic",
        )

    # --- Helpers ---

    @staticmethod
    def _flatten_sources(
        tables: list[Table],
    ) -> tuple[list[Column], dict[str, list[Any]]]:
        columns: list[Column] = []
        data: dict[str, list[Any]] = {}
        seen: set[str] = set()
        for table in tables:
            for col in table.columns:
                key = f"{table.name}.{col.name}"
                if key not in seen:
                    seen.add(key)
                    columns.append(col)
                    data[col.name] = table.data.get(col.name, [])
        return columns, data

    @staticmethod
    def _flatten_target_columns(tables: list[Table]) -> list[Column]:
        columns: list[Column] = []
        for table in tables:
            columns.extend(table.columns)
        return columns

    def _profile_sources(
        self,
        columns: list[Column],
        data: dict[str, list[Any]],
    ) -> dict[str, DataProfile]:
        profiles: dict[str, DataProfile] = {}
        for col in columns:
            values = data.get(col.name, [])
            profiles[col.name] = self._data_profiler.profile(
                col.name, values, col.dtype
            )
        return profiles
