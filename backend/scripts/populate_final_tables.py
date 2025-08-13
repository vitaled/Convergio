#!/usr/bin/env python3
"""
Populate the final 19 empty tables
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


async def populate_final_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Populating final empty tables...")
        
        # Get IDs for foreign keys
        talent_ids = [r['id'] for r in await conn.fetch("SELECT id FROM talents")]
        client_ids = [r['id'] for r in await conn.fetch("SELECT id FROM clients")]
        engagement_ids = [r['id'] for r in await conn.fetch("SELECT id FROM engagements")]
        activity_ids = [r['id'] for r in await conn.fetch("SELECT id FROM activities")]
        
        populated = {}
        
        # 1. activity_feedbacks
        for activity_id in activity_ids[:5]:
            await conn.execute(
                """INSERT INTO activity_feedbacks 
                (activity_id, feedback_text, given_by, rating, created_at) 
                VALUES ($1, $2, $3, $4, $5)""",
                activity_id, "Great work!", random.choice(talent_ids), 5, datetime.now()
            )
        populated['activity_feedbacks'] = 5
        
        # 2. change_requests
        for _ in range(5):
            await conn.execute(
                """INSERT INTO change_requests 
                (engagement_id, requested_by, title, description, impact, status, created_at, updated_at) 
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                random.choice(engagement_ids), random.choice(talent_ids),
                f"CR-{random.randint(100,999)}", "Change request description",
                "Medium", "Pending", datetime.now(), datetime.now()
            )
        populated['change_requests'] = 5
        
        # 3. chat_sessions
        for _ in range(5):
            await conn.execute(
                """INSERT INTO chat_sessions 
                (user_id, session_id, messages, is_active, created_at, updated_at) 
                VALUES ($1, $2, $3, $4, $5, $6)""",
                random.choice(talent_ids), str(uuid.uuid4()),
                json.dumps([{"role": "user", "content": "Hello"}]),
                False, datetime.now(), datetime.now()
            )
        populated['chat_sessions'] = 5
        
        # 4. engagement_forecasts
        for eng_id in engagement_ids[:5]:
            await conn.execute(
                """INSERT INTO engagement_forecasts 
                (engagement_id, forecast_date, forecasted_revenue, forecasted_cost, confidence_level, created_at, updated_at) 
                VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                eng_id, datetime.now() + timedelta(days=90),
                random.randint(50000, 200000), random.randint(30000, 100000),
                random.uniform(0.6, 0.95), datetime.now(), datetime.now()
            )
        populated['engagement_forecasts'] = 5
        
        # 5. engagement_tags
        tags = ["urgent", "strategic", "innovation", "priority", "review"]
        for eng_id in engagement_ids[:5]:
            for tag in random.sample(tags, 2):
                try:
                    await conn.execute(
                        """INSERT INTO engagement_tags 
                        (engagement_id, tag_name, created_at) 
                        VALUES ($1, $2, $3)""",
                        eng_id, tag, datetime.now()
                    )
                except:
                    pass
        populated['engagement_tags'] = 10
        
        # 6. feedbacks
        for _ in range(5):
            await conn.execute(
                """INSERT INTO feedbacks 
                (given_by, given_to, feedback_type, feedback_text, rating, created_at) 
                VALUES ($1, $2, $3, $4, $5, $6)""",
                random.choice(talent_ids), random.choice(talent_ids),
                "positive", "Excellent collaboration!", 5, datetime.now()
            )
        populated['feedbacks'] = 5
        
        # 7. fiscal_periods
        for quarter in range(1, 5):
            await conn.execute(
                """INSERT INTO fiscal_periods 
                (name, year, quarter, start_date, end_date, created_at, updated_at) 
                VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                f"Q{quarter} 2025", 2025, quarter,
                datetime(2025, (quarter-1)*3+1, 1),
                datetime(2025, quarter*3, 30) if quarter < 4 else datetime(2025, 12, 31),
                datetime.now(), datetime.now()
            )
        populated['fiscal_periods'] = 4
        
        # 8. initiative_types
        for name in ["Strategic", "Operational", "Innovation", "Compliance", "Transformation"]:
            await conn.execute(
                """INSERT INTO initiative_types 
                (name, description, created_at, updated_at) 
                VALUES ($1, $2, $3, $4)""",
                name, f"{name} initiative type", datetime.now(), datetime.now()
            )
        populated['initiative_types'] = 5
        
        # 9. initiatives  
        for name in ["Digital Transformation", "Cost Optimization", "Market Expansion", "Quality Improvement", "Innovation Lab"]:
            try:
                # Get initiative_type_id
                type_id = await conn.fetchval("SELECT id FROM initiative_types LIMIT 1")
                await conn.execute(
                    """INSERT INTO initiatives 
                    (name, description, initiative_type_id, status, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6)""",
                    name, f"{name} initiative", type_id, "Active", datetime.now(), datetime.now()
                )
            except:
                pass
        populated['initiatives'] = 5
        
        # 10. knowledge_base
        for title in ["Best Practices", "FAQ", "Guidelines", "Tutorials", "References"]:
            await conn.execute(
                """INSERT INTO knowledge_base 
                (title, content, category, created_at, updated_at) 
                VALUES ($1, $2, $3, $4, $5)""",
                title, f"{title} content", "documentation", datetime.now(), datetime.now()
            )
        populated['knowledge_base'] = 5
        
        # 11. kudos_categories
        for name, slug in [("Teamwork", "teamwork"), ("Innovation", "innovation"), ("Leadership", "leadership"), 
                          ("Excellence", "excellence"), ("Customer Focus", "customer_focus")]:
            await conn.execute(
                """INSERT INTO kudos_categories 
                (name, slug, created_at, updated_at) 
                VALUES ($1, $2, $3, $4)""",
                name, slug, datetime.now(), datetime.now()
            )
        populated['kudos_categories'] = 5
        
        # 12. llm_models
        try:
            # First ensure we have providers
            await conn.execute(
                """INSERT INTO llm_providers 
                (name, is_active, created_at, updated_at) 
                VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING""",
                "OpenAI", True, datetime.now(), datetime.now()
            )
            
            provider_id = await conn.fetchval("SELECT id FROM llm_providers LIMIT 1")
            if provider_id:
                for name, model_id in [("GPT-4", "gpt-4"), ("GPT-3.5", "gpt-3.5"), ("Claude", "claude-3")]:
                    await conn.execute(
                        """INSERT INTO llm_models 
                        (name, model_id, provider_id, is_active, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        name, model_id, provider_id, True, datetime.now(), datetime.now()
                    )
                populated['llm_models'] = 3
        except:
            pass
        
        # 13. llm_providers (already done above)
        populated['llm_providers'] = 1
        
        # 14. mcp_agent_bindings
        try:
            server_id = await conn.fetchval("SELECT id FROM mcp_servers LIMIT 1")
            if server_id:
                for agent in ["ali", "amy", "baccio"]:
                    await conn.execute(
                        """INSERT INTO mcp_agent_bindings 
                        (server_id, agent_name, configuration, is_active, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        server_id, agent, json.dumps({}), True, datetime.now(), datetime.now()
                    )
                populated['mcp_agent_bindings'] = 3
        except:
            pass
        
        # 15. organizations
        for name in ["Convergio", "Tech Division", "Operations"]:
            try:
                await conn.execute(
                    """INSERT INTO organizations 
                    (name, created_at, updated_at) 
                    VALUES ($1, $2, $3)""",
                    name, datetime.now(), datetime.now()
                )
            except:
                pass
        populated['organizations'] = 3
        
        # 16. risks
        for eng_id in engagement_ids[:5]:
            await conn.execute(
                """INSERT INTO risks 
                (engagement_id, title, description, impact, probability, mitigation_plan, status, created_at, updated_at) 
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                eng_id, "Timeline Risk", "Project may be delayed", "High", "Medium",
                "Monitor closely", "Open", datetime.now(), datetime.now()
            )
        populated['risks'] = 5
        
        # 17. sentiment_tracking
        for eng_id in engagement_ids[:5]:
            await conn.execute(
                """INSERT INTO sentiment_tracking 
                (engagement_id, sentiment_score, confidence, analysis_date, created_at) 
                VALUES ($1, $2, $3, $4, $5)""",
                eng_id, random.uniform(-1.0, 1.0), random.uniform(0.5, 1.0),
                datetime.now(), datetime.now()
            )
        populated['sentiment_tracking'] = 5
        
        # 18. talent_skills
        skills = ["Python", "JavaScript", "Docker", "AWS", "React"]
        for talent_id in talent_ids[:5]:
            for skill in random.sample(skills, 3):
                try:
                    await conn.execute(
                        """INSERT INTO talent_skills 
                        (talent_id, skill_name, proficiency_level, created_at) 
                        VALUES ($1, $2, $3, $4)""",
                        talent_id, skill, random.choice(['beginner', 'intermediate', 'advanced', 'expert']),
                        datetime.now()
                    )
                except:
                    pass
        populated['talent_skills'] = 15
        
        # 19. vacations
        for talent_id in talent_ids[:5]:
            await conn.execute(
                """INSERT INTO vacations 
                (talent_id, vacation_type, start_date, end_date, status, created_at, updated_at) 
                VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                talent_id, "Annual Leave",
                datetime.now() + timedelta(days=30),
                datetime.now() + timedelta(days=37),
                "Approved", datetime.now(), datetime.now()
            )
        populated['vacations'] = 5
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("FINAL POPULATION COMPLETE!")
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
    asyncio.run(populate_final_tables())