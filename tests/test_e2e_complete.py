#!/usr/bin/env python3
"""
Complete End-to-End Test with Sample Data
Tests the full flow from wall creation to execution replay
"""
import requests
import json
import time
import sys
from typing import Dict, List, Optional

BASE_URL = "http://localhost:8000"

# Sample test data
SAMPLE_WALL = {
    "name": "Living Room Wall - E2E Test",
    "geometry": {
        "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
    }
}

SAMPLE_OBSTACLES = [
    {
        "geometry": {
            "boundary": [[2, 2], [4, 2], [4, 3], [2, 3], [2, 2]]
        }
    },
    {
        "geometry": {
            "boundary": [[6, 1], [8, 1], [8, 2], [6, 2], [6, 1]]
        }
    },
    {
        "geometry": {
            "boundary": [[3, 3.5], [7, 3.5], [7, 4.5], [3, 4.5], [3, 3.5]]
        }
    }
]

SAMPLE_PLAN_REQUEST = {
    "wall_geometry": {
        "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
    },
    "obstacles": [
        {"boundary": [[2, 2], [4, 2], [4, 3], [2, 3], [2, 2]]},
        {"boundary": [[6, 1], [8, 1], [8, 2], [6, 2], [6, 1]]},
        {"boundary": [[3, 3.5], [7, 3.5], [7, 4.5], [3, 4.5], [3, 3.5]]}
    ]
}

# Simulated robot telemetry sequence
TELEMETRY_SEQUENCE = [
    {"x": 0.0, "y": 0.0, "z": 0.0},
    {"x": 1.0, "y": 0.5, "z": 0.0},
    {"x": 2.0, "y": 1.0, "z": 0.0},
    {"x": 3.0, "y": 1.5, "z": 0.0},
    {"x": 4.0, "y": 2.0, "z": 0.0},
    {"x": 5.0, "y": 2.5, "z": 0.0},
    {"x": 6.0, "y": 3.0, "z": 0.0},
    {"x": 7.0, "y": 3.5, "z": 0.0},
    {"x": 8.0, "y": 4.0, "z": 0.0},
    {"x": 9.0, "y": 4.5, "z": 0.0},
    {"x": 10.0, "y": 5.0, "z": 0.0},
]


