"""
FastAPI Backend - WebSocket + REST API bridge between React UI and Python AI engines
"""

import asyncio
import json
import uuid
import threading
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from audio.audio_manager import AudioManager
from ai.ai_controller import AIController
from core.logging_config import get_logger
from config.settings import config
from domain.controller import AppController, RecordingState

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_queue: asyncio.Queue = asyncio.Queue()

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._event_loop = loop

    async def connect(self, ws: WebSocket):
        await ws.accept()
        client_id = str(uuid.uuid4())
        self.active[client_id] = ws
        logger.info(f"WebSocket client connected: {client_id}")
        return client_id

    def disconnect(self, client_id: str):
        self.active.pop(client_id, None)
        logger.info(f"WebSocket client disconnected: {client_id}")

    async def broadcast(self, message: dict):
        msg_type = message.get("type", "")
        if msg_type == "audio_level":
            level = message.get("level", 0)
            logger.info(f"[BROADCAST] audio_level={level:.3f} to {len(self.active)} clients")
        if not self.active:
            return
        dead = []
        for client_id, ws in self.active.items():
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(client_id)
        for cid in dead:
            self.active.pop(cid, None)

    async def send_to(self, client_id: str, message: dict):
        ws = self.active.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.active.pop(client_id, None)

    def broadcast_sync(self, message: dict):
        if self._event_loop and self._event_loop.is_running():
            self._event_loop.call_soon_threadsafe(
                lambda m=message: self._async_queue.put_nowait(m)
            )
        else:
            logger.warning("[WS] Cannot broadcast - event loop not running")

    async def process_queue(self):
        logger.info("[WS] process_queue started")
        while True:
            message = await self._async_queue.get()
            await self.broadcast(message)


controller: Optional[AppController] = None
ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global controller
    controller = AppController()

    ws_manager.set_event_loop(asyncio.get_event_loop())
    queue_task = asyncio.create_task(ws_manager.process_queue())

    def on_subtitle_update(original, translated, speaker_id):
        bubble_id = str(uuid.uuid4())
        logger.info(f"[WS] subtitle_update: '{original[:50]}...' -> '{translated[:30]}...'")
        ws_manager.broadcast_sync({
            "type": "subtitle_update",
            "bubble_id": bubble_id,
            "original": original,
            "translated": translated,
            "speaker_id": speaker_id,
        })
        return bubble_id

    def on_translation_complete(bubble_id, translated):
        logger.info(f"[WS] translation_complete: '{translated[:30]}...'")
        ws_manager.broadcast_sync({
            "type": "translation_complete",
            "bubble_id": bubble_id,
            "translated": translated,
        })

    def on_status_change(status, color):
        logger.info(f"[WS] status_change: {status}")
        ws_manager.broadcast_sync({
            "type": "status_change",
            "status": status,
            "color": color,
        })

    def on_audio_level(level):
        ws_manager.broadcast_sync({
            "type": "audio_level",
            "level": level,
        })

    controller.callbacks.on_subtitle_update = on_subtitle_update
    controller.callbacks.on_translation_complete = on_translation_complete
    controller.callbacks.on_status_change = on_status_change
    controller.callbacks.on_audio_level = on_audio_level

    success = controller.initialize_engines()
    ws_manager.broadcast_sync({
        "type": "status_change",
        "status": "已連接" if success else "連接失敗",
        "color": "#10b981" if success else "#F43F5E",
    })
    ws_manager.broadcast_sync({
        "type": "engines_ready",
        "ready": success,
    })

    yield

    queue_task.cancel()
    if controller:
        controller.cleanup()
    logger.info("Backend shutdown complete")


