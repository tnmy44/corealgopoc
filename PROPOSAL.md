# Harmonisation Algorithm Proposal

## Problem

Given current source tables and a target CDM schema, produce a SQL query that transforms the sources into the target — by learning from past pipelines stored in a Knowledge Graph (KG).

Two hard sub-problems:

1. **Query Adaptation** — A past pipeline's SQL targeted different source tables (different names, splits, joins). Rewrite it for current sources.
2. **Query Stitching** — Each target column may be resolved from a different past pipeline. The per-column queries may have incompatible structures (different JOINs, GROUP BYs). Combine them into one final query.

## Design Principles

- **Deterministic first, LLM last.** Exhaust string matching, data profiling, KG lookups, and structural merging before invoking an LLM. This minimises token cost and makes results reproducible.
- **Per-column resolution, group-level stitching.** Resolve each column independently (parallelisable, streamable), then group by structural compatibility before merging.
- **Learn expressions and joins separately.** The best pipeline for a column's business logic (expression) may differ from the best source of join conditions between tables. These are independent concerns.

## Architecture

### Phase 1 — Pipeline Discovery

Query the KG with current source schemas + target schema. Return a ranked set of candidate past pipelines with metadata: source schemas, target columns, full SQL, per-column pruned SQL, lineage.

Scoring combines:
- Source table similarity (name + schema overlap)
- Target column coverage (how many target columns this pipeline produced)
- Data profile similarity (value distributions, null rates, cardinality)

This is a coarse filter — returns top-K candidates, not a single winner.

### Phase 2 — Per-Column Resolution

For each target column, independently and in parallel:

1. **Select best pipeline** — Score each candidate pipeline for this specific column (column name match + expression pattern + data profile of involved source columns).
2. **Extract signature** — Parse the pipeline's pruned SQL for this column into a structured `ColumnMapping`:
   ```
   ColumnMapping:
     target_column:  "person_name"
     expression:     "CONCAT(p.first_name, ' ', p.last_name)"
     source_tables:  [{name: "persons", alias: "p", columns: ["first_name", "last_name"]}]
     joins:          [{type: LEFT, table: "persons", alias: "p", on: "t.pid = p.id"}]
     filters:        []
     group_by:       []
     pipeline:       "pipeline_A"
     confidence:     0.92
   ```
   This requires predicate pushdown: trace backwards through the past query's DAG to find the *minimal* operations needed for this column, stripping pass-through operations that existed for other columns.
3. **Adapt references** — Replace past table/column names with current source equivalents using string matching + data profiling. After this step, no past-pipeline references remain.

**Streamable**: Each resolved column can be sent to the frontend immediately.

**Fallback**: If no pipeline scores above threshold for a column, mark it as `unresolved` for Phase 5.

### Phase 3 — Signature Grouping

Group the resolved columns by structural compatibility of their adapted signatures.

**Signature** = the query skeleton minus the SELECT expression: `{source_tables, joins, filters, group_by}`.

Grouping proceeds in phases of decreasing strictness:

1. **Exact match** — Identical skeletons → same group.
2. **Superset absorption** — One skeleton is a strict superset of another (e.g., column A needs `FROM t` but column B needs `FROM t LEFT JOIN p`). The simpler column can use the more complete skeleton without affecting its result. → Merge into the superset group.
3. **Compatible merge** — Same tables, different GROUP BY or filters. GROUP BY clauses can be unioned (add all group expressions); filters can be ANDed if semantically compatible. → Merge with clause combination.
4. **Ungroupable** — Fundamentally different table sets with no overlap. → Kept separate for Phase 4.

After grouping, each group has a single merged skeleton + a list of SELECT expressions.

### Phase 4 — Cross-Group Merging (Stitching)

Merge the signature groups into one (or few) final queries. Attempted in order:

1. **Historical co-occurrence** — If two groups' columns originally came from the same past pipeline, use that pipeline's query structure to merge them. The past SQL already demonstrated how these tables relate.

2. **KG join lookup** — Query the KG: "has any past pipeline ever joined table set A with table set B?" If yes, extract the join conditions from that pipeline. The pipeline chosen for join conditions can differ from the ones chosen for expressions.

