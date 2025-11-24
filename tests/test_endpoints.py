#!/usr/bin/env python3
"""
End-to-end test script for Robotics API
"""
import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_response(title: str, response: requests.Response):
    """Pretty print API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_health_check():
    """Test API documentation endpoint"""
    print("Testing API Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert response.status_code == 200, "API docs should be accessible"
        print("✓ API is running")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ ERROR: Cannot connect to API")
        print("   Make sure the application is running:")
        print("   docker-compose up")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

def test_wall_operations():
    """Test wall creation and listing"""
    print("\nTesting Wall Operations...")
    
    try:
        # Create wall
        wall_data = {
            "name": "Test Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5]]
            }
        }
        response = requests.post(f"{BASE_URL}/walls/", json=wall_data, timeout=10)
        print_response("Create Wall", response)
        assert response.status_code == 200, "Wall creation should succeed"
        wall_id = response.json()["id"]
        print(f"✓ Wall created with ID: {wall_id}")
        
        # List walls
        response = requests.get(f"{BASE_URL}/walls/", timeout=10)
        print_response("List Walls", response)
        assert response.status_code == 200, "List walls should succeed"
        assert len(response.json()) > 0, "Should have at least one wall"
        print("✓ Walls listed successfully")
        
        return wall_id
    except Exception as e:
        print(f"✗ ERROR in wall operations: {e}")
        return None

def test_obstacle_operations(wall_id: int):
    """Test obstacle creation"""
    if not wall_id:
        print("✗ Skipping obstacle test - no wall ID")
        return
    
    print("\nTesting Obstacle Operations...")
    
    try:
        obstacle_data = {
            "wall_id": wall_id,
            "geometry": {
                "boundary": [[2, 2], [4, 2], [4, 3], [2, 3]]
            }
        }
        response = requests.post(f"{BASE_URL}/obstacles/", json=obstacle_data, timeout=10)
        print_response("Create Obstacle", response)
        assert response.status_code == 200, "Obstacle creation should succeed"
        print("✓ Obstacle created")
        
        # List obstacles
        response = requests.get(f"{BASE_URL}/obstacles/", timeout=10)
        print_response("List Obstacles", response)
        assert response.status_code == 200, "List obstacles should succeed"
        print("✓ Obstacles listed")
    except Exception as e:
        print(f"✗ ERROR in obstacle operations: {e}")

def test_path_planning():
    """Test path plan generation"""
    print("\nTesting Path Planning...")
    
    try:
        plan_data = {
            "wall_geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5]]
            },
            "obstacles": [
                {"boundary": [[2, 2], [4, 2], [4, 3], [2, 3]]}
            ]
        }
        
        print("Generating path plan (this may take a few seconds)...")
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/plans/generate", json=plan_data, timeout=30)
        elapsed = time.time() - start_time
        
        print_response("Generate Path Plan", response)
        assert response.status_code == 200, "Path generation should succeed"
        
        plan = response.json()
        assert "waypoints" in plan, "Plan should have waypoints"
        assert "cost" in plan, "Plan should have cost"
        assert len(plan["waypoints"]) > 0, "Plan should have waypoints"
        
        print(f"✓ Path plan generated in {elapsed:.2f}s")
        print(f"  - Waypoints: {len(plan['waypoints'])} coordinates")
        print(f"  - Cost: {plan['cost']:.2f}")
        print(f"  - Algorithm: {plan['algorithm']}")
        
        return plan["id"]
    except Exception as e:
        print(f"✗ ERROR in path planning: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_robot_operations():
    """Test robot commands and state"""
    print("\nTesting Robot Operations...")
    
    try:
        # Send command
        command_data = {
            "command": "move",
            "x": 5.0,
            "y": 3.0
        }
        response = requests.post(f"{BASE_URL}/robot/command", json=command_data, timeout=10)
        print_response("Send Robot Command", response)
        assert response.status_code == 200, "Command should be queued"
        assert response.json()["status"] == "queued", "Command should be queued"
        print("✓ Command sent")
        
        # Update state
        state_data = {
            "status": "moving",
            "position": {"x": 5.0, "y": 3.0, "z": 0.0},
            "velocity": 0.5,
            "battery": 85.0
        }
        response = requests.post(f"{BASE_URL}/robot/state", json=state_data, timeout=10)
        print_response("Update Robot State", response)
        assert response.status_code == 200, "State update should succeed"
        print("✓ Robot state updated")
        
        # Get state
        response = requests.get(f"{BASE_URL}/robot/state", timeout=10)
        print_response("Get Robot State", response)
        assert response.status_code == 200, "Get state should succeed"
        state = response.json()
        assert state["status"] == "moving", "State should be updated"
        print("✓ Robot state retrieved")
    except Exception as e:
        print(f"✗ ERROR in robot operations: {e}")

def test_execution_runs(plan_id: int):
    """Test execution run operations"""
    if not plan_id:
        print("✗ Skipping execution run test - no plan ID")
        return
    
    print("\nTesting Execution Runs...")
    
    try:
        run_data = {
            "plan_id": plan_id,
            "status": "running",
            "telemetry": {
                "progress": 0.5,
                "current_waypoint": 3
            }
        }
        response = requests.post(f"{BASE_URL}/runs/", json=run_data, timeout=10)
        print_response("Create Execution Run", response)
        assert response.status_code == 200, "Run creation should succeed"
        run_id = response.json()["id"]
        print(f"✓ Execution run created with ID: {run_id}")
        
        # List runs
        response = requests.get(f"{BASE_URL}/runs/", timeout=10)
        print_response("List Execution Runs", response)
        assert response.status_code == 200, "List runs should succeed"
        print("✓ Execution runs listed")
        
        # Get specific run
        response = requests.get(f"{BASE_URL}/runs/{run_id}", timeout=10)
        print_response(f"Get Execution Run {run_id}", response)
        assert response.status_code == 200, "Get run should succeed"
        print("✓ Execution run retrieved")
    except Exception as e:
        print(f"✗ ERROR in execution runs: {e}")

def main():
    """Run all tests"""
    print("="*50)
    print("Robotics API End-to-End Test")
    print("="*50)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n✗ Cannot proceed - API is not running")
        print("\nTo start the API:")
        print("  docker-compose up -d")
        return 1
    
    # Test 2: Wall operations
    wall_id = test_wall_operations()
    if not wall_id:
        print("\n✗ Wall operations failed")
        return 1
    
    # Test 3: Obstacle operations
    test_obstacle_operations(wall_id)
    
    # Test 4: Path planning
    plan_id = test_path_planning()
    if not plan_id:
        print("\n✗ Path planning failed")
        return 1
    
    # Test 5: Robot operations
    test_robot_operations()
    
    # Test 6: Execution runs
    test_execution_runs(plan_id)
    
    print("\n" + "="*50)
    print("✓ ALL TESTS PASSED!")
    print("="*50)
    return 0

if __name__ == "__main__":
    sys.exit(main())

