"""Socket.IO сервер для Ergodeon."""

import os
import logging
from pathlib import Path

import socketio
from litestar import Litestar, get

from openrouter_agent.server.agent_session import AgentSession
from openrouter_agent.server.events import (
    EVT_INPUT, EVT_CONFIRM_RESP, EVT_COMMAND,
)

log = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
)
sessions: dict[str, AgentSession] = {}


@sio.event
async def connect(sid, environ):
    log.info(f"client connected: {sid}")
    sessions[sid] = AgentSession(sio, sid)


@sio.event
async def disconnect(sid):
    log.info(f"client disconnected: {sid}")
    session = sessions.pop(sid, None)
    if session:
        session.cleanup()


@sio.on(EVT_INPUT)
async def on_input(sid, data):
    session = sessions.get(sid)
    if not session:
        return
    text = data if isinstance(data, str) else data.get("text", "")
    await session.handle_input(text)


@sio.on(EVT_CONFIRM_RESP)
async def on_confirm_response(sid, data):
    session = sessions.get(sid)
    if session:
        session.handle_confirm_response(data if isinstance(data, dict) else {"response": data})


@sio.on(EVT_COMMAND)
async def on_command(sid, data):
    session = sessions.get(sid)
    if not session:
        return
    command = data.get("command", "") if isinstance(data, dict) else str(data)
    await session.handle_command(command, data if isinstance(data, dict) else {})


@get("/health")
async def health() -> dict:
    return {"status": "ok", "sessions": len(sessions)}


_litestar = Litestar(route_handlers=[health])

# uvicorn openrouter_agent.server.app:app подхватывает этот объект
app = socketio.ASGIApp(sio, other_asgi_app=_litestar)