3. **PK/FK inference** — Check warehouse metadata or data analysis (unique columns, foreign key patterns) for join keys between the disjoint table sets. Default to LEFT JOIN to avoid losing rows.

4. **Schema-based LLM** — Give the LLM just the output schemas of the two CTEs + source table names. Ask it to infer a merge condition. Lightweight — small prompt.

5. **Full LLM merge** — Give the LLM the full queries for both groups. Last resort — larger prompt but handles arbitrary complexity.

Each successful merge reduces the number of groups. The process repeats until one group remains or all remaining groups are irreconcilable (→ separate CTEs joined at the end).

### Phase 5 — Final Assembly + LLM Fallback

At this point we have:
- A merged deterministic query covering ~90% of target columns
- A small set of `unresolved` columns (from Phase 2) that had no pipeline match

Send a single LLM prompt containing:
- The merged deterministic query (as context, not for regeneration)
- The unresolved target columns with their type/description
- Current source schemas + sample data

The LLM fills in only the missing columns. Token usage is minimal because the bulk of the query is already solved.

**Output**: Final SQL query producing the full target CDM table.

### Streaming Strategy

| Phase | Streamable? | What the frontend shows |
|-------|:-----------:|------------------------|
| 1. Discovery | No | "Searching past pipelines..." |
| 2. Per-column resolution | **Yes** — each column as it resolves | Column mapping table filling in row by row |
| 3. Signature grouping | No (fast, <1s) | "Grouping compatible columns..." |
| 4. Cross-group merging | **Yes** — each merged group | DAG building up as groups merge |
| 5. LLM fallback | **Yes** — LLM streams tokens | Remaining columns filling in |

Phase 2 is where most user-visible progress happens. Phases 3-4 are fast deterministic steps. Phase 5 only fires for the residual columns.

**Caveat**: Phase 4 merging could theoretically alter Phase 2 results (e.g., adding GROUP BY to a column that didn't need one). In practice this is rare — within a signature group the skeleton is already compatible. If it does happen, the frontend updates the affected columns. This is preferable to blocking all streaming until merge completes.

## Key Assumptions

- **Primary keys are known** — either from warehouse metadata or user-provided. Required for PK/FK join inference in Phase 4. Without them, join discovery degrades to KG lookup or LLM.
- **Target CDM is fixed** — the target schema doesn't change between harmonisation sessions. This means past pipeline target columns are directly comparable to current target columns.
- **KG contains lineage** — past pipelines store not just full SQL but per-column pruned SQL and source/target schemas. This is the data model already defined in `tests/algo/TESTS.md`.

## Complexity

| Phase | Complexity | Notes |
|-------|-----------|-------|
| 1. Discovery | O(P) | P = number of past pipelines in KG |
| 2. Per-column resolution | O(C * P) | C = target columns, parallelisable |
| 3. Signature grouping | O(C^2) | Pairwise skeleton comparison |
| 4. Cross-group merging | O(G^2) | G = number of groups, typically small |
| 5. LLM fallback | O(1) | Single prompt for residual columns |

The expensive step is Phase 2 (C * P comparisons), but it's embarrassingly parallel. Phases 3-4 operate on the much smaller set of groups (G << C).

## What the Test Cases Exercise

| Test Case | Phase Stressed | Challenge |
|-----------|---------------|-----------|
| `join_left_vs_inner` | Phase 2 (pipeline selection) | Data profiling must distinguish LEFT vs INNER JOIN based on null patterns |
| `union_divergent_transforms` | Phase 2 (adaptation) | Past has 2 UNIONed tables, current has 1 pre-joined table — structural bridge |
| `different_union_splits` | Phase 2 (adaptation) | Same UNION structure but different partitioning dimension — semantic gap, likely LLM |
| `single_source_to_join` | Phase 4 (cross-group merge) | Past had 1 table, current has 2 — must discover join condition |
| `same_data_different_aggregation` | Phase 3 (grouping) | Two pipelines with different filter/aggregate order on identical data |
