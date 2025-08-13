#!/usr/bin/env python3
"""
Populate remaining tables with CORRECT schema from database
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


async def inspect_and_populate():
    """Inspect actual schema and populate correctly"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🔍 Inspecting actual database schema for empty tables...")
        
        # Get list of empty tables
        empty_tables = await conn.fetch("""
            SELECT t.tablename 
            FROM pg_tables t
            WHERE t.schemaname = 'public'
            AND NOT EXISTS (
                SELECT 1 FROM information_schema.tables it
                WHERE it.table_schema = 'public' 
                AND it.table_name = t.tablename
                AND EXISTS (
                    SELECT 1 FROM information_schema.columns c
                    WHERE c.table_schema = 'public' 
                    AND c.table_name = it.table_name
                    LIMIT 1
                )
                AND (SELECT COUNT(*) FROM information_schema.tables t2 
                     WHERE t2.table_schema = 'public' 
                     AND t2.table_name = t.tablename) > 0
            )
            ORDER BY tablename
        """)
        
        # Check which tables are actually empty
        really_empty = []
        for row in empty_tables:
            table = row['tablename']
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            if count == 0:
                really_empty.append(table)
        
        logger.info(f"Found {len(really_empty)} empty tables to populate")
        
        populated = {}
        
        for table in really_empty:
            logger.info(f"\n{'='*50}")
            logger.info(f"Inspecting table: {table}")
            
            # Get actual schema
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """, table)
            
            logger.info(f"Columns in {table}:")
            for col in columns:
                logger.info(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")
            
            # Now populate based on ACTUAL schema
            if table == 'chat_sessions':
                # Check exact columns
                cols = {c['column_name']: c for c in columns}
                if 'talent_id' in cols:  # Uses talent_id not user_id
                    talent_ids = await conn.fetch("SELECT id FROM talents LIMIT 5")
                    for talent in talent_ids:
                        try:
                            await conn.execute("""
                                INSERT INTO chat_sessions (id, talent_id, session_type, messages, is_active, created_at, updated_at)
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """, str(uuid.uuid4()), talent['id'], 'support', 
                            json.dumps([{"role": "user", "content": "Hello"}]), 
                            False, datetime.now(), datetime.now())
                            populated[table] = populated.get(table, 0) + 1
                        except Exception as e:
                            logger.debug(f"Error: {e}")
            
            elif table == 'llm_models':
                # Use actual column names
                provider_ids = await conn.fetch("SELECT id FROM llm_providers LIMIT 3")
                for i, prov in enumerate(provider_ids):
                    try:
                        await conn.execute("""
                            INSERT INTO llm_models (provider_id, model_name, display_name, 
                            model_version, context_window, is_active, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """, prov['id'], f"model-{i+1}", f"Model {i+1}", "v1", 
                        4096, True, datetime.now(), datetime.now())
                        populated[table] = populated.get(table, 0) + 1
                    except Exception as e:
                        logger.debug(f"Error: {e}")
            
            elif table == 'talent_skills':
                # Check actual columns
                cols = {c['column_name']: c for c in columns}
                if 'skill_id' in cols:  # Uses skill_id not skill_name
                    talent_ids = await conn.fetch("SELECT id FROM talents LIMIT 3")
                    skill_ids = await conn.fetch("SELECT id FROM skills LIMIT 5")
                    for talent in talent_ids:
                        for skill in random.sample(list(skill_ids), min(3, len(skill_ids))):
                            try:
                                await conn.execute("""
                                    INSERT INTO talent_skills (talent_id, skill_id, proficiency, created_at)
                                    VALUES ($1, $2, $3, $4)
                                """, talent['id'], skill['id'], random.randint(1, 10), datetime.now())
                                populated[table] = populated.get(table, 0) + 1
                            except Exception as e:
                                logger.debug(f"Error: {e}")
            
            elif table == 'engagement_tags':
                # Check actual columns
                cols = {c['column_name']: c for c in columns}
                if 'target_id' in cols:  # Uses target_id not engagement_id
                    engagement_ids = await conn.fetch("SELECT id FROM engagements LIMIT 5")
                    tags = ['urgent', 'priority', 'review', 'strategic']
                    for eng in engagement_ids:
                        for tag in random.sample(tags, 2):
                            try:
                                await conn.execute("""
                                    INSERT INTO engagement_tags (target_id, tag, created_at)
                                    VALUES ($1, $2, $3)
                                """, eng['id'], tag, datetime.now())
                                populated[table] = populated.get(table, 0) + 1
                            except Exception as e:
                                logger.debug(f"Error: {e}")
            
            elif table == 'sentiment_tracking':
                # Check actual columns
                cols = {c['column_name']: c for c in columns}
                engagement_ids = await conn.fetch("SELECT id FROM engagements LIMIT 5")
                for eng in engagement_ids:
                    try:
                        score = round(random.uniform(-1.0, 1.0), 2)
                        score = max(-1.0, min(1.0, score))  # Ensure within range
                        
                        # Build query based on actual columns
                        if 'target_id' in cols:
                            await conn.execute("""
                                INSERT INTO sentiment_tracking (target_id, target_type, sentiment_score, 
                                confidence, analysis_date, created_at)
                                VALUES ($1, $2, $3, $4, $5, $6)
                            """, eng['id'], 'engagement', score, random.uniform(0.5, 1.0),
                            datetime.now().date(), datetime.now())
                        else:
                            # Try without target_id/target_type
                            await conn.execute("""
                                INSERT INTO sentiment_tracking (sentiment_score, confidence, 
                                analysis_date, created_at)
                                VALUES ($1, $2, $3, $4)
                            """, score, random.uniform(0.5, 1.0),
                            datetime.now().date(), datetime.now())
                        populated[table] = populated.get(table, 0) + 1
                    except Exception as e:
                        logger.debug(f"Error: {e}")
            
            elif table == 'initiatives':
                # Needs owner_id
                cols = {c['column_name']: c for c in columns}
                if 'owner_id' in cols:
                    talent_ids = await conn.fetch("SELECT id FROM talents LIMIT 3")
                    type_ids = await conn.fetch("SELECT id FROM initiative_types LIMIT 3")
                    for i, (talent, itype) in enumerate(zip(talent_ids, type_ids)):
                        try:
                            await conn.execute("""
                                INSERT INTO initiatives (name, description, initiative_type_id, 
                                owner_id, status, created_at, updated_at)
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """, f"Initiative {i+1}", f"Description {i+1}", itype['id'],
                            talent['id'], 'Active', datetime.now(), datetime.now())
                            populated[table] = populated.get(table, 0) + 1
                        except Exception as e:
                            logger.debug(f"Error: {e}")
            
            elif table == 'knowledge_base':
                # Check actual columns
                cols = {c['column_name']: c for c in columns}
                talent_ids = await conn.fetch("SELECT id FROM talents LIMIT 1")
                author_id = talent_ids[0]['id'] if talent_ids else None
                
                articles = [
                    ("Getting Started", "Welcome to the platform"),
                    ("API Guide", "API documentation"),
                    ("Best Practices", "Best practices guide")
                ]
                
                for title, content in articles:
                    try:
                        # Build insert based on actual columns
                        if 'tags' in cols:
                            await conn.execute("""
                                INSERT INTO knowledge_base (title, content, tags, author_id, 
                                views, created_at, updated_at)
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """, title, content, json.dumps(["guide", "docs"]), 
                            author_id, 0, datetime.now(), datetime.now())
                        else:
                            await conn.execute("""
                                INSERT INTO knowledge_base (title, content, author_id, 
                                views, created_at, updated_at)
                                VALUES ($1, $2, $3, $4, $5, $6)
                            """, title, content, author_id, 0, datetime.now(), datetime.now())
                        populated[table] = populated.get(table, 0) + 1
                    except Exception as e:
                        logger.debug(f"Error: {e}")
            
            elif table == 'fiscal_periods':
                # Check actual columns
                cols = {c['column_name']: c for c in columns}
                fiscal_year_ids = await conn.fetch("SELECT id FROM fiscal_years LIMIT 1")
                
                if fiscal_year_ids:
                    year_id = fiscal_year_ids[0]['id']
                    for q in range(1, 5):
                        try:
                            await conn.execute("""
                                INSERT INTO fiscal_periods (fiscal_year_id, period_number, 
                                period_type, start_date, end_date, created_at, updated_at)
                                VALUES ($1, $2, $3, $4, $5, $6, $7)
                            """, year_id, q, 'quarter',
                            datetime(2025, (q-1)*3+1, 1).date(),
                            datetime(2025, q*3, 28 if q < 4 else 31).date(),
                            datetime.now(), datetime.now())
                            populated[table] = populated.get(table, 0) + 1
                        except Exception as e:
                            logger.debug(f"Error: {e}")
            
            elif table == 'kudos_categories':
                # Check actual columns
                cols = {c['column_name']: c for c in columns}
                categories = [
                    ("Teamwork", "Team collaboration", "👥"),
                    ("Innovation", "Creative solutions", "💡"),
                    ("Leadership", "Great leadership", "👑")
                ]
                
                for name, desc, icon in categories:
                    try:
                        await conn.execute("""
                            INSERT INTO kudos_categories (name, description, icon, 
                            created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5)
                        """, name, desc, icon, datetime.now(), datetime.now())
                        populated[table] = populated.get(table, 0) + 1
                    except Exception as e:
                        logger.debug(f"Error: {e}")
            
            elif table == 'mcp_agent_bindings':
                # Check actual columns
                cols = {c['column_name']: c for c in columns}
                server_ids = await conn.fetch("SELECT id FROM mcp_servers LIMIT 1")
                
                if server_ids:
                    server_id = server_ids[0]['id']
                    agents = ['ali', 'amy', 'baccio']
                    
                    for agent in agents:
                        try:
                            # Use actual column name
                            if 'mcp_server_id' in cols:
                                await conn.execute("""
                                    INSERT INTO mcp_agent_bindings (mcp_server_id, agent_id, 
                                    configuration, is_active, created_at, updated_at)
                                    VALUES ($1, $2, $3, $4, $5, $6)
                                """, server_id, agent, json.dumps({"role": agent}),
                                True, datetime.now(), datetime.now())
                            else:
                                # Try other column names
                                await conn.execute("""
                                    INSERT INTO mcp_agent_bindings (agent_id, 
                                    configuration, is_active, created_at, updated_at)
                                    VALUES ($1, $2, $3, $4, $5)
                                """, agent, json.dumps({"role": agent}),
                                True, datetime.now(), datetime.now())
                            populated[table] = populated.get(table, 0) + 1
                        except Exception as e:
                            logger.debug(f"Error: {e}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("CORRECT SCHEMA POPULATION COMPLETE!")
        for table, count in sorted(populated.items()):
            logger.info(f"✅ {table}: {count} rows")
        logger.info(f"Total rows inserted: {sum(populated.values())}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(inspect_and_populate())