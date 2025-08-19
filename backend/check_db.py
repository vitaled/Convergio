#!/usr/bin/env python3
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.database import get_async_session

async def check_database():
    try:
        async with get_async_session() as db:
            # Check engagements
            result = await db.execute('SELECT COUNT(*) FROM engagements')
            engagements_count = result.scalar()
            print(f'Engagements count: {engagements_count}')
            
            # Check activities
            result = await db.execute('SELECT COUNT(*) FROM activities')
            activities_count = result.scalar()
            print(f'Activities count: {activities_count}')
            
            # Check if tables exist
            result = await db.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('engagements', 'activities')
                ORDER BY table_name
            """)
            tables = result.fetchall()
            print(f'Available tables: {[t[0] for t in tables]}')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database())
