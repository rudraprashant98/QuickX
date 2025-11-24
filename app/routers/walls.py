from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.schemas import WallCreate, WallRead
from app.services import wall_service

router = APIRouter(prefix="/walls", tags=["walls"])


@router.post("/", response_model=WallRead)
async def create_wall(payload: WallCreate, session: AsyncSession = Depends(get_db_session)):
    return await wall_service.create_wall(session, payload)


@router.get("/", response_model=list[WallRead])
async def list_walls(session: AsyncSession = Depends(get_db_session)):
    return await wall_service.list_walls(session)


@router.get("/{wall_id}", response_model=WallRead)
async def get_wall(wall_id: int, session: AsyncSession = Depends(get_db_session)):
    from fastapi import HTTPException
    wall = await wall_service.get_wall(session, wall_id)
    if not wall:
        raise HTTPException(status_code=404, detail="Wall not found")
    return wall
