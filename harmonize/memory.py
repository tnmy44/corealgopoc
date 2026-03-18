from __future__ import annotations

from harmonize.interfaces import MemoryStore
from harmonize.models import PastMapping


class InMemoryStore(MemoryStore):
    """Simple in-memory store for past mappings. Useful for testing."""

    def __init__(self) -> None:
        self._mappings: list[PastMapping] = []

    def store_mapping(self, mapping: PastMapping) -> None:
        self._mappings.append(mapping)

    def retrieve_mappings(
        self,
        target_columns: list[str],
        source_columns: list[str],
        industry: str | None = None,
    ) -> dict[str, list[PastMapping]]:
        target_set = {tc.lower() for tc in target_columns}
        result: dict[str, list[PastMapping]] = {}
        for mapping in self._mappings:
            if mapping.target_column.lower() in target_set:
                key = mapping.target_column.lower()
                result.setdefault(key, []).append(mapping)
        return result
