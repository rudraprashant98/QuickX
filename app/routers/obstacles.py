from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.schemas import ObstacleCreate, ObstacleRead
from app.services import obstacle_service

router = APIRouter(prefix="/obstacles", tags=["obstacles"])


@router.post("/", response_model=ObstacleRead)
async def create_obstacle(payload: ObstacleCreate, session: AsyncSession = Depends(get_db_session)):
    return await obstacle_service.create_obstacle(session, payload)


@router.get("/", response_model=list[ObstacleRead])
async def list_obstacles(wall_id: Optional[int] = None, session: AsyncSession = Depends(get_db_session)):
    return await obstacle_service.list_obstacles(session, wall_id)


@router.get("/{obstacle_id}", response_model=ObstacleRead)
async def get_obstacle(obstacle_id: int, session: AsyncSession = Depends(get_db_session)):
    from fastapi import HTTPException
    obstacle = await obstacle_service.get_obstacle(session, obstacle_id)
    if not obstacle:
        raise HTTPException(status_code=404, detail="Obstacle not found")
    return obstacle
