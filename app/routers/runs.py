from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.schemas import ExecutionRunCreate, ExecutionRunRead
from app.services import execution_service

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/", response_model=ExecutionRunRead)
async def create_run(payload: ExecutionRunCreate, session: AsyncSession = Depends(get_db_session)):
    return await execution_service.create_run(session, payload)


@router.get("/", response_model=list[ExecutionRunRead])
async def list_runs(session: AsyncSession = Depends(get_db_session)):
    return await execution_service.list_runs(session)


@router.get("/{run_id}", response_model=ExecutionRunRead)
async def get_run(run_id: int, session: AsyncSession = Depends(get_db_session)):
    run = await execution_service.get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
