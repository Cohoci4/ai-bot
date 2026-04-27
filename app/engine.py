"""AI reasoning engine — manages conversation, tool calls, and streaming."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Callable, Coroutine

from openai import AsyncOpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.models.schemas import ToolCall, ToolResult, WSMessage, WSMessageType
from app.system_prompt import SYSTEM_PROMPT, TOOL_DEFINITIONS
from app.tools.executor import ToolExecutor
from app.tools.task_manager import TaskManager

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10


class AIEngine:
    """Manages a conversation with the LLM and executes tool calls."""

    def __init__(
        self,
        approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
    ) -> None:
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.task_manager = TaskManager()
        self.tool_executor = ToolExecutor(self.task_manager, approval_callback)
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    async def chat(self, user_message: str) -> AsyncIterator[WSMessage]:
        """Process a user message and yield WebSocket messages (chunks, tool calls, etc.)."""
        self.messages.append({"role": "user", "content": user_message})

        for _round in range(MAX_TOOL_ROUNDS):
            try:
                response = await self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=self.messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    stream=True,
                )
            except Exception as exc:
                yield WSMessage(
                    type=WSMessageType.ERROR,
                    data={"message": f"OpenAI API error: {exc}"},
                )
                return

            collected_content = ""
            tool_calls_data: dict[int, dict[str, Any]] = {}

            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                # Stream text content
                if delta.content:
                    collected_content += delta.content
                    yield WSMessage(
                        type=WSMessageType.ASSISTANT_CHUNK,
                        data={"content": delta.content},
                    )

                # Collect tool call fragments
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_data:
                            tool_calls_data[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.id:
                            tool_calls_data[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_data[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_data[idx]["arguments"] += tc.function.arguments

            # If we got text content with no tool calls, we're done
            if collected_content and not tool_calls_data:
                self.messages.append({"role": "assistant", "content": collected_content})
                yield WSMessage(type=WSMessageType.ASSISTANT_DONE, data={})
                return

            # Build the assistant message with tool calls
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": collected_content or None}
            if tool_calls_data:
                assistant_msg["tool_calls"] = []
                for idx in sorted(tool_calls_data):
                    tc_data = tool_calls_data[idx]
                    assistant_msg["tool_calls"].append({
                        "id": tc_data["id"],
                        "type": "function",
                        "function": {
                            "name": tc_data["name"],
                            "arguments": tc_data["arguments"],
                        },
                    })
            self.messages.append(assistant_msg)

            if not tool_calls_data:
                yield WSMessage(type=WSMessageType.ASSISTANT_DONE, data={})
                return

            # Execute each tool call
            for idx in sorted(tool_calls_data):
                tc_data = tool_calls_data[idx]
                tool_name = tc_data["name"]

                try:
                    arguments = json.loads(tc_data["arguments"]) if tc_data["arguments"] else {}
                except json.JSONDecodeError:
                    arguments = {}

                yield WSMessage(
                    type=WSMessageType.TOOL_CALL,
                    data={"name": tool_name, "arguments": arguments},
                )

                tool_call = ToolCall(name=tool_name, arguments=arguments)
                result: ToolResult = await self.tool_executor.execute(tool_call)

                yield WSMessage(
                    type=WSMessageType.TOOL_RESULT,
                    data={
                        "tool_name": result.tool_name,
                        "success": result.success,
                        "output": result.output,
                    },
                )

                # If this is a task update, send task info
                if tool_name == "task":
                    yield WSMessage(
                        type=WSMessageType.TASK_UPDATE,
                        data={"tasks": [t.model_dump() for t in self.task_manager.tasks]},
                    )

                # Add tool result to conversation
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc_data["id"],
                    "content": result.output,
                })

            # Loop continues so the model can process tool results

        yield WSMessage(
            type=WSMessageType.ERROR,
            data={"message": "Maximum tool call rounds reached"},
        )
