import asyncio
import time

import pytest

from app.utils.visualization import VisualizationHub


@pytest.mark.slow


class WebsocketTestClient:
    def __init__(self):
        self.messages: list[dict] = []
        self.timestamps: list[float] = []

    async def send_json(self, message):
        self.messages.append(message)
        self.timestamps.append(time.perf_counter())

    def __hash__(self) -> int:  # allow placement in sets
        return id(self)


@pytest.mark.asyncio
async def test_telemetry_websocket_load():
    hub = VisualizationHub()
    clients = [WebsocketTestClient() for _ in range(10)]
    hub.telemetry_clients = set(clients)

    robots = 20
    messages_per_robot = 5
    latencies: list[float] = []

    async def produce(robot_id: int):
        for idx in range(messages_per_robot):
            payload = {"robot": robot_id, "x": idx, "y": robot_id}
            start = time.perf_counter()
            await hub.broadcast(payload, "telemetry")
            latencies.append(time.perf_counter() - start)

    await asyncio.gather(*(produce(rid) for rid in range(robots)))

    expected_messages = robots * messages_per_robot
    for client in clients:
        assert len(client.messages) == expected_messages

    assert latencies and max(latencies) < 0.05
