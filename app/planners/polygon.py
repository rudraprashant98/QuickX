from __future__ import annotations

from shapely.geometry import Polygon
from shapely.ops import triangulate
from typing import List


def decompose_polygon(boundary: list[tuple[float, float]], obstacles: list[list[tuple[float, float]]]) -> List[Polygon]:
    base_polygon = Polygon(boundary)
    for obstacle in obstacles:
        base_polygon = base_polygon.difference(Polygon(obstacle))
    if base_polygon.is_empty:
        return []
    return triangulate(base_polygon)
