"""Web browsing tool — search and fetch pages."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from app.models.schemas import ToolResult
from app.tools.network_utils import is_internal_address

_HEADERS = {
    "User-Agent": "DevinX-Bot/0.1 (https://github.com/Cohoci4/ai-bot)"
}


async def browse_web(arguments: dict) -> ToolResult:
    action = arguments.get("action", "search")
    query_or_url = arguments.get("query_or_url", "")
    extract_pattern = arguments.get("extract_pattern")

    if not query_or_url:
        return ToolResult(tool_name="browse_web", success=False, output="query_or_url is required")

    if action == "search":
        return await _search(query_or_url)
    elif action == "open":
        return await _open_page(query_or_url, extract_pattern)
    else:
        return ToolResult(tool_name="browse_web", success=False, output=f"Unknown action: {action}")


async def _search(query: str) -> ToolResult:
    url = "https://html.duckduckgo.com/html/"
    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
            resp = await client.post(url, data={"q": query})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            results = []
            for r in soup.select(".result__body")[:5]:
                title_el = r.select_one(".result__title a")
                snippet_el = r.select_one(".result__snippet")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": title_el.get("href", ""),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })

            output = "\n\n".join(
                f"**{r['title']}**\n{r['url']}\n{r['snippet']}" for r in results
            ) or "No results found"

            return ToolResult(
                tool_name="browse_web",
                success=True,
                output=output,
                data={"results": results},
            )
    except Exception as exc:
        return ToolResult(tool_name="browse_web", success=False, output=f"Search error: {exc}")


async def _open_page(url: str, extract_pattern: str | None) -> ToolResult:
    if is_internal_address(url):
        return ToolResult(
            tool_name="browse_web",
            success=False,
            output=f"Blocked: internal/private network address ({url}). Browsing internal IPs is restricted.",
        )

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=15, follow_redirects=False) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            if extract_pattern:
                elements = soup.select(extract_pattern)
                text = "\n".join(el.get_text(strip=True) for el in elements)
            else:
                text = soup.get_text(separator="\n", strip=True)

            if len(text) > 8000:
                text = text[:8000] + "\n... (truncated)"

            return ToolResult(
                tool_name="browse_web",
                success=True,
                output=text,
                data={"url": url, "length": len(text)},
            )
    except Exception as exc:
        return ToolResult(tool_name="browse_web", success=False, output=f"Fetch error: {exc}")
