"""Monitoring tool — health checks for running services."""

from __future__ import annotations

import ipaddress
import socket
import time
from urllib.parse import urlparse

import httpx

from app.models.schemas import ToolResult


def _is_internal_address(url: str) -> bool:
    """Check if a URL resolves to a private/loopback/link-local IP address."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return True

        # Resolve hostname to IP
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
    except (socket.gaierror, ValueError, OSError):
        return True
    return False


async def app_healthcheck(arguments: dict) -> ToolResult:
    """Check the health of a running service endpoint."""
    endpoint = arguments.get("endpoint", "")

    if not endpoint:
        return ToolResult(
            tool_name="app_healthcheck",
            success=False,
            output="endpoint is required",
        )

    if _is_internal_address(endpoint):
        return ToolResult(
            tool_name="app_healthcheck",
            success=False,
            output=f"Blocked: internal/private network address ({endpoint}). Health checks to internal IPs are restricted.",
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
