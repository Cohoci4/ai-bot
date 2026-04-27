"""Self-diagnosis and recovery tools."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from app.config import WORKSPACE_DIR
from app.models.schemas import ToolResult


async def self_test(arguments: dict) -> ToolResult:
    """Verify connectivity to all subsystems and report status."""
    results: dict[str, str] = {}

    # Check workspace directory
    results["workspace"] = "ok" if WORKSPACE_DIR.is_dir() else "missing"

    # Check git
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        results["git"] = "ok" if proc.returncode == 0 else "error"
    except Exception:
        results["git"] = "unavailable"

    # Check terminal
    try:
        proc = await asyncio.create_subprocess_exec(
            "echo", "test",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        results["terminal"] = "ok" if proc.returncode == 0 else "error"
    except Exception:
        results["terminal"] = "unavailable"

    # Check Python
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        results["python"] = stdout.decode().strip() if proc.returncode == 0 else "error"
    except Exception:
        results["python"] = "unavailable"

    # Check memory file
    memory_file = WORKSPACE_DIR / ".devinx_memory.json"
    results["memory_store"] = "ok" if memory_file.exists() else "empty (no saved knowledge)"

    # Check OpenAI key
    results["openai_key"] = "configured" if os.getenv("OPENAI_API_KEY") else "not set"

    all_ok = all(v in ("ok", "configured") or v.startswith("Python") for v in results.values())
    lines = [f"  {k}: {v}" for k, v in results.items()]

    return ToolResult(
        tool_name="self_test",
        success=True,
        output=f"Self-test {'PASSED' if all_ok else 'PARTIAL'}:\n" + "\n".join(lines),
        data={"subsystems": results, "all_ok": all_ok},
    )


async def restore_state(arguments: dict) -> ToolResult:
    """Re-initialize workspace after a restart."""
    actions: list[str] = []

    # Check if workspace exists
    if not WORKSPACE_DIR.is_dir():
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        actions.append("Created workspace directory")

    # Check if there's a git repo in workspace
    git_dir = WORKSPACE_DIR / ".git"
    if git_dir.is_dir():
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "pull", "--rebase",
                cwd=str(WORKSPACE_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            output = stdout.decode(errors="replace")
            actions.append(f"Git pull: {output.strip()[:200]}")
        except Exception as exc:
            actions.append(f"Git pull failed: {exc}")
    else:
        actions.append("No git repository found in workspace")

    # Check for saved memory
    memory_file = WORKSPACE_DIR / ".devinx_memory.json"
    if memory_file.exists():
        actions.append("Memory store found and accessible")
    else:
        actions.append("No saved memory found (fresh start)")

    return ToolResult(
        tool_name="restore_state",
        success=True,
        output="State restored:\n" + "\n".join(f"  - {a}" for a in actions),
        data={"actions": actions},
    )
