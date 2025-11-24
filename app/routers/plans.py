from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.planners.planner import PathPlanner
from app.schemas import PathPlanCreate, PathPlanRead, PlanGenerationRequest
from app.services import plan_service
from app.utils.visualization import hub

router = APIRouter(prefix="/plans", tags=["plans"])
planner = PathPlanner()


@router.post("/", response_model=PathPlanRead)
async def create_plan(payload: PathPlanCreate, session: AsyncSession = Depends(get_db_session)):
    plan = await plan_service.create_plan(session, payload)
    await hub.broadcast({"path": _reshape(plan.waypoints)}, "path")
    return plan


@router.get("/", response_model=list[PathPlanRead])
async def list_plans(session: AsyncSession = Depends(get_db_session)):
    return await plan_service.list_plans(session)


@router.post("/generate", response_model=PathPlanRead)
async def generate_plan(
    payload: PlanGenerationRequest,
    session: AsyncSession = Depends(get_db_session),
):
    from fastapi import HTTPException
    try:
        waypoints, cost = planner.generate_trajectory(payload.wall_geometry, payload.obstacles)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Path planning failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during path planning: {str(e)}")
    
    plan_payload = PathPlanCreate(wall_id=None, waypoints=waypoints, cost=cost, algorithm=planner.last_algorithm)
    plan = await plan_service.create_plan(session, plan_payload)
    await hub.broadcast(
        {"path": _reshape(plan.waypoints), "walls": payload.wall_geometry.get("boundary"), "obstacles": payload.obstacles},
        "path",
    )
    return plan


def _reshape(coords: list[float]) -> list[list[float]]:
    return [coords[i : i + 2] for i in range(0, len(coords), 2)]