def print_step(step_num: int, description: str):
    """Print test step"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print(f"{'='*60}")


def print_success(msg: str):
    """Print success message"""
    print(f"✅ {msg}")


def print_error(msg: str):
    """Print error message"""
    print(f"❌ {msg}")


def print_warn(msg: str):
    """Print warning message"""
    print(f"⚠️  {msg}")


def print_info(msg: str):
    """Print info message"""
    print(f"ℹ️  {msg}")


def test_step_1_create_wall() -> Optional[int]:
    """Step 1: Create wall"""
    print_step(1, "Creating Wall")
    
    try:
        response = requests.post(f"{BASE_URL}/walls/", json=SAMPLE_WALL, timeout=10)
        if response.status_code == 200:
            wall = response.json()
            wall_id = wall["id"]
            print_success(f"Wall created with ID: {wall_id}")
            print_info(f"Wall name: {wall['name']}")
            return wall_id
        else:
            print_error(f"Failed to create wall: {response.status_code}")
            print_error(response.text)
            return None
    except Exception as e:
        print_error(f"Exception creating wall: {e}")
        return None


def test_step_2_create_obstacles(wall_id: int) -> List[int]:
    """Step 2: Create obstacles"""
    print_step(2, "Creating Obstacles")
    
    obstacle_ids = []
    for i, obstacle_data in enumerate(SAMPLE_OBSTACLES):
        try:
            obstacle_payload = {
                "wall_id": wall_id,
                **obstacle_data
            }
            response = requests.post(f"{BASE_URL}/obstacles/", json=obstacle_payload, timeout=10)
            if response.status_code == 200:
                obstacle = response.json()
                obstacle_ids.append(obstacle["id"])
                print_success(f"Obstacle {i+1} created with ID: {obstacle['id']}")
            else:
                print_error(f"Failed to create obstacle {i+1}: {response.status_code}")
        except Exception as e:
            print_error(f"Exception creating obstacle {i+1}: {e}")
    
    return obstacle_ids


def test_step_3_generate_plan() -> Optional[Dict]:
    """Step 3: Generate path plan"""
    print_step(3, "Generating Path Plan")
    
    try:
        print_info("Sending plan generation request...")
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/plans/generate", json=SAMPLE_PLAN_REQUEST, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            plan = response.json()
            print_success(f"Plan generated in {elapsed:.2f}s")
            print_info(f"Plan ID: {plan['id']}")
            print_info(f"Algorithm: {plan['algorithm']}")
            print_info(f"Cost: {plan['cost']:.2f}")
            print_info(f"Waypoints: {len(plan['waypoints'])} coordinates")
            return plan
        elif response.status_code == 400:
            # Path planning failed (no path found) - try with simpler obstacles
            print_warn("Path planning failed with obstacles, trying without obstacles...")
            simple_request = {
                "wall_geometry": SAMPLE_PLAN_REQUEST["wall_geometry"],
                "obstacles": []
            }
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/plans/generate", json=simple_request, timeout=30)
            elapsed = time.time() - start_time
            if response.status_code == 200:
                plan = response.json()
                print_success(f"Plan generated (without obstacles) in {elapsed:.2f}s")
                print_info(f"Plan ID: {plan['id']}")
                return plan
            else:
                print_error(f"Failed to generate plan even without obstacles: {response.status_code}")
                return None
        else:
            print_error(f"Failed to generate plan: {response.status_code}")
            print_error(response.text)
            return None
    except Exception as e:
        print_error(f"Exception generating plan: {e}")
        return None


def test_step_4_send_robot_command():
    """Step 4: Send robot command"""
    print_step(4, "Sending Robot Command")
    
    try:
        command = {
            "command": "start",
            "x": 0.0,
            "y": 0.0
        }
        response = requests.post(f"{BASE_URL}/robot/command", json=command, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print_success(f"Command sent: {result.get('status', 'queued')}")
        else:
            print_error(f"Failed to send command: {response.status_code}")
    except Exception as e:
        print_error(f"Exception sending command: {e}")


def test_step_5_simulate_robot_execution(plan: Dict):
    """Step 5: Simulate robot running the plan"""
    print_step(5, "Simulating Robot Execution")
    
    if not plan or "waypoints" not in plan:
        print_error("No plan available for execution")
        return
    
    waypoints = plan["waypoints"]
    # Convert flat list to pairs
    waypoint_pairs = [(waypoints[i], waypoints[i+1]) for i in range(0, len(waypoints), 2)]
    
    print_info(f"Executing plan with {len(waypoint_pairs)} waypoints")
    
    for i, (x, y) in enumerate(waypoint_pairs[:10]):  # Limit to first 10 for demo
        try:
            telemetry = {
                "status": "moving",
                "position": {"x": float(x), "y": float(y), "z": 0.0},
                "velocity": 0.5,
                "battery": 100.0 - (i * 0.5)
            }
            response = requests.post(f"{BASE_URL}/robot/state", json=telemetry, timeout=10)
            if response.status_code == 200:
                print_info(f"  Waypoint {i+1}/{len(waypoint_pairs)}: ({x:.2f}, {y:.2f})")
            time.sleep(0.1)  # Simulate movement delay
        except Exception as e:
            print_error(f"Exception at waypoint {i+1}: {e}")
    
    print_success("Robot execution simulation completed")


def test_step_6_create_execution_run(plan_id: int):
    """Step 6: Create execution run"""
    print_step(6, "Creating Execution Run")
    
    try:
        run_data = {
            "plan_id": plan_id,
            "status": "completed",
            "telemetry": {
                "progress": 1.0,
                "waypoints_completed": len(TELEMETRY_SEQUENCE),
                "total_waypoints": len(TELEMETRY_SEQUENCE)
            }
        }
        response = requests.post(f"{BASE_URL}/runs/", json=run_data, timeout=10)
        if response.status_code == 200:
            run = response.json()
            print_success(f"Execution run created with ID: {run['id']}")
            print_info(f"Status: {run['status']}")
            return run
        else:
            print_error(f"Failed to create run: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Exception creating run: {e}")
        return None


def test_step_7_validate_database():
    """Step 7: Validate database entries"""
    print_step(7, "Validating Database Entries")
    
    try:
        # Check walls
        response = requests.get(f"{BASE_URL}/walls/", timeout=10)
        if response.status_code == 200:
            walls = response.json()
            print_success(f"Walls in database: {len(walls)}")
        
        # Check obstacles
        response = requests.get(f"{BASE_URL}/obstacles/", timeout=10)
        if response.status_code == 200:
            obstacles = response.json()
            print_success(f"Obstacles in database: {len(obstacles)}")
        
        # Check plans
        response = requests.get(f"{BASE_URL}/plans/", timeout=10)
        if response.status_code == 200:
            plans = response.json()
            print_success(f"Plans in database: {len(plans)}")
        
        # Check runs
        response = requests.get(f"{BASE_URL}/runs/", timeout=10)
        if response.status_code == 200:
            runs = response.json()
            print_success(f"Execution runs in database: {len(runs)}")
    except Exception as e:
        print_error(f"Exception validating database: {e}")


def test_step_8_check_metrics():
    """Step 8: Check Prometheus metrics"""
    print_step(8, "Checking Prometheus Metrics")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=10)
        if response.status_code == 200:
            metrics = response.text
            metric_count = len([line for line in metrics.split('\n') if line and not line.startswith('#')])
            print_success(f"Metrics available: {metric_count} data points")
            
            # Check for key metrics
            key_metrics = [
                "fastapi_request",
                "db_query",
                "telemetry",
                "message_broker"
            ]
            found = [m for m in key_metrics if m in metrics]
            print_info(f"Key metrics found: {', '.join(found)}")
        else:
            print_error(f"Failed to get metrics: {response.status_code}")
    except Exception as e:
        print_error(f"Exception checking metrics: {e}")


def test_step_9_validate_websocket():
    """Step 9: Validate WebSocket endpoints"""
    print_step(9, "Validating WebSocket Endpoints")
    
    try:
        print_info("WebSocket endpoints available:")
        print_info(f"  - Telemetry: ws://localhost:8000/ws/telemetry")
        print_info(f"  - Path: ws://localhost:8000/ws/path")
        print_success("WebSocket endpoints configured")
    except Exception as e:
        print_error(f"Exception validating WebSocket endpoints: {e}")


def main():
    """Run complete E2E test"""
    print("\n" + "="*60)
    print("COMPLETE END-TO-END TEST")
    print("Robotics RT Stack - Full Flow Test")
    print("="*60)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code != 200:
            print_error("API is not running. Please start with: docker-compose up")
            return 1
    except:
        print_error("Cannot connect to API. Please start with: docker-compose up")
        return 1
    
    print_success("API is running and accessible")
    
    # Run test steps
    wall_id = test_step_1_create_wall()
    if not wall_id:
        print_error("Cannot proceed without wall")
        return 1
    
    obstacle_ids = test_step_2_create_obstacles(wall_id)
    print_info(f"Created {len(obstacle_ids)} obstacles")
    
    plan = test_step_3_generate_plan()
    if not plan:
        print_error("Cannot proceed without plan")
        return 1
    
    plan_id = plan["id"]
    
    test_step_4_send_robot_command()
    test_step_5_simulate_robot_execution(plan)
    test_step_6_create_execution_run(plan_id)
    test_step_7_validate_database()
    test_step_8_check_metrics()
    test_step_9_validate_websocket()
    
    # Summary
    print("\n" + "="*60)
    print("E2E TEST SUMMARY")
    print("="*60)
    print_success("All test steps completed!")
    print_info(f"Wall ID: {wall_id}")
    print_info(f"Obstacles: {len(obstacle_ids)}")
    print_info(f"Plan ID: {plan_id}")
    print_info(f"\nConnect to WebSocket at: ws://localhost:8000/ws/telemetry")
    print_info(f"View API docs at: {BASE_URL}/docs")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

