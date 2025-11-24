from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.schemas import PathPlanCreate


async def create_plan(session: AsyncSession, payload: PathPlanCreate) -> models.PathPlan:
    plan = models.PathPlan(
        wall_id=payload.wall_id,
        waypoints=payload.waypoints,
        cost=payload.cost,
        algorithm=payload.algorithm,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def list_plans(session: AsyncSession) -> List[models.PathPlan]:
    result = await session.execute(select(models.PathPlan))
    return result.scalars().all()
