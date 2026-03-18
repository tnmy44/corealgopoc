from harmonize.models import MappingResult
from harmonize.validation import SimpleMappingValidator


class TestSimpleMappingValidator:
    def setup_method(self):
        self.validator = SimpleMappingValidator()

    def test_valid_mapping(self):
        mapping = MappingResult(
            target_column="fullname",
            expression="concat(firstname, lastname)",
            source_columns=["firstname", "lastname"],
            confidence=0.95,
            method="deterministic",
        )
        source_data = {
            "firstname": ["Alice", "Bob"],
            "lastname": ["Smith", "Jones"],
        }
        result = self.validator.validate(mapping, source_data)
        assert result.is_valid is True
        assert result.errors == []

    def test_missing_source_column(self):
        mapping = MappingResult(
            target_column="fullname",
            expression="concat(firstname, middlename)",
            source_columns=["firstname", "middlename"],
            confidence=0.8,
            method="llm",
        )
        source_data = {"firstname": ["Alice"]}
        result = self.validator.validate(mapping, source_data)
        assert result.is_valid is False
        assert any("middlename" in e for e in result.errors)

    def test_empty_expression(self):
        mapping = MappingResult(
            target_column="fullname",
            expression="",
            source_columns=[],
            confidence=0.0,
            method="llm",
        )
        result = self.validator.validate(mapping, {})
        assert result.is_valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_case_insensitive_column_check(self):
        mapping = MappingResult(
            target_column="fullname",
            expression="FirstName",
            source_columns=["FirstName"],
            confidence=0.9,
            method="deterministic",
        )
        source_data = {"firstname": ["Alice"]}
        result = self.validator.validate(mapping, source_data)
        assert result.is_valid is True
