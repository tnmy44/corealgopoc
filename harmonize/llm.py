from __future__ import annotations

from typing import Any

from harmonize.interfaces import LLMProvider
from harmonize.models import Column, MappingResult, PastMapping


class StubLLMProvider(LLMProvider):
    """Stub that generates a simple direct-column mapping expression.

    For testing purposes only. Replace with a real LLM integration.
    """

    def generate_mapping(
        self,
        target_column: Column,
        source_columns: list[Column],
        source_data: dict[str, list[Any]],
        past_mappings: list[PastMapping] | None = None,
    ) -> MappingResult:
        # Naive: pick the first source column as the expression
        if source_columns:
            expr = source_columns[0].name
            src_cols = [source_columns[0].name]
        else:
            expr = "NULL"
            src_cols = []

        return MappingResult(
            target_column=target_column.name,
            expression=expr,
            source_columns=src_cols,
            confidence=0.5,
            method="llm",
        )
