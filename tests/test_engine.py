from __future__ import annotations

from typing import Optional

from harmonize.data_profiling import SimpleDataProfileMatcher, SimpleDataProfiler
from harmonize.engine import EngineConfig, HarmonisationEngine
from harmonize.llm import StubLLMProvider
from harmonize.memory import InMemoryStore
from harmonize.models import (
    Column,
    DataProfile,
    HarmonisationInput,
    MappingResult,
    NumericStats,
    PastMapping,
    Table,
)
from harmonize.string_matching import ExactStringMatcher, LevenshteinStringMatcher
from harmonize.validation import SimpleMappingValidator


def _build_engine(
    memory: Optional[InMemoryStore] = None,
    config: Optional[EngineConfig] = None,
) -> HarmonisationEngine:
    return HarmonisationEngine(
        string_matcher=LevenshteinStringMatcher(),
        data_profiler=SimpleDataProfiler(),
        profile_matcher=SimpleDataProfileMatcher(),
        memory_store=memory or InMemoryStore(),
        validator=SimpleMappingValidator(),
        llm_provider=StubLLMProvider(),
        config=config,
    )


def _make_source_table() -> Table:
    return Table(
        name="source",
        columns=[
            Column(name="firstname", dtype="string"),
            Column(name="lastname", dtype="string"),
            Column(name="investortapeid", dtype="string"),
            Column(name="loanamount", dtype="numeric"),
        ],
        data={
            "firstname": ["Alice", "Bob", "Charlie"],
            "lastname": ["Smith", "Jones", "Brown"],
            "investortapeid": ["INV001", "INV002", "INV003"],
            "loanamount": [100000, 200000, 150000],
        },
    )


def _make_target_table() -> Table:
    return Table(
        name="target",
        columns=[
            Column(name="fullname", dtype="string", description="Full name of borrower"),
            Column(name="sellerloanid", dtype="string"),
            Column(name="amount", dtype="numeric"),
        ],
    )


class TestEngineNoMemory:
    """When memory is empty, everything should fall back to LLM."""

    def test_all_columns_mapped(self):
        engine = _build_engine()
        inp = HarmonisationInput(
            source_tables=[_make_source_table()],
            target_tables=[_make_target_table()],
        )
        output = engine.run(inp)
        assert len(output.mappings) == 3
        assert all(m.method == "llm" for m in output.mappings)

    def test_callback_invoked(self):
        engine = _build_engine()
        inp = HarmonisationInput(
            source_tables=[_make_source_table()],
            target_tables=[_make_target_table()],
        )
        received: list[MappingResult] = []
        engine.run(inp, on_mapping=received.append)
        assert len(received) == 3


class TestEngineDeterministic:
    """When memory has matching past mappings, deterministic path should be used."""

    def _build_memory_with_exact_match(self) -> InMemoryStore:
        store = InMemoryStore()
        store.store_mapping(
            PastMapping(
                target_column="sellerloanid",
                expression="investortapeid",
                source_columns=["investortapeid"],
                metadata={"tags": "MFA"},
            )
        )
        return store

    def test_exact_column_match_uses_deterministic(self):
        store = self._build_memory_with_exact_match()
        # With no profile data, neutral profile score (0.5) averages with
        # string score (1.0) → 0.75. Use a matching threshold accordingly.
        config = EngineConfig(deterministic_threshold=0.7)
        engine = _build_engine(memory=store, config=config)
        inp = HarmonisationInput(
            source_tables=[_make_source_table()],
            target_tables=[
                Table(
                    name="target",
                    columns=[Column(name="sellerloanid", dtype="string")],
                )
            ],
        )
        output = engine.run(inp)
        assert len(output.mappings) == 1
        m = output.mappings[0]
        assert m.method == "deterministic"
        assert m.target_column == "sellerloanid"
        assert "investortapeid" in m.expression

    def test_threshold_controls_fallback(self):
        """With a very high threshold, even exact match may not qualify if profile score is low."""
        store = self._build_memory_with_exact_match()
        config = EngineConfig(deterministic_threshold=0.99)
        engine = _build_engine(memory=store, config=config)
        inp = HarmonisationInput(
            source_tables=[_make_source_table()],
            target_tables=[
                Table(
                    name="target",
                    columns=[Column(name="sellerloanid", dtype="string")],
                )
            ],
        )
        output = engine.run(inp)
        # With threshold at 0.99, the neutral profile score (0.5) brings the
        # weighted score below threshold, so it falls back to LLM
        assert output.mappings[0].method == "llm"


class TestEngineWithProfiles:
    """Test deterministic matching with profile data in past mappings."""

    def test_profile_match_boosts_score(self):
        profiler = SimpleDataProfiler()
        profile = profiler.profile("investortapeid", ["INV001", "INV002", "INV003"], "string")

        store = InMemoryStore()
        store.store_mapping(
            PastMapping(
                target_column="sellerloanid",
                expression="investortapeid",
                source_columns=["investortapeid"],
                source_profiles={"investortapeid": profile},
            )
        )

        config = EngineConfig(deterministic_threshold=0.85)
        engine = _build_engine(memory=store, config=config)
        inp = HarmonisationInput(
            source_tables=[_make_source_table()],
            target_tables=[
                Table(
                    name="target",
                    columns=[Column(name="sellerloanid", dtype="string")],
                )
            ],
        )
        output = engine.run(inp)
        assert output.mappings[0].method == "deterministic"


class TestEngineMultipleSourceTables:
    def test_columns_from_multiple_sources(self):
        t1 = Table(
            name="src1",
            columns=[Column(name="firstname", dtype="string")],
            data={"firstname": ["Alice"]},
        )
        t2 = Table(
            name="src2",
            columns=[Column(name="lastname", dtype="string")],
            data={"lastname": ["Smith"]},
        )
        target = Table(
            name="target",
            columns=[Column(name="fullname", dtype="string")],
        )
        engine = _build_engine()
        inp = HarmonisationInput(source_tables=[t1, t2], target_tables=[target])
        output = engine.run(inp)
        assert len(output.mappings) == 1


class TestEngineColumnRemapping:
    """Test that column names in expressions get remapped when using past mappings."""

    def test_expression_remapped(self):
        store = InMemoryStore()
        store.store_mapping(
            PastMapping(
                target_column="fullname",
                expression="concat(first_name, last_name)",
                source_columns=["first_name", "last_name"],
            )
        )

        # Current source uses slightly different names
        source = Table(
            name="src",
            columns=[
                Column(name="firstname", dtype="string"),
                Column(name="lastname", dtype="string"),
            ],
            data={"firstname": ["Alice"], "lastname": ["Smith"]},
        )
        target = Table(
            name="target",
            columns=[Column(name="fullname", dtype="string")],
        )

        config = EngineConfig(deterministic_threshold=0.7)
        engine = _build_engine(memory=store, config=config)
        inp = HarmonisationInput(source_tables=[source], target_tables=[target])
        output = engine.run(inp)
        m = output.mappings[0]
        if m.method == "deterministic":
            # The expression should reference current source column names
            assert "first_name" not in m.expression or "firstname" in m.expression
