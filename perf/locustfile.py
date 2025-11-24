import json
import random
import time

from locust import HttpUser, LoadTestShape, between, events, task
from prometheus_client import Histogram, start_http_server

PLANNER_LATENCY = Histogram(
    "locust_plan_latency_seconds",
    "p99 / latency observations for /plans/generate",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
    labelnames=("endpoint",),
)
DB_LATENCY = Histogram(
    "locust_db_latency_seconds",
    "Proxy for DB read/write endpoints",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5),
    labelnames=("endpoint",),
)

start_http_server(9201)


@events.request.add_listener
def _track_metrics(request_type, name, response_time, response_length, response, context, exception):
    elapsed = response_time / 1000.0
    if name.startswith("/plans"):
        PLANNER_LATENCY.labels(endpoint=name).observe(elapsed)
    if name in {"/walls/", "/obstacles/"}:
        DB_LATENCY.labels(endpoint=name).observe(elapsed)


class PlannerUser(HttpUser):
    wait_time = between(0.05, 0.2)

    def on_start(self):
        self.wall_geometry = {"boundary": [[0, 0], [40, 0], [40, 40], [0, 40], [0, 0]]}
        self.wall_id = None
        self.plan_id = None

    def _random_obstacles(self):
        obstacles = []
        for _ in range(random.randint(3, 15)):
            cx = random.uniform(5, 35)
            cy = random.uniform(5, 35)
            size = random.uniform(1, 3)
            obstacles.append({
                "boundary": [
                    [cx - size, cy - size],
                    [cx + size, cy - size],
                    [cx + size, cy + size],
                    [cx - size, cy + size],
                    [cx - size, cy - size],  # Close polygon
                ]
            })
        return obstacles

    @task(3)
    def plan_generation(self):
        payload = {"wall_geometry": self.wall_geometry, "obstacles": self._random_obstacles()}
        with self.client.post("/plans/generate", json=payload, catch_response=True, timeout=30) as response:
            if response.status_code == 200:
                data = response.json()
                self.plan_id = data.get("id")
            elif response.status_code == 400:
                response.failure("Path planning failed (no path found)")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def create_wall(self):
        payload = {
            "name": f"LoadTest Wall {random.randint(1000, 9999)}",
            "geometry": {
                "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
            }
        }
        with self.client.post("/walls/", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                self.wall_id = response.json().get("id")
            else:
                response.failure(f"Wall creation failed: {response.status_code}")

    @task(1)
    def list_walls(self):
        self.client.get("/walls/")

    @task(1)
    def list_obstacles(self):
        self.client.get("/obstacles/")

    @task(1)
    def list_plans(self):
        self.client.get("/plans/")

    @task(1)
    def update_robot_state(self):
        payload = {
            "status": "moving",
            "position": {"x": random.uniform(0, 10), "y": random.uniform(0, 5), "z": 0.0},
            "velocity": random.uniform(0, 1),
            "battery": random.uniform(50, 100)
        }
        self.client.post("/robot/state", json=payload)

    @task(1)
    def get_robot_state(self):
        self.client.get("/robot/state")


class BurstShape(LoadTestShape):
    stages = (
        {"duration": 60, "users": 100, "spawn_rate": 20},
        {"duration": 120, "users": 10000, "spawn_rate": 500},
        {"duration": 240, "users": 200, "spawn_rate": 50},
    )

    def tick(self):
        run_time = time.time() - self.get_start_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
            run_time -= stage["duration"]
        return None
