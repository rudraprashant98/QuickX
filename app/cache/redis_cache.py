import asyncio
import json
from typing import Any, Optional

import aioredis

from app.core.config import get_settings

settings = get_settings()


class RedisCache:
    def __init__(self) -> None:
        self._pool: Optional[aioredis.Redis] = None

    async def _get_pool(self) -> aioredis.Redis:
        if not self._pool:
            self._pool = await aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        return self._pool

    async def get(self, key: str) -> Any:
        pool = await self._get_pool()
        data = await pool.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        pool = await self._get_pool()
        await pool.set(key, json.dumps(value), ex=ttl)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None


cache = RedisCache()
