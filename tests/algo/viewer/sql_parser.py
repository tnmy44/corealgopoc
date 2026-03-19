"""SQL to DAG parser using sqlglot."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional

import sqlglot
from sqlglot import exp


@dataclass
class DAGNode:
    id: str
    label: str
    node_type: str  # "source", "cte", "output"
    operation: str  # "SELECT", "JOIN", "LEFT_JOIN", "FILTER", "GROUP_BY", "UNION", "SQL"
    sql: str  # The SQL fragment for this node
    executable_sql: str  # Full executable SQL up to this node

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DAGEdge:
    source: str
    target: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SQLDag:
    nodes: List[DAGNode] = field(default_factory=list)
    edges: List[DAGEdge] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


def classify_operation(ast: exp.Expression) -> str:
    """Classify the SQL operation type from an AST node.

    If multiple clauses match, returns "SQL" (generic SQL statement).
    """
    matches = []

    # Check for joins
    joins = list(ast.find_all(exp.Join))
    if joins:
        for j in joins:
            join_text = j.sql().upper()
            if "LEFT" in join_text:
                matches.append("LEFT_JOIN")
                break
        else:
            matches.append("JOIN")

    # Check for UNION
    if ast.find(exp.Union):
        matches.append("UNION")

    # Check for GROUP BY
    if ast.find(exp.Group):
        matches.append("GROUP_BY")

    # Check for WHERE
    if ast.find(exp.Where):
        matches.append("FILTER")

    if len(matches) == 0:
        return "SELECT"
    if len(matches) == 1:
        return matches[0]
    return "SQL"


def _extract_table_refs(ast: exp.Expression) -> List[str]:
    """Extract all table references from a SQL AST."""
    tables = []
    for table in ast.find_all(exp.Table):
        name = table.name
        if name:
            tables.append(name)
    return tables


def parse_sql_to_dag(sql: str) -> SQLDag:
    """Parse a SQL string into a DAG of nodes and edges."""
    sql = sql.strip()
    if not sql:
        return SQLDag()

    # Strip comment lines at top
    lines = sql.split("\n")
    clean_lines = [l for l in lines if not l.strip().startswith("--")]
    clean_sql = "\n".join(clean_lines).strip()
    if not clean_sql:
        return SQLDag()

    try:
        ast = sqlglot.parse_one(clean_sql)
    except Exception:
        # If parsing fails, return a single output node
        return SQLDag(
            nodes=[DAGNode(
                id="output",
                label="Output",
                node_type="output",
                operation="SELECT",
                sql=clean_sql,
                executable_sql=clean_sql,
            )],
            edges=[],
        )

    dag = SQLDag()
    cte_names = set()

    # Extract CTEs
    with_clause = ast.find(exp.With)
    if with_clause:
        for cte in with_clause.expressions:
            if isinstance(cte, exp.CTE):
                alias = cte.alias
                cte_names.add(alias)
                cte_ast = cte.this  # the inner SELECT
                node = DAGNode(
                    id=f"cte_{alias}",
                    label=alias,
                    node_type="cte",
                    operation=classify_operation(cte_ast),
                    sql=cte_ast.sql(pretty=True),
                    executable_sql="",  # filled in by build_node_sql
                )
                dag.nodes.append(node)

    # Extract source tables (tables not matching any CTE name)
    all_table_refs = _extract_table_refs(ast)
    source_tables = set()
    for t in all_table_refs:
        if t not in cte_names:
            source_tables.add(t)

    for table_name in sorted(source_tables):
        node = DAGNode(
            id=f"source_{table_name}",
            label=table_name,
            node_type="source",
            operation="SOURCE",
            sql=f"SELECT * FROM {table_name}",
            executable_sql=f"SELECT * FROM {table_name}",
        )
        dag.nodes.append(node)

    # Output node (the final SELECT)
    # Get the main query body (without WITH clause)
    main_select = ast
    output_op = classify_operation(ast)
    # For the output SQL, show just the final SELECT part
    if with_clause:
        # The main body is everything after the WITH
        main_body = ast.this if hasattr(ast, 'this') and isinstance(ast, exp.With) else ast
        # Get the SQL of just the final select
        final_select = ast.copy()
        # Remove the WITH clause for display
        try:
            no_with = final_select.copy()
            with_node = no_with.find(exp.With)
            if with_node:
                with_node.pop()
            output_sql = no_with.sql(pretty=True)
        except Exception:
            output_sql = clean_sql
    else:
        output_sql = clean_sql

    output_node = DAGNode(
        id="output",
        label="Output",
        node_type="output",
        operation=output_op,
        sql=output_sql,
        executable_sql=clean_sql,
    )
    dag.nodes.append(output_node)

    # Build edges
    # Source tables → CTE nodes (or output if no CTEs)
    if cte_names:
        # For each CTE, find which source tables it references
        if with_clause:
            cte_list = list(with_clause.expressions)
            for i, cte in enumerate(cte_list):
                if isinstance(cte, exp.CTE):
                    alias = cte.alias
                    cte_ast = cte.this
                    refs = _extract_table_refs(cte_ast)
                    for ref in refs:
                        if ref in source_tables:
                            dag.edges.append(DAGEdge(
                                source=f"source_{ref}",
                                target=f"cte_{alias}",
                            ))
                        elif ref in cte_names:
                            dag.edges.append(DAGEdge(
                                source=f"cte_{ref}",
                                target=f"cte_{alias}",
                            ))

            # Final SELECT references → output
            # Get tables referenced in the main body (after WITH)
            try:
                no_with = ast.copy()
                with_node = no_with.find(exp.With)
                if with_node:
                    with_node.pop()
                main_refs = _extract_table_refs(no_with)
            except Exception:
                main_refs = []

            for ref in main_refs:
                if ref in cte_names:
                    dag.edges.append(DAGEdge(
                        source=f"cte_{ref}",
                        target="output",
                    ))
                elif ref in source_tables:
                    dag.edges.append(DAGEdge(
                        source=f"source_{ref}",
                        target="output",
                    ))
    else:
        # No CTEs: source tables → output directly
        for table_name in sorted(source_tables):
            dag.edges.append(DAGEdge(
                source=f"source_{table_name}",
                target="output",
            ))

    # Build executable SQL for each node
    _build_executable_sql(dag, clean_sql, with_clause, cte_names)

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for e in dag.edges:
        key = (e.source, e.target)
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)
    dag.edges = unique_edges

    return dag


def _build_executable_sql(
    dag: SQLDag,
    original_sql: str,
    with_clause: Optional[exp.With],
    cte_names: set,
) -> None:
    """Build executable SQL for each node in the DAG."""
    for node in dag.nodes:
        if node.node_type == "source":
            # Already set
            pass
        elif node.node_type == "cte":
            cte_alias = node.label
            # Include all CTEs up to and including this one, then SELECT * FROM it
            if with_clause:
                cte_list = list(with_clause.expressions)
                included_ctes = []
                for cte in cte_list:
                    if isinstance(cte, exp.CTE):
                        included_ctes.append(cte.sql(pretty=True))
                        if cte.alias == cte_alias:
                            break
                cte_sql = ",\n".join(included_ctes)
                node.executable_sql = f"WITH {cte_sql}\nSELECT * FROM {cte_alias}"
        elif node.node_type == "output":
            node.executable_sql = original_sql
