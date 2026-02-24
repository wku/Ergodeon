"""AgentSession - WebSocket сессия через UnifiedRouter."""

import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any

from openrouter_agent.agent.unified_router import UnifiedRouter, ProgressCallback, RequestResult
from openrouter_agent.agent.config import PipelineConfig
from openrouter_agent.server.events import *

log = logging.getLogger(__name__)


class WebProgress(ProgressCallback):
    def __init__(self, sio, sid: str):
        self._sio = sio
        self._sid = sid
        self._confirm_future: Optional[asyncio.Future] = None

    async def _emit(self, event: str, data: Any = None):
        await self._sio.emit(event, data, to=self._sid)

    async def on_phase_start(self, phase: str, desc: str):
        await self._emit(EVT_STATUS, {"phase": phase, "description": desc})

    async def on_step_start(self, step_num, total: int, desc: str):
        await self._emit(EVT_STATUS, {
            "step": step_num, "total": total, "description": desc,
        })

    async def on_step_done(self, step_num, status: str):
        await self._emit(EVT_STATUS, {"step": step_num, "status": status})

    async def on_message(self, text: str, msg_type: str = "system"):
        await self._emit(EVT_MESSAGE, {"text": text, "type": msg_type})

    async def on_review_request(self, msg: str) -> str:
        self._confirm_future = asyncio.get_event_loop().create_future()
        await self._emit(EVT_CONFIRM, {"message": msg, "type": "review"})
        try:
            return await asyncio.wait_for(self._confirm_future, timeout=600)
        except asyncio.TimeoutError:
            return "ok"
        finally:
            self._confirm_future = None

    async def on_done(self, status: str):
        await self._emit(EVT_DONE, {"status": status})

    def resolve_confirm(self, response: str):
        if self._confirm_future and not self._confirm_future.done():
            self._confirm_future.set_result(response)


class SocketIOLogHandler(logging.Handler):
    def __init__(self, sio, sid: str):
        super().__init__()
        self._sio = sio
        self._sid = sid

    def emit(self, record):
        try:
            msg = self.format(record)
            asyncio.ensure_future(
                self._sio.emit(EVT_LOG, {"message": msg, "level": record.levelname},
                               to=self._sid)
            )
        except Exception:
            pass


class AgentSession:
    def __init__(self, sio, sid: str):
        self.sio = sio
        self.sid = sid
        self.progress = WebProgress(sio, sid)
        self._log_handler = SocketIOLogHandler(sio, sid)
        self._log_handler.setLevel(logging.INFO)
        logging.getLogger("openrouter_agent").addHandler(self._log_handler)

        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        config = PipelineConfig.from_env()
        auto_confirm = os.getenv("AUTO_CONFIRM", "false").lower() == "true"

        self.router = UnifiedRouter(
            api_key=api_key,
            model=model,
            confirmation_callback=None if auto_confirm else self._confirm_tool,
            pipeline_config=config,
            progress=self.progress,
        )
        self._tool_confirm_future: Optional[asyncio.Future] = None
        self._patch_tools_once()

    def _patch_tools_once(self):
        for name, tool in self.router.tools_registry._tools.items():
            original_run = tool.run

            async def _wrapped(args, _name=name, _orig=original_run):
                await self.sio.emit(EVT_TOOL_CALL, {"tool": _name, "args": str(args)},
                                    to=self.sid)
                result = await _orig(args)
                await self.sio.emit(EVT_TOOL_RESULT, {
                    "tool": _name, "result": str(result)[:2000],
                }, to=self.sid)
                return result

            tool.run = _wrapped

    async def _confirm_tool(self, tool_name: str, args: Any) -> bool:
        self._tool_confirm_future = asyncio.get_event_loop().create_future()
        await self.sio.emit(EVT_CONFIRM, {
            "message": f"Подтвердите {tool_name}",
            "tool": tool_name,
            "args": str(args),
            "type": "tool",
        }, to=self.sid)
        try:
            resp = await asyncio.wait_for(self._tool_confirm_future, timeout=120)
            return resp in (True, "true", "yes", "y", "да")
        except asyncio.TimeoutError:
            return False
        finally:
            self._tool_confirm_future = None

    async def handle_input(self, text: str):
        try:
            result = await self.router.handle_request(text)
            payload = {
                "workflow": result.workflow,
                "status": result.status,
                "message": result.message,
                "stage": result.stage_num,
            }
            if result.data:
                payload["data"] = result.data
            await self.sio.emit(EVT_MESSAGE, {
                "text": result.message or f"[{result.workflow}] {result.status}",
                "type": "result",
                "payload": payload,
            }, to=self.sid)
        except Exception as e:
            log.error(f"handle_input error: {e}", exc_info=True)
            await self.sio.emit(EVT_ERROR, {"error": str(e)}, to=self.sid)

    def handle_confirm_response(self, data: Dict):
        response = data.get("response", "")
        if self.progress._confirm_future and not self.progress._confirm_future.done():
            self.progress.resolve_confirm(response)
        elif self._tool_confirm_future and not self._tool_confirm_future.done():
            self._tool_confirm_future.set_result(response)

    async def handle_command(self, command: str, data: Dict = None):
        data = data or {}
        if command == "set_project":
            path = data.get("path", "")
            await self.handle_input(f"project {path}")
        elif command == "resume":
            await self.handle_input("resume")
        elif command == "reset":
            await self.handle_input("reset")
        else:
            await self.handle_input(f"{command} {json.dumps(data)}")

    def cleanup(self):
        logging.getLogger("openrouter_agent").removeHandler(self._log_handler)
