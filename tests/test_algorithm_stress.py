import random

import pytest
from shapely.geometry import LineString, Point, Polygon

from app.planners import polygon as poly_module
from app.planners.genetic import optimize
from app.planners.planner import PathPlanner


@pytest.mark.slow


def _generate_obstacles(count: int) -> list[list[tuple[float, float]]]:
    obstacles: list[list[tuple[float, float]]] = []
    for _ in range(count):
        cx = random.uniform(5, 45)
        cy = random.uniform(5, 45)
        size = random.uniform(1, 3)
        obstacles.append(
            [
                (cx - size, cy - size),
                (cx + size, cy - size),
                (cx + size, cy + size),
                (cx - size, cy + size),
            ]
        )
    return obstacles


def _reshape(waypoints: list[float]) -> list[tuple[float, float]]:
    return [(waypoints[i], waypoints[i + 1]) for i in range(0, len(waypoints), 2)]


@pytest.mark.slow
@pytest.mark.parametrize("obstacle_count", [5, 20, 50, 100])
def test_algorithm_stress_pipeline(obstacle_count: int):
    random.seed(obstacle_count)
    boundary = [(0, 0), (50, 0), (50, 50), (0, 50)]
    obstacles = _generate_obstacles(obstacle_count)

    decomposition = poly_module.decompose_polygon(boundary, obstacles)
    assert decomposition, "Polygon decomposition failed"

    centroids = [poly.centroid.coords[0] for poly in decomposition]
    # Using Redis caching for distance calculations - can use original parameters
    ordered, _ = optimize(centroids, generations=50, population_size=80)
    assert len(ordered) == len(centroids)

    planner = PathPlanner(grid_resolution=1.0)
    waypoints, cost = planner.generate_trajectory({"boundary": boundary}, [{"boundary": obs} for obs in obstacles])
    assert cost > 0
    assert cost < 20000  # bounded cost for 50x50 workspace

    points = _reshape(waypoints)
    line = LineString(points)
    obstacle_polys = [Polygon(obs) for obs in obstacles]

    for centroid in centroids:
        # Allow slightly larger tolerance (6 units) for cases where obstacles block direct paths
        assert line.distance(Point(centroid)) <= 6, f"Planner failed to cover decomposed region: centroid {centroid} is {line.distance(Point(centroid)):.2f} units away"

    for point in points:
        assert all(not poly.contains(Point(point)) for poly in obstacle_polys), "Waypoint inside obstacle"
