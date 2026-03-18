from harmonize.llm import StubLLMProvider
from harmonize.models import Column


class TestStubLLMProvider:
    def setup_method(self):
        self.llm = StubLLMProvider()

    def test_generates_mapping_from_first_source(self):
        target = Column(name="fullname", dtype="string")
        sources = [
            Column(name="firstname", dtype="string"),
            Column(name="lastname", dtype="string"),
        ]
        data = {"firstname": ["Alice"], "lastname": ["Smith"]}
        result = self.llm.generate_mapping(target, sources, data)
        assert result.target_column == "fullname"
        assert result.method == "llm"
        assert result.expression == "firstname"
        assert result.source_columns == ["firstname"]

    def test_no_source_columns(self):
        target = Column(name="fullname", dtype="string")
        result = self.llm.generate_mapping(target, [], {})
        assert result.expression == "NULL"
        assert result.source_columns == []
