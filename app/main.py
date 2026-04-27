"""FastAPI application — serves the chat UI and WebSocket endpoint."""

from __future__ import annotations

import asyncio
import json
import logging

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import HOST, PORT
from app.engine import AIEngine
from app.models.schemas import WSMessage, WSMessageType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="DevinX Ultimate", version="0.2.0")

# Serve static assets
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    logger.info("Client connected")

    approval_event: asyncio.Event = asyncio.Event()
    approval_result: list[bool] = [False]

    critical_event: asyncio.Event = asyncio.Event()
    critical_result: list[bool] = [False]

    incoming_queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def approval_callback(command: str) -> bool:
        await ws.send_text(
            WSMessage(
                type=WSMessageType.APPROVAL_REQUEST,
                data={"command": command},
            ).model_dump_json()
        )
        approval_event.clear()
        await approval_event.wait()
        return approval_result[0]

    async def critical_callback(command: str) -> bool:
        await ws.send_text(
            WSMessage(
                type=WSMessageType.CRITICAL_REQUEST,
                data={"command": command},
            ).model_dump_json()
        )
        critical_event.clear()
        await critical_event.wait()
        return critical_result[0]

    engine = AIEngine(
        approval_callback=approval_callback,
        critical_callback=critical_callback,
    )

    async def reader_task():
        try:
            while True:
                raw = await ws.receive_text()
                data = json.loads(raw)

                if data.get("type") == "approval_response":
                    approval_result[0] = data.get("approved", False)
                    approval_event.set()
                elif data.get("type") == "critical_response":
                    critical_result[0] = data.get("confirmed", False)
                    critical_event.set()
                else:
                    await incoming_queue.put(data)
        except WebSocketDisconnect:
            approval_result[0] = False
            approval_event.set()
            critical_result[0] = False
            critical_event.set()
            await incoming_queue.put(None)
        except Exception:
            approval_result[0] = False
            approval_event.set()
            critical_result[0] = False
            critical_event.set()
            await incoming_queue.put(None)

    async def processor_task():
        try:
            while True:
                data = await incoming_queue.get()
                if data is None:
                    break

                user_msg = data.get("message", "")
                if not user_msg.strip():
                    continue

                async for ws_msg in engine.chat(user_msg):
                    await ws.send_text(ws_msg.model_dump_json())
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logger.exception("Processor error: %s", exc)

    reader = asyncio.create_task(reader_task())
    processor = asyncio.create_task(processor_task())

    try:
        await asyncio.gather(reader, processor)
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
    finally:
        reader.cancel()
        processor.cancel()
        logger.info("Client disconnected")


def run():
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)


if __name__ == "__main__":
    run()
