#!/usr/bin/env python3
"""
Populate the final 12 empty tables with correct constraints
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


async def populate_final_12():
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Populating final 12 tables with correct schema...")
        
        populated = {}
        
        # Get existing IDs for foreign keys
        talent_ids = [r['id'] for r in await conn.fetch("SELECT id FROM talents")]
        engagement_ids = [r['id'] for r in await conn.fetch("SELECT id FROM engagements")]
        server_ids = [r['id'] for r in await conn.fetch("SELECT id FROM mcp_servers")]
        
        if not talent_ids:
            logger.error("No talents found - cannot populate dependent tables")
            return
        
        # 1. organizations - needs created_by_id
        logger.info("Populating organizations...")
        for i in range(5):
            try:
                await conn.execute(
                    """INSERT INTO organizations (name, domain, created_by_id, is_active, 
                    fiscal_year_start, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    f"Organization {i+1}", f"org{i+1}.com", random.choice(talent_ids), 
                    True, "01-01", datetime.now(), datetime.now()
                )
                populated['organizations'] = populated.get('organizations', 0) + 1
            except Exception as e:
                logger.debug(f"Failed org {i}: {str(e)[:100]}")
        
        # 2. llm_providers - all required fields
        logger.info("Populating llm_providers...")
        providers = [
            ("OpenAI", "OpenAI", "openai", "https://api.openai.com", "v1", "api_key", "token", "USD"),
            ("Anthropic", "Anthropic", "anthropic", "https://api.anthropic.com", "v1", "api_key", "token", "USD"),
            ("Google", "Google AI", "google", "https://generativelanguage.googleapis.com", "v1", "api_key", "token", "USD"),
            ("Azure", "Azure OpenAI", "azure", "https://azure.openai.com", "v1", "oauth", "token", "USD"),
            ("AWS", "AWS Bedrock", "bedrock", "https://bedrock.aws.amazon.com", "v1", "iam", "token", "USD")
        ]
        
        for name, display_name, ptype, base_url, api_ver, auth_type, calc_method, currency in providers:
            try:
                await conn.execute(
                    """INSERT INTO llm_providers (name, display_name, provider_type, base_url, 
                    api_version, authentication_type, cost_calculation_method, default_currency,
                    is_active, configuration, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)""",
                    name, display_name, ptype, base_url, api_ver, auth_type, calc_method, 
                    currency, True, json.dumps({"configured": True}), datetime.now(), datetime.now()
                )
                populated['llm_providers'] = populated.get('llm_providers', 0) + 1
            except Exception as e:
                logger.debug(f"Failed provider {name}: {str(e)[:100]}")
        
        # 3. llm_models - needs provider_id
        logger.info("Populating llm_models...")
        provider_ids = [r['id'] for r in await conn.fetch("SELECT id FROM llm_providers")]
        if provider_ids:
            models = [
                ("gpt-4", "GPT-4", provider_ids[0] if len(provider_ids) > 0 else None),
                ("gpt-3.5-turbo", "GPT-3.5 Turbo", provider_ids[0] if len(provider_ids) > 0 else None),
                ("claude-3-opus", "Claude 3 Opus", provider_ids[1] if len(provider_ids) > 1 else None),
                ("claude-3-sonnet", "Claude 3 Sonnet", provider_ids[1] if len(provider_ids) > 1 else None),
                ("gemini-pro", "Gemini Pro", provider_ids[2] if len(provider_ids) > 2 else None)
            ]
            
            for model_id, name, provider_id in models:
                if provider_id:
                    try:
                        await conn.execute(
                            """INSERT INTO llm_models (name, model_id, provider_id, is_active, 
                            created_at, updated_at) 
                            VALUES ($1, $2, $3, $4, $5, $6)""",
                            name, model_id, provider_id, True, datetime.now(), datetime.now()
                        )
                        populated['llm_models'] = populated.get('llm_models', 0) + 1
                    except Exception as e:
                        logger.debug(f"Failed model {name}: {str(e)[:100]}")
        
        # 4. initiative_types
        logger.info("Populating initiative_types...")
        for name, desc in [
            ("Strategic", "Strategic initiatives for long-term goals"),
            ("Operational", "Day-to-day operational improvements"),
            ("Innovation", "Innovation and R&D initiatives"),
            ("Compliance", "Regulatory and compliance initiatives"),
            ("Digital", "Digital transformation initiatives")
        ]:
            try:
                await conn.execute(
                    """INSERT INTO initiative_types (name, description, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4)""",
                    name, desc, datetime.now(), datetime.now()
                )
                populated['initiative_types'] = populated.get('initiative_types', 0) + 1
            except Exception as e:
                logger.debug(f"Failed initiative_type {name}: {str(e)[:100]}")
        
        # 5. initiatives - needs initiative_type_id
        logger.info("Populating initiatives...")
        type_ids = [r['id'] for r in await conn.fetch("SELECT id FROM initiative_types")]
        if type_ids:
            for i, name in enumerate(["Cloud Migration", "Cost Optimization", "Customer Experience", 
                                      "Data Analytics", "Security Enhancement"]):
                try:
                    await conn.execute(
                        """INSERT INTO initiatives (name, description, initiative_type_id, 
                        status, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        name, f"{name} initiative", random.choice(type_ids), 
                        "Active", datetime.now(), datetime.now()
                    )
                    populated['initiatives'] = populated.get('initiatives', 0) + 1
                except Exception as e:
                    logger.debug(f"Failed initiative {name}: {str(e)[:100]}")
        
        # 6. kudos_categories
        logger.info("Populating kudos_categories...")
        for name, slug in [
            ("Teamwork", "teamwork"),
            ("Innovation", "innovation"),
            ("Leadership", "leadership"),
            ("Excellence", "excellence"),
            ("Customer Focus", "customer-focus")
        ]:
            try:
                await conn.execute(
                    """INSERT INTO kudos_categories (name, slug, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4)""",
                    name, slug, datetime.now(), datetime.now()
                )
                populated['kudos_categories'] = populated.get('kudos_categories', 0) + 1
            except Exception as e:
                logger.debug(f"Failed kudos_category {name}: {str(e)[:100]}")
        
        # 7. fiscal_periods
        logger.info("Populating fiscal_periods...")
        for year in [2024, 2025]:
            for quarter in range(1, 5):
                try:
                    start_month = (quarter - 1) * 3 + 1
                    end_month = quarter * 3
                    start_date = datetime(year, start_month, 1)
                    if end_month == 12:
                        end_date = datetime(year, 12, 31)
                    else:
                        end_date = datetime(year, end_month, 28)
                    
                    await conn.execute(
                        """INSERT INTO fiscal_periods (name, year, quarter, start_date, 
                        end_date, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        f"Q{quarter} {year}", year, quarter, start_date, end_date,
                        datetime.now(), datetime.now()
                    )
                    populated['fiscal_periods'] = populated.get('fiscal_periods', 0) + 1
                except Exception as e:
                    logger.debug(f"Failed fiscal_period Q{quarter} {year}: {str(e)[:100]}")
        
        # 8. knowledge_base
        logger.info("Populating knowledge_base...")
        kb_items = [
            ("Best Practices", "Collection of best practices for project delivery", "practices"),
            ("API Documentation", "Complete API documentation and examples", "technical"),
            ("User Guide", "Comprehensive user guide for the platform", "guides"),
            ("FAQ", "Frequently asked questions and answers", "support"),
            ("Architecture", "System architecture and design documentation", "technical")
        ]
        
        for title, content, category in kb_items:
            try:
                await conn.execute(
                    """INSERT INTO knowledge_base (title, content, category, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5)""",
                    title, content, category, datetime.now(), datetime.now()
                )
                populated['knowledge_base'] = populated.get('knowledge_base', 0) + 1
            except Exception as e:
                logger.debug(f"Failed kb {title}: {str(e)[:100]}")
        
        # 9. engagement_tags - check for duplicates
        logger.info("Populating engagement_tags...")
        if engagement_ids:
            tags = ["urgent", "priority", "review", "strategic", "blocked"]
            for eng_id in engagement_ids[:5]:
                for tag in random.sample(tags, 2):
                    try:
                        # Check if already exists
                        exists = await conn.fetchval(
                            "SELECT 1 FROM engagement_tags WHERE engagement_id = $1 AND tag_name = $2",
                            eng_id, tag
                        )
                        if not exists:
                            await conn.execute(
                                """INSERT INTO engagement_tags (engagement_id, tag_name, created_at) 
                                VALUES ($1, $2, $3)""",
                                eng_id, tag, datetime.now()
                            )
                            populated['engagement_tags'] = populated.get('engagement_tags', 0) + 1
                    except Exception as e:
                        logger.debug(f"Failed tag {tag} for engagement {eng_id}: {str(e)[:100]}")
        
        # 10. mcp_agent_bindings - needs server_id
        logger.info("Populating mcp_agent_bindings...")
        if server_ids:
            agents = ["ali", "amy", "baccio", "dante", "eva"]
            for agent in agents:
                try:
                    await conn.execute(
                        """INSERT INTO mcp_agent_bindings (server_id, agent_name, configuration, 
                        is_active, created_at, updated_at) 
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        random.choice(server_ids), agent, json.dumps({"role": agent}), 
                        True, datetime.now(), datetime.now()
                    )
                    populated['mcp_agent_bindings'] = populated.get('mcp_agent_bindings', 0) + 1
                except Exception as e:
                    logger.debug(f"Failed agent {agent}: {str(e)[:100]}")
        
        # 11. chat_sessions - needs explicit UUID id
        logger.info("Populating chat_sessions...")
        for i, talent_id in enumerate(talent_ids[:5]):
            try:
                session_uuid = str(uuid.uuid4())
                await conn.execute(
                    """INSERT INTO chat_sessions (id, user_id, session_id, messages, 
                    is_active, created_at, updated_at) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    str(uuid.uuid4()), talent_id, session_uuid,
                    json.dumps([
                        {"role": "user", "content": "Hello, I need help"},
                        {"role": "assistant", "content": "Hello! How can I assist you today?"}
                    ]),
                    i == 0,  # Only first session is active
                    datetime.now(), datetime.now()
                )
                populated['chat_sessions'] = populated.get('chat_sessions', 0) + 1
            except Exception as e:
                logger.debug(f"Failed chat_session {i}: {str(e)[:100]}")
        
        # 12. sentiment_tracking - score between -1 and 1
        logger.info("Populating sentiment_tracking...")
        if engagement_ids:
            for eng_id in engagement_ids[:10]:
                try:
                    # Ensure score is within -1 to 1
                    score = random.uniform(-1.0, 1.0)
                    score = max(-1.0, min(1.0, score))  # Clamp to range
                    
                    await conn.execute(
                        """INSERT INTO sentiment_tracking (engagement_id, sentiment_score, 
                        confidence, analysis_date, created_at) 
                        VALUES ($1, $2, $3, $4, $5)""",
                        eng_id, score, random.uniform(0.5, 1.0),
                        datetime.now(), datetime.now()
                    )
                    populated['sentiment_tracking'] = populated.get('sentiment_tracking', 0) + 1
                except Exception as e:
                    logger.debug(f"Failed sentiment for engagement {eng_id}: {str(e)[:100]}")
        
        # 13. talent_skills - check what proficiency values are allowed
        logger.info("Populating talent_skills...")
        skills = ["Python", "JavaScript", "TypeScript", "Docker", "AWS", "React", "PostgreSQL", "Redis"]
        
        # First try to understand the proficiency constraint
        try:
            # Check constraint definition
            constraint_info = await conn.fetchval("""
                SELECT pg_get_constraintdef(c.oid) 
                FROM pg_constraint c
                WHERE c.conname LIKE '%proficiency%'
                AND c.conrelid = 'talent_skills'::regclass
            """)
            logger.info(f"Proficiency constraint: {constraint_info}")
        except:
            pass
        
        for talent_id in talent_ids[:5]:
            for skill in random.sample(skills, 3):
                # Try different proficiency formats
                for prof in [1, 2, 3, 4, 5]:  # Try numeric values 1-5
                    try:
                        await conn.execute(
                            """INSERT INTO talent_skills (talent_id, skill_name, 
                            proficiency_level, created_at) 
                            VALUES ($1, $2, $3, $4)""",
                            talent_id, skill, prof, datetime.now()
                        )
                        populated['talent_skills'] = populated.get('talent_skills', 0) + 1
                        break  # Success, move to next skill
                    except Exception as e:
                        if prof == 5:  # Last attempt failed
                            logger.debug(f"Failed skill {skill} for talent {talent_id}: {str(e)[:100]}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("FINAL 12 TABLES POPULATION COMPLETE!")
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
    asyncio.run(populate_final_12())