from __future__ import annotations

import asyncio
import time
from typing import Set

from fastapi import WebSocket

from app.core.metrics import TELEMETRY_LATENCY, TELEMETRY_THROUGHPUT


class VisualizationHub:
    def __init__(self) -> None:
        self.telemetry_clients: Set[WebSocket] = set()
        self.path_clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def register(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        async with self._lock:
            if channel == "telemetry":
                self.telemetry_clients.add(websocket)
            else:
                self.path_clients.add(websocket)

    async def unregister(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.telemetry_clients.discard(websocket)
            self.path_clients.discard(websocket)

    async def broadcast(self, message: dict, channel: str) -> None:
        # Ultra-fast path: check clients first without any overhead
        if channel == "telemetry":
            if not self.telemetry_clients:
                return
            clients = self.telemetry_clients
        else:
            if not self.path_clients:
                return
            clients = self.path_clients
        
        # Only do expensive operations if we have clients
        start = time.perf_counter()
        dead = []
        for client in list(clients):
            try:
                await client.send_json(message)
            except Exception:
                dead.append(client)
        duration = time.perf_counter() - start
        
        # Update metrics
        TELEMETRY_THROUGHPUT.labels(channel=channel).inc(len(clients))
        TELEMETRY_LATENCY.labels(channel=channel).observe(duration)
        
        if dead:
            async with self._lock:
                for client in dead:
                    self.telemetry_clients.discard(client)
                    self.path_clients.discard(client)


hub = VisualizationHub()
