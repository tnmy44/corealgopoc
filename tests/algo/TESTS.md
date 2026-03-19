Tests for human review of harmonisation flow are stored using the following directory structure.
All SQL must be in **DuckDB dialect** (e.g. use `strptime`/`CAST` instead of `TO_DATE`).

- **tests/algo/**
  - **sometestname/** (One test represents one harmonisation session)
    - **task.yaml**, containing:
      - `description` — what the test exercises and expected algorithm behaviour
      - `sources[]` — each with `name`, `file` (relative path to CSV), `schema[]` (`name`, `type`)
      - `target` — `table` name, `columns[]` (`name`, `type`, `description`)
    - **sourcedata/**(source1.csv, source2.csv, …) — file stems must match source `name` in task.yaml
    - **memory/**
      - pastpipeline1/
        - **memory.yaml**, containing:
          - `description` — what this past pipeline did and why
          - `sources[]` — source schemas present in this pipeline
          - `target_columns` — keyed by target column name, each with `source_columns[]` and `sql_file`.
        - **full.sql** — Full SQL query to generate the output data (matching CDM schema) from the source data
        - **sql/**(sellerloanid.sql, secondtargetcolumn.sql) — *Pruned SQL for one specific column. Same structure as full.sql (same JOINs, CTEs, filters) but only projecting columns needed to produce this one target column.*
        - **pastdata/**(source1.csv, source2.csv) — file stems must match source `name` in memory.yaml
      - pastpipeline2/
        - (similar data for each past pipeline)
    - **expected/**
      - **full.sql** — the full SQL the algorithm should produce; add a comment indicating source (e.g. `-- Source: deterministic match from pastpipeline1`)
      - **sql/**(targetcol1.sql, targetcol2.sql) — *Pruned SQL for one specific target column. Same structure as full.sql (same JOINs, CTEs, filters) but only projecting columns needed to produce this one target column.*
  - someothertest/
    - …

## SQL Style

All SQL (past pipeline SQL and expected SQL) should prefer **multiple simple CTEs** over single large statements with many clauses. Each CTE should ideally contain only one major SQL clause (JOIN, WHERE, GROUP BY, UNION, CASE expression, etc.). This makes the DAG structure explicit and easier to reason about during harmonisation.

For example, instead of:
```sql
SELECT ... FROM a LEFT JOIN b ON ... WHERE ... GROUP BY ...
```
Prefer:
```sql
WITH
joined AS (SELECT ... FROM a LEFT JOIN b ON ...),
filtered AS (SELECT ... FROM joined WHERE ...),
aggregated AS (SELECT ... FROM filtered GROUP BY ...)
SELECT ... FROM aggregated
```

## Purpose

Test cases should highlight tricky harmonisation scenarios where:

1. **Column overlap exists but adaptation is hard** — Some or all target columns have a similar column in a past pipeline's sources, but the past pipeline's per-column SQL cannot be directly reused against the current sources because:
   - The current sources have a **different number of tables** (e.g. past had one pre-joined table, current has separate fact/dimension tables requiring a JOIN)
   - The current sources have **different join keys** or join structure (e.g. past used INNER JOIN, current needs LEFT JOIN on different columns)
   - The current sources encode the same information **differently** (e.g. past had separate `credit_amount`/`debit_amount` columns, current has a single `amount` with a `txn_type` discriminator)

2. **Cross-pipeline merging is hard** — Two or more past pipelines each provide useful SQL for different target columns, but their SQL structures differ (different JOINs, different CTEs, different filters), making it non-trivial to merge expressions from pipeline A with the join structure from pipeline B into one final query.

3. **Complete LLM fallback** — No past pipeline provides a usable pattern for the required transformation (e.g. pivoted→unpivoted data requiring UNION ALL, or conditional aggregation with no precedent), so the algorithm must fall back to LLM generation.

These map to the two hardest steps of deterministic harmonisation:

- **Query Adaptation** — Converting a past pipeline's SQL/mappings to work against the *current* source tables. The historical mapping may target differently joined, split, or named sources. Adaptation must introduce or remove JOINs, GROUP BYs, or UNIONs to bridge the structural gap.
- **Query Stitching** — Given a per-target-column "pruned" SQL query, combining them into a single final query that produces the full target table. Stitching is only possible when all column-specific queries share compatible structure (same JOINs, same CTEs, same filters). Test cases should exercise situations where the pruned queries diverge in structure, making stitching non-trivial.

## Data Consistency Rule

All data sources across a test case — current `sourcedata/` and every pipeline's `pastdata/` — must represent **the same underlying information**. The schemas, table splits, and formats may differ (e.g. data might be pre-joined in one source but split into fact/dimension tables in another, column names may differ, date formats may vary), but the actual entities and their relationships must be consistent.

For example, if the current source has transactions for persons P001, P002, and P999, then:
- A past pipeline whose data has **unmatched foreign keys** (to test LEFT JOIN) should also have transactions referencing a person ID that doesn't exist in its persons table.
- A past pipeline whose data has **full referential integrity** (to test INNER JOIN) should have every transaction matched to a person.
- The specific IDs and values can differ (P101 vs P001), but the *pattern* of the data (null rates, format distributions, cardinality) must match the scenario being tested.

This ensures the algorithm's data profiling can meaningfully compare current data against each pipeline's past data to select the right mapping.

## Viewing Test Cases

```bash
.venv/bin/python tests/algo/viewer/app.py
# Open http://localhost:5555
```

