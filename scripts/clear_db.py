"""
Clear database script.
Drops all tables and recreates them.
"""
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db import models  # noqa: F401 - ensure models are registered with Base

settings = get_settings()


async def clear_db():
    """Clear database by dropping and recreating all tables"""
    print("Connecting to database...")
    engine = create_async_engine(settings.database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
        
        print("Dropping all tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("Tables dropped")
        
        print("Creating tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created")
        
        print("\nDatabase cleared and reinitialized!")
        
    except Exception as e:
        print(f"Error clearing database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(clear_db())

