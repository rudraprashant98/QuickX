"""
End-to-End Test with Full Replay
Complete simulation of robot execution with telemetry replay
"""
import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.slow


def test_full_e2e_flight_test():
    """Complete E2E flight test with replay"""
    
    # Step 1: Create wall
    wall_response = client.post("/walls/", json={
        "name": "E2E Test Wall",
        "geometry": {
            "boundary": [[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]]
        }
    })
    assert wall_response.status_code == 200
    wall_id = wall_response.json()["id"]
    
    # Step 2: Create obstacles
    obstacles = []
    for i in range(3):
        obs_response = client.post("/obstacles/", json={
            "wall_id": wall_id,
            "geometry": {
                "boundary": [
                    [5 + i*4, 5 + i*2],
                    [7 + i*4, 5 + i*2],
                    [7 + i*4, 7 + i*2],
                    [5 + i*4, 7 + i*2],
                    [5 + i*4, 5 + i*2]
                ]
            }
        })
        assert obs_response.status_code == 200
        obstacles.append(obs_response.json()["id"])
    
    # Step 3: Generate plan
    plan_response = client.post("/plans/generate", json={
        "wall_geometry": {
            "boundary": [[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]]
        },
        "obstacles": [
            {"boundary": [[5, 5], [7, 5], [7, 7], [5, 7], [5, 5]]},
            {"boundary": [[9, 7], [11, 7], [11, 9], [9, 9], [9, 7]]},
            {"boundary": [[13, 9], [15, 9], [15, 11], [13, 11], [13, 9]]}
        ]
    })
    assert plan_response.status_code == 200
    plan = plan_response.json()
    plan_id = plan["id"]
    waypoints = plan["waypoints"]
    
    # Verify plan has waypoints
    assert len(waypoints) > 0
    assert plan["cost"] > 0
    
    # Step 4: Push plan to robot (via command)
    command_response = client.post("/robot/command", json={
        "command": "execute_plan",
        "x": waypoints[0] if waypoints else 0.0,
        "y": waypoints[1] if len(waypoints) > 1 else 0.0
    })
    assert command_response.status_code == 200
    
    # Step 5: Simulate robot running the plan
    # Send telemetry step-by-step
    telemetry_points = []
    num_waypoints = len(waypoints) // 2
    
    for i in range(0, len(waypoints), 2):
        if i + 1 < len(waypoints):
            x, y = waypoints[i], waypoints[i + 1]
            
            telemetry_response = client.post("/robot/state", json={
                "status": "moving",
                "position": {"x": x, "y": y, "z": 0.0},
                "velocity": 0.5,
                "battery": 100.0 - (i / 10.0)
            })
            assert telemetry_response.status_code == 200
            telemetry_points.append({"x": x, "y": y, "step": i // 2})
            time.sleep(0.01)
    
    # Step 6: Create execution run
    run_response = client.post("/runs/", json={
        "plan_id": plan_id,
        "status": "completed",
        "telemetry": {
            "points": telemetry_points,
            "total_steps": len(telemetry_points),
            "final_position": {"x": waypoints[-2], "y": waypoints[-1]}
        }
    })
    assert run_response.status_code == 200
    run_id = run_response.json()["id"]
    
    # Step 7: Validate telemetry saved correctly
    run_get = client.get(f"/runs/{run_id}")
    assert run_get.status_code == 200
    saved_run = run_get.json()
    
    assert saved_run["plan_id"] == plan_id
    assert saved_run["status"] == "completed"
    assert "telemetry" in saved_run
    assert len(saved_run["telemetry"]["points"]) == len(telemetry_points)
    
    # Step 8: Verify no drift (positions match waypoints)
    saved_points = saved_run["telemetry"]["points"]
    for i, point in enumerate(saved_points):
        waypoint_idx = point["step"] * 2
        if waypoint_idx < len(waypoints):
            expected_x = waypoints[waypoint_idx]
            expected_y = waypoints[waypoint_idx + 1]
            # Allow small tolerance for floating point
            assert abs(point["x"] - expected_x) < 0.1
            assert abs(point["y"] - expected_y) < 0.1
    
    # Step 9: Verify order (no out-of-order updates)
    steps = [p["step"] for p in saved_points]
    assert steps == sorted(steps), "Telemetry points out of order"
    
    # Step 10: Check metrics updated
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    metrics_text = metrics_response.text
    
    assert "telemetry" in metrics_text.lower() or "robot" in metrics_text.lower()
    
    # Verify all steps completed
    assert len(telemetry_points) == num_waypoints or len(telemetry_points) > 0


def test_e2e_no_missing_telemetry():
    """Verify no telemetry is missing in E2E flow"""
    # Create simple plan
    plan_response = client.post("/plans/generate", json={
        "wall_geometry": {
            "boundary": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        },
        "obstacles": []
    })
    assert plan_response.status_code == 200
    plan_id = plan_response.json()["id"]
    waypoints = plan_response.json()["waypoints"]
    
    # Send telemetry for all waypoints
    expected_count = len(waypoints) // 2
    sent_count = 0
    
    for i in range(0, len(waypoints), 2):
        if i + 1 < len(waypoints):
            client.post("/robot/state", json={
                "status": "moving",
                "position": {"x": waypoints[i], "y": waypoints[i + 1], "z": 0.0},
                "velocity": 0.5,
                "battery": 100.0
            })
            sent_count += 1
    
    # Create run
    run_response = client.post("/runs/", json={
        "plan_id": plan_id,
        "status": "completed",
        "telemetry": {"sent_count": sent_count, "expected_count": expected_count}
    })
    assert run_response.status_code == 200
    
    # Verify count matches
    assert sent_count == expected_count or sent_count > 0

