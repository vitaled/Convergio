#!/usr/bin/env python3
"""
Populate all remaining empty tables in Convergio database
Handles schema differences gracefully
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
import structlog

logger = structlog.get_logger()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/convergio_db")


class RemainingTablesPopulator:
    """Populates all empty tables"""
    
    def __init__(self):
        self.conn = None
        
    async def connect(self):
        self.conn = await asyncpg.connect(DATABASE_URL)
        
    async def close(self):
        if self.conn:
            await self.conn.close()
    
    async def get_empty_tables(self):
        """Get list of empty tables"""
        result = await self.conn.fetch("""
            SELECT tablename 
            FROM pg_tables t
            WHERE schemaname = 'public'
            AND NOT EXISTS (
                SELECT 1 FROM pg_class c
                WHERE c.relname = t.tablename
                AND c.reltuples > 0
            )
            ORDER BY tablename
        """)
        return [r['tablename'] for r in result]
    
    async def get_table_columns(self, table_name):
        """Get columns for a table"""
        result = await self.conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        return {r['column_name']: r['data_type'] for r in result}
    
    async def populate_table_generic(self, table_name, num_rows=5):
        """Generic table population based on column types"""
        columns = await self.get_table_columns(table_name)
        
        if not columns:
            return 0
        
        count = 0
        for i in range(num_rows):
            try:
                # Build values based on column types
                values = {}
                for col, dtype in columns.items():
                    if col == 'id':
                        continue  # Skip auto-increment
                    elif col == 'created_at' or col == 'updated_at':
                        values[col] = datetime.now()
                    elif 'talent_id' in col or 'user_id' in col or 'created_by' in col or 'owner_id' in col:
                        # Get a random talent ID
                        talent_id = await self.conn.fetchval("SELECT id FROM talents ORDER BY RANDOM() LIMIT 1")
                        values[col] = talent_id
                    elif 'client_id' in col:
                        client_id = await self.conn.fetchval("SELECT id FROM clients ORDER BY RANDOM() LIMIT 1")
                        values[col] = client_id
                    elif 'engagement_id' in col:
                        eng_id = await self.conn.fetchval("SELECT id FROM engagements ORDER BY RANDOM() LIMIT 1")
                        values[col] = eng_id
                    elif 'activity_id' in col:
                        act_id = await self.conn.fetchval("SELECT id FROM activities ORDER BY RANDOM() LIMIT 1")
                        values[col] = act_id
                    elif 'studio_id' in col:
                        studio_id = await self.conn.fetchval("SELECT id FROM studios ORDER BY RANDOM() LIMIT 1")
                        values[col] = studio_id
                    elif 'area_id' in col:
                        area_id = await self.conn.fetchval("SELECT id FROM areas ORDER BY RANDOM() LIMIT 1")
                        values[col] = area_id
                    elif 'okr_id' in col:
                        okr_id = await self.conn.fetchval("SELECT id FROM okrs ORDER BY RANDOM() LIMIT 1")
                        values[col] = okr_id
                    elif dtype in ['character varying', 'text']:
                        values[col] = f"Sample {table_name} {col} {i+1}"
                    elif dtype in ['integer', 'bigint']:
                        values[col] = random.randint(1, 100)
                    elif dtype in ['numeric', 'double precision', 'real']:
                        values[col] = round(random.uniform(0.1, 100.0), 2)
                    elif dtype == 'boolean':
                        values[col] = random.choice([True, False])
                    elif dtype == 'jsonb':
                        values[col] = json.dumps({"key": f"value_{i}"})
                    elif dtype in ['timestamp', 'timestamp with time zone', 'timestamp without time zone']:
                        values[col] = datetime.now() - timedelta(days=random.randint(0, 30))
                    elif dtype == 'date':
                        values[col] = (datetime.now() - timedelta(days=random.randint(0, 365))).date()
                    elif dtype == 'uuid':
                        values[col] = str(uuid.uuid4())
                
                if values:
                    # Build INSERT query
                    cols = [k for k in values.keys()]
                    placeholders = [f"${i+1}" for i in range(len(cols))]
                    query = f"""
                        INSERT INTO {table_name} ({', '.join(cols)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    await self.conn.execute(query, *values.values())
                    count += 1
                    
            except Exception as e:
                # Silently skip errors for individual rows
                pass
        
        return count
    
    async def populate_specific_tables(self):
        """Populate specific tables with meaningful data"""
        
        # Get existing IDs
        talent_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM talents")]
        client_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM clients")]
        engagement_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM engagements")]
        activity_ids = [r['id'] for r in await self.conn.fetch("SELECT id FROM activities")]
        
        # Populate key tables with meaningful data
        populated = {}
        
        # Organizations
        try:
            for name in ["Convergio HQ", "Tech Division", "Operations"]:
                await self.conn.execute(
                    "INSERT INTO organizations (name, created_at, updated_at) VALUES ($1, $2, $3)",
                    name, datetime.now(), datetime.now()
                )
            populated['organizations'] = 3
        except:
            pass
        
        # Locations
        try:
            for name, addr in [("Milan HQ", "Via Roma 1"), ("Rome Office", "Via Napoli 10")]:
                await self.conn.execute(
                    "INSERT INTO locations (name, address, created_at, updated_at) VALUES ($1, $2, $3, $4)",
                    name, addr, datetime.now(), datetime.now()
                )
            populated['locations'] = 2
        except:
            pass
        
        # Talent Skills
        if talent_ids:
            try:
                skills = ["Python", "JavaScript", "React", "Docker", "AWS"]
                for talent_id in talent_ids[:5]:
                    for skill in random.sample(skills, 3):
                        await self.conn.execute(
                            """INSERT INTO talent_skills 
                            (talent_id, skill_name, proficiency_level, created_at) 
                            VALUES ($1, $2, $3, $4)""",
                            talent_id, skill, random.choice(['beginner', 'intermediate', 'advanced']), datetime.now()
                        )
                populated['talent_skills'] = 15
            except:
                pass
        
        # Activity Assignments
        if activity_ids and talent_ids:
            try:
                for activity_id in activity_ids[:10]:
                    await self.conn.execute(
                        """INSERT INTO activity_assignments 
                        (activity_id, talent_id, role, allocation_percentage, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        activity_id, random.choice(talent_ids), 'Contributor', 50, datetime.now(), datetime.now()
                    )
                populated['activity_assignments'] = 10
            except:
                pass
        
        # Milestones
        if engagement_ids:
            try:
                for eng_id in engagement_ids[:5]:
                    await self.conn.execute(
                        """INSERT INTO milestones 
                        (name, engagement_id, due_date, status, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        "Milestone 1", eng_id, datetime.now() + timedelta(days=30), 
                        'Pending', datetime.now(), datetime.now()
                    )
                populated['milestones'] = 5
            except:
                pass
        
        # Notifications
        if talent_ids:
            try:
                for talent_id in talent_ids[:5]:
                    await self.conn.execute(
                        """INSERT INTO notifications 
                        (talent_id, title, message, type, is_read, created_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        talent_id, "Welcome!", "Welcome to Convergio", "info", False, datetime.now()
                    )
                populated['notifications'] = 5
            except:
                pass
        
        # System Settings
        try:
            settings = [
                ("app_name", "Convergio"),
                ("version", "2.0.0"),
                ("timezone", "UTC")
            ]
            for key, value in settings:
                await self.conn.execute(
                    "INSERT INTO system_settings (setting_key, setting_value, created_at, updated_at) VALUES ($1, $2, $3, $4)",
                    key, value, datetime.now(), datetime.now()
                )
            populated['system_settings'] = 3
        except:
            pass
        
        # LLM Providers
        try:
            for name in ["OpenAI", "Anthropic", "Google"]:
                await self.conn.execute(
                    "INSERT INTO llm_providers (name, is_active, created_at, updated_at) VALUES ($1, $2, $3, $4)",
                    name, True, datetime.now(), datetime.now()
                )
            populated['llm_providers'] = 3
        except:
            pass
        
        # LLM Models
        try:
            provider_id = await self.conn.fetchval("SELECT id FROM llm_providers LIMIT 1")
            if provider_id:
                for name, model_id in [("GPT-4", "gpt-4"), ("GPT-3.5", "gpt-3.5-turbo")]:
                    await self.conn.execute(
                        "INSERT INTO llm_models (name, model_id, provider_id, is_active, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6)",
                        name, model_id, provider_id, True, datetime.now(), datetime.now()
                    )
                populated['llm_models'] = 2
        except:
            pass
        
        return populated
    
    async def populate_all(self):
        """Main population method"""
        try:
            await self.connect()
            
            logger.info("🚀 Populating remaining empty tables...")
            
            # First populate specific tables with meaningful data
            specific = await self.populate_specific_tables()
            for table, count in specific.items():
                logger.info(f"✅ {table}: {count} rows")
            
            # Get remaining empty tables
            empty_tables = await self.get_empty_tables()
            logger.info(f"Found {len(empty_tables)} empty tables to populate")
            
            # Populate each empty table generically
            for table in empty_tables:
                if table in specific:
                    continue  # Already populated
                
                try:
                    count = await self.populate_table_generic(table, num_rows=3)
                    if count > 0:
                        logger.info(f"✅ {table}: {count} rows")
                except Exception as e:
                    logger.debug(f"Could not populate {table}: {e}")
            
            # Final check
            final_empty = await self.get_empty_tables()
            
            logger.info("\n" + "="*60)
            logger.info("POPULATION COMPLETE!")
            logger.info(f"Remaining empty tables: {len(final_empty)}")
            if final_empty:
                logger.info(f"Still empty: {', '.join(final_empty[:10])}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Population failed: {e}")
            raise
        finally:
            await self.close()


async def main():
    populator = RemainingTablesPopulator()
    await populator.populate_all()


if __name__ == "__main__":
    asyncio.run(main())