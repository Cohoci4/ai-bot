"""Terminal command execution with 3-tier safety: safe, requires_approval, critical."""

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

CRITICAL_PATTERNS = [
    "rm -rf /",
    "mkfs",
    "dd if=",
    "> /dev/",
    ":(){ :|:& };:",
    "drop database",
    "--force-with-lease",
    "git push --force",
    "git push -f",
]


def _classify_safety(command: str, explicit_level: str) -> str:
    """Determine the effective safety level for a command."""
    cmd_lower = command.lower()

    if explicit_level == "critical":
        return "critical"

    if any(pat in cmd_lower for pat in CRITICAL_PATTERNS):
        return "critical"

    if explicit_level == "requires_approval":
        return "requires_approval"

    if any(pat in cmd_lower for pat in DANGEROUS_PATTERNS):
        return "requires_approval"

    return explicit_level or "safe"


async def run_terminal_command(
    arguments: dict,
    approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
    critical_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
) -> ToolResult:
    command = arguments.get("command", "")
    explicit_level = arguments.get("safety_level", "safe")

    if not command.strip():
        return ToolResult(
            tool_name="run_terminal_command",
            success=False,
            output="Empty command",
        )

    safety_level = _classify_safety(command, explicit_level)

    if safety_level == "critical":
        cb = critical_callback or approval_callback
        if cb is not None:
            approved = await cb(command)
            if not approved:
                return ToolResult(
                    tool_name="run_terminal_command",
                    success=False,
                    output="CRITICAL command rejected by user",
                    data={"safety_level": "critical"},
                )
        else:
            return ToolResult(
                tool_name="run_terminal_command",
                success=False,
                output="CRITICAL command requires explicit confirmation but no callback provided",
                data={"safety_level": "critical"},
            )
    elif safety_level == "requires_approval":
        if approval_callback is not None:
            approved = await approval_callback(command)
            if not approved:
                return ToolResult(
                    tool_name="run_terminal_command",
                    success=False,
                    output="Command rejected by user",
                    data={"safety_level": "requires_approval"},
                )
        else:
            return ToolResult(
                tool_name="run_terminal_command",
                success=False,
                output="Command requires approval but no callback provided",
                data={"safety_level": "requires_approval"},
            )

    try:
        env = os.environ.copy()
        proc = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(WORKSPACE_DIR),
            env=env,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode(errors="replace")

        if len(output) > 10_000:
            output = output[:10_000] + "\n... (truncated)"

        return ToolResult(
            tool_name="run_terminal_command",
            success=proc.returncode == 0,
            output=output,
            data={"exit_code": proc.returncode, "safety_level": safety_level},
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
            output="Command timed out after 30 seconds (interactive programs are not supported)",
            data={"safety_level": safety_level},
        )
    except Exception as exc:
        return ToolResult(
            tool_name="run_terminal_command",
            success=False,
            output=f"Error: {exc}",
            data={"safety_level": safety_level},
        )
