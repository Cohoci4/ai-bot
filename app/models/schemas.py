"""Pydantic models for request/response schemas and tool definitions."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Task models
# ---------------------------------------------------------------------------
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(BaseModel):
    task_id: str
    title: str
    status: TaskStatus = TaskStatus.PENDING
    details: str = ""


# ---------------------------------------------------------------------------
# Tool call models
# ---------------------------------------------------------------------------
class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: str
    data: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Chat models
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    tool_calls: list[ToolCall] | None = None
    tool_results: list[ToolResult] | None = None


# ---------------------------------------------------------------------------
# WebSocket message types
# ---------------------------------------------------------------------------
class WSMessageType(str, Enum):
    USER_MESSAGE = "user_message"
    ASSISTANT_CHUNK = "assistant_chunk"
    ASSISTANT_DONE = "assistant_done"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TASK_UPDATE = "task_update"
    ERROR = "error"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"


class WSMessage(BaseModel):
    type: WSMessageType
    data: dict[str, Any] = Field(default_factory=dict)
