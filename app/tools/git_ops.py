"""Git operation tools — status, branch, add, commit, diff."""

from __future__ import annotations

import asyncio

from app.config import WORKSPACE_DIR
from app.models.schemas import ToolResult


async def _git(args: list[str]) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        "git",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(WORKSPACE_DIR),
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass
        return 1, "Git command timed out after 30 seconds"
    return proc.returncode or 0, stdout.decode(errors="replace")


async def git_status(_arguments: dict) -> ToolResult:
    rc, out = await _git(["status", "--short"])
    return ToolResult(
        tool_name="git_status",
        success=rc == 0,
        output=out or "(clean working tree)",
    )


async def git_branch(arguments: dict) -> ToolResult:
    name = arguments.get("name")
    if name:
        rc, out = await _git(["checkout", "-B", name])
    else:
        rc, out = await _git(["branch", "--list"])
    return ToolResult(tool_name="git_branch", success=rc == 0, output=out)


async def git_add(arguments: dict) -> ToolResult:
    paths = arguments.get("paths", ["."])
    if isinstance(paths, str):
        paths = [paths]
    rc, out = await _git(["add", *paths])
    return ToolResult(tool_name="git_add", success=rc == 0, output=out or "Staged changes")


async def git_commit(arguments: dict) -> ToolResult:
    message = arguments.get("message", "auto-commit")
    rc, out = await _git(["commit", "-m", message])
    return ToolResult(tool_name="git_commit", success=rc == 0, output=out)


async def git_diff(arguments: dict) -> ToolResult:
    cached = arguments.get("cached", False)
    cmd = ["diff"]
    if cached:
        cmd.append("--cached")
    rc, out = await _git(cmd)
    return ToolResult(tool_name="git_diff", success=rc == 0, output=out or "(no diff)")
