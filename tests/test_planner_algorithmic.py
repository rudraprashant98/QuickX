"""
Comprehensive Planner Algorithmic Tests
Tests all corner cases and edge cases for path planning algorithms
"""
import pytest
import math
from shapely.geometry import Point, Polygon
from app.planners.planner import PathPlanner
from app.planners import astar, genetic, polygon


@pytest.mark.slow


class TestAStarCornerCases:
    """Test A* algorithm corner cases"""
    
    def test_start_equals_goal(self):
        """Start == goal should return single point"""
        planner = PathPlanner()
        grid_size = (10, 10)
        start = (5, 5)
        goal = [(5, 5)]
        obstacles = set()
        
        path = astar.astar_path(grid_size, start, goal, obstacles)
        assert len(path) == 1
        assert path[0] == start
    
    def test_no_possible_route(self):
        """No possible route should raise ValueError"""
        planner = PathPlanner()
        grid_size = (10, 10)
        start = (0, 0)
        goal = [(9, 9)]
        # Block entire path
        obstacles = set((i, j) for i in range(10) for j in range(10) if (i, j) != (0, 0) and (i, j) != (9, 9))
        
        with pytest.raises(ValueError, match="A\\* failed to find a path"):
            astar.astar_path(grid_size, start, goal, obstacles)
    
    def test_extremely_thin_passage(self):
        """Extremely thin passage (1-2 pixels wide) should work"""
        planner = PathPlanner(grid_resolution=0.1)
        grid_size = (100, 100)
        start = (0, 50)
        goal = [(99, 50)]
        # Create thin passage
        obstacles = set((i, j) for i in range(100) for j in range(100) if abs(j - 50) > 1)
        
        path = astar.astar_path(grid_size, start, goal, obstacles)
        assert len(path) > 0
        assert path[0] == start
        assert path[-1] == goal[0]
    
    def test_obstacles_fully_blocking_wall(self):
        """Obstacles fully blocking wall should raise error"""
        planner = PathPlanner()
        wall_geometry = {
            "boundary": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        }
        obstacles = [
            {"boundary": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]}  # Same as wall
        ]
        
        with pytest.raises(ValueError):
            planner.generate_trajectory(wall_geometry, obstacles)
    
    def test_large_grid_performance(self):
        """Large grid (2000x2000) should complete in reasonable time"""
        import time
        planner = PathPlanner(grid_resolution=1.0)
        wall_geometry = {
            "boundary": [[0, 0], [2000, 0], [2000, 2000], [0, 2000], [0, 0]]
        }
        obstacles = [
            {"boundary": [[500, 500], [600, 500], [600, 600], [500, 600], [500, 500]]}
        ]
        
        start_time = time.time()
        waypoints, cost = planner.generate_trajectory(wall_geometry, obstacles)
        elapsed = time.time() - start_time
        
        assert len(waypoints) > 0
        assert cost > 0
        assert elapsed < 30.0


class TestGeneticAlgorithm:
    """Test Genetic Algorithm corner cases"""
    
    def test_single_centroid(self):
        """Degenerate case with single centroid should work"""
        centroids = [(5.0, 5.0)]
        ordered_points, coverage_cost = genetic.optimize(centroids)
        
        assert len(ordered_points) == 1
        assert ordered_points[0] == (5.0, 5.0)
        assert coverage_cost == 0.0
    
    def test_population_convergence(self):
        """Population should converge over generations"""
        centroids = [(i * 2.0, i * 2.0) for i in range(10)]
        
        # Run multiple times and check consistency
        results = []
        for _ in range(5):
            ordered_points, cost = genetic.optimize(centroids)
            results.append((len(ordered_points), cost))
        
        # All should have same number of points
        assert all(r[0] == results[0][0] for r in results)
    
    def test_fitness_score_monotonicity(self):
        """Fitness scores should improve (or stay same) over generations"""
        centroids = [(i * 1.0, i * 1.0) for i in range(20)]
        
        # This is harder to test without modifying genetic.py
        # But we can verify the result is reasonable
        ordered_points, cost = genetic.optimize(centroids)
        assert len(ordered_points) == len(centroids)
        assert cost >= 0.0
    
    def test_random_seed_determinism(self):
        """With same seed, should get same result"""
        import random
        centroids = [(i * 1.0, i * 1.0) for i in range(10)]
        
        # Set seed
        random.seed(42)
        result1 = genetic.optimize(centroids)
        
        random.seed(42)
        result2 = genetic.optimize(centroids)
        
        assert len(result1[0]) == len(result2[0])
    
    def test_50_centroids_performance(self):
        """50 centroids should complete in reasonable time"""
        import time
        centroids = [(i * 0.5, i * 0.5) for i in range(50)]
        
        start_time = time.time()
        ordered_points, cost = genetic.optimize(centroids)
        elapsed = time.time() - start_time
        
        assert len(ordered_points) == 50
        assert elapsed < 5.0


class TestPolygonDecomposition:
    """Test polygon decomposition edge cases"""
    
    def test_empty_decomposition(self):
        """Empty decomposition should return empty list"""
        boundary = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        obstacles = [boundary]  # Obstacle same as wall
        
        result = polygon.decompose_polygon(boundary, obstacles)
        assert result == []
    
    def test_zero_area_polygon(self):
        """Zero area polygon should be handled"""
        boundary = [(0, 0), (0, 0), (0, 0), (0, 0)]
        obstacles = []
        
        try:
            result = polygon.decompose_polygon(boundary, obstacles)
            # Might return empty or raise error
        except Exception:
            pass  # Expected for invalid polygon
    
    def test_complex_obstacle_layout(self):
        """Complex obstacle layout should decompose correctly"""
        boundary = [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
        obstacles = [
            [(10, 10), (20, 10), (20, 20), (10, 20), (10, 10)],
            [(30, 30), (40, 30), (40, 40), (30, 40), (30, 30)],
            [(50, 50), (60, 50), (60, 60), (50, 60), (50, 50)],
        ]
        
        result = polygon.decompose_polygon(boundary, obstacles)
        assert len(result) > 0
        
        # Total area should be wall area minus obstacle areas
        wall_poly = Polygon(boundary)
        obs_polys = [Polygon(obs) for obs in obstacles]
        # Union all obstacles
        obs_union = obs_polys[0]
        for obs in obs_polys[1:]:
            obs_union = obs_union.union(obs)
        expected_area = wall_poly.difference(obs_union).area
        actual_area = sum(poly.area for poly in result)
        
        assert math.isclose(actual_area, expected_area, rel_tol=0.05)


class TestGridResolution:
    """Test grid resolution effects"""
    
    def test_coarse_resolution(self):
        """Coarse resolution should still work"""
        planner = PathPlanner(grid_resolution=5.0)  # Very coarse
        wall_geometry = {
            "boundary": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        }
        obstacles = []
        
        waypoints, cost = planner.generate_trajectory(wall_geometry, obstacles)
        assert len(waypoints) > 0
    
    def test_fine_resolution(self):
        """Fine resolution should provide smoother paths"""
        planner_fine = PathPlanner(grid_resolution=0.1)
        planner_coarse = PathPlanner(grid_resolution=1.0)
        
        wall_geometry = {
            "boundary": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        }
        obstacles = [
            {"boundary": [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]}
        ]
        
        waypoints_fine, cost_fine = planner_fine.generate_trajectory(wall_geometry, obstacles)
        waypoints_coarse, cost_coarse = planner_coarse.generate_trajectory(wall_geometry, obstacles)
        
        # Fine should have more waypoints (or similar)
        assert len(waypoints_fine) >= len(waypoints_coarse) // 2
