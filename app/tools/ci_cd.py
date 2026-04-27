"""CI/CD and deployment tools — pipeline status, triggers, logs, and deployments."""

from __future__ import annotations

import datetime
from typing import Any, Callable, Coroutine

from app.models.schemas import ToolResult

# Simulated CI/CD state
_pipeline_state: dict[str, Any] = {
    "status": "idle",
    "jobs": [],
    "last_run": None,
}


async def ci_status(arguments: dict) -> ToolResult:
    """Return current CI/CD pipeline status."""
    return ToolResult(
        tool_name="ci_status",
        success=True,
        output=f"Pipeline status: {_pipeline_state['status']}\nJobs: {len(_pipeline_state['jobs'])}\nLast run: {_pipeline_state['last_run'] or 'never'}",
        data=_pipeline_state,
    )


async def ci_trigger(
    arguments: dict,
    approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
) -> ToolResult:
    """Trigger a CI/CD job. Requires approval."""
    job_name = arguments.get("job_name", "")

    if not job_name:
        return ToolResult(
            tool_name="ci_trigger",
            success=False,
            output="job_name is required",
        )

    if approval_callback is not None:
        approved = await approval_callback(f"Trigger CI job: {job_name}")
        if not approved:
            return ToolResult(
                tool_name="ci_trigger",
                success=False,
                output="CI job trigger rejected by user",
            )
    else:
        return ToolResult(
            tool_name="ci_trigger",
            success=False,
            output="CI trigger requires approval but no callback provided",
        )

    job_id = f"job-{len(_pipeline_state['jobs']) + 1}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    job = {"job_id": job_id, "name": job_name, "status": "running", "started_at": now}
    _pipeline_state["jobs"].append(job)
    _pipeline_state["status"] = "running"
    _pipeline_state["last_run"] = now

    return ToolResult(
        tool_name="ci_trigger",
        success=True,
        output=f"CI job '{job_name}' triggered. Job ID: {job_id}",
        data=job,
    )


async def ci_get_logs(arguments: dict) -> ToolResult:
    """Get logs from a CI/CD job."""
    job_id = arguments.get("job_id", "")

    if not job_id:
        return ToolResult(
            tool_name="ci_get_logs",
            success=False,
            output="job_id is required",
        )

    for job in _pipeline_state["jobs"]:
        if job["job_id"] == job_id:
            return ToolResult(
                tool_name="ci_get_logs",
                success=True,
                output=f"[{job_id}] {job['name']} — Status: {job['status']}\n(Simulated log output)",
                data={"job_id": job_id, "logs": "(simulated)", "job": job},
            )

    return ToolResult(
        tool_name="ci_get_logs",
        success=False,
        output=f"Job '{job_id}' not found",
    )


async def deploy_preview(
    arguments: dict,
    approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
) -> ToolResult:
    """Create a preview deployment. Requires approval."""
    if approval_callback is not None:
        approved = await approval_callback("Create preview deployment")
        if not approved:
            return ToolResult(
                tool_name="deploy_preview",
                success=False,
                output="Preview deployment rejected by user",
            )
    else:
        return ToolResult(
            tool_name="deploy_preview",
            success=False,
            output="Deploy requires approval but no callback provided",
        )

    return ToolResult(
        tool_name="deploy_preview",
        success=True,
        output="Preview deployment created (simulated). URL: https://preview-abc123.example.com",
        data={"url": "https://preview-abc123.example.com", "simulated": True},
    )


async def deploy_staging(
    arguments: dict,
    approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
) -> ToolResult:
    """Deploy to staging. Requires approval."""
    if approval_callback is not None:
        approved = await approval_callback("Deploy to staging environment")
        if not approved:
            return ToolResult(
                tool_name="deploy_staging",
                success=False,
                output="Staging deployment rejected by user",
            )
    else:
        return ToolResult(
            tool_name="deploy_staging",
            success=False,
            output="Deploy requires approval but no callback provided",
        )

    return ToolResult(
        tool_name="deploy_staging",
        success=True,
        output="Staging deployment successful (simulated). URL: https://staging.example.com",
        data={"url": "https://staging.example.com", "simulated": True},
    )
