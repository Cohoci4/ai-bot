"""Central tool executor — routes tool calls to implementations."""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from app.models.schemas import ToolCall, ToolResult
from app.tools.file_ops import edit_file, read_file, write_file
from app.tools.git_ops import git_add, git_branch, git_commit, git_diff, git_status
from app.tools.task_manager import TaskManager
from app.tools.terminal import run_terminal_command
from app.tools.web_browse import browse_web


class ToolExecutor:
    """Routes tool calls to their implementations and returns results."""

    def __init__(
        self,
        task_manager: TaskManager,
        approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
    ) -> None:
        self.task_manager = task_manager
        self.approval_callback = approval_callback

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        name = tool_call.name
        args = tool_call.arguments

        # Synchronous tools
        sync_tools: dict[str, Callable[..., ToolResult]] = {
            "task": self.task_manager.execute,
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
        }

        if name in sync_tools:
            return sync_tools[name](args)

        # Async tools
        async_tools: dict[str, Callable[..., Coroutine[Any, Any, ToolResult]]] = {
            "run_terminal_command": lambda a: run_terminal_command(a, self.approval_callback),
            "git_status": git_status,
            "git_branch": git_branch,
            "git_add": git_add,
            "git_commit": git_commit,
            "git_diff": git_diff,
            "browse_web": browse_web,
        }

        handler = async_tools.get(name)
        if handler:
            return await handler(args)

        # Special: complete_task — just acknowledge
        if name == "complete_task":
            summary = args.get("summary", "Task completed")
            notes = args.get("notes", "")
            return ToolResult(
                tool_name="complete_task",
                success=True,
                output=f"✓ {summary}" + (f"\nNotes: {notes}" if notes else ""),
            )

        # Special: human_input — pass through
        if name == "human_input":
            return ToolResult(
                tool_name="human_input",
                success=True,
                output=args.get("question", ""),
                data={"options": args.get("options", [])},
            )

        return ToolResult(
            tool_name=name,
            success=False,
            output=f"Unknown tool: {name}",
        )
