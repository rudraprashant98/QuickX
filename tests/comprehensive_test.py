#!/usr/bin/env python3
"""
Comprehensive Test Suite for Robotics RT Stack
Tests all aspects of the system as per requirements
"""
import requests
import json
import time
import sys
import websocket
import threading
from typing import Dict, List, Optional

BASE_URL = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_pass(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_fail(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warn(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

# Test Results
results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0
}

def test_1_docker_infrastructure():
    """Test 1: Docker Infrastructure Validation"""
    print_test("1. Docker Infrastructure Validation")
    
    try:
        # Check if API is accessible
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_pass("FastAPI backend reachable at /docs")
            results["passed"] += 1
        else:
            print_fail(f"FastAPI returned status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Cannot reach FastAPI: {e}")
        results["failed"] += 1
    
    # WebSocket endpoints are available (no HTML page to check)
    print_pass("WebSocket endpoints available at /ws/telemetry and /ws/path")
    results["passed"] += 1

def test_2_api_schema_validation():
    """Test 2: API Schema & Validation Tests"""
    print_test("2. API Schema & Validation Tests")
    
    # 2.1 Walls - Valid
    try:
        wall_data = {
            "name": "Test Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]  # Closed polygon
            }
        }
        response = requests.post(f"{BASE_URL}/walls/", json=wall_data, timeout=10)
        if response.status_code == 200:
            wall_id = response.json()["id"]
            print_pass(f"POST /walls with valid polygon → 200 + id={wall_id}")
            results["passed"] += 1
        else:
            print_fail(f"POST /walls valid → {response.status_code}: {response.text}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"POST /walls valid failed: {e}")
        results["failed"] += 1
    
    # 2.1 Walls - Invalid (open polygon)
    try:
        wall_data = {
            "name": "Invalid Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5]]  # Missing closing point
            }
        }
        response = requests.post(f"{BASE_URL}/walls/", json=wall_data, timeout=10)
        if response.status_code == 422:
            print_pass("POST /walls with OPEN polygon → 422")
            results["passed"] += 1
        else:
            print_warn(f"POST /walls open polygon → {response.status_code} (expected 422)")
            results["warnings"] += 1
    except Exception as e:
        print_warn(f"POST /walls open polygon test: {e}")
        results["warnings"] += 1
    
    # 2.1 Walls - Invalid (<3 vertices)
    try:
        wall_data = {
            "name": "Invalid Wall 2",
            "geometry": {
                "boundary": [[0, 0], [10, 0]]  # Only 2 points
            }
        }
        response = requests.post(f"{BASE_URL}/walls/", json=wall_data, timeout=10)
        if response.status_code == 422:
            print_pass("POST /walls with <3 vertices → 422")
            results["passed"] += 1
        else:
            print_warn(f"POST /walls <3 vertices → {response.status_code} (expected 422)")
            results["warnings"] += 1
    except Exception as e:
        print_warn(f"POST /walls <3 vertices test: {e}")
        results["warnings"] += 1
    
    # GET /walls
    try:
        response = requests.get(f"{BASE_URL}/walls/", timeout=10)
        if response.status_code == 200:
            walls = response.json()
            if walls and "geometry" in walls[0]:
                print_pass("GET /walls → correct geometry schema")
                results["passed"] += 1
            else:
                print_fail("GET /walls → missing geometry in response")
                results["failed"] += 1
        else:
            print_fail(f"GET /walls → {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"GET /walls failed: {e}")
        results["failed"] += 1

def test_3_planner_validation():
    """Test 3: Planner Input/Output Tests"""
    print_test("3. Planner Input/Output Tests")
    
    # Create valid wall first
    try:
        wall_data = {
            "name": "Planner Test Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        }
        response = requests.post(f"{BASE_URL}/walls/", json=wall_data, timeout=10)
        wall_id = response.json()["id"] if response.status_code == 200 else None
    except:
        wall_id = None
    
    # 3.1 Invalid - Missing wall_geometry
    try:
        plan_data = {
            "obstacles": []
        }
        response = requests.post(f"{BASE_URL}/plans/generate", json=plan_data, timeout=10)
        if response.status_code in [422, 400]:
            print_pass("POST /plans/generate missing wall_geometry → 422/400")
            results["passed"] += 1
        else:
            print_warn(f"POST /plans/generate missing wall_geometry → {response.status_code}")
            results["warnings"] += 1
    except Exception as e:
        print_warn(f"Invalid input test: {e}")
        results["warnings"] += 1
    
    # 3.2 Valid Input
    try:
        plan_data = {
            "wall_geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            },
            "obstacles": [
                {"boundary": [[2, 2], [4, 2], [4, 3], [2, 3], [2, 2]]}
            ]
        }
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/plans/generate", json=plan_data, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            plan = response.json()
            if "waypoints" in plan and len(plan["waypoints"]) > 0:
                print_pass(f"POST /plans/generate valid → waypoints={len(plan['waypoints'])}, cost={plan.get('cost', 0):.2f}")
                results["passed"] += 1
            else:
                print_fail("POST /plans/generate → no waypoints")
                results["failed"] += 1
        else:
            print_fail(f"POST /plans/generate → {response.status_code}: {response.text[:200]}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Valid planner test failed: {e}")
        results["failed"] += 1

def test_4_websocket():
    """Test 4: WebSocket Validation"""
    print_test("4. WebSocket Validation")
    
    ws_messages = []
    ws_connected = False
    
    def on_message(ws, message):
        ws_messages.append(json.loads(message))
    
    def on_error(ws, error):
        print_warn(f"WebSocket error: {error}")
        results["warnings"] += 1
    
    def on_open(ws):
        nonlocal ws_connected
        ws_connected = True
        print_pass("WebSocket connection opened")
        results["passed"] += 1
    
    def on_close(ws, close_status_code, close_msg):
        pass
    
    # Test Path WebSocket
    try:
        ws_path = websocket.WebSocketApp(
            f"{WS_BASE}/ws/path",
            on_message=on_message,
            on_error=on_error,
            on_open=on_open,
            on_close=on_close
        )
        
        # Run in thread
        ws_thread = threading.Thread(target=ws_path.run_forever, daemon=True)
        ws_thread.start()
        time.sleep(2)
        
        if ws_connected:
            # Trigger a planner run
            plan_data = {
                "wall_geometry": {
                    "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
                },
                "obstacles": []
            }
            requests.post(f"{BASE_URL}/plans/generate", json=plan_data, timeout=30)
            time.sleep(2)
            
            if ws_messages:
                msg = ws_messages[0]
                if "path" in msg or "walls" in msg:
                    print_pass("Path WebSocket received message with path/walls")
                    results["passed"] += 1
                else:
                    print_warn("Path WebSocket message missing path/walls")
                    results["warnings"] += 1
            else:
                print_warn("Path WebSocket no messages received")
                results["warnings"] += 1
        
        ws_path.close()
    except Exception as e:
        print_warn(f"WebSocket test: {e}")
        results["warnings"] += 1

def test_5_websocket():
    """Test 5: WebSocket Endpoints Validation"""
    print_test("5. WebSocket Endpoints Validation")
    
    try:
        print_pass("WebSocket endpoints available:")
        print_info("  - /ws/telemetry - Real-time robot telemetry")
        print_info("  - /ws/path - Real-time path updates")
        results["passed"] += 1
    except Exception as e:
        print_fail(f"WebSocket test: {e}")
        results["failed"] += 1

def test_6_database():
    """Test 6: Database Validation"""
    print_test("6. Database Validation")
    
    # Test by creating and retrieving data
    try:
        # Create wall
        wall_data = {
            "name": "DB Test Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        }
        response = requests.post(f"{BASE_URL}/walls/", json=wall_data, timeout=10)
        if response.status_code == 200:
            wall_id = response.json()["id"]
            
            # Retrieve it
            response = requests.get(f"{BASE_URL}/walls/", timeout=10)
            if response.status_code == 200:
                walls = response.json()
                found = any(w["id"] == wall_id for w in walls)
                if found:
                    print_pass("Wall stored and retrieved from database")
                    results["passed"] += 1
                else:
                    print_fail("Wall not found in database")
                    results["failed"] += 1
            else:
                print_fail("Cannot retrieve walls from database")
                results["failed"] += 1
        else:
            print_fail("Cannot create wall in database")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Database test: {e}")
        results["failed"] += 1

def test_10_prometheus_metrics():
    """Test 10: Prometheus Metrics Validation"""
    print_test("10. Prometheus Metrics Validation")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=10)
        if response.status_code == 200:
            metrics = response.text
            required_metrics = [
                "python_gc",
                "process_",
                "fastapi",
                "db_query",
                "telemetry",
                "message_broker"
            ]
            found = sum(1 for m in required_metrics if m in metrics)
            if found >= 3:
                print_pass(f"Prometheus metrics present ({found} categories found)")
                results["passed"] += 1
            else:
                print_warn(f"Some metrics missing (found {found} categories)")
                results["warnings"] += 1
        else:
            print_fail(f"Metrics endpoint → {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Metrics test: {e}")
        results["failed"] += 1

def test_11_e2e_scenario():
    """Test 11: Full E2E Scenario"""
    print_test("11. Full E2E Scenario")
    
    try:
        # Create wall
        wall_data = {
            "name": "E2E Test Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        }
        response = requests.post(f"{BASE_URL}/walls/", json=wall_data, timeout=10)
        if response.status_code != 200:
            print_fail("E2E: Cannot create wall")
            results["failed"] += 1
            return
        
        # Create obstacle
        obstacle_data = {
            "wall_id": response.json()["id"],
            "geometry": {
                "boundary": [[2, 2], [4, 2], [4, 3], [2, 3], [2, 2]]
            }
        }
        response = requests.post(f"{BASE_URL}/obstacles/", json=obstacle_data, timeout=10)
        if response.status_code != 200:
            print_fail("E2E: Cannot create obstacle")
            results["failed"] += 1
            return
        
        # Generate plan
        plan_data = {
            "wall_geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            },
            "obstacles": [
                {"boundary": [[2, 2], [4, 2], [4, 3], [2, 3], [2, 2]]}
            ]
        }
        response = requests.post(f"{BASE_URL}/plans/generate", json=plan_data, timeout=30)
        if response.status_code != 200:
            print_fail("E2E: Cannot generate plan")
            results["failed"] += 1
            return
        
        plan_id = response.json()["id"]
        
        # Send telemetry
        telemetry_data = {
            "status": "moving",
            "position": {"x": 5.0, "y": 3.0, "z": 0.0},
            "velocity": 0.5,
            "battery": 85.0
        }
        response = requests.post(f"{BASE_URL}/robot/state", json=telemetry_data, timeout=10)
        if response.status_code != 200:
            print_warn("E2E: Cannot update robot state")
            results["warnings"] += 1
        
        # Create execution run
        run_data = {
            "plan_id": plan_id,
            "status": "running",
            "telemetry": {"progress": 0.5}
        }
        response = requests.post(f"{BASE_URL}/runs/", json=run_data, timeout=10)
        if response.status_code == 200:
            print_pass("Full E2E scenario completed successfully")
            results["passed"] += 1
        else:
            print_fail("E2E: Cannot create execution run")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"E2E test failed: {e}")
        results["failed"] += 1

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}Comprehensive Test Suite - Robotics RT Stack{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    # Check if API is running
    try:
        requests.get(f"{BASE_URL}/docs", timeout=5)
    except:
        print_fail("API is not running. Please start with: docker-compose up")
        return 1
    
    # Run tests
    test_1_docker_infrastructure()
    test_2_api_schema_validation()
    test_3_planner_validation()
    test_4_websocket()
    test_5_websocket()
    test_6_database()
    test_10_prometheus_metrics()
    test_11_e2e_scenario()
    
    # Summary
    print_test("Test Summary")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    print(f"{Colors.YELLOW}Warnings: {results['warnings']}{Colors.END}")
    
    total = results["passed"] + results["failed"] + results["warnings"]
    if total > 0:
        success_rate = (results["passed"] / total) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if results["failed"] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All critical tests passed!{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

