# Harmonization Engine Architecture

## Overview

Column harmonization engine that maps source table columns to target table columns via SQL expressions. Combines deterministic memory-based matching with LLM fallback for robustness.

**Core Question**: Given new source data, can we reuse past SQL expressions safely?

## System Components

### 1. Domain Models (`models.py`)

**Data Structures**:
- `Column`, `Table` — Schema representation with metadata
- `DataProfile` — Statistical fingerprint of column data (dtype, null rate, unique count, type-specific distributions)
- `NumericStats`, `StringStats`, `BooleanStats` — Type-specific profile details
- `PastMapping` — Stored mapping with expression + source profiles
- `MappingResult` — Generated mapping with confidence + method
- `ValidationResult`, `HarmonisationInput`, `HarmonisationOutput` — I/O contracts

### 2. Interfaces (`interfaces.py`)

**Abstract Base Classes**:
- `StringMatcher` — Column name similarity (e.g., Levenshtein, fuzzy)
- `DataProfiler` — Generate statistical profiles from raw data
- `DataProfileMatcher` — Compare profiles for format compatibility
- `MemoryStore` — Persist and retrieve past mappings
- `MappingValidator` — Validate SQL expressions
- `LLMProvider` — Generate mappings via LLM when deterministic path fails

### 3. Orchestrator (`engine.py`)

**HarmonisationEngine** — Central coordinator with two-path decision logic:

```
For each target column:
  1. Retrieve past mappings from memory (source_table_name → target_column)
  2. For each past mapping:
      a. String match: compare column names (past source cols ↔ new source cols)
      b. Profile match: compare data distributions (past profiles ↔ new profiles)
      c. Combined score = (string_weight × string_score) + (profile_weight × profile_score)
  3. If score ≥ threshold → DETERMINISTIC path (reuse SQL expression)
  4. Else → LLM path (generate new mapping, store for future)
```

**EngineConfig**:
- `string_weight`, `profile_weight` — scoring weights (default 0.5 each)
- `match_threshold` — accept/reject cutoff (default 0.9)
- `use_profiles` — enable/disable profile matching

### 4. Implementations

#### String Matching (`string_matching.py`)
- `LevenshteinMatcher` — Edit distance normalized by max length
- `FuzzyMatcher` — Token-based fuzzy matching (uses fuzzywuzzy)

#### Data Profiling (`data_profiling.py`)
- **Profiler**: `PandasProfiler` — Auto-detect dtype, compute statistics (histograms, patterns, quartiles)
- **Matchers** (5 algorithms):
  - `SimpleDataProfileMatcher` — Null rate + unique rate + one type signal (baseline)
  - `DistributionProfileMatcher` — **Best discriminator** (90% format discrimination): weighted combination of null rate, unique rate, histogram intersection, range overlap, pattern Jaccard
  - `WassersteinProfileMatcher` — Earth-mover distance for numeric, pattern cosine for strings
  - `EnhancedProfileMatcher` — Kitchen-sink (more signals, worse discrimination due to noise)
  - `WeightedCombinationProfileMatcher` — Ensemble of multiple matchers

#### Memory (`memory.py`)
- `InMemoryStore` — Dict-based storage (ephemeral)
- `FileMemoryStore` — JSON persistence to disk

#### Validation (`validation.py`)
- `BasicValidator` — SQL syntax checks, forbidden keywords (DROP, DELETE)

#### LLM (`llm.py`)
- `OpenAIProvider` — GPT-based mapping generation with schema context

## Data Flow

```
┌─────────────────┐
│  User Request   │
│ (source/target) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│          HarmonisationEngine.harmonise()            │
│  ┌──────────────────────────────────────────────┐   │
│  │ For each target column:                      │   │
│  │   1. Profile source data (DataProfiler)      │   │
│  │   2. Retrieve past mappings (MemoryStore)    │   │
│  │   3. Score each candidate:                   │   │
│  │      - String match (StringMatcher)          │   │
│  │      - Profile match (DataProfileMatcher)    │   │
│  │   4. Decision:                               │   │
│  │      ┌─────────────────┬──────────────────┐  │   │
│  │      │  score ≥ 0.9?   │   score < 0.9?   │  │   │
│  │      │  DETERMINISTIC  │      LLM         │  │   │
│  │      │  (reuse expr)   │  (generate new)  │  │   │
│  │      └─────────────────┴──────────────────┘  │   │
│  │   5. Validate (MappingValidator)             │   │
│  │   6. Store if new (MemoryStore.store())      │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ HarmonisationOutput │
│ (mappings list) │
└─────────────────┘
```

## Key Design Decisions

### Interface-Implementation Separation
All core abstractions defined as ABCs in `interfaces.py`, enabling:
- Pluggable algorithms (swap matchers without changing engine)
- Easy testing with mocks
- Clear contracts for extensions

### Profile-Based Format Discrimination
**Problem**: "Same column name" ≠ "same format" (date format changes, unit scaling, encoding shifts)

**Solution**: Statistical profiles capture data distribution. Profile matcher answers: "Is this new data in the same format as past data?"

**Current best**: `DistributionProfileMatcher` achieves 90% discrimination, 82% optimal accuracy on real-world format transformations.

### Two-Path Strategy
- **Deterministic path** (fast, safe): Reuse proven expressions when data format unchanged
- **LLM path** (expensive, creative): Generate new mappings when format drifts or no past mapping exists
- **Threshold tuning**: `match_threshold=0.9` balances precision vs recall

### Neutral Profile Scores
When no past profiles exist, profile matcher returns 0.5 (neutral) rather than 0 or 1, preventing false confidence. This means string match alone can't reach the 0.9 threshold with default 0.5 weights.

## Testing

- **Unit tests** (`tests/test_*.py`): 40+ tests covering all components
- **Evaluation framework** (`tests/dataprofiling/test_eval_data_profiling.py`): Measures discrimination between same-format vs different-format pairs on real mortgage loan data (145 columns, 50 testable transformations)
- **Metrics**: Discrimination rate, optimal accuracy, margin, latency

## Technology

- **Python 3.9.6** (requires `from __future__ import annotations` for type hints)
- **Dependencies**: pandas, numpy, scipy, fuzzywuzzy, openai
- **Testing**: pytest 8.4.2
