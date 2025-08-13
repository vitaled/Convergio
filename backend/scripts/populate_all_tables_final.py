#!/usr/bin/env python3
"""
Final comprehensive database population script
Checks actual schema and populates ALL empty tables
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


async def get_table_schema(conn, table_name):
    """Get actual columns for a table"""
    result = await conn.fetch("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = $1
        ORDER BY ordinal_position
    """, table_name)
    return {r['column_name']: {
        'type': r['data_type'], 
        'nullable': r['is_nullable'] == 'YES',
        'default': r['column_default']
    } for r in result}


async def generate_value_for_column(conn, col_name, col_info):
    """Generate appropriate value based on column name and type"""
    dtype = col_info['type']
    
    # Skip auto-generated columns
    if col_info['default'] and ('nextval' in col_info['default'] or 'gen_random_uuid' in col_info['default']):
        return None
    
    # Handle foreign keys
    if 'talent_id' in col_name or 'user_id' in col_name or 'created_by' in col_name or 'given_by' in col_name or 'given_to' in col_name:
        talent_id = await conn.fetchval("SELECT id FROM talents ORDER BY RANDOM() LIMIT 1")
        return talent_id if talent_id else None
    elif 'client_id' in col_name:
        client_id = await conn.fetchval("SELECT id FROM clients ORDER BY RANDOM() LIMIT 1")
        return client_id if client_id else None
    elif 'engagement_id' in col_name:
        eng_id = await conn.fetchval("SELECT id FROM engagements ORDER BY RANDOM() LIMIT 1")
        return eng_id if eng_id else None
    elif 'activity_id' in col_name:
        act_id = await conn.fetchval("SELECT id FROM activities ORDER BY RANDOM() LIMIT 1")
        return act_id if act_id else None
    elif 'provider_id' in col_name:
        prov_id = await conn.fetchval("SELECT id FROM llm_providers ORDER BY RANDOM() LIMIT 1")
        return prov_id if prov_id else None
    elif 'server_id' in col_name:
        server_id = await conn.fetchval("SELECT id FROM mcp_servers ORDER BY RANDOM() LIMIT 1")
        return server_id if server_id else None
    elif 'initiative_type_id' in col_name:
        type_id = await conn.fetchval("SELECT id FROM initiative_types ORDER BY RANDOM() LIMIT 1")
        return type_id if type_id else None
    
    # Handle specific column names
    if col_name == 'created_at' or col_name == 'updated_at':
        return datetime.now()
    elif col_name == 'session_id':
        return str(uuid.uuid4())
    elif col_name == 'name' or col_name == 'title':
        return f"Sample {random.randint(100, 999)}"
    elif col_name == 'description' or col_name == 'content' or col_name == 'feedback' or col_name == 'message':
        return f"Sample content for {col_name}"
    elif col_name == 'status':
        return random.choice(['pending', 'active', 'completed', 'review'])
    elif col_name == 'type' or col_name == 'category':
        return random.choice(['type1', 'type2', 'type3'])
    elif col_name == 'rating' or col_name == 'score':
        return random.randint(1, 5)
    elif col_name == 'email':
        return f"user{random.randint(100, 999)}@example.com"
    elif col_name == 'slug':
        return f"slug-{random.randint(100, 999)}"
    elif col_name == 'tag_name':
        return random.choice(['urgent', 'priority', 'review', 'strategic'])
    elif col_name == 'skill_name':
        return random.choice(['Python', 'JavaScript', 'Docker', 'AWS', 'React'])
    elif col_name == 'proficiency_level':
        return random.choice(['beginner', 'intermediate', 'advanced', 'expert'])
    elif col_name == 'impact' or col_name == 'probability':
        return random.choice(['Low', 'Medium', 'High'])
    elif col_name == 'confidence_level' or col_name == 'sentiment_score':
        return random.uniform(0.0, 1.0)
    elif col_name == 'allocation_percentage':
        return random.randint(10, 100)
    elif col_name == 'is_active' or col_name == 'is_read':
        return random.choice([True, False])
    elif col_name == 'year' or col_name == 'quarter':
        return random.randint(1, 4)
    elif col_name == 'start_date' or col_name == 'due_date' or col_name == 'forecast_date' or col_name == 'analysis_date':
        return datetime.now() + timedelta(days=random.randint(1, 90))
    elif col_name == 'end_date':
        return datetime.now() + timedelta(days=random.randint(91, 180))
    elif col_name == 'vacation_type' or col_name == 'feedback_type':
        return random.choice(['Annual', 'Sick', 'Personal', 'Other'])
    elif col_name == 'model_id':
        return f"model-{random.randint(100, 999)}"
    elif col_name == 'agent_name':
        return random.choice(['ali', 'amy', 'baccio'])
    elif col_name == 'setting_key':
        return f"key_{random.randint(100, 999)}"
    elif col_name == 'setting_value':
        return f"value_{random.randint(100, 999)}"
    elif col_name == 'role':
        return random.choice(['admin', 'user', 'contributor', 'viewer'])
    elif col_name == 'address':
        return f"Via {random.choice(['Roma', 'Milano', 'Napoli'])} {random.randint(1, 100)}"
    elif col_name == 'mitigation_plan':
        return "Monitor and review regularly"
    elif col_name == 'messages':
        return json.dumps([{"role": "user", "content": "Hello"}])
    elif col_name == 'configuration':
        return json.dumps({"key": "value"})
    elif col_name == 'forecasted_revenue' or col_name == 'forecasted_cost':
        return random.randint(10000, 100000)
    
    # Generic handling by data type
    if dtype in ['character varying', 'text']:
        return f"Sample {col_name}"
    elif dtype in ['integer', 'bigint']:
        return random.randint(1, 100)
    elif dtype in ['numeric', 'double precision', 'real']:
        return round(random.uniform(0.1, 100.0), 2)
    elif dtype == 'boolean':
        return random.choice([True, False])
    elif dtype == 'jsonb':
        return json.dumps({"key": f"value_{random.randint(1, 100)}"})
    elif dtype in ['timestamp', 'timestamp with time zone', 'timestamp without time zone']:
        return datetime.now()
    elif dtype == 'date':
        return datetime.now().date()
    elif dtype == 'uuid':
        return str(uuid.uuid4())
    
    return None


