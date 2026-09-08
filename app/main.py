import asyncio
import os
import platform
import socket

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from app.ndi_discovery import discovery
from app.system_metrics import get_system_metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    discovery.start()
    yield
    discovery.stop()


app = FastAPI(
    title="Fordo NDI Streamer",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def dashboard():
    return FileResponse("app/static/index.html")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "hostname": socket.gethostname(),
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "pid": os.getpid(),
    }


@app.get("/api/sources")
async def sources():
    found = discovery.get_sources()

    return {
        "count": len(found),
        "sources": found,
    }


@app.get("/api/system")
async def system():
    metrics = get_system_metrics()
    metrics["ndi_source_count"] = len(discovery.get_sources())
    metrics["discovery_running"] = discovery._running
    return metrics


@app.websocket("/ws/status")
async def status_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            sources = discovery.get_sources()
            metrics = get_system_metrics()

            await websocket.send_json({
                "sources": {
                    "count": len(sources),
                    "items": sources,
                },
                "system": metrics,
                "discovery_running": discovery._running,
            })

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        pass
