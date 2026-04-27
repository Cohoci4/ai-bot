"""Monitoring tool — health checks for running services."""

from __future__ import annotations

import time

import httpx

from app.models.schemas import ToolResult


async def app_healthcheck(arguments: dict) -> ToolResult:
    """Check the health of a running service endpoint."""
    endpoint = arguments.get("endpoint", "")

    if not endpoint:
        return ToolResult(
            tool_name="app_healthcheck",
            success=False,
            output="endpoint is required",
        )

    # Block internal network addresses unless explicitly allowed
    blocked_prefixes = ("http://localhost", "http://127.0.0.1", "http://10.", "http://192.168.")
    if any(endpoint.lower().startswith(p) for p in blocked_prefixes):
        return ToolResult(
            tool_name="app_healthcheck",
            success=False,
            output=f"Blocked: internal network address ({endpoint}). Health checks to internal IPs are restricted.",
        )

    try:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(endpoint)
        elapsed_ms = round((time.monotonic() - start) * 1000)

        healthy = 200 <= resp.status_code < 400
        return ToolResult(
            tool_name="app_healthcheck",
            success=healthy,
            output=f"{'Healthy' if healthy else 'Unhealthy'} — Status: {resp.status_code}, Response time: {elapsed_ms}ms",
            data={
                "endpoint": endpoint,
                "status_code": resp.status_code,
                "response_time_ms": elapsed_ms,
                "healthy": healthy,
            },
        )
    except Exception as exc:
        return ToolResult(
            tool_name="app_healthcheck",
            success=False,
            output=f"Health check failed: {exc}",
            data={"endpoint": endpoint},
        )
