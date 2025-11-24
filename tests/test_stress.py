import asyncio

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.slow
@pytest.mark.anyio
async def test_stress_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        async def send(idx: int):
            payload = {"name": f"Wall-{idx}", "geometry": {"boundary": [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]}}
            response = await client.post("/walls/", json=payload)
            assert response.status_code == 200
        await asyncio.gather(*(send(i) for i in range(100)))

