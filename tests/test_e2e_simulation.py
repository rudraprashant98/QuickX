import pytest
from app.routers import robot as robot_router


@pytest.mark.slow


def test_end_to_end_simulation(client, monkeypatch):
    published = []

    class StubBroker:
        def publish_command(self, routing_key, payload):
            published.append((routing_key, payload))

    monkeypatch.setattr(robot_router, "get_rabbitmq", lambda: StubBroker())
    monkeypatch.setattr(robot_router, "get_mqtt", lambda: StubBroker())

    wall_payload = {"name": "Lab", "geometry": {"boundary": [[0, 0], [20, 0], [20, 20], [0, 20]]}}
    wall = client.post("/walls/", json=wall_payload).json()

    obstacle_payload = {"wall_id": wall["id"], "geometry": {"boundary": [[5, 5], [8, 5], [8, 8], [5, 8]]}}
    client.post("/obstacles/", json=obstacle_payload)

    plan_req = {
        "wall_geometry": wall_payload["geometry"],
        "obstacles": [obstacle_payload["geometry"]],
    }
    plan_resp = client.post("/plans/generate", json=plan_req)
    assert plan_resp.status_code == 200
    plan = plan_resp.json()

    cmd_resp = client.post("/robot/command", json={"command": "start"})
    assert cmd_resp.status_code == 200
    assert published, "Command not published"

    telemetry_points = [
        {"status": "move", "position": {"x": idx, "y": idx}, "velocity": 0.5, "battery": 80.0}
        for idx in range(5)
    ]
    for state in telemetry_points:
        state_resp = client.post("/robot/state", json=state)
        assert state_resp.status_code == 200

    run_payload = {"plan_id": plan["id"], "status": "completed", "telemetry": {"points": telemetry_points}}
    run_resp = client.post("/runs/", json=run_payload)
    assert run_resp.status_code == 200
    run_id = run_resp.json()["id"]

    fetched = client.get(f"/runs/{run_id}")
    assert fetched.status_code == 200
    assert fetched.json()["telemetry"]["points"][0]["status"] == "move"
