"""Screenshot and visual comparison tools."""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

from app.config import WORKSPACE_DIR
from app.models.schemas import ToolResult


async def take_screenshot(arguments: dict) -> ToolResult:
    """Capture a screenshot of a web page (simulated — stores page HTML snapshot)."""
    url = arguments.get("url", "")
    full_page = arguments.get("full_page", False)

    if not url:
        return ToolResult(
            tool_name="take_screenshot",
            success=False,
            output="url is required",
        )

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        # Save a text snapshot
        screenshots_dir = WORKSPACE_DIR / ".screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"screenshot_{url_hash}.html"
        filepath = screenshots_dir / filename
        filepath.write_text(resp.text[:50000], encoding="utf-8")

        return ToolResult(
            tool_name="take_screenshot",
            success=True,
            output=f"Screenshot saved: {filepath.relative_to(WORKSPACE_DIR)}\nURL: {url}\nFull page: {full_page}\nSize: {len(resp.text)} bytes",
            data={
                "path": str(filepath.relative_to(WORKSPACE_DIR)),
                "url": url,
                "full_page": full_page,
            },
        )
    except Exception as exc:
        return ToolResult(
            tool_name="take_screenshot",
            success=False,
            output=f"Screenshot failed: {exc}",
        )


async def visual_comparison(arguments: dict) -> ToolResult:
    """Compare two screenshots and return a similarity score."""
    path1 = arguments.get("screenshot1_path", "")
    path2 = arguments.get("screenshot2_path", "")

    if not path1 or not path2:
        return ToolResult(
            tool_name="visual_comparison",
            success=False,
            output="Both screenshot1_path and screenshot2_path are required",
        )

    file1 = WORKSPACE_DIR / path1
    file2 = WORKSPACE_DIR / path2

    if not file1.exists():
        return ToolResult(
            tool_name="visual_comparison",
            success=False,
            output=f"File not found: {path1}",
        )
    if not file2.exists():
        return ToolResult(
            tool_name="visual_comparison",
            success=False,
            output=f"File not found: {path2}",
        )

    # Simple text-based comparison (in production this would be pixel-based)
    content1 = file1.read_text(encoding="utf-8", errors="replace")
    content2 = file2.read_text(encoding="utf-8", errors="replace")

    if content1 == content2:
        similarity = 100.0
    else:
        # Simple character-level similarity
        common = sum(1 for a, b in zip(content1, content2) if a == b)
        max_len = max(len(content1), len(content2), 1)
        similarity = round((common / max_len) * 100, 2)

    return ToolResult(
        tool_name="visual_comparison",
        success=True,
        output=f"Similarity: {similarity}%\nFile 1: {path1} ({len(content1)} chars)\nFile 2: {path2} ({len(content2)} chars)",
        data={
            "similarity_percent": similarity,
            "file1": path1,
            "file2": path2,
            "identical": similarity == 100.0,
        },
    )
