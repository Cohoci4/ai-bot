"""Memory and learning tools — persistent knowledge store."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import WORKSPACE_DIR
from app.models.schemas import ToolResult

MEMORY_FILE = WORKSPACE_DIR / ".devinx_memory.json"

VALID_CATEGORIES = {"architecture", "convention", "user_preference", "error_solution"}


def _load_memory() -> dict[str, dict[str, str]]:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_memory(data: dict[str, dict[str, str]]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def memorize(arguments: dict) -> ToolResult:
    """Store a piece of knowledge in persistent memory."""
    category = arguments.get("category", "")
    key = arguments.get("key", "")
    value = arguments.get("value", "")
    overwrite = arguments.get("overwrite", False)

    if category not in VALID_CATEGORIES:
        return ToolResult(
            tool_name="memorize",
            success=False,
            output=f"Invalid category: {category}. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}",
        )

    if not key or not value:
        return ToolResult(
            tool_name="memorize",
            success=False,
            output="Both key and value are required",
        )

    memory = _load_memory()
    if category not in memory:
        memory[category] = {}

    if key in memory[category] and not overwrite:
        return ToolResult(
            tool_name="memorize",
            success=False,
            output=f"Key '{key}' already exists in '{category}'. Set overwrite=true to replace.",
        )

    memory[category][key] = value
    _save_memory(memory)

    return ToolResult(
        tool_name="memorize",
        success=True,
        output=f"Stored [{category}] {key} = {value[:100]}{'...' if len(value) > 100 else ''}",
        data={"category": category, "key": key},
    )


def recall(arguments: dict) -> ToolResult:
    """Retrieve stored knowledge from memory."""
    category = arguments.get("category", "")
    key = arguments.get("key", "")

    if not category or not key:
        return ToolResult(
            tool_name="recall",
            success=False,
            output="Both category and key are required",
        )

    memory = _load_memory()
    cat_data = memory.get(category, {})

    if key in cat_data:
        return ToolResult(
            tool_name="recall",
            success=True,
            output=cat_data[key],
            data={"category": category, "key": key, "value": cat_data[key]},
        )

    # Partial match — return all keys in the category
    if cat_data:
        keys = ", ".join(sorted(cat_data.keys()))
        return ToolResult(
            tool_name="recall",
            success=False,
            output=f"Key '{key}' not found in '{category}'. Available keys: {keys}",
        )

    return ToolResult(
        tool_name="recall",
        success=False,
        output=f"No memories stored in category '{category}'",
    )


def learn_from_mistake(arguments: dict) -> ToolResult:
    """Save a symptom-solution pair for future reference."""
    issue_description = arguments.get("issue_description", "")
    resolution = arguments.get("resolution", "")

    if not issue_description or not resolution:
        return ToolResult(
            tool_name="learn_from_mistake",
            success=False,
            output="Both issue_description and resolution are required",
        )

    memory = _load_memory()
    if "error_solution" not in memory:
        memory["error_solution"] = {}

    # Use a sanitized key from the issue description
    key = issue_description[:80].replace(" ", "_").lower()
    memory["error_solution"][key] = json.dumps({
        "issue": issue_description,
        "resolution": resolution,
    }, ensure_ascii=False)
    _save_memory(memory)

    return ToolResult(
        tool_name="learn_from_mistake",
        success=True,
        output=f"Learned: {issue_description[:100]}\nResolution: {resolution[:100]}",
        data={"key": key},
    )
