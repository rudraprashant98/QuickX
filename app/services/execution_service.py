from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.schemas import ExecutionRunCreate


async def create_run(session: AsyncSession, payload: ExecutionRunCreate) -> models.ExecutionRun:
    run = models.ExecutionRun(
        plan_id=payload.plan_id,
        status=payload.status,
        telemetry=payload.telemetry,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def list_runs(session: AsyncSession) -> List[models.ExecutionRun]:
    result = await session.execute(select(models.ExecutionRun))
    return result.scalars().all()


async def get_run(session: AsyncSession, run_id: int) -> Optional[models.ExecutionRun]:
    return await session.get(models.ExecutionRun, run_id)
