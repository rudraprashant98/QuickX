from fastapi import APIRouter, WebSocket

from app.utils.visualization import hub

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/telemetry")
async def telemetry_ws(websocket: WebSocket):
    await hub.register(websocket, "telemetry")
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        await hub.unregister(websocket)


@router.websocket("/path")
async def path_ws(websocket: WebSocket):
    await hub.register(websocket, "path")
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        await hub.unregister(websocket)
