import math

import pytest
from shapely.geometry import LineString, Point, Polygon

from app.planners.planner import PathPlanner
from app.planners import polygon as poly_module


def _reshape(waypoints: list[float]) -> list[tuple[float, float]]:
    return [(waypoints[i], waypoints[i + 1]) for i in range(0, len(waypoints), 2)]


@pytest.mark.parametrize("max_step", [1.0, 2.0])
def test_waypoint_spacing_and_obstacle_exclusion(max_step: float):
    boundary = [(0, 0), (20, 0), (20, 20), (0, 20)]
    obstacles = [[(5, 5), (7, 5), (7, 7), (5, 7)], [(12, 12), (15, 12), (15, 15), (12, 15)]]
    planner = PathPlanner(grid_resolution=max_step / 2)
    waypoints, _ = planner.generate_trajectory({"boundary": boundary}, [{"boundary": obs} for obs in obstacles])

    points = _reshape(waypoints)
    obstacle_polys = [Polygon(obs) for obs in obstacles]

    for idx in range(1, len(points)):
        dist = math.dist(points[idx - 1], points[idx])
        assert dist <= max_step * 10, f"Waypoint spacing exceeded robot capability: {dist} > {max_step * 10}"

    for point in points:
        assert all(not poly.contains(Point(point)) for poly in obstacle_polys), "A* entered obstacle"


def test_polygon_decomposition_covers_wall_area():
    boundary = [(0, 0), (30, 0), (30, 30), (0, 30)]
    obstacles = [[(10, 10), (15, 10), (15, 15), (10, 15)]]
    decomposed = poly_module.decompose_polygon(boundary, obstacles)
    wall_poly = Polygon(boundary)
    obstacle_poly = Polygon(obstacles[0])
    decomposed_area = sum(piece.area for piece in decomposed)
    expected_area = wall_poly.difference(obstacle_poly).area
    assert math.isclose(decomposed_area, expected_area, rel_tol=0.05)
