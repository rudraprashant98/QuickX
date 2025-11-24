from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Index
from sqlalchemy.orm import relationship

from .base import Base


class Wall(Base):
    __tablename__ = "walls"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    geometry = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_wall_created_at', 'created_at'),
    )

    obstacles = relationship("Obstacle", back_populates="wall")
    plans = relationship("PathPlan", back_populates="wall")


class Obstacle(Base):
    __tablename__ = "obstacles"

    id = Column(Integer, primary_key=True, index=True)
    wall_id = Column(Integer, ForeignKey("walls.id", ondelete="CASCADE"), index=True)
    geometry = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_obstacle_wall_id', 'wall_id'),
        Index('idx_obstacle_created_at', 'created_at'),
    )

    wall = relationship("Wall", back_populates="obstacles")


class PathPlan(Base):
    __tablename__ = "path_plans"

    id = Column(Integer, primary_key=True, index=True)
    wall_id = Column(Integer, ForeignKey("walls.id", ondelete="SET NULL"), index=True)
    waypoints = Column(JSON, nullable=False)
    cost = Column(Float, nullable=False, index=True)
    algorithm = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_plan_wall_id', 'wall_id'),
        Index('idx_plan_algorithm', 'algorithm'),
        Index('idx_plan_cost', 'cost'),
        Index('idx_plan_created_at', 'created_at'),
    )

    wall = relationship("Wall", back_populates="plans")
    runs = relationship("ExecutionRun", back_populates="plan")


class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("path_plans.id", ondelete="SET NULL"), index=True)
    status = Column(String(30), nullable=False, index=True)
    telemetry = Column(JSON, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    finished_at = Column(DateTime, index=True)

    __table_args__ = (
        Index('idx_run_plan_id', 'plan_id'),
        Index('idx_run_status', 'status'),
        Index('idx_run_started_at', 'started_at'),
        Index('idx_run_finished_at', 'finished_at'),
    )

    plan = relationship("PathPlan", back_populates="runs")


class RobotState(Base):
    __tablename__ = "robot_states"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(30), nullable=False, index=True)
    position = Column(JSON, nullable=False)
    velocity = Column(Float, default=0.0, index=True)
    battery = Column(Float, default=100.0, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_robot_status', 'status'),
        Index('idx_robot_updated_at', 'updated_at'),
    )