async def populate_table(conn, table_name, num_rows=5):
    """Populate a single table with appropriate data"""
    try:
        # Check if already has data
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        if count > 0:
            logger.info(f"⏭️  {table_name} already has {count} rows, skipping")
            return 0
        
        # Get schema
        schema = await get_table_schema(conn, table_name)
        if not schema:
            logger.warning(f"❌ Could not get schema for {table_name}")
            return 0
        
        inserted = 0
        for i in range(num_rows):
            # Build values
            columns = []
            values = []
            param_count = 0
            
            for col_name, col_info in schema.items():
                if col_name == 'id':
                    continue  # Skip auto-increment
                
                value = await generate_value_for_column(conn, col_name, col_info)
                if value is not None:
                    columns.append(col_name)
                    values.append(value)
                    param_count += 1
            
            if columns:
                placeholders = [f"${i+1}" for i in range(len(columns))]
                query = f"""
                    INSERT INTO {table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                try:
                    await conn.execute(query, *values)
                    inserted += 1
                except Exception as e:
                    # Some rows might fail due to constraints, that's OK
                    logger.debug(f"Row {i} failed for {table_name}: {str(e)[:100]}")
        
        if inserted > 0:
            logger.info(f"✅ {table_name}: {inserted} rows")
        return inserted
        
    except Exception as e:
        logger.error(f"Failed to populate {table_name}: {e}")
        return 0


async def populate_all_empty_tables():
    """Main function to populate all empty tables"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Starting complete database population...")
        
        # Get all empty tables
        empty_tables = await conn.fetch("""
            SELECT t.tablename 
            FROM pg_tables t
            WHERE t.schemaname = 'public'
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns c
                WHERE c.table_schema = 'public' 
                AND c.table_name = t.tablename
                AND c.column_default LIKE '%nextval%'
            )
            OR t.tablename IN (
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                AND tablename IN (
                    SELECT table_name FROM (
                        SELECT table_name, 
                               (SELECT COUNT(*) FROM information_schema.tables t2 
                                WHERE t2.table_name = cols.table_name) as cnt
                        FROM information_schema.columns cols
                        WHERE table_schema = 'public'
                        GROUP BY table_name
                    ) x
                )
            )
            ORDER BY tablename
        """)
        
        all_tables = [r['tablename'] for r in empty_tables]
        
        # Check which ones are actually empty
        empty_list = []
        for table in all_tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            if count == 0:
                empty_list.append(table)
        
        logger.info(f"Found {len(empty_list)} empty tables to populate")
        
        # Special handling for tables with dependencies
        priority_tables = [
            'organizations',
            'llm_providers', 
            'initiative_types',
            'kudos_categories',
            'fiscal_periods'
        ]
        
        # Populate priority tables first
        for table in priority_tables:
            if table in empty_list:
                await populate_table(conn, table, num_rows=5)
        
        # Now populate the rest
        for table in empty_list:
            if table not in priority_tables:
                await populate_table(conn, table, num_rows=5)
        
        # Final status check
        logger.info("\n" + "="*60)
        logger.info("POPULATION COMPLETE!")
        
        # Count final status
        final_empty = []
        populated = []
        for table in all_tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            if count == 0:
                final_empty.append(table)
            else:
                populated.append((table, count))
        
        logger.info(f"✅ Populated tables: {len(populated)}")
        logger.info(f"❌ Still empty: {len(final_empty)}")
        
        if final_empty:
            logger.info(f"Empty tables: {', '.join(final_empty[:10])}")
        
        # Total rows
        total_rows = sum(count for _, count in populated)
        logger.info(f"📊 Total rows in database: {total_rows:,}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(populate_all_empty_tables())