"""
Database initialization script.
Creates all tables if they don't exist.
Run this after starting PostgreSQL.
"""
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import ExecutionRun, Obstacle, PathPlan, RobotState, Wall

settings = get_settings()


async def init_db():
    """Initialize database by creating all tables"""
    print("Connecting to database...")
    engine = create_async_engine(settings.database_url, echo=True)
    
    try:
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        
        # Create all tables
        print("Creating tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Tables created successfully")
        
        print("\nDatabase initialized successfully!")
        print("You can now start the application.")
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())

