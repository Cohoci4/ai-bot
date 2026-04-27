"""Assumptions tracking tool — log, list, and clear assumptions."""

from __future__ import annotations

from app.models.schemas import ToolResult


class AssumptionsManager:
    """In-memory store for assumptions made during planning/implementation."""

    def __init__(self) -> None:
        self._assumptions: list[dict[str, str]] = []

    def execute(self, arguments: dict) -> ToolResult:
        action = arguments.get("action", "list")
        handler = {
            "add": self._add,
            "list": self._list,
            "clear": self._clear,
        }.get(action)

        if handler is None:
            return ToolResult(
                tool_name="assumptions_log",
                success=False,
                output=f"Unknown action: {action}",
            )
        return handler(arguments)

    def _add(self, args: dict) -> ToolResult:
        assumption = args.get("assumption", "")
        context = args.get("context", "")

        if not assumption:
            return ToolResult(
                tool_name="assumptions_log",
                success=False,
                output="assumption is required",
            )

        entry = {"assumption": assumption, "context": context}
        self._assumptions.append(entry)
        return ToolResult(
            tool_name="assumptions_log",
            success=True,
            output=f"Assumption logged: {assumption}",
            data={"index": len(self._assumptions) - 1, **entry},
        )

    def _list(self, _args: dict) -> ToolResult:
        if not self._assumptions:
            return ToolResult(
                tool_name="assumptions_log",
                success=True,
                output="No assumptions logged yet.",
                data={"assumptions": []},
            )

        lines = []
        for i, a in enumerate(self._assumptions, 1):
            line = f"{i}. {a['assumption']}"
            if a["context"]:
                line += f" (context: {a['context']})"
            lines.append(line)

        return ToolResult(
            tool_name="assumptions_log",
            success=True,
            output="\n".join(lines),
            data={"assumptions": self._assumptions},
        )

    def _clear(self, _args: dict) -> ToolResult:
        count = len(self._assumptions)
        self._assumptions.clear()
        return ToolResult(
            tool_name="assumptions_log",
            success=True,
            output=f"Cleared {count} assumption(s).",
        )

    @property
    def assumptions(self) -> list[dict[str, str]]:
        return list(self._assumptions)
