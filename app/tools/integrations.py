"""Team integration tools — Jira, Slack, and report generation."""

from __future__ import annotations

import datetime
import html as html_module
from typing import Any

from app.models.schemas import ToolResult


async def jira_update(arguments: dict) -> ToolResult:
    """Update a Jira issue status and add a comment."""
    issue_key = arguments.get("issue_key", "")
    status = arguments.get("status", "")
    comment = arguments.get("comment", "")

    if not issue_key:
        return ToolResult(
            tool_name="jira_update",
            success=False,
            output="issue_key is required",
        )

    parts = [f"Issue: {issue_key}"]
    if status:
        parts.append(f"Status → {status}")
    if comment:
        parts.append(f"Comment: {comment}")

    return ToolResult(
        tool_name="jira_update",
        success=True,
        output=f"Jira updated (simulated): {' | '.join(parts)}",
        data={
            "issue_key": issue_key,
            "status": status,
            "comment": comment,
            "simulated": True,
        },
    )


async def slack_notify(arguments: dict) -> ToolResult:
    """Send a notification to a Slack channel."""
    channel = arguments.get("channel", "")
    message = arguments.get("message", "")

    if not channel or not message:
        return ToolResult(
            tool_name="slack_notify",
            success=False,
            output="Both channel and message are required",
        )

    return ToolResult(
        tool_name="slack_notify",
        success=True,
        output=f"Slack notification sent (simulated): #{channel} — {message[:200]}",
        data={"channel": channel, "message": message, "simulated": True},
    )


def generate_report(
    arguments: dict,
    tasks: list[dict[str, Any]] | None = None,
    assumptions: list[dict[str, str]] | None = None,
) -> ToolResult:
    """Generate a standalone HTML report of current task status."""
    title = arguments.get("title", "DevinX Report")
    include_screenshots = arguments.get("include_screenshots", False)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    tasks = tasks or []
    assumptions = assumptions or []

    task_rows = ""
    for t in tasks:
        status_icon = {"pending": "&#x23F3;", "in_progress": "&#x1F504;", "done": "&#x2705;"}.get(
            t.get("status", "pending"), "&#x2753;"
        )
        task_rows += f"""<tr>
            <td>{status_icon}</td>
            <td>{html_module.escape(t.get('task_id', ''))}</td>
            <td>{html_module.escape(t.get('title', ''))}</td>
            <td>{html_module.escape(t.get('status', ''))}</td>
            <td>{html_module.escape(t.get('details', ''))}</td>
        </tr>"""

    assumption_items = ""
    for a in assumptions:
        assumption_items += f"<li><strong>{html_module.escape(a.get('assumption', ''))}</strong>"
        ctx = a.get("context", "")
        if ctx:
            assumption_items += f" <em>({html_module.escape(ctx)})</em>"
        assumption_items += "</li>"

    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html_module.escape(title)}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #0d1117; color: #e6edf3; }}
h1 {{ color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 12px; }}
h2 {{ color: #bc8cff; margin-top: 32px; }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
th, td {{ padding: 8px 12px; border: 1px solid #30363d; text-align: left; }}
th {{ background: #161b22; color: #8b949e; font-size: 12px; text-transform: uppercase; }}
tr:hover {{ background: #161b22; }}
ul {{ padding-left: 20px; }}
li {{ margin-bottom: 8px; }}
.meta {{ color: #8b949e; font-size: 13px; }}
</style>
</head>
<body>
<h1>{html_module.escape(title)}</h1>
<p class="meta">Generated: {now}</p>

<h2>Tasks ({len(tasks)})</h2>
{"<table><tr><th></th><th>ID</th><th>Title</th><th>Status</th><th>Details</th></tr>" + task_rows + "</table>" if tasks else "<p>No tasks.</p>"}

<h2>Assumptions ({len(assumptions)})</h2>
{"<ul>" + assumption_items + "</ul>" if assumptions else "<p>No assumptions logged.</p>"}

</body>
</html>"""

    return ToolResult(
        tool_name="generate_report",
        success=True,
        output=f"Report generated: {title} ({len(tasks)} tasks, {len(assumptions)} assumptions)",
        data={"html": report_html, "title": title},
    )
