from fastapi.testclient import TestClient


def test_create_wall(client: TestClient):
    # Polygon must be closed (first and last point same)
    payload = {"name": "Test", "geometry": {"boundary": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]}}
    response = client.post("/walls/", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Test"


def test_plan_generation(client: TestClient):
    # Polygon must be closed (first and last point same)
    payload = {
        "wall_geometry": {"boundary": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]},
        "obstacles": [],
    }
    response = client.post("/plans/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "hybrid_genetic_astar"


def test_robot_state(client: TestClient):
    payload = {"status": "idle", "position": {"x": 1, "y": 2}, "velocity": 0.0, "battery": 90.0}
    response = client.post("/robot/state", json=payload)
    assert response.status_code == 200
    state = response.json()
    assert state["status"] == "idle"
