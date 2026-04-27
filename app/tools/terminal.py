"""Terminal command execution tool with approval gating for destructive ops."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Callable, Coroutine

from app.config import WORKSPACE_DIR
from app.models.schemas import ToolResult

DANGEROUS_PATTERNS = [
    "rm -rf",
    "rm -r",
    "mkfs",
    "dd if=",
    "> /dev/",
    ":(){ :|:& };:",
    "--force",
    "force push",
    "drop database",
    "drop table",
    "truncate",
]


def _is_dangerous(command: str) -> bool:
    cmd_lower = command.lower()
    return any(pat in cmd_lower for pat in DANGEROUS_PATTERNS)


async def run_terminal_command(
    arguments: dict,
    approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
) -> ToolResult:
    command = arguments.get("command", "")
    requires_approval = arguments.get("requires_approval", False)

    if not command.strip():
        return ToolResult(
            tool_name="run_terminal_command",
            success=False,
            output="Empty command",
        )

    if requires_approval or _is_dangerous(command):
        if approval_callback is not None:
            approved = await approval_callback(command)
            if not approved:
                return ToolResult(
                    tool_name="run_terminal_command",
                    success=False,
                    output="Command rejected by user",
                )
        else:
            return ToolResult(
                tool_name="run_terminal_command",
                success=False,
                output="Destructive command requires approval but no callback provided",
            )

    try:
        env = os.environ.copy()
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(WORKSPACE_DIR),
            env=env,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        output = stdout.decode(errors="replace")

        if len(output) > 10_000:
            output = output[:10_000] + "\n... (truncated)"

        return ToolResult(
            tool_name="run_terminal_command",
            success=proc.returncode == 0,
            output=output,
            data={"exit_code": proc.returncode},
        )

    except asyncio.TimeoutError:
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass
        return ToolResult(
            tool_name="run_terminal_command",
            success=False,
            output="Command timed out after 60 seconds",
        )
    except Exception as exc:
        return ToolResult(
            tool_name="run_terminal_command",
            success=False,
            output=f"Error: {exc}",
        )
