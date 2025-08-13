#!/usr/bin/env python3
"""
Populate tables with strict varchar constraints
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


async def populate_constrained_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Populating tables with varchar constraints...")
        
        populated = {}
        
        # 1. organizations - varchar(10)
        for i in range(5):
            try:
                await conn.execute(
                    """INSERT INTO organizations (name, created_at, updated_at) 
                    VALUES ($1, $2, $3)""",
                    f"ORG{i+1}", datetime.now(), datetime.now()
                )
                populated['organizations'] = populated.get('organizations', 0) + 1
            except:
                pass
        
        # 2. llm_providers - varchar(3)
        for name in ["OAI", "ANT", "GGL", "AZR", "AWS"]:
            try:
                await conn.execute(
                    """INSERT INTO llm_providers (name, is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4)""",
                    name[:3], True, datetime.now(), datetime.now()
                )
                populated['llm_providers'] = populated.get('llm_providers', 0) + 1
            except:
                pass
        
        # 3. llm_models - varchar(3) for name
        provider_id = await conn.fetchval("SELECT id FROM llm_providers LIMIT 1")
        if provider_id:
            for name in ["GP4", "GP3", "CL3", "CL2", "GEM"]:
                try:
                    await conn.execute(
                        """INSERT INTO llm_models (name, model_id, provider_id, is_active, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        name[:3], f"model-{name}", provider_id, True, datetime.now(), datetime.now()
                    )
                    populated['llm_models'] = populated.get('llm_models', 0) + 1
                except:
                    pass
        
        # 4. initiative_types - varchar(10)
        for name in ["Strategic", "Operation", "Innovation", "Compliance", "Transform"]:
            try:
                await conn.execute(
                    """INSERT INTO initiative_types (name, description, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4)""",
                    name[:10], f"{name} initiative type", datetime.now(), datetime.now()
                )
                populated['initiative_types'] = populated.get('initiative_types', 0) + 1
            except:
                pass
        
        # 5. initiatives - needs initiative_type_id
        type_id = await conn.fetchval("SELECT id FROM initiative_types LIMIT 1")
        if type_id:
            for i in range(5):
                try:
                    await conn.execute(
                        """INSERT INTO initiatives (name, description, initiative_type_id, status, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        f"INIT{i+1}", f"Initiative {i+1}", type_id, "Active", datetime.now(), datetime.now()
                    )
                    populated['initiatives'] = populated.get('initiatives', 0) + 1
                except:
                    pass
        
        # 6. kudos_categories - varchar(10)
        for name in ["Teamwork", "Innovation", "Leadership", "Excellence", "Customer"]:
            try:
                await conn.execute(
                    """INSERT INTO kudos_categories (name, slug, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4)""",
                    name[:10], name[:10].lower(), datetime.now(), datetime.now()
                )
                populated['kudos_categories'] = populated.get('kudos_categories', 0) + 1
            except:
                pass
        
        # 7. fiscal_periods - varchar(10) for name
        for q in range(1, 5):
            try:
                await conn.execute(
                    """INSERT INTO fiscal_periods (name, year, quarter, start_date, end_date, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    f"Q{q} 2025", 2025, q,
                    datetime(2025, (q-1)*3+1, 1),
                    datetime(2025, q*3, 30 if q < 4 else 31),
                    datetime.now(), datetime.now()
                )
                populated['fiscal_periods'] = populated.get('fiscal_periods', 0) + 1
            except:
                pass
        
        # 8. knowledge_base - varchar(10) for title
        for i in range(5):
            try:
                await conn.execute(
                    """INSERT INTO knowledge_base (title, content, category, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    f"KB{i+1}", f"Knowledge base content {i+1}", "docs", datetime.now(), datetime.now()
                )
                populated['knowledge_base'] = populated.get('knowledge_base', 0) + 1
            except:
                pass
        
        # 9. engagement_tags - varchar(10) for tag_name
        engagement_ids = [r['id'] for r in await conn.fetch("SELECT id FROM engagements LIMIT 5")]
        for eng_id in engagement_ids:
            for tag in ["urgent", "priority", "review"]:
                try:
                    await conn.execute(
                        """INSERT INTO engagement_tags (engagement_id, tag_name, created_at) 
                        VALUES ($1, $2, $3)""",
                        eng_id, tag[:10], datetime.now()
                    )
                    populated['engagement_tags'] = populated.get('engagement_tags', 0) + 1
                except:
                    pass
        
        # 10. mcp_agent_bindings - varchar(10) for agent_name
        server_id = await conn.fetchval("SELECT id FROM mcp_servers LIMIT 1")
        if server_id:
            for agent in ["ali", "amy", "baccio"]:
                try:
                    await conn.execute(
                        """INSERT INTO mcp_agent_bindings (server_id, agent_name, configuration, is_active, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        server_id, agent[:10], json.dumps({}), True, datetime.now(), datetime.now()
                    )
                    populated['mcp_agent_bindings'] = populated.get('mcp_agent_bindings', 0) + 1
                except:
                    pass
        
        # 11. chat_sessions - needs explicit ID
        talent_ids = [r['id'] for r in await conn.fetch("SELECT id FROM talents LIMIT 5")]
        for talent_id in talent_ids:
            try:
                await conn.execute(
                    """INSERT INTO chat_sessions (id, user_id, session_id, messages, is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    str(uuid.uuid4()), talent_id, str(uuid.uuid4()),
                    json.dumps([{"role": "user", "content": "Hello"}]),
                    False, datetime.now(), datetime.now()
                )
                populated['chat_sessions'] = populated.get('chat_sessions', 0) + 1
            except:
                pass
        
        # 12. sentiment_tracking - score must be between -1 and 1
        engagement_ids = [r['id'] for r in await conn.fetch("SELECT id FROM engagements LIMIT 5")]
        for eng_id in engagement_ids:
            try:
                await conn.execute(
                    """INSERT INTO sentiment_tracking (engagement_id, sentiment_score, confidence, analysis_date, created_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    eng_id, random.uniform(-1.0, 1.0), random.uniform(0.5, 1.0),
                    datetime.now(), datetime.now()
                )
                populated['sentiment_tracking'] = populated.get('sentiment_tracking', 0) + 1
            except:
                pass
        
        # 13. talent_skills - specific proficiency values
        talent_ids = [r['id'] for r in await conn.fetch("SELECT id FROM talents LIMIT 5")]
        skills = ["Python", "JavaScript", "Docker", "AWS", "React"]
        for talent_id in talent_ids:
            for skill in random.sample(skills, 3):
                try:
                    # Check what proficiency levels are allowed
                    await conn.execute(
                        """INSERT INTO talent_skills (talent_id, skill_name, proficiency_level, created_at) 
                        VALUES ($1, $2, $3, $4)""",
                        talent_id, skill, random.randint(1, 5), datetime.now()
                    )
                    populated['talent_skills'] = populated.get('talent_skills', 0) + 1
                except:
                    # Try with numeric value
                    try:
                        await conn.execute(
                            """INSERT INTO talent_skills (talent_id, skill_name, proficiency_level, created_at) 
                            VALUES ($1, $2, $3, $4)""",
                            talent_id, skill, str(random.randint(1, 5)), datetime.now()
                        )
                        populated['talent_skills'] = populated.get('talent_skills', 0) + 1
                    except:
                        pass
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("CONSTRAINED TABLES POPULATION COMPLETE!")
        for table, count in populated.items():
            logger.info(f"✅ {table}: {count} rows")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(populate_constrained_tables())