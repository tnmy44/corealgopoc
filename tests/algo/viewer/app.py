"""Flask server for the SQL DAG viewer."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from flask import Flask, jsonify, render_template, request

from sql_parser import parse_sql_to_dag
from query_runner import QueryRunner

app = Flask(__name__)

# Base directory containing all test cases
ALGO_DIR = Path(__file__).resolve().parent.parent  # tests/algo/

# Test case directories (exclude 'viewer' itself)
EXCLUDED_DIRS = {"viewer", "__pycache__"}


def discover_test_cases() -> List[Dict[str, Any]]:
    """Discover all test case directories under tests/algo/."""
    cases = []
    for entry in sorted(ALGO_DIR.iterdir()):
        if entry.is_dir() and entry.name not in EXCLUDED_DIRS:
            task_yaml = entry / "task.yaml"
            if task_yaml.exists():
                with open(task_yaml) as f:
                    task = yaml.safe_load(f)
                cases.append({
                    "id": entry.name,
                    "description": task.get("description", "").strip(),
                })
    return cases


def load_test_case(case_id: str) -> Optional[Dict[str, Any]]:
    """Load full test case data."""
    case_dir = ALGO_DIR / case_id
    if not case_dir.is_dir():
        return None

    task_yaml = case_dir / "task.yaml"
    if not task_yaml.exists():
        return None

    with open(task_yaml) as f:
        task = yaml.safe_load(f)

    result: Dict[str, Any] = {
        "id": case_id,
        "description": task.get("description", "").strip(),
        "sources": [],
        "target": task.get("target", {}),
        "pipelines": [],
        "expected_sql": None,
        "expected_dag": None,
        "expected_column_sqls": {},
    }

    # Load source data previews
    for src in task.get("sources", []):
        src_file = case_dir / src.get("file", "")
        src_info = {
            "name": src.get("name", ""),
            "schema": src.get("schema", []),
            "file": str(src_file) if src_file.exists() else None,
            "preview": _preview_csv(src_file) if src_file.exists() else None,
        }
        result["sources"].append(src_info)

    # Load expected SQL and DAG (new layout: expected/full.sql + expected/sql/*.sql)
    expected_dir = case_dir / "expected"
    expected_full_path = expected_dir / "full.sql"
    if expected_full_path.exists():
        expected_sql = expected_full_path.read_text()
        result["expected_sql"] = expected_sql
        result["expected_dag"] = parse_sql_to_dag(expected_sql).to_dict()

        # Load per-column expected SQL
        expected_sql_dir = expected_dir / "sql"
        if expected_sql_dir.is_dir():
            for sql_file in sorted(expected_sql_dir.glob("*.sql")):
                col_name = sql_file.stem
                col_sql = sql_file.read_text()
                result["expected_column_sqls"][col_name] = {
                    "sql": col_sql,
                    "dag": parse_sql_to_dag(col_sql).to_dict(),
                }

    # Discover pipelines in memory/
    memory_dir = case_dir / "memory"
    if memory_dir.is_dir():
        for pipeline_dir in sorted(memory_dir.iterdir()):
            if pipeline_dir.is_dir() and not pipeline_dir.name.startswith("."):
                pipeline = _load_pipeline(pipeline_dir, case_dir)
                if pipeline:
                    result["pipelines"].append(pipeline)

    return result


def _load_pipeline(pipeline_dir: Path, case_dir: Path) -> Optional[Dict[str, Any]]:
    """Load a single pipeline from its directory."""
    memory_yaml = pipeline_dir / "memory.yaml"
    if not memory_yaml.exists():
        return None

    with open(memory_yaml) as f:
        mem = yaml.safe_load(f)

    pipeline: Dict[str, Any] = {
        "name": pipeline_dir.name,
        "description": mem.get("description", "").strip(),
        "full_sql": None,
        "full_dag": None,
        "column_sqls": {},
        "past_sources": [],
    }

    # Load full.sql if present
    full_sql_path = pipeline_dir / "full.sql"
    if full_sql_path.exists():
        full_sql = full_sql_path.read_text()
        pipeline["full_sql"] = full_sql
        pipeline["full_dag"] = parse_sql_to_dag(full_sql).to_dict()

    # Load per-column SQL
    target_columns = mem.get("target_columns", {})
    for col_name, col_info in target_columns.items():
        sql_file = col_info.get("sql_file", "")
        sql_path = pipeline_dir / sql_file
        col_entry: Dict[str, Any] = {
            "source_columns": col_info.get("source_columns", []),
            "sql": None,
            "dag": None,
        }
        if sql_path.exists():
            col_sql = sql_path.read_text()
            col_entry["sql"] = col_sql
            col_entry["dag"] = parse_sql_to_dag(col_sql).to_dict()

        # Load intermediate columns if present
        intermediates = col_info.get("intermediate_columns", {})
        if intermediates:
            col_entry["intermediates"] = {}
            for int_name, int_info in intermediates.items():
                int_sql_path = pipeline_dir / int_info.get("sql_file", "")
                int_entry = {"sql": None, "dag": None}
                if int_sql_path.exists():
                    int_sql = int_sql_path.read_text()
                    int_entry["sql"] = int_sql
                    int_entry["dag"] = parse_sql_to_dag(int_sql).to_dict()
                col_entry["intermediates"][int_name] = int_entry

        pipeline["column_sqls"][col_name] = col_entry

    # Load past source data previews
    pastdata_dir = pipeline_dir / "pastdata"
    if pastdata_dir.is_dir():
        for csv_file in sorted(pastdata_dir.glob("*.csv")):
            table_name = csv_file.stem
            pipeline["past_sources"].append({
                "name": table_name,
                "file": str(csv_file),
                "preview": _preview_csv(csv_file),
            })

    return pipeline


def _preview_csv(csv_path: Path, max_rows: int = 10) -> Optional[Dict[str, Any]]:
    """Preview a CSV file by reading it with DuckDB."""
    try:
        runner = QueryRunner()
        runner.conn.execute(
            f"CREATE TABLE _preview AS SELECT * FROM read_csv_auto('{csv_path}')"
        )
        result = runner.conn.execute(f"SELECT * FROM _preview LIMIT {max_rows}")
        columns = [desc[0] for desc in result.description]
        rows = [list(row) for row in result.fetchall()]
        # Sanitize
        from query_runner import _sanitize_rows
        rows = _sanitize_rows(rows)
        runner.close()
        return {"columns": columns, "rows": rows}
    except Exception as e:
        return {"columns": [], "rows": [], "error": str(e)}


def _get_csv_paths_for_context(
    case_id: str, data_context: str
) -> Dict[str, str]:
    """Get CSV paths for a given data context.

    data_context is either "source" or "past:<pipeline_name>"
    """
    case_dir = ALGO_DIR / case_id

    if data_context == "source":
        # Use sourcedata/ CSVs
        source_dir = case_dir / "sourcedata"
        if source_dir.is_dir():
            return {
                csv.stem: str(csv)
                for csv in source_dir.glob("*.csv")
            }
    elif data_context.startswith("past:"):
        pipeline_name = data_context[5:]
        pastdata_dir = case_dir / "memory" / pipeline_name / "pastdata"
        if pastdata_dir.is_dir():
            return {
                csv.stem: str(csv)
                for csv in pastdata_dir.glob("*.csv")
            }

    return {}


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/test-cases")
def api_test_cases():
    return jsonify(discover_test_cases())


@app.route("/api/test-cases/<case_id>")
def api_test_case(case_id: str):
    case = load_test_case(case_id)
    if case is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(case)


@app.route("/api/execute", methods=["POST"])
def api_execute():
    body = request.get_json(force=True)
    case_id = body.get("test_case_id", "")
    sql = body.get("sql", "")
    data_context = body.get("data_context", "source")

    csv_paths = _get_csv_paths_for_context(case_id, data_context)
    if not csv_paths:
        return jsonify({"columns": [], "rows": [], "error": "No CSV data found for context"})

    runner = QueryRunner()
    runner.load_csvs(csv_paths)
    result = runner.execute_node(sql)
    runner.close()
    return jsonify(result)


if __name__ == "__main__":
    print(f"Test cases directory: {ALGO_DIR}")
    print(f"Discovered test cases: {[c['id'] for c in discover_test_cases()]}")
    app.run(host="0.0.0.0", port=5555, debug=True)
