from prometheus_client import Counter, Histogram

REQUEST_LATENCY = Histogram(
    "fastapi_request_latency_seconds",
    "Latency of FastAPI requests",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
    labelnames=("method", "endpoint", "status_code"),
)

DB_LATENCY = Histogram(
    "db_query_latency_seconds",
    "Latency of database operations",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2),
    labelnames=("statement",),
)

BROKER_EVENTS = Counter(
    "message_broker_events_total",
    "Count of message broker events",
    labelnames=("broker", "event"),
)

WORKER_TASKS = Counter(
    "worker_tasks_total",
    "Celery worker task executions",
    labelnames=("task", "status"),
)

TELEMETRY_THROUGHPUT = Counter(
    "telemetry_broadcast_messages_total",
    "Telemetry/messages broadcast to visualization clients",
    labelnames=("channel",),
)

TELEMETRY_LATENCY = Histogram(
    "telemetry_broadcast_latency_seconds",
    "Latency for visualization broadcasts",
    buckets=(0.0005, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1),
    labelnames=("channel",),
)
