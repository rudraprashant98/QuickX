import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.services import wall_service
from app.schemas import WallCreate


@pytest.mark.asyncio
async def test_wall_persistence(session_factory):
    async with session_factory() as session:  # type: AsyncSession
        # Polygon must be closed and have at least 3 vertices
        wall = await wall_service.create_wall(session, WallCreate(name="Lab", geometry={"boundary": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]}))
        assert isinstance(wall.id, int)
        result = await session.get(models.Wall, wall.id)
        assert result is not None
