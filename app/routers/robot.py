from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.messaging.manager import get_mqtt, get_rabbitmq
from app.schemas import RobotCommand, RobotStateCreate, RobotStateRead
from app.services import robot_service
from app.utils.visualization import hub

router = APIRouter(prefix="/robot", tags=["robot"])


def _publish_command(payload: dict) -> None:
    rabbit = get_rabbitmq()
    mqtt = get_mqtt()
    if rabbit:
        rabbit.publish_command("robot.command", payload)
    if mqtt:
        mqtt.publish("robot/commands", payload, qos=2)


@router.post("/command")
async def issue_command(
    command: RobotCommand,
    background_tasks: BackgroundTasks,
):
    payload = command.dict(exclude_none=True)
    background_tasks.add_task(_publish_command, payload)
    return {"status": "queued"}


@router.post("/state", response_model=RobotStateRead)
async def update_state(payload: RobotStateCreate, session: AsyncSession = Depends(get_db_session)):
    state = await robot_service.upsert_robot_state(session, payload)
    await hub.broadcast(payload.position, "telemetry")
    return state


@router.get("/state", response_model=Optional[RobotStateRead])
async def get_state(session: AsyncSession = Depends(get_db_session)):
    return await robot_service.get_robot_state(session)
