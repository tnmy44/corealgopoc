from __future__ import annotations

from typing import Any

from harmonize.interfaces import MappingValidator
from harmonize.models import DataProfile, MappingResult, ValidationResult


class SimpleMappingValidator(MappingValidator):
    """Basic validator that checks source columns exist in the provided data."""

    def validate(
        self,
        mapping: MappingResult,
        source_data: dict[str, list[Any]],
        target_profile: DataProfile | None = None,
    ) -> ValidationResult:
        errors: list[str] = []

        # Check all referenced source columns exist
        available = {k.lower() for k in source_data}
        for col in mapping.source_columns:
            if col.lower() not in available:
                errors.append(f"Source column '{col}' not found in source data")

        # Check expression is non-empty
        if not mapping.expression or not mapping.expression.strip():
            errors.append("Mapping expression is empty")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
