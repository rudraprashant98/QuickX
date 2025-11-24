import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("MESSAGING_ENABLED", "false")

from app.db.base import Base
from app.dependencies import get_db_session
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True, scope="session")
async def override_session_dependency(session_factory):
    async def _get_session() -> AsyncSession:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _get_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    return TestClient(app)
