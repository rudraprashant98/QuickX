from __future__ import annotations

import logging
from celery import Celery

from app.core.config import get_settings
from app.core.metrics import WORKER_TASKS

settings = get_settings()

celery_app = Celery(
    "robotics_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.execute_plan")
def execute_plan(self, plan_id: int) -> dict:
    WORKER_TASKS.labels(task=self.name, status="started").inc()
    logger.info("Executing plan %s", plan_id)
    result = {"plan_id": plan_id, "status": "completed"}
    WORKER_TASKS.labels(task=self.name, status="completed").inc()
    return result
