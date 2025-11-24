import time
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import REQUEST_LATENCY


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).observe(process_time)
        return response