app = FastAPI(title="QwenASR Pro", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/config")
async def get_config():
    return controller.get_current_config() if controller else {}


@app.post("/api/config")
async def update_config(settings: Dict[str, Any]):
    if controller:
        controller.update_config(settings)
        return {"status": "ok"}
    return {"status": "error", "message": "Controller not initialized"}


@app.get("/api/status")
async def get_status():
    if controller:
        return {
            "engines_ready": controller.is_engines_ready(),
            "is_recording": controller.is_recording,
            "audio_source": controller.audio_source,
            "src_lang": controller.src_lang,
            "tgt_lang": controller.tgt_lang,
        }
    return {"engines_ready": False, "is_recording": False}


@app.get("/api/devices")
async def get_devices(source: str = "mic"):
    if controller:
        devices = controller.get_audio_devices(source)
        return {"devices": devices, "parsed": [
            {"name": d, "index": controller.audio_mgr.parse_device_index(d)} for d in devices
        ]}
    return {"devices": [], "parsed": []}


@app.get("/api/apps")
async def get_apps():
    if controller:
        apps = controller.get_audio_apps()
        return {"apps": [{"name": n, "pid": p} for n, p in apps]}
    return {"apps": []}


@app.post("/api/source")
async def set_source(data: Dict[str, Any]):
    if controller:
        controller.set_audio_source(data.get("source", "mic"), data.get("target_app", ""))
        return {"status": "ok"}
    return {"status": "error"}


@app.post("/api/lang")
async def set_lang(data: Dict[str, Any]):
    if controller:
        controller.src_lang = data.get("src", "auto")
        controller.tgt_lang = data.get("tgt", "zh")
        if controller.ai_ctrl.translate_engine:
            controller.ai_ctrl.translate_engine.target_lang = data.get("tgt", "zh")
        return {"status": "ok"}
    return {"status": "error"}


@app.post("/api/record/start")
async def start_recording(data: Dict[str, Any] = None):
    if controller:
        device_index = None
        if data:
            device_index = data.get("device_index")
            if device_index is not None:
                device_index = int(device_index)
        logger.info(f"Starting recording with device_index={device_index}")
        success = controller.start_recording(device_index=device_index)
        return {"success": success}
    return {"success": False}


@app.post("/api/record/stop")
async def stop_recording():
    if controller:
        controller.stop_recording()
        return {"status": "ok"}
    return {"status": "error"}


@app.post("/api/export/srt")
async def export_srt(data: Dict[str, Any]):
    if controller:
        filepath = data.get("filepath", "subtitle.srt")
        success = controller.save_subtitles(filepath)
        return {"success": success}
    return {"success": False}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    client_id = await ws_manager.connect(ws)

    if controller:
        await ws_manager.send_to(client_id, {
            "type": "initial_state",
            "engines_ready": controller.is_engines_ready(),
            "is_recording": controller.is_recording,
            "audio_source": controller.audio_source,
            "src_lang": controller.src_lang,
            "tgt_lang": controller.tgt_lang,
            "config": controller.get_current_config(),
            "asr_ready": controller.ai_ctrl.asr_engine.loaded if controller.ai_ctrl.asr_engine else False,
            "translate_ready": controller.ai_ctrl.translate_engine.loaded if controller.ai_ctrl.translate_engine else False,
        })
        if controller.is_engines_ready():
            await ws_manager.send_to(client_id, {"type": "status_change", "status": "已連接", "color": "#10b981"})
        else:
            await ws_manager.send_to(client_id, {"type": "status_change", "status": "連接失敗", "color": "#F43F5E"})
        await ws_manager.send_to(client_id, {"type": "engines_ready", "ready": controller.is_engines_ready()})

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "start_recording":
                device_index = data.get("device_index")
                if device_index is not None:
                    device_index = int(device_index)
                success = controller.start_recording(device_index=device_index) if controller else False
                await ws_manager.send_to(client_id, {"type": "record_state", "is_recording": success})

            elif msg_type == "stop_recording":
                if controller:
                    controller.stop_recording()
                await ws_manager.send_to(client_id, {"type": "record_state", "is_recording": False})

            elif msg_type == "set_source":
                source = data.get("source", "mic")
                target_app = data.get("target_app", "")
                logger.info(f"[WS] set_source: source={source}, target_app={target_app}")
                if controller:
                    was_recording = controller.is_recording
                    if was_recording:
                        logger.info("[WS] Source changed while recording, restarting...")
                        controller.stop_recording()
                        await asyncio.sleep(0.5)
                    controller.set_audio_source(source, target_app)
                    logger.info(f"[WS] audio_source now = {controller.audio_source}")
                    if was_recording:
                        success = controller.start_recording(device_index=None)
                        await ws_manager.send_to(client_id, {"type": "record_state", "is_recording": success})
                        logger.info(f"[WS] Recording restarted with source={source}, success={success}")

            elif msg_type == "set_lang":
                if controller:
                    controller.src_lang = data.get("src", "auto")
                    controller.tgt_lang = data.get("tgt", "zh")
                    if controller.ai_ctrl.translate_engine:
                        controller.ai_ctrl.translate_engine.target_lang = data.get("tgt", "zh")

            elif msg_type == "update_config":
                if controller:
                    controller.update_config(data.get("settings", {}))

            elif msg_type == "ping":
                await ws_manager.send_to(client_id, {"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        ws_manager.disconnect(client_id)