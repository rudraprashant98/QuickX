from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.schemas import WallCreate


async def create_wall(session: AsyncSession, payload: WallCreate) -> models.Wall:
    wall = models.Wall(name=payload.name, geometry=payload.geometry)
    session.add(wall)
    await session.commit()
    await session.refresh(wall)
    return wall


async def list_walls(session: AsyncSession) -> List[models.Wall]:
    result = await session.execute(select(models.Wall))
    return result.scalars().all()


async def get_wall(session: AsyncSession, wall_id: int) -> Optional[models.Wall]:
    result = await session.execute(select(models.Wall).where(models.Wall.id == wall_id))
    return result.scalar_one_or_none()
