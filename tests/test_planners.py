from app.planners.astar import astar_path
from app.planners.genetic import optimize
from app.planners.planner import PathPlanner


def test_astar_finds_path():
    path = astar_path((5, 5), (0, 0), [(4, 4)], obstacles=[])
    assert path[0] == (0, 0)


def test_genetic_optimizer():
    points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    route, cost = optimize(points, generations=10, population_size=10)
    assert len(route) == 3
    assert cost >= 0


def test_path_planner():
    planner = PathPlanner()
    wall = {"boundary": [[0, 0], [5, 0], [5, 5], [0, 5]]}
    waypoints, cost = planner.generate_trajectory(wall, [])
    assert len(waypoints) > 0
    assert cost > 0
