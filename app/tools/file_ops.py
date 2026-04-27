"""File operation tools — read, write, and edit files within the workspace."""

from __future__ import annotations

from pathlib import Path

from app.config import WORKSPACE_DIR
from app.models.schemas import ToolResult


def _safe_path(rel: str) -> Path:
    """Resolve a relative path inside the workspace, preventing traversal."""
    target = (WORKSPACE_DIR / rel).resolve()
    if not str(target).startswith(str(WORKSPACE_DIR)):
        raise PermissionError("Path escapes workspace directory")
    return target


def read_file(arguments: dict) -> ToolResult:
    path_str = arguments.get("path", "")
    encoding = arguments.get("encoding", "utf-8")

    try:
        target = _safe_path(path_str)
        if not target.is_file():
            return ToolResult(tool_name="read_file", success=False, output=f"File not found: {path_str}")
        content = target.read_text(encoding=encoding)
        return ToolResult(
            tool_name="read_file",
            success=True,
            output=content,
            data={"path": str(target.relative_to(WORKSPACE_DIR)), "size": len(content)},
        )
    except PermissionError as exc:
        return ToolResult(tool_name="read_file", success=False, output=str(exc))
    except Exception as exc:
        return ToolResult(tool_name="read_file", success=False, output=f"Error: {exc}")


def write_file(arguments: dict) -> ToolResult:
    path_str = arguments.get("path", "")
    content = arguments.get("content", "")
    overwrite = arguments.get("overwrite", False)

    try:
        target = _safe_path(path_str)
        if target.exists() and not overwrite:
            return ToolResult(
                tool_name="write_file",
                success=False,
                output=f"File exists: {path_str}. Set overwrite=true to replace.",
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(
            tool_name="write_file",
            success=True,
            output=f"Written {len(content)} chars to {path_str}",
            data={"path": str(target.relative_to(WORKSPACE_DIR))},
        )
    except PermissionError as exc:
        return ToolResult(tool_name="write_file", success=False, output=str(exc))
    except Exception as exc:
        return ToolResult(tool_name="write_file", success=False, output=f"Error: {exc}")


def edit_file(arguments: dict) -> ToolResult:
    path_str = arguments.get("path", "")
    operation = arguments.get("operation", "")
    start_line = arguments.get("start_line", 0)
    end_line = arguments.get("end_line", None)
    new_text = arguments.get("new_text", "")

    try:
        target = _safe_path(path_str)
        if not target.is_file():
            return ToolResult(tool_name="edit_file", success=False, output=f"File not found: {path_str}")

        lines = target.read_text().splitlines(keepends=True)

        if operation == "replace_between":
            if end_line is None:
                end_line = start_line
            new_lines = new_text.splitlines(keepends=True)
            if new_text and not new_text.endswith("\n"):
                new_lines[-1] += "\n"
            lines[start_line - 1 : end_line] = new_lines

        elif operation == "insert_after":
            insert_lines = new_text.splitlines(keepends=True)
            if new_text and not new_text.endswith("\n"):
                insert_lines[-1] += "\n"
            lines[start_line:start_line] = insert_lines

        elif operation == "delete_lines":
            if end_line is None:
                end_line = start_line
            del lines[start_line - 1 : end_line]

        else:
            return ToolResult(
                tool_name="edit_file",
                success=False,
                output=f"Unknown operation: {operation}",
            )

        target.write_text("".join(lines))
        return ToolResult(
            tool_name="edit_file",
            success=True,
            output=f"Edited {path_str} ({operation})",
            data={"path": str(target.relative_to(WORKSPACE_DIR))},
        )

    except PermissionError as exc:
        return ToolResult(tool_name="edit_file", success=False, output=str(exc))
    except Exception as exc:
        return ToolResult(tool_name="edit_file", success=False, output=f"Error: {exc}")
