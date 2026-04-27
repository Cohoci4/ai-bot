"""Task management tool — create, update, list, and complete subtasks."""

from __future__ import annotations

from app.models.schemas import Task, TaskStatus, ToolResult


class TaskManager:
    """In-memory task store for the current session."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def execute(self, arguments: dict) -> ToolResult:
        action = arguments.get("action", "list")
        handler = {
            "create": self._create,
            "update": self._update,
            "complete": self._complete,
            "list": self._list,
        }.get(action)

        if handler is None:
            return ToolResult(
                tool_name="task",
                success=False,
                output=f"Unknown action: {action}",
            )
        return handler(arguments)

    # ------------------------------------------------------------------
    def _create(self, args: dict) -> ToolResult:
        task_id = args.get("task_id", "")
        title = args.get("title", "Untitled")
        status = TaskStatus(args.get("status", "pending"))
        details = args.get("details", "")

        if not task_id:
            return ToolResult(tool_name="task", success=False, output="task_id is required")

        task = Task(task_id=task_id, title=title, status=status, details=details)
        self._tasks[task_id] = task
        return ToolResult(
            tool_name="task",
            success=True,
            output=f"Task '{task_id}' created: {title}",
            data=task.model_dump(),
        )

    def _update(self, args: dict) -> ToolResult:
        task_id = args.get("task_id", "")
        task = self._tasks.get(task_id)
        if task is None:
            return ToolResult(tool_name="task", success=False, output=f"Task '{task_id}' not found")

        if "title" in args:
            task.title = args["title"]
        if "status" in args:
            task.status = TaskStatus(args["status"])
        if "details" in args:
            task.details = args["details"]

        return ToolResult(
            tool_name="task",
            success=True,
            output=f"Task '{task_id}' updated",
            data=task.model_dump(),
        )

    def _complete(self, args: dict) -> ToolResult:
        task_id = args.get("task_id", "")
        task = self._tasks.get(task_id)
        if task is None:
            return ToolResult(tool_name="task", success=False, output=f"Task '{task_id}' not found")

        task.status = TaskStatus.DONE
        return ToolResult(
            tool_name="task",
            success=True,
            output=f"Task '{task_id}' marked as done",
            data=task.model_dump(),
        )

    def _list(self, _args: dict) -> ToolResult:
        tasks = [t.model_dump() for t in self._tasks.values()]
        return ToolResult(
            tool_name="task",
            success=True,
            output=f"{len(tasks)} task(s)",
            data={"tasks": tasks},
        )

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks.values())
