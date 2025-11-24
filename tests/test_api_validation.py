"""
Comprehensive API Validation Tests
Tests all validation rules to achieve 100% coverage
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPolygonValidation:
    """Test polygon geometry validation"""
    
    def test_valid_polygon(self):
        """Valid closed polygon should pass"""
        response = client.post("/walls/", json={
            "name": "Valid Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        })
        assert response.status_code == 200
        assert "id" in response.json()
    
    def test_polygon_less_than_3_vertices(self):
        """Polygon with <3 vertices should return 422"""
        response = client.post("/walls/", json={
            "name": "Invalid Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0]]  # Only 2 points
            }
        })
        assert response.status_code == 422
    
    def test_open_polygon(self):
        """Open polygon (not closed) should return 422"""
        response = client.post("/walls/", json={
            "name": "Open Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5]]  # Missing closing point
            }
        })
        assert response.status_code == 422
    
    def test_degenerate_polygon_all_same_points(self):
        """Degenerate polygon (all points same) should return 422"""
        response = client.post("/walls/", json={
            "name": "Degenerate Wall",
            "geometry": {
                "boundary": [[0, 0], [0, 0], [0, 0], [0, 0]]
            }
        })
        assert response.status_code == 422
    
    def test_self_intersecting_polygon(self):
        """Self-intersecting polygon should be handled"""
        # Bow-tie polygon
        response = client.post("/walls/", json={
            "name": "Self Intersect",
            "geometry": {
                "boundary": [[0, 0], [10, 10], [10, 0], [0, 10], [0, 0]]
            }
        })
        assert response.status_code in [200, 422]
    
    def test_non_numeric_coordinates(self):
        """Non-numeric coordinates should return 422"""
        response = client.post("/walls/", json={
            "name": "Invalid Coords",
            "geometry": {
                "boundary": [["a", "b"], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        })
        assert response.status_code == 422
    
    def test_missing_boundary(self):
        """Missing boundary should return 422"""
        response = client.post("/walls/", json={
            "name": "No Boundary",
            "geometry": {}
        })
        assert response.status_code == 422
    
    def test_empty_body(self):
        """Empty body should return 422"""
        response = client.post("/walls/", json={})
        assert response.status_code == 422
    
    def test_large_payload(self):
        """Large payload should be handled"""
        large_boundary = [[i, i] for i in range(1000)]
        large_boundary.append(large_boundary[0])  # Close polygon
        response = client.post("/walls/", json={
            "name": "Large",
            "geometry": {"boundary": large_boundary}
        })
        # With reduced size, might return 200 or 413
        assert response.status_code in [200, 413, 422]


class TestObstacleValidation:
    """Test obstacle validation"""
    
    def test_obstacle_outside_wall(self):
        """Obstacle outside wall should return 400"""
        # Create wall first
        wall_response = client.post("/walls/", json={
            "name": "Test Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        })
        wall_id = wall_response.json()["id"]
        
        # Try to create obstacle outside wall
        response = client.post("/obstacles/", json={
            "wall_id": wall_id,
            "geometry": {
                "boundary": [[20, 20], [25, 20], [25, 25], [20, 25], [20, 20]]  # Outside
            }
        })
        assert response.status_code == 400
    
    def test_overlapping_obstacles(self):
        """Overlapping obstacles should return 400"""
        wall_response = client.post("/walls/", json={
            "name": "Test Wall",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        })
        wall_id = wall_response.json()["id"]
        
        # Create first obstacle
        client.post("/obstacles/", json={
            "wall_id": wall_id,
            "geometry": {
                "boundary": [[2, 2], [4, 2], [4, 3], [2, 3], [2, 2]]
            }
        })
        
        # Try to create overlapping obstacle
        response = client.post("/obstacles/", json={
            "wall_id": wall_id,
            "geometry": {
                "boundary": [[3, 2.5], [5, 2.5], [5, 3.5], [3, 3.5], [3, 2.5]]  # Overlaps
            }
        })
        assert response.status_code == 400


class TestPlanGenerationValidation:
    """Test plan generation validation"""
    
    def test_missing_wall_geometry(self):
        """Missing wall_geometry should return 422"""
        response = client.post("/plans/generate", json={
            "obstacles": []
        })
        assert response.status_code == 422
    
    def test_empty_obstacles_allowed(self):
        """Empty obstacles array should be allowed"""
        response = client.post("/plans/generate", json={
            "wall_geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            },
            "obstacles": []
        })
        assert response.status_code in [200, 400]  # 400 if path planning fails


class TestWaypointValidation:
    """Test waypoint validation"""
    
    def test_odd_number_waypoints(self):
        """Waypoints with odd number should return 422"""
        response = client.post("/plans/", json={
            "wall_id": None,
            "waypoints": [0.0, 0.0, 1.0],  # Odd number
            "cost": 1.0,
            "algorithm": "test"
        })
        assert response.status_code == 422
    
    def test_non_numeric_waypoints(self):
        """Non-numeric waypoints should return 422"""
        response = client.post("/plans/", json={
            "wall_id": None,
            "waypoints": ["a", "b", "c", "d"],
            "cost": 1.0,
            "algorithm": "test"
        })
        assert response.status_code == 422


class TestRobotStateValidation:
    """Test robot state validation"""
    
    def test_missing_position_coordinates(self):
        """Missing position coordinates should return 422"""
        response = client.post("/robot/state", json={
            "status": "moving",
            "position": {"x": 5.0},  # Missing y
            "velocity": 0.5,
            "battery": 85.0
        })
        assert response.status_code == 422
    
    def test_invalid_battery_range(self):
        """Battery >100 should return 422"""
        response = client.post("/robot/state", json={
            "status": "moving",
            "position": {"x": 5.0, "y": 3.0},
            "velocity": 0.5,
            "battery": 150.0  # Invalid
        })
        assert response.status_code == 422
    
    def test_negative_velocity(self):
        """Negative velocity should return 422"""
        response = client.post("/robot/state", json={
            "status": "moving",
            "position": {"x": 5.0, "y": 3.0},
            "velocity": -1.0,  # Invalid
            "battery": 85.0
        })
        assert response.status_code == 422

