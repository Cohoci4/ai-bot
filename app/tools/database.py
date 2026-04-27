"""Database interaction tools — read-only queries and approved mutations."""

from __future__ import annotations

import re
from typing import Any, Callable, Coroutine

from app.models.schemas import ToolResult

# Simulated database connections (in production these would be real DB clients)
_connections: dict[str, dict[str, str]] = {}


_MUTATION_KEYWORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "MERGE", "REPLACE",
})


def _is_select_only(query: str) -> bool:
    normalized = query.strip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("EXPLAIN")):
        return False
    if ";" in normalized.rstrip(";").rstrip():
        return False
    for keyword in _MUTATION_KEYWORDS:
        if keyword in normalized:
            return False
    return True


async def db_query(arguments: dict) -> ToolResult:
    """Execute a read-only SELECT query."""
    connection_ref = arguments.get("connection_ref", "")
    query = arguments.get("query", "")

    if not connection_ref:
        return ToolResult(
            tool_name="db_query",
            success=False,
            output="connection_ref is required",
        )

    if not query.strip():
        return ToolResult(
            tool_name="db_query",
            success=False,
            output="query is required",
        )

    if not _is_select_only(query):
        return ToolResult(
            tool_name="db_query",
            success=False,
            output="db_query only supports SELECT/EXPLAIN queries. Use db_execute for mutations.",
        )

    # In production, this would execute against a real database
    return ToolResult(
        tool_name="db_query",
        success=True,
        output=f"[DB:{connection_ref}] Query executed successfully (simulated). Query: {query}",
        data={"connection_ref": connection_ref, "query": query, "rows": [], "simulated": True},
    )


async def db_execute(
    arguments: dict,
    approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
) -> ToolResult:
    """Execute a mutation query (INSERT, UPDATE, DDL). Always requires approval."""
    connection_ref = arguments.get("connection_ref", "")
    query = arguments.get("query", "")

    if not connection_ref:
        return ToolResult(
            tool_name="db_execute",
            success=False,
            output="connection_ref is required",
        )

    if not query.strip():
        return ToolResult(
            tool_name="db_execute",
            success=False,
            output="query is required",
        )

    # Always require approval for mutations
    if approval_callback is not None:
        approved = await approval_callback(f"[DB MUTATION] {connection_ref}: {query}")
        if not approved:
            return ToolResult(
                tool_name="db_execute",
                success=False,
                output="Database mutation rejected by user",
            )
    else:
        return ToolResult(
            tool_name="db_execute",
            success=False,
            output="Database mutations require approval but no callback provided",
        )

    return ToolResult(
        tool_name="db_execute",
        success=True,
        output=f"[DB:{connection_ref}] Mutation executed successfully (simulated). Query: {query}",
        data={"connection_ref": connection_ref, "query": query, "simulated": True},
    )
