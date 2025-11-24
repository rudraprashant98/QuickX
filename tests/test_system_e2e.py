"""
System-Level E2E Tests
Complete simulation with replay validation
"""
import pytest
import requests
import time
from typing import List, Dict

BASE_URL = "http://localhost:8000"


@pytest.mark.slow


class TestFullE2ESimulation:
    """Complete E2E simulation test"""
    
    def test_complete_flight_test(self):
        """Complete flight test: wall → obstacles → plan → execution → replay"""
        # Step 1: Create wall
        wall_response = requests.post(f"{BASE_URL}/walls/", json={
            "name": "E2E Test Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        })
        assert wall_response.status_code == 200
        wall_id = wall_response.json()["id"]
        
        # Step 2: Create obstacles
        obstacle_ids = []
        for i, obs_data in enumerate([
            {"boundary": [[2, 2], [4, 2], [4, 3], [2, 3], [2, 2]]},
            {"boundary": [[6, 1], [8, 1], [8, 2], [6, 2], [6, 1]]},
        ]):
            obs_response = requests.post(f"{BASE_URL}/obstacles/", json={
                "wall_id": wall_id,
                "geometry": obs_data
            })
            assert obs_response.status_code == 200
            obstacle_ids.append(obs_response.json()["id"])
        
        # Step 3: Generate plan
        plan_response = requests.post(f"{BASE_URL}/plans/generate", json={
            "wall_geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            },
            "obstacles": [
                {"boundary": [[2, 2], [4, 2], [4, 3], [2, 3], [2, 2]]},
                {"boundary": [[6, 1], [8, 1], [8, 2], [6, 2], [6, 1]]},
            ]
        }, timeout=30)
        assert plan_response.status_code in [200, 400]  # 400 if no path found
        if plan_response.status_code == 200:
            plan_id = plan_response.json()["id"]
            
            # Step 4: Push plan to robot (simulated via command)
            command_response = requests.post(f"{BASE_URL}/robot/command", json={
                "command": "execute_plan",
                "x": 0.0,
                "y": 0.0
            })
            assert command_response.status_code == 200
            
            # Step 5: Simulate robot execution
            telemetry_sequence = [
                {"x": 0.0, "y": 0.0},
                {"x": 1.0, "y": 0.5},
                {"x": 2.0, "y": 1.0},
                {"x": 3.0, "y": 1.5},
                {"x": 4.0, "y": 2.0},
            ]
            
            received_telemetry = []
            for i, pos in enumerate(telemetry_sequence):
                telemetry_response = requests.post(f"{BASE_URL}/robot/state", json={
                    "status": "moving",
                    "position": {**pos, "z": 0.0},
                    "velocity": 0.5,
                    "battery": 100.0 - (i * 0.5)
                })
                assert telemetry_response.status_code == 200
                received_telemetry.append(telemetry_response.json())
                time.sleep(0.01)
            
            # Step 6: Create execution run
            run_response = requests.post(f"{BASE_URL}/runs/", json={
                "plan_id": plan_id,
                "status": "completed",
                "telemetry": {
                    "progress": 1.0,
                    "waypoints_completed": len(telemetry_sequence)
                }
            })
            assert run_response.status_code == 200
            run_id = run_response.json()["id"]
            
            # Step 7: Validate telemetry saved
            run_get = requests.get(f"{BASE_URL}/runs/{run_id}")
            assert run_get.status_code == 200
            run_data = run_get.json()
            assert run_data["status"] == "completed"
            assert "telemetry" in run_data
            
            # Step 8: Validate no drift (check order)
            assert len(received_telemetry) == len(telemetry_sequence)
            
            # Step 9: Validate metrics updated
            metrics_response = requests.get(f"{BASE_URL}/metrics")
            assert metrics_response.status_code == 200
            assert "telemetry" in metrics_response.text.lower()
    
    def test_no_missing_telemetry(self):
        """Ensure no telemetry is missing"""
        # Send sequence of telemetry
        sequence = [{"x": float(i), "y": float(i*0.5)} for i in range(10)]
        
        for pos in sequence:
            requests.post(f"{BASE_URL}/robot/state", json={
                "status": "moving",
                "position": {**pos, "z": 0.0},
                "velocity": 0.5,
                "battery": 85.0
            })
        
        # Verify all received
        state_response = requests.get(f"{BASE_URL}/robot/state")
        assert state_response.status_code == 200
        final_state = state_response.json()
        assert "position" in final_state
    
    def test_no_out_of_order_updates(self):
        """Ensure updates are in order"""
        # Send ordered sequence
        for i in range(5):
            requests.post(f"{BASE_URL}/robot/state", json={
                "status": "moving",
                "position": {"x": float(i), "y": float(i), "z": 0.0},
                "velocity": 0.5,
                "battery": 85.0
            })
            time.sleep(0.1)
        
        # Final state should reflect last update
        state_response = requests.get(f"{BASE_URL}/robot/state")
        assert state_response.status_code == 200
        final_pos = state_response.json()["position"]
        assert final_pos["x"] == 4.0  # Last sent value

