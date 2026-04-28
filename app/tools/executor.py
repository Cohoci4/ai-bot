"""Central tool executor — routes tool calls to implementations."""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from app.models.schemas import ToolCall, ToolResult
from app.tools.assumptions import AssumptionsManager
from app.tools.ci_cd import ci_get_logs, ci_status, ci_trigger, deploy_preview, deploy_staging
from app.tools.database import db_execute, db_query
from app.tools.diagnostics import restore_state, self_test
from app.tools.file_ops import edit_file, read_file, write_file
from app.tools.git_ops import git_add, git_branch, git_commit, git_diff, git_status
from app.tools.integrations import generate_report, jira_update, slack_notify
from app.tools.memory import learn_from_mistake, memorize, recall
from app.tools.monitoring import app_healthcheck
from app.tools.screenshots import take_screenshot, visual_comparison
from app.tools.task_manager import TaskManager
from app.tools.terminal import run_terminal_command


class ToolExecutor:
    """Routes tool calls to their implementations and returns results."""

    def __init__(
        self,
        task_manager: TaskManager,
        assumptions_manager: AssumptionsManager,
        approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
        critical_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
    ) -> None:
        self.task_manager = task_manager
        self.assumptions_manager = assumptions_manager
        self.approval_callback = approval_callback
        self.critical_callback = critical_callback

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        name = tool_call.name
        args = tool_call.arguments

        # --- Synchronous tools ---
        sync_tools: dict[str, Callable[..., ToolResult]] = {
            "task": self.task_manager.execute,
            "assumptions_log": self.assumptions_manager.execute,
            "read_file": read_file,
            "write_file": write_file,
            "edit_file": edit_file,
            "memorize": memorize,
            "recall": recall,
            "learn_from_mistake": learn_from_mistake,
        }

        if name in sync_tools:
            return sync_tools[name](args)

        # --- Async tools (no approval needed) ---
        async_simple: dict[str, Callable[..., Coroutine[Any, Any, ToolResult]]] = {
            "git_status": git_status,
            "git_branch": git_branch,
            "git_add": git_add,
            "git_commit": git_commit,
            "git_diff": git_diff,
            "browse_web": self._browse_web,
            "take_screenshot": take_screenshot,
            "visual_comparison": visual_comparison,
            "db_query": db_query,
            "ci_status": ci_status,
            "ci_get_logs": ci_get_logs,
            "app_healthcheck": app_healthcheck,
            "jira_update": jira_update,
            "slack_notify": slack_notify,
            "self_test": self_test,
            "restore_state": restore_state,
        }

        handler = async_simple.get(name)
        if handler:
            return await handler(args)

        # --- Async tools (with approval) ---
        if name == "run_terminal_command":
            return await run_terminal_command(args, self.approval_callback, self.critical_callback)

        if name == "db_execute":
            return await db_execute(args, self.approval_callback)

        if name == "ci_trigger":
            return await ci_trigger(args, self.approval_callback)

        if name == "deploy_preview":
            return await deploy_preview(args, self.approval_callback)

        if name == "deploy_staging":
            return await deploy_staging(args, self.approval_callback)

        # --- Report generation (needs task/assumptions context) ---
        if name == "generate_report":
            tasks_data = [t.model_dump() for t in self.task_manager.tasks]
            assumptions_data = self.assumptions_manager.assumptions
            return generate_report(args, tasks=tasks_data, assumptions=assumptions_data)

        # --- Special: complete_task ---
        if name == "complete_task":
            summary = args.get("summary", "Task completed")
            notes = args.get("notes", "")
            return ToolResult(
                tool_name="complete_task",
                success=True,
                output=f"Task completed: {summary}" + (f"\nNotes: {notes}" if notes else ""),
            )

        # --- Special: human_input ---
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

    async def _browse_web(self, args: dict) -> ToolResult:
        from app.tools.web_browse import browse_web
        return await browse_web(args)
