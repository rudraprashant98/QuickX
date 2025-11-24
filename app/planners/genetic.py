from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

from app.cache.sync_cache import sync_cache

Point = Tuple[float, float]


def distance(a: Point, b: Point) -> float:
    """Calculate distance between two points, using cache if available."""
    # Normalize point order for cache key (smaller point first)
    if a < b:
        key_a, key_b = a, b
    else:
        key_a, key_b = b, a
    
    # Try cache first
    cached = sync_cache.get("distance", key_a, key_b)
    if cached is not None:
        return cached
    
    # Calculate distance
    dist = math.hypot(a[0] - b[0], a[1] - b[1])
    
    # Cache result (TTL: 1 hour)
    sync_cache.set("distance", key_a, key_b, value=dist, ttl=3600)
    
    return dist


def route_length(route: Sequence[Point]) -> float:
    """Calculate route length, using cached distances."""
    # Create cache key from route (preserve order - route length depends on point order)
    route_tuple = tuple(route)
    cached = sync_cache.get("route_length", route_tuple)
    if cached is not None:
        return cached
    
    # Calculate route length using cached distances
    total = sum(distance(route[i], route[(i + 1) % len(route)]) for i in range(len(route)))
    
    # Cache result (TTL: 1 hour)
    sync_cache.set("route_length", route_tuple, value=total, ttl=3600)
    
    return total


def crossover(parent1: Sequence[Point], parent2: Sequence[Point]) -> List[Point]:
    size = len(parent1)
    start, end = sorted(random.sample(range(size), 2))
    child = [None] * size
    child[start:end] = parent1[start:end]
    fill_values = [gene for gene in parent2 if gene not in child]
    idx = 0
    for i in range(size):
        if child[i] is None:
            child[i] = fill_values[idx]
            idx += 1
    return child  # type: ignore


def mutate(route: List[Point], rate: float = 0.01) -> None:
    for i in range(len(route)):
        if random.random() < rate:
            j = random.randint(0, len(route) - 1)
            route[i], route[j] = route[j], route[i]


def optimize(points: Sequence[Point], generations: int = 200, population_size: int = 50) -> tuple[list[Point], float]:
    if len(points) < 2:
        return list(points), 0.0

    # Pre-compute distance matrix for all point pairs (cached)
    # This eliminates repeated distance calculations during optimization
    distance_matrix: dict[tuple[Point, Point], float] = {}
    points_list = list(points)
    
    for i, p1 in enumerate(points_list):
        for j, p2 in enumerate(points_list):
            if i != j:
                # Normalize key (smaller point first)
                key = (p1, p2) if p1 < p2 else (p2, p1)
                if key not in distance_matrix:
                    # Try cache first
                    cached = sync_cache.get("distance", key[0], key[1])
                    if cached is not None:
                        distance_matrix[key] = cached
                    else:
                        dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                        distance_matrix[key] = dist
                        # Cache for future use
                        sync_cache.set("distance", key[0], key[1], value=dist, ttl=3600)
    
    # Fast distance lookup function using pre-computed matrix
    def fast_distance(a: Point, b: Point) -> float:
        key = (a, b) if a < b else (b, a)
        return distance_matrix.get(key, math.hypot(a[0] - b[0], a[1] - b[1]))
    
    # Fast route length using pre-computed distances
    def fast_route_length(route: Sequence[Point]) -> float:
        return sum(fast_distance(route[i], route[(i + 1) % len(route)]) for i in range(len(route)))

    population = [random.sample(points_list, len(points_list)) for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fast_route_length)
        survivors = population[: population_size // 2]
        offspring = []
        while len(offspring) + len(survivors) < population_size:
            parent1, parent2 = random.sample(survivors, 2)
            child = crossover(parent1, parent2)
            mutate(child)
            offspring.append(child)
        population = survivors + offspring

    best = min(population, key=fast_route_length)
    return best, fast_route_length(best)
