# Robotics Real-Time Control Stack

It’s a FastAPI + PostgreSQL + Redis + RabbitMQ/MQTT stack that plans robot paths, tracks execution, and streams telemetry in real time. Point it at a wall layout, sprinkle in obstacles, hit the planner, and watch the robot follow along while you keep an eye on metrics and logs.

---
## Demo Video
<a href="https://drive.google.com/file/d/1L1NJLyZvBsgHGJL4hXLAqIIW98b0epoE/view?usp=sharing" target="_blank">
  ▶️ Watch Demo Video
</a>

## Before You Dive In

The happy path is simple:

1. Describe the environment (walls + obstacles).
2. Ask the planner for a set of waypoints.
3. Stream commands over MQTT or RabbitMQ.
4. Mirror telemetry over WebSocket and stash everything in Postgres.

A few mental bookmarks:

- FastAPI fronts the APIs, PostgreSQL holds the truth, Redis/Celery take the long jobs, and RabbitMQ/MQTT push bits toward robots.
- REST handles CRUD, WebSockets keep dashboards breathing, MQTT or RabbitMQ keep devices honest.
- Use it when you need a realistic robotics backend but don’t feel like reinventing planners, telemetry hubs, or ops wiring.

---

## How Everything Flows

```
 ┌─────────┐      ┌───────────┐      ┌──────────────┐
 │ Clients │ ---> │ FastAPI   │ ---> │ PostgreSQL    │
 │ (UI,CLI)│      │ Routers   │      │ + Redis Cache │
 └─────────┘      └───────────┘      └──────┬───────┘
        │            │   ▲                  │
        │            ▼   │                  │
        │        Services│        ┌─────────▼────────┐
        │            │   │        │ Messaging Layer  │
        │            ▼   │        │ MQTT + RabbitMQ  │
        │        Planners│        └─────────▲────────┘
        │            │   │                  │
        ▼            ▼   │                  ▼
   WebSocket Hub  Background Tasks     Robot / Simulator
```

- **Planners** crunch A* or Genetic strategies and return waypoints.
- **Messaging layer** publishes control frames over MQTT or RabbitMQ.
- **WebSocket hub** mirrors telemetry and plan updates to dashboards.
- **Celery worker** handles long-running or retry-friendly tasks.

---

## Setup Options

### 1. Docker (fastest path)

```bash
cd /Users/prashantgiri/Project/xyz/10X
docker-compose up -d
sleep 25                    # give services time to warm up
docker-compose ps
curl http://localhost:8000/docs
```

Keep the first run boring: start everything, give it ~30 s, then poke the docs. If you’re curious, here’s where everything lands:

- API/Docs `http://localhost:8000/docs`
- Metrics `http://localhost:8000/metrics`
- Telemetry WebSocket `ws://localhost:8000/ws/telemetry`
- Path WebSocket `ws://localhost:8000/ws/path`
- RabbitMQ UI `http://localhost:15672` (guest/guest)
- Kibana `http://localhost:5601`

### 2. Local Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+asyncpg://robotics:robotics@localhost:5432/robotics"
export REDIS_URL="redis://localhost:6379/0"
export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
export MQTT_HOST="localhost"
export MQTT_PORT="1883"

python scripts/init_db.py
python scripts/create_indexes.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The local route is nice when you want to set breakpoints inside planners. Just remember to keep PostgreSQL/Redis/RabbitMQ running somewhere reachable.

### 3. .env starter

```
DATABASE_URL=postgresql+asyncpg://robotics:robotics@localhost:5432/robotics
SYNC_DATABASE_URL=postgresql+psycopg://robotics:robotics@localhost:5432/robotics
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
MQTT_HOST=localhost
MQTT_PORT=1883
ELASTIC_URL=http://localhost:9200
MESSAGING_ENABLED=true
```

---

## Key Domain Objects

- **Walls** – outer shells (polygons) that tell the planner where the robot may live.
- **Obstacles** – holes punched inside a wall to keep robots from clipping furniture.
- **Plans** – bundles of waypoints, cost info, and metadata; produced by A* or GA.
- **Robot state** – whatever the robot last reported: pose, velocity, battery.
- **Runs** – execution diary: inputs + outputs + timestamps.
- **Telemetry** – small JSON blobs riding the WebSocket so dashboards feel alive.

---

## Project Map

