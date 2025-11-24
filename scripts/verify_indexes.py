#!/usr/bin/env python3
"""
Verify database indexes created by create_indexes.py
This script queries the PostgreSQL database to show all indexes
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

settings = get_settings()


async def verify_indexes():
    """Query and display all indexes in the database"""
    print("Connecting to database...")
    engine = create_async_engine(settings.database_url, echo=False)
    
    try:
        async with engine.connect() as conn:
            # Query to get all indexes with their details
            query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            
            result = await conn.execute(query)
            indexes = result.fetchall()
            
            if not indexes:
                print("✗ No indexes found in the database")
                print("  Run 'python scripts/create_indexes.py' first to create indexes")
                return 1
            
            print(f"\n✓ Found {len(indexes)} indexes in the database:\n")
            print("=" * 80)
            
            current_table = None
            for idx in indexes:
                schema, table, index_name, index_def = idx
                
                # Print table header when table changes
                if table != current_table:
                    if current_table is not None:
                        print()  # Blank line between tables
                    print(f"\n📊 Table: {table}")
                    print("-" * 80)
                    current_table = table
                
                # Extract index type and columns
                index_type = "B-tree"  # Default
                if "UNIQUE" in index_def:
                    index_type = "UNIQUE"
                elif "PARTIAL" in index_def.upper():
                    index_type = "PARTIAL"
                
                print(f"  • {index_name}")
                print(f"    Type: {index_type}")
                print(f"    Definition: {index_def}")
                print()
            
            print("=" * 80)
            
            # Summary by table
            print("\n📈 Summary by Table:")
            print("-" * 80)
            table_counts = {}
            for idx in indexes:
                table = idx[1]
                table_counts[table] = table_counts.get(table, 0) + 1
            
            for table, count in sorted(table_counts.items()):
                print(f"  {table}: {count} index(es)")
            
            print("\n✓ Index verification complete!")
            return 0
            
    except Exception as e:
        print(f"✗ Error querying indexes: {e}")
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    exit(asyncio.run(verify_indexes()))

