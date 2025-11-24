from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.instrumentation import MetricsMiddleware
from app.core.logging import configure_logging
from app.messaging.manager import get_mqtt, get_rabbitmq
from app.routers import metrics, obstacles, plans, robot, runs, visualization, walls

configure_logging()
settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input"),
        }
        # Convert ValueError in ctx to string
        if "ctx" in error and "error" in error["ctx"]:
            ctx_error = error["ctx"]["error"]
            if isinstance(ctx_error, Exception):
                serializable_error["ctx"] = {"error": str(ctx_error)}
            else:
                serializable_error["ctx"] = error["ctx"]
        elif "ctx" in error:
            serializable_error["ctx"] = error["ctx"]
        errors.append(serializable_error)
    
    return JSONResponse(
        status_code=422,
        content={"detail": errors, "body": exc.body},
    )


@app.middleware("http")
async def check_request_size(request: Request, call_next):
    """Limit request body size to 5MB"""
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        if len(body) > 5 * 1024 * 1024:  # 5MB
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large. Maximum size is 5MB."}
            )
        # Recreate request with body for downstream handlers
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    return await call_next(request)

app.include_router(walls.router)
app.include_router(obstacles.router)
app.include_router(plans.router)
app.include_router(robot.router)
app.include_router(runs.router)
app.include_router(metrics.router)
app.include_router(visualization.router)


@app.on_event("startup")
async def startup_event() -> None:
    logging.getLogger(__name__).info("Starting application components")
    if settings.messaging_enabled:
        get_rabbitmq()
        get_mqtt()