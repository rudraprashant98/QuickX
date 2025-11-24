from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from shapely.geometry import Polygon
from shapely.validation import make_valid

from app.db import models
from app.schemas import ObstacleCreate


async def create_obstacle(session: AsyncSession, payload: ObstacleCreate) -> models.Obstacle:
    # Verify wall exists
    wall_result = await session.execute(select(models.Wall).where(models.Wall.id == payload.wall_id))
    wall = wall_result.scalar_one_or_none()
    if not wall:
        raise HTTPException(status_code=404, detail=f"Wall with id {payload.wall_id} not found")
    
    # Validate obstacle is inside wall boundary
    try:
        wall_boundary = wall.geometry.get("boundary", [])
        if wall_boundary:
            wall_poly = Polygon(wall_boundary)
            if not wall_poly.is_valid:
                wall_poly = make_valid(wall_poly)
            
            obs_boundary = payload.geometry.get("boundary", [])
            if obs_boundary:
                obs_poly = Polygon(obs_boundary)
                if not obs_poly.is_valid:
                    obs_poly = make_valid(obs_poly)
                
                # Check if obstacle is inside wall
                if not wall_poly.contains(obs_poly):
                    raise HTTPException(
                        status_code=400,
                        detail="Obstacle must be inside the wall boundary"
                    )
        
        # Check for overlapping obstacles with same wall
        existing_obstacles_result = await session.execute(
            select(models.Obstacle).where(models.Obstacle.wall_id == payload.wall_id)
        )
        existing_obstacles = existing_obstacles_result.scalars().all()
        
        obs_boundary = payload.geometry.get("boundary", [])
        if obs_boundary:
            new_obs_poly = Polygon(obs_boundary)
            if not new_obs_poly.is_valid:
                new_obs_poly = make_valid(new_obs_poly)
            
            for existing_obs in existing_obstacles:
                existing_boundary = existing_obs.geometry.get("boundary", [])
                if existing_boundary:
                    existing_poly = Polygon(existing_boundary)
                    if not existing_poly.is_valid:
                        existing_poly = make_valid(existing_poly)
                    
                    # Check for overlap (intersects but not just touching)
                    if new_obs_poly.intersects(existing_poly) and not new_obs_poly.touches(existing_poly):
                        raise HTTPException(
                            status_code=400,
                            detail="Obstacle overlaps with existing obstacle"
                        )
    except HTTPException:
        raise
    except Exception:
        # If geometry validation fails, allow it (handled by planner)
        pass
    
    obstacle = models.Obstacle(wall_id=payload.wall_id, geometry=payload.geometry)
    session.add(obstacle)
    await session.commit()
    await session.refresh(obstacle)
    return obstacle


async def list_obstacles(session: AsyncSession, wall_id: Optional[int] = None) -> List[models.Obstacle]:
    stmt = select(models.Obstacle)
    if wall_id:
        stmt = stmt.where(models.Obstacle.wall_id == wall_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_obstacle(session: AsyncSession, obstacle_id: int) -> Optional[models.Obstacle]:
    result = await session.execute(select(models.Obstacle).where(models.Obstacle.id == obstacle_id))
    return result.scalar_one_or_none()
