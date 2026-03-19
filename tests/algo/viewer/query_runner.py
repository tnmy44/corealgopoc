"""Execute SQL queries against CSV data using DuckDB."""
from __future__ import annotations

from typing import Dict, List, Any

import duckdb


class QueryRunner:
    """Loads CSV files into DuckDB and executes SQL queries against them."""

    def __init__(self):
        self.conn = duckdb.connect(":memory:")

    def close(self):
        self.conn.close()

    def load_csvs(self, csv_paths: Dict[str, str]) -> None:
        """Load CSV files into DuckDB tables.

        Args:
            csv_paths: mapping of table_name -> absolute file path to CSV
        """
        for table_name, csv_path in csv_paths.items():
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.execute(
                f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')"
            )

    def execute_node(self, sql: str, max_rows: int = 100) -> Dict[str, Any]:
        """Execute a SQL query and return results.

        Returns:
            dict with keys: columns (list[str]), rows (list[list]), error (str|None)
        """
        sql = sql.strip()
        if not sql:
            return {"columns": [], "rows": [], "error": "Empty SQL"}

        # Strip comment lines
        lines = sql.split("\n")
        clean_lines = [l for l in lines if not l.strip().startswith("--")]
        clean_sql = "\n".join(clean_lines).strip()
        if not clean_sql:
            return {"columns": [], "rows": [], "error": "Empty SQL after removing comments"}

        try:
            result = self.conn.execute(clean_sql)
            columns = [desc[0] for desc in result.description]
            rows = [list(row) for row in result.fetchmany(max_rows)]
            rows = _sanitize_rows(rows)
            return {"columns": columns, "rows": rows, "error": None}
        except Exception as e:
            return {"columns": [], "rows": [], "error": str(e)}


def _sanitize_rows(rows: List[List[Any]]) -> List[List[Any]]:
    """Convert non-JSON-serializable values to strings."""
    sanitized = []
    for row in rows:
        sanitized_row = []
        for val in row:
            if val is None:
                sanitized_row.append(None)
            elif isinstance(val, (str, int, float, bool)):
                sanitized_row.append(val)
            else:
                sanitized_row.append(str(val))
        sanitized.append(sanitized_row)
    return sanitized
