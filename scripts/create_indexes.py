#!/usr/bin/env python3
"""
Create database indexes for performance
Run this after database initialization
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

settings = get_settings()


async def create_indexes():
    """Create all performance indexes"""
    print("Connecting to database...")
    engine = create_async_engine(settings.database_url, echo=True)
    
    indexes = [
        # Walls indexes
        "CREATE INDEX IF NOT EXISTS idx_wall_name ON walls(name);",
        "CREATE INDEX IF NOT EXISTS idx_wall_created_at ON walls(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_wall_name_created ON walls(name, created_at);",  # Composite
        
        # Obstacles indexes
        "CREATE INDEX IF NOT EXISTS idx_obstacle_wall_id ON obstacles(wall_id);",
        "CREATE INDEX IF NOT EXISTS idx_obstacle_created_at ON obstacles(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_obstacle_wall_created ON obstacles(wall_id, created_at);",  # Composite
        
        # Path plans indexes
        "CREATE INDEX IF NOT EXISTS idx_plan_wall_id ON path_plans(wall_id);",
        "CREATE INDEX IF NOT EXISTS idx_plan_algorithm ON path_plans(algorithm);",
        "CREATE INDEX IF NOT EXISTS idx_plan_cost ON path_plans(cost);",
        "CREATE INDEX IF NOT EXISTS idx_plan_created_at ON path_plans(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_plan_algorithm_cost ON path_plans(algorithm, cost);",  # Composite
        "CREATE INDEX IF NOT EXISTS idx_plan_wall_created ON path_plans(wall_id, created_at);",  # Composite
        
        # Execution runs indexes
        "CREATE INDEX IF NOT EXISTS idx_run_plan_id ON execution_runs(plan_id);",
        "CREATE INDEX IF NOT EXISTS idx_run_status ON execution_runs(status);",
        "CREATE INDEX IF NOT EXISTS idx_run_started_at ON execution_runs(started_at);",
        "CREATE INDEX IF NOT EXISTS idx_run_finished_at ON execution_runs(finished_at);",
        "CREATE INDEX IF NOT EXISTS idx_run_plan_status ON execution_runs(plan_id, status);",  # Composite
        "CREATE INDEX IF NOT EXISTS idx_run_status_started ON execution_runs(status, started_at);",  # Composite
        
        # Robot state indexes
        "CREATE INDEX IF NOT EXISTS idx_robot_status ON robot_states(status);",
        "CREATE INDEX IF NOT EXISTS idx_robot_updated_at ON robot_states(updated_at);",
        "CREATE INDEX IF NOT EXISTS idx_robot_status_updated ON robot_states(status, updated_at);",  # Composite
        
        # Additional performance indexes
        "CREATE INDEX IF NOT EXISTS idx_plan_cost_algorithm ON path_plans(cost, algorithm) WHERE cost > 0;",  # Partial index
        "CREATE INDEX IF NOT EXISTS idx_run_active ON execution_runs(status, started_at) WHERE finished_at IS NULL;",  # Partial index
    ]
    
    try:
        async with engine.begin() as conn:
            for idx_sql in indexes:
                print(f"Creating index: {idx_sql.split()[5]}...")
                await conn.execute(text(idx_sql))
            print("\n✓ All indexes created successfully!")
    except Exception as e:
        print(f"✗ Error creating indexes: {e}")
        return 1
    finally:
        await engine.dispose()
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(create_indexes()))

