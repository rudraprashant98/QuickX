from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from shapely.geometry import Polygon, Point
from shapely.validation import make_valid


def validate_polygon_geometry(v: dict, max_vertices: int = 1000) -> dict:
    """Validate polygon geometry with comprehensive checks"""
    if not isinstance(v, dict):
        raise ValueError("Geometry must be a dictionary")
    
    boundary = v.get("boundary", [])
    if not isinstance(boundary, list):
        raise ValueError("Boundary must be a list")
    
    # Check minimum vertices
    if len(boundary) < 3:
        raise ValueError("Polygon must have at least 3 vertices")
    
    # Check maximum vertices (prevent DoS)
    if len(boundary) > max_vertices:
        raise ValueError(f"Polygon cannot have more than {max_vertices} vertices")
    
    # Check all points are numeric
    for i, point in enumerate(boundary):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(f"Point {i} must be a list/tuple of 2 coordinates")
        try:
            float(point[0])
            float(point[1])
        except (ValueError, TypeError):
            raise ValueError(f"Point {i} coordinates must be numeric")
    
    # Check polygon closure
    if boundary[0] != boundary[-1]:
        raise ValueError("Polygon must be closed (first and last point must be the same)")
    
    # Check for degenerate polygon (all points same)
    if len(set(tuple(p) for p in boundary)) < 3:
        raise ValueError("Polygon is degenerate (all points are the same or too few unique points)")
    
    # Check for self-intersection using Shapely
    try:
        poly = Polygon(boundary)
        if not poly.is_valid:
            # Try to make valid
            poly = make_valid(poly)
            if poly.is_empty or poly.area == 0:
                raise ValueError("Polygon is invalid or has zero area")
    except Exception as e:
        raise ValueError(f"Invalid polygon geometry: {str(e)}")
    
    return v


class WallCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    geometry: dict
    
    @field_validator('geometry')
    @classmethod
    def validate_geometry(cls, v):
        return validate_polygon_geometry(v)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class WallRead(WallCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2


class ObstacleCreate(BaseModel):
    wall_id: int = Field(..., gt=0)
    geometry: dict
    
    @field_validator('geometry')
    @classmethod
    def validate_geometry(cls, v):
        return validate_polygon_geometry(v)


class ObstacleRead(ObstacleCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2


class PathPlanCreate(BaseModel):
    wall_id: Optional[int] = Field(None, gt=0)
    waypoints: List[float] = Field(..., min_items=2, max_length=10000)  # Max 5000 waypoints
    cost: float = Field(..., ge=0.0)
    algorithm: str = Field(..., pattern=r"^[A-Za-z0-9_]+$", min_length=1, max_length=50)
    
    @field_validator('waypoints')
    @classmethod
    def validate_waypoints(cls, v):
        if len(v) % 2 != 0:
            raise ValueError("Waypoints must have even number of coordinates (x, y pairs)")
        for i, coord in enumerate(v):
            if not isinstance(coord, (int, float)):
                raise ValueError(f"Waypoint coordinate {i} must be numeric")
        return v


class PathPlanRead(PathPlanCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2


class PlanGenerationRequest(BaseModel):
    wall_geometry: dict
    obstacles: List[dict] = Field(default_factory=list, max_length=100)  # Max 100 obstacles
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "wall_geometry": {
                        "boundary": [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
                    },
                    "obstacles": []
                }
            ]
        }
    }
    
    @field_validator('wall_geometry')
    @classmethod
    def validate_wall_geometry(cls, v):
        return validate_polygon_geometry(v)
    
    @field_validator('obstacles')
    @classmethod
    def validate_obstacles(cls, v):
        for i, obs in enumerate(v):
            if not isinstance(obs, dict):
                raise ValueError(f"Obstacle {i} must be a dictionary")
            validate_polygon_geometry(obs)
        return v
    
    @model_validator(mode='after')
    def validate_obstacles_inside_wall(self):
        """Validate that obstacles are inside the wall boundary"""
        wall_geometry = self.wall_geometry
        obstacles = self.obstacles
        
        if not wall_geometry or not obstacles:
            return self
        
        try:
            wall_boundary = wall_geometry.get('boundary', [])
            if not wall_boundary:
                return self
            
            wall_poly = Polygon(wall_boundary)
            if not wall_poly.is_valid:
                wall_poly = make_valid(wall_poly)
            
            for i, obs in enumerate(obstacles):
                obs_boundary = obs.get('boundary', [])
                if not obs_boundary:
                    continue
                
                obs_poly = Polygon(obs_boundary)
                if not obs_poly.is_valid:
                    obs_poly = make_valid(obs_poly)
                
                # Check if obstacle is inside wall
                if not wall_poly.contains(obs_poly):
                    raise ValueError(f"Obstacle {i} is outside the wall boundary")
                
                # Check for overlapping obstacles
                for j, other_obs in enumerate(obstacles[i+1:], start=i+1):
                    other_boundary = other_obs.get('boundary', [])
                    if not other_boundary:
                        continue
                    
                    other_poly = Polygon(other_boundary)
                    if not other_poly.is_valid:
                        other_poly = make_valid(other_poly)
                    
                    if obs_poly.intersects(other_poly) and not obs_poly.touches(other_poly):
                        raise ValueError(f"Obstacle {i} overlaps with obstacle {j}")
        except ValueError:
            raise
        except Exception as e:
            # If validation fails due to geometry issues, let it pass
            # The planner will handle it
            pass
        
        return self


class ExecutionRunCreate(BaseModel):
    plan_id: Optional[int]
    status: str
    telemetry: dict


class ExecutionRunRead(ExecutionRunCreate):
    id: int
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True  # Pydantic v2


class RobotCommand(BaseModel):
    command: str
    x: Optional[float]
    y: Optional[float]


class RobotTelemetry(BaseModel):
    position: dict
    speed: float
    status: str


class RobotStateCreate(BaseModel):
    status: str = Field(..., min_length=1, max_length=30)
    position: dict
    velocity: float = Field(..., ge=0.0)
    battery: float = Field(..., ge=0.0, le=100.0)
    
    @field_validator('position')
    @classmethod
    def validate_position(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Position must be a dictionary")
        required_keys = ['x', 'y']
        for key in required_keys:
            if key not in v:
                raise ValueError(f"Position must contain '{key}' coordinate")
            if not isinstance(v[key], (int, float)):
                raise ValueError(f"Position '{key}' must be numeric")
        return v


class RobotStateRead(RobotStateCreate):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2