```
10X/
├── app/
│   ├── main.py                # FastAPI entry point
│   ├── core/                  # Config, logging, metrics
│   ├── db/                    # SQLAlchemy base/session
│   ├── routers/               # REST + WebSocket endpoints
│   ├── services/              # Business logic
│   ├── planners/              # A*, GA, polygon helpers
│   ├── messaging/             # MQTT & RabbitMQ clients
│   ├── tasks/worker.py        # Celery worker bootstrap
│   ├── utils/visualization.py # WebSocket broadcaster
│   ├── cache/redis_cache.py   # Redis helpers
│   └── schemas.py             # Pydantic models
├── tests/                     # pytest suites (API, planner, etc.)
├── perf/locustfile.py         # Load testing profile
├── docs/swagger.json          # Frozen OpenAPI spec
├── docs/Robotics_API.postman_collection.json
├── docker-compose.yml / Dockerfile
├── scripts/ (init_db, create_indexes, check_services, ...)
└── README.md
```

---

## API Surface Snapshot

- `POST /walls/`, `GET /walls/`
- `POST /obstacles/`, `GET /obstacles/?wall_id=...`
- `POST /plans/`, `POST /plans/generate`, `GET /plans/`
- `POST /robot/command`, `POST /robot/state`, `GET /robot/state`
- `POST /runs/`, `GET /runs/`, `GET /runs/{id}`
- `WebSocket /ws/telemetry`, `WebSocket /ws/path`
- `GET /metrics`

Swagger UI at `http://localhost:8000/docs`.

---

## Typical End-to-End Flow

1. Create a wall:
   ```bash
   curl -X POST http://localhost:8000/walls/ \
     -H "Content-Type: application/json" \
     -d '{"name":"Test Wall","geometry":{"boundary":[[0,0],[10,0],[10,5],[0,5],[0,0]]}}'
   ```
2. Add obstacles to that wall (pillars, cabinets, etc.).
3. Request a plan:
   ```bash
   curl -X POST http://localhost:8000/plans/generate \
     -H "Content-Type: application/json" \
     -d '{"wall_geometry":{"boundary":[[0,0],[10,0],[10,5],[0,5],[0,0]]},
          "obstacles":[{"boundary":[[2,2],[4,2],[4,3],[2,3],[2,2]]}] }'
   ```
4. Stream the waypoints via MQTT/RabbitMQ using `POST /robot/command`.
5. Report robot state back with `POST /robot/state`.
6. Track the whole execution through `POST /runs/` and WebSockets.

Run the full scripted version anytime:

```bash
python3 test_e2e_complete_flow.py
```

It sets up the wall, sprinkles obstacles, runs the planner, fakes motion, watches telemetry, checks Prometheus, and peeks into the DB so you know everything talks to everything.

---

## Testing & Quality

```bash
# All tests
pytest tests/ -v

# Focused suites
pytest tests/test_api_validation_100.py -v
pytest tests/test_planner_algorithmic.py -v
pytest tests/test_e2e_replay.py -v

# Coverage
pytest tests/ --cov=app --cov-report=html
```

Test buckets include API validation, planner math, messaging resiliency, WebSocket chaos, E2E replay, leak detection, security scans, and performance (see `tests/` naming).

Use Postman by importing `docs/Robotics_API.postman_collection.json` and pointing `base_url` to `http://localhost:8000`.

Load testing (Locust):

```bash
pip install locust
locust -f perf/locustfile.py --headless -u 100 -r 25 -t 3m --host http://localhost:8000
# or
locust -f perf/locustfile.py --host http://localhost:8000   # UI at http://localhost:8089
```

---

## Monitoring & Operations

- **Prometheus**: `http://localhost:8000/metrics`
  - Key series: `fastapi_request_latency_seconds`, `db_query_latency_seconds`, `telemetry_broadcast_messages_total`, `planner_compute_seconds`, `process_resident_memory_bytes`.
- **Logging**: piped to Elasticsearch/Kibana (`http://localhost:9200`, `http://localhost:5601`). Follow along with `docker-compose logs -f app` or `docker-compose logs -f`.
- **Health script**: `./scripts/check_services.sh` or `make check-services`.
- **WebSocket smoke test**:
  ```javascript
  const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
  ws.onmessage = (e) => console.log('Telemetry', JSON.parse(e.data));
  ```

---

## Database Moves

```bash
# Initialize schema
docker-compose exec app python scripts/init_db.py
# or locally
python scripts/init_db.py

# Maintain indexes
docker-compose exec app python scripts/create_indexes.py
```

Tables: `walls`, `obstacles`, `path_plans`, `execution_runs`, `robot_states`. Every FK column is indexed, plus composite and partial indexes for frequent filters.

Sample queries:

