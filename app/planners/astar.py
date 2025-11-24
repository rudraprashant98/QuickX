from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Iterable, List, Sequence, Tuple

GridPoint = Tuple[int, int]


def heuristic(a: GridPoint, b: GridPoint) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar_path(
    grid_size: Tuple[int, int],
    start: GridPoint,
    goals: Sequence[GridPoint],
    obstacles: Iterable[GridPoint],
) -> List[GridPoint]:
    blocked = set(obstacles)
    width, height = grid_size
    open_set: list[tuple[float, GridPoint]] = []
    heapq.heappush(open_set, (0.0, start))
    came_from: dict[GridPoint, GridPoint] = {}
    g_score = defaultdict(lambda: float("inf"))
    g_score[start] = 0.0
    goal_set = set(goals)

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while open_set:
        _, current = heapq.heappop(open_set)
        if current in goal_set:
            return _reconstruct_path(came_from, current)

        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            if not (0 <= neighbor[0] < width and 0 <= neighbor[1] < height):
                continue
            if neighbor in blocked:
                continue

            tentative_g = g_score[current] + 1
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + min(heuristic(neighbor, goal) for goal in goal_set)
                heapq.heappush(open_set, (f_score, neighbor))

    raise ValueError("A* failed to find a path")


def _reconstruct_path(came_from: dict[GridPoint, GridPoint], current: GridPoint) -> List[GridPoint]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path
