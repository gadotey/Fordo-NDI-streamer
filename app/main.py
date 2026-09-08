import asyncio
import os
import platform
import socket

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from app.ndi_discovery import discovery


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


@app.websocket("/ws/sources")
async def source_websocket(websocket: WebSocket):
    await websocket.accept()

    previous = None

    try:
        while True:
            current = discovery.get_sources()

            if current != previous:
                await websocket.send_json(
                    {
                        "count": len(current),
                        "sources": current,
                    }
                )
                previous = current

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