```sql
SELECT * FROM walls ORDER BY created_at DESC;
SELECT * FROM obstacles WHERE wall_id = 1;
SELECT * FROM path_plans WHERE wall_id = 1 ORDER BY cost ASC;
SELECT * FROM execution_runs WHERE plan_id = 1 ORDER BY started_at DESC;
SELECT * FROM robot_states ORDER BY updated_at DESC LIMIT 1;
```

Alembic workflow:

```bash
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
alembic downgrade -1
```

---

## Docker Services Cheat Sheet

| Service      | Port(s)     | Role                        |
|--------------|-------------|-----------------------------|
| app          | 8000        | FastAPI application         |
| postgres     | 5432        | Primary database            |
| redis        | 6379        | Cache + Celery broker       |
| rabbitmq     | 5672 / 15672| Broker + management UI      |
| mqtt         | 1883        | MQTT broker                 |
| elasticsearch| 9200        | Log storage                 |
| kibana       | 5601        | Log visualization           |
| logstash     | -           | Log pipeline                |
| worker       | -           | Celery worker               |

Service management:

```bash
docker-compose up -d
docker-compose down
docker-compose restart app
docker-compose logs -f app
docker-compose build --no-cache app && docker-compose up -d app
```

Reset DB (pick one):

```bash
CLEAR_DB_ON_START=true docker-compose up -d
docker-compose down -v && docker-compose up -d
docker-compose exec app python scripts/clear_db.py
docker-compose exec app python scripts/create_indexes.py
```

---

## Troubleshooting Cheatsheet

- **Port 8000 dead**  
  `docker-compose ps app`, then `docker-compose logs app`, restart with `docker-compose restart app`. Rebuild if code changed.

- **Database refuses connections**  
  `docker-compose logs postgres`, `docker-compose exec postgres psql -U robotics -d robotics -c "SELECT 1;"`, rerun `scripts/init_db.py` if needed.

- **Messaging hiccups (RabbitMQ/MQTT)**  
  `docker-compose ps rabbitmq mqtt`, inspect logs, `docker-compose restart rabbitmq mqtt`.

- **Memory creeping up**  
  `docker stats`, restart services, purge old execution data:
  ```bash
  docker-compose exec postgres psql -U robotics -d robotics \
    -c "DELETE FROM execution_runs WHERE finished_at < NOW() - INTERVAL '7 days';"
  ```

---

## Developer Workflow

1. Work inside `app/`.
2. Run `pytest tests/`.
3. Optional: `python3 tests/test_e2e_complete_flow.py`.
4. `docker-compose logs -f app` while testing.
5. Sanity-check Swagger + WebSockets.
6. Commit with a clear message.

Need a new feature? Sketch the schema, build the service, wire the router, register it in `app/main.py`, and keep business logic out of routers so the worker can call it too.

---

## Performance & Security Notes

- Targets: planning < 2s, API p50 < 100 ms (p99 < 500 ms), WebSocket latency < 50 ms, 100+ concurrent calls.
- Optimizations already wired: indexes, async DB sessions, Redis cache, Celery offloading.
- Security baseline: Pydantic validation, SQLAlchemy ORM, 5 MB payload cap, permissive CORS (tighten for prod), sanitized error responses.
- Production TODOs: JWT auth, strict CORS, HTTPS, rate limiting, broker auth, encrypted secrets, request signing.

---

## Deployment Tips

- Set env vars for whichever platform runs the container.
- Prefer managed PostgreSQL/Redis/RabbitMQ for reliability.
- Put FastAPI behind nginx/traefik for TLS.
- Wire up Prometheus/Grafana and ELK in production.
- Back up databases and add a load balancer if you expect spikes.

Docker image:

```bash
docker build -t robotics-rt-stack:latest .
docker run -d -p 8000:8000 \
  -e DATABASE_URL="..." \
  -e REDIS_URL="..." \
  robotics-rt-stack:latest
```

---

## Extra References

- Swagger spec: `docs/swagger.json`
- Postman collection: `docs/Robotics_API.postman_collection.json`
- E2E helper: `tests/test_e2e_complete_flow.py`
- Performance profile: `perf/locustfile.py`

---

## Contributing

1. Cut a feature branch.
2. Build your change (schema → service → router).
3. Add/adjust tests.
4. Run the suite.
5. Open a PR with context screenshots/logs if relevant.

---

## License

[Add your license here]

---

## Need Help?

1. `docker-compose logs -f`
2. Visit `http://localhost:8000/docs`
3. Run `./scripts/check_services.sh`
4. Re-read the troubleshooting table above

Still stuck? Drop an issue with logs and whatever you were trying to do. We’ve probably hit that snag before.

Happy robotics hacking!
