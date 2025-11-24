from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
from shapely.geometry import Point, Polygon

from . import astar, genetic, polygon


class PathPlanner:
    def __init__(self, grid_resolution: float = 0.5):
        self.grid_resolution = grid_resolution
        self.last_algorithm = "hybrid_genetic_astar"

    def generate_trajectory(
        self, wall_geometry: dict, obstacles: list[dict]
    ) -> tuple[list[float], float]:
        boundary = [tuple(point) for point in wall_geometry.get("boundary", [])]
        obstacle_polys = [list(map(tuple, obs.get("boundary", []))) for obs in obstacles]
        decomposition = polygon.decompose_polygon(boundary, obstacle_polys)
        if not decomposition:
            raise ValueError("Invalid geometry provided")

        centroids = [poly.centroid.coords[0] for poly in decomposition]
        ordered_points, coverage_cost = genetic.optimize(centroids)

        grid_waypoints: list[Tuple[float, float]] = []
        int_obstacles = self._obstacle_grid(obstacle_polys)
        
        # Filter waypoints to ensure they're not in obstacles
        def is_valid_point(pt: Tuple[float, float]) -> bool:
            """Check if point is not inside any obstacle"""
            pt_obj = Point(pt)
            for obs_poly in obstacle_polys:
                if len(obs_poly) >= 3:
                    poly = Polygon(obs_poly)
                    if poly.contains(pt_obj):
                        return False
            return True

        for start, goal in zip(ordered_points[:-1], ordered_points[1:]):
            start_grid = self._to_grid(start)
            goal_grid = self._to_grid(goal)
            try:
                segment = astar.astar_path(self._grid_size(boundary), start_grid, [goal_grid], int_obstacles)
                waypoints_segment = [self._from_grid(p) for p in segment]
                # Filter out waypoints that are inside obstacles
                valid_waypoints = [wp for wp in waypoints_segment if is_valid_point(wp)]
                if valid_waypoints:
                    grid_waypoints.extend(valid_waypoints)
                elif is_valid_point(start):
                    # If all waypoints are invalid, at least add start if valid
                    grid_waypoints.append(start)
            except ValueError:
                # If A* can't find a path, add start point if it's valid
                if is_valid_point(start) and (not grid_waypoints or grid_waypoints[-1] != start):
                    grid_waypoints.append(start)
                # Skip blocked segments
                continue

        if not grid_waypoints and ordered_points:
            # Find first valid point
            for pt in ordered_points:
                if is_valid_point(pt):
                    grid_waypoints = [pt]
                    break
            if not grid_waypoints:
                grid_waypoints = [ordered_points[0]]

        flat_waypoints = [coord for point in grid_waypoints for coord in point]
        total_cost = coverage_cost + self._path_cost(grid_waypoints)
        return flat_waypoints, total_cost

    def _grid_size(self, boundary: Iterable[Tuple[float, float]]) -> tuple[int, int]:
        xs, ys = zip(*boundary)
        width = int((max(xs) - min(xs)) / self.grid_resolution) + 1
        height = int((max(ys) - min(ys)) / self.grid_resolution) + 1
        return width, height

    def _to_grid(self, point: Tuple[float, float]) -> tuple[int, int]:
        return (
            int(point[0] / self.grid_resolution),
            int(point[1] / self.grid_resolution),
        )

    def _from_grid(self, point: tuple[int, int]) -> tuple[float, float]:
        return (
            point[0] * self.grid_resolution,
            point[1] * self.grid_resolution,
        )

    def _obstacle_grid(self, obstacles: list[list[tuple[float, float]]]) -> set[tuple[int, int]]:
        blocked: set[tuple[int, int]] = set()
        if not obstacles:
            return blocked
        for vertices in obstacles:
            if len(vertices) < 3:
                continue
            poly = Polygon(vertices)
            minx, miny, maxx, maxy = poly.bounds
            gx_min = int(minx / self.grid_resolution)
            gx_max = int(maxx / self.grid_resolution) + 1
            gy_min = int(miny / self.grid_resolution)
            gy_max = int(maxy / self.grid_resolution) + 1
            for gx in range(gx_min, gx_max):
                for gy in range(gy_min, gy_max):
                    center = (
                        (gx + 0.5) * self.grid_resolution,
                        (gy + 0.5) * self.grid_resolution,
                    )
                    if poly.contains(Point(center)):
                        blocked.add((gx, gy))
        return blocked

    def _path_cost(self, waypoints: list[tuple[float, float]]) -> float:
        if len(waypoints) < 2:
            return 0.0
        diffs = np.diff(np.array(waypoints), axis=0)
        segment_lengths = np.linalg.norm(diffs, axis=1)
        return float(segment_lengths.sum())
