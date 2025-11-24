from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.schemas import RobotStateCreate


async def upsert_robot_state(session: AsyncSession, payload: RobotStateCreate) -> models.RobotState:
    result = await session.execute(select(models.RobotState).limit(1))
    state = result.scalars().first()
    if state:
        state.status = payload.status
        state.position = payload.position
        state.velocity = payload.velocity
        state.battery = payload.battery
    else:
        state = models.RobotState(**payload.model_dump())
        session.add(state)
    await session.commit()
    await session.refresh(state)
    return state


async def get_robot_state(session: AsyncSession) -> Optional[models.RobotState]:
    result = await session.execute(select(models.RobotState).limit(1))
    return result.scalars().first()
