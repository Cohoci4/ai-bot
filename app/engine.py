"""AI reasoning engine — manages conversation, tool calls, and streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Callable, Coroutine

from openai import AsyncOpenAI, RateLimitError

from app.config import LLM_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL
from app.models.schemas import ToolCall, ToolResult, WSMessage, WSMessageType
from app.system_prompt import SYSTEM_PROMPT, TOOL_DEFINITIONS
from app.tools.assumptions import AssumptionsManager
from app.tools.executor import ToolExecutor
from app.tools.task_manager import TaskManager

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10


class AIEngine:
    """Manages a conversation with the LLM and executes tool calls."""

    def __init__(
        self,
        approval_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
        critical_callback: Callable[[str], Coroutine[Any, Any, bool]] | None = None,
    ) -> None:
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=LLM_BASE_URL)
        self.task_manager = TaskManager()
        self.assumptions_manager = AssumptionsManager()
        self.tool_executor = ToolExecutor(
            self.task_manager,
            self.assumptions_manager,
            approval_callback,
            critical_callback,
        )
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    async def chat(self, user_message: str) -> AsyncIterator[WSMessage]:
        """Process a user message and yield WebSocket messages (chunks, tool calls, etc.)."""
        self.messages.append({"role": "user", "content": user_message})

        for _round in range(MAX_TOOL_ROUNDS):
            response = None
            for _retry in range(3):
                try:
                    response = await self.client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=self.messages,
                        tools=TOOL_DEFINITIONS,
                        tool_choice="auto",
                        stream=True,
                    )
                    break
                except RateLimitError as exc:
                    wait_secs = 15 * (_retry + 1)
                    logger.warning("Rate limited, retrying in %ds: %s", wait_secs, exc)
                    yield WSMessage(
                        type=WSMessageType.ASSISTANT_CHUNK,
                        data={"content": f"\n⏳ Rate limited, retrying in {wait_secs}s...\n"},
                    )
                    await asyncio.sleep(wait_secs)
                except Exception as exc:
                    yield WSMessage(
                        type=WSMessageType.ERROR,
                        data={"message": f"API error: {exc}"},
                    )
                    return
            if response is None:
                yield WSMessage(
                    type=WSMessageType.ERROR,
                    data={"message": "Rate limit exceeded after retries. Please wait a minute and try again."},
                )
                return

            collected_content = ""
            tool_calls_data: dict[int, dict[str, Any]] = {}

            try:
                async for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta is None:
                        continue

                    if delta.content:
                        collected_content += delta.content
                        yield WSMessage(
                            type=WSMessageType.ASSISTANT_CHUNK,
                            data={"content": delta.content},
                        )

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
            except Exception as exc:
                logger.warning("Streaming error, retrying without stream: %s", exc)
                collected_content = ""
                tool_calls_data = {}
                yield WSMessage(
                    type=WSMessageType.CONTENT_RESET,
                    data={},
                )
                try:
                    fallback = await self.client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=self.messages,
                        tools=TOOL_DEFINITIONS,
                        tool_choice="auto",
                        stream=False,
                    )
                    choice = fallback.choices[0]
                    if choice.message.content:
                        collected_content = choice.message.content
                        yield WSMessage(
                            type=WSMessageType.ASSISTANT_CHUNK,
                            data={"content": collected_content},
                        )
                    if choice.message.tool_calls:
                        for tc in choice.message.tool_calls:
                            tool_calls_data[len(tool_calls_data)] = {
                                "id": tc.id,
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                except Exception as exc2:
                    logger.exception("Fallback also failed: %s", exc2)
                    yield WSMessage(
                        type=WSMessageType.ERROR,
                        data={"message": f"AI error: {exc2}"},
                    )
                    return

            if collected_content and not tool_calls_data:
                self.messages.append({"role": "assistant", "content": collected_content})
                yield WSMessage(type=WSMessageType.ASSISTANT_DONE, data={})
                return

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

                # Task sidebar update
                if tool_name == "task":
                    yield WSMessage(
                        type=WSMessageType.TASK_UPDATE,
                        data={"tasks": [t.model_dump() for t in self.task_manager.tasks]},
                    )

                # Assumptions update
                if tool_name == "assumptions_log":
                    yield WSMessage(
                        type=WSMessageType.ASSUMPTIONS_UPDATE,
                        data={"assumptions": self.assumptions_manager.assumptions},
                    )

                # Report generation — send HTML to client
                if tool_name == "generate_report" and result.success and result.data:
                    yield WSMessage(
                        type=WSMessageType.REPORT,
                        data={"html": result.data.get("html", ""), "title": result.data.get("title", "")},
                    )

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc_data["id"],
                    "content": result.output,
                })

        yield WSMessage(
            type=WSMessageType.ERROR,
            data={"message": "Maximum tool call rounds reached"},
        )
