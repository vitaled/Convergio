#!/usr/bin/env python3
"""
Populate the 10 empty tables using REAL database schema
NO ASSUMPTIONS - only use actual column names from database
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


async def get_columns(conn, table_name):
    """Get actual column names and types for a table"""
    result = await conn.fetch("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = $1
        ORDER BY ordinal_position
    """, table_name)
    return {r['column_name']: {
        'type': r['data_type'],
        'nullable': r['is_nullable'] == 'YES',
        'default': r['column_default']
    } for r in result}


async def populate_real_schema():
    """Populate using ACTUAL database schema"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Populating 10 empty tables with REAL schema...")
        populated = {}
        
        # Get foreign key IDs we'll need
        talent_ids = [r['id'] for r in await conn.fetch("SELECT id FROM talents")]
        engagement_ids = [r['id'] for r in await conn.fetch("SELECT id FROM engagements")]
        skill_ids = [r['id'] for r in await conn.fetch("SELECT id FROM skills")]
        initiative_type_ids = [r['id'] for r in await conn.fetch("SELECT id FROM initiative_types")]
        fiscal_year_ids = [r['id'] for r in await conn.fetch("SELECT id FROM fiscal_years")]
        llm_provider_ids = [r['id'] for r in await conn.fetch("SELECT id FROM llm_providers")]
        mcp_server_ids = [r['id'] for r in await conn.fetch("SELECT id FROM mcp_servers")]
        
        # 1. chat_sessions - inspect and populate
        logger.info("Populating chat_sessions...")
        cols = await get_columns(conn, 'chat_sessions')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        # Check which talent column exists
        talent_col = None
        if 'talent_id' in cols:
            talent_col = 'talent_id'
        elif 'user_id' in cols:
            talent_col = 'user_id'
        
        if talent_col and talent_ids:
            for i in range(min(5, len(talent_ids))):
                try:
                    values = {
                        'id': str(uuid.uuid4()),
                        talent_col: talent_ids[i],
                        'messages': json.dumps([{"role": "user", "content": f"Hello {i+1}"}]),
                        'is_active': i == 0,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Add session_type if it exists
                    if 'session_type' in cols:
                        values['session_type'] = 'chat'
                    # Add session_id if it exists
                    if 'session_id' in cols:
                        values['session_id'] = str(uuid.uuid4())
                    
                    # Filter to only columns that exist
                    valid_cols = [k for k in values.keys() if k in cols]
                    valid_values = [values[k] for k in valid_cols]
                    
                    query = f"""
                        INSERT INTO chat_sessions ({', '.join(valid_cols)})
                        VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                    """
                    
                    await conn.execute(query, *valid_values)
                    populated['chat_sessions'] = populated.get('chat_sessions', 0) + 1
                except Exception as e:
                    logger.debug(f"chat_sessions error: {e}")
        
        # 2. engagement_tags
        logger.info("Populating engagement_tags...")
        cols = await get_columns(conn, 'engagement_tags')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        # Check which engagement column exists
        eng_col = 'target_id' if 'target_id' in cols else 'engagement_id' if 'engagement_id' in cols else None
        tag_col = 'tag' if 'tag' in cols else 'tag_name' if 'tag_name' in cols else None
        
        if eng_col and tag_col and engagement_ids:
            tags = ['urgent', 'priority', 'review', 'strategic', 'blocked']
            for eng_id in engagement_ids[:5]:
                for tag in random.sample(tags, 2):
                    try:
                        values = {
                            eng_col: eng_id,
                            tag_col: tag,
                            'created_at': datetime.now()
                        }
                        
                        # Add target_type if needed
                        if 'target_type' in cols:
                            values['target_type'] = 'engagement'
                        
                        valid_cols = [k for k in values.keys() if k in cols]
                        valid_values = [values[k] for k in valid_cols]
                        
                        query = f"""
                            INSERT INTO engagement_tags ({', '.join(valid_cols)})
                            VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                        """
                        
                        await conn.execute(query, *valid_values)
                        populated['engagement_tags'] = populated.get('engagement_tags', 0) + 1
                    except Exception as e:
                        if 'duplicate' not in str(e).lower():
                            logger.debug(f"engagement_tags error: {e}")
        
        # 3. fiscal_periods
        logger.info("Populating fiscal_periods...")
        cols = await get_columns(conn, 'fiscal_periods')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        if fiscal_year_ids:
            for year_id in fiscal_year_ids[:1]:
                for q in range(1, 5):
                    try:
                        values = {
                            'fiscal_year_id': year_id,
                            'period_number': q,
                            'period_type': 'quarter',
                            'start_date': datetime(2025, (q-1)*3+1, 1).date(),
                            'end_date': datetime(2025, q*3, 28 if q < 4 else 31).date(),
                            'created_at': datetime.now(),
                            'updated_at': datetime.now()
                        }
                        
                        valid_cols = [k for k in values.keys() if k in cols]
                        valid_values = [values[k] for k in valid_cols]
                        
                        query = f"""
                            INSERT INTO fiscal_periods ({', '.join(valid_cols)})
                            VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                        """
                        
                        await conn.execute(query, *valid_values)
                        populated['fiscal_periods'] = populated.get('fiscal_periods', 0) + 1
                    except Exception as e:
                        logger.debug(f"fiscal_periods error: {e}")
        
        # 4. initiatives
        logger.info("Populating initiatives...")
        cols = await get_columns(conn, 'initiatives')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        if 'owner_id' in cols and talent_ids and initiative_type_ids:
            names = ["Cloud Migration", "Cost Optimization", "Customer Experience", "AI Integration", "Security Enhancement"]
            for i, name in enumerate(names[:min(5, len(talent_ids), len(initiative_type_ids))]):
                try:
                    values = {
                        'name': name,
                        'description': f"{name} initiative",
                        'initiative_type_id': initiative_type_ids[i % len(initiative_type_ids)],
                        'owner_id': talent_ids[i % len(talent_ids)],
                        'status': 'Active',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    valid_cols = [k for k in values.keys() if k in cols]
                    valid_values = [values[k] for k in valid_cols]
                    
                    query = f"""
                        INSERT INTO initiatives ({', '.join(valid_cols)})
                        VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                    """
                    
                    await conn.execute(query, *valid_values)
                    populated['initiatives'] = populated.get('initiatives', 0) + 1
                except Exception as e:
                    logger.debug(f"initiatives error: {e}")
        
        # 5. knowledge_base
        logger.info("Populating knowledge_base...")
        cols = await get_columns(conn, 'knowledge_base')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        articles = [
            ("Getting Started Guide", "Complete guide for new users"),
            ("API Documentation", "REST API reference"),
            ("Best Practices", "Platform best practices"),
            ("Troubleshooting", "Common issues and solutions"),
            ("Architecture Overview", "System architecture guide")
        ]
        
        for title, content in articles:
            try:
                values = {
                    'title': title,
                    'content': content,
                    'views': 0,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # Add optional fields if they exist
                if 'author_id' in cols and talent_ids:
                    values['author_id'] = random.choice(talent_ids)
                if 'tags' in cols:
                    values['tags'] = json.dumps(['guide', 'documentation'])
                if 'category' in cols:
                    values['category'] = 'documentation'
                
                valid_cols = [k for k in values.keys() if k in cols]
                valid_values = [values[k] for k in valid_cols]
                
                query = f"""
                    INSERT INTO knowledge_base ({', '.join(valid_cols)})
                    VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                """
                
                await conn.execute(query, *valid_values)
                populated['knowledge_base'] = populated.get('knowledge_base', 0) + 1
            except Exception as e:
                logger.debug(f"knowledge_base error: {e}")
        
        # 6. kudos_categories
        logger.info("Populating kudos_categories...")
        cols = await get_columns(conn, 'kudos_categories')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        categories = [
            ("Teamwork", "Great team collaboration", "👥"),
            ("Innovation", "Creative problem solving", "💡"),
            ("Leadership", "Exceptional leadership", "👑"),
            ("Excellence", "Outstanding performance", "⭐"),
            ("Customer Focus", "Customer satisfaction", "🤝")
        ]
        
        for name, desc, icon in categories:
            try:
                values = {
                    'name': name,
                    'description': desc,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                if 'icon' in cols:
                    values['icon'] = icon
                if 'slug' in cols:
                    values['slug'] = name.lower().replace(' ', '-')
                
                valid_cols = [k for k in values.keys() if k in cols]
                valid_values = [values[k] for k in valid_cols]
                
                query = f"""
                    INSERT INTO kudos_categories ({', '.join(valid_cols)})
                    VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                """
                
                await conn.execute(query, *valid_values)
                populated['kudos_categories'] = populated.get('kudos_categories', 0) + 1
            except Exception as e:
                logger.debug(f"kudos_categories error: {e}")
        
        # 7. llm_models
        logger.info("Populating llm_models...")
        cols = await get_columns(conn, 'llm_models')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        if llm_provider_ids:
            models = [
                ("gpt-4", "GPT-4", "v1", 8192),
                ("gpt-3.5-turbo", "GPT-3.5 Turbo", "v1", 4096),
                ("claude-3-opus", "Claude 3 Opus", "v1", 200000),
                ("claude-3-sonnet", "Claude 3 Sonnet", "v1", 200000),
                ("gemini-pro", "Gemini Pro", "v1", 32768)
            ]
            
            for model_name, display_name, version, context in models[:len(llm_provider_ids)]:
                try:
                    values = {
                        'provider_id': llm_provider_ids[0],
                        'is_active': True,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Use correct column names
                    if 'model_name' in cols:
                        values['model_name'] = model_name
                    elif 'name' in cols:
                        values['name'] = model_name
                    
                    if 'display_name' in cols:
                        values['display_name'] = display_name
                    if 'model_version' in cols:
                        values['model_version'] = version
                    if 'context_window' in cols:
                        values['context_window'] = context
                    
                    valid_cols = [k for k in values.keys() if k in cols]
                    valid_values = [values[k] for k in valid_cols]
                    
                    query = f"""
                        INSERT INTO llm_models ({', '.join(valid_cols)})
                        VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                    """
                    
                    await conn.execute(query, *valid_values)
                    populated['llm_models'] = populated.get('llm_models', 0) + 1
                except Exception as e:
                    logger.debug(f"llm_models error: {e}")
        
        # 8. mcp_agent_bindings
        logger.info("Populating mcp_agent_bindings...")
        cols = await get_columns(conn, 'mcp_agent_bindings')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        if mcp_server_ids:
            agents = ['ali', 'amy', 'baccio', 'dante', 'eva']
            for agent in agents:
                try:
                    values = {
                        'configuration': json.dumps({'role': agent, 'enabled': True}),
                        'is_active': True,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # Check which server column exists
                    if 'mcp_server_id' in cols:
                        values['mcp_server_id'] = mcp_server_ids[0]
                    elif 'server_id' in cols:
                        values['server_id'] = mcp_server_ids[0]
                    
                    # Check which agent column exists
                    if 'agent_id' in cols:
                        values['agent_id'] = agent
                    elif 'agent_name' in cols:
                        values['agent_name'] = agent
                    
                    valid_cols = [k for k in values.keys() if k in cols]
                    valid_values = [values[k] for k in valid_cols]
                    
                    query = f"""
                        INSERT INTO mcp_agent_bindings ({', '.join(valid_cols)})
                        VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                    """
                    
                    await conn.execute(query, *valid_values)
                    populated['mcp_agent_bindings'] = populated.get('mcp_agent_bindings', 0) + 1
                except Exception as e:
                    logger.debug(f"mcp_agent_bindings error: {e}")
        
        # 9. sentiment_tracking
        logger.info("Populating sentiment_tracking...")
        cols = await get_columns(conn, 'sentiment_tracking')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        for eng_id in engagement_ids[:10]:
            try:
                score = round(random.uniform(-1.0, 1.0), 2)
                values = {
                    'sentiment_score': score,
                    'confidence': round(random.uniform(0.5, 1.0), 2),
                    'analysis_date': datetime.now().date(),
                    'created_at': datetime.now()
                }
                
                # Check which target columns exist
                if 'target_id' in cols:
                    values['target_id'] = eng_id
                    if 'target_type' in cols:
                        values['target_type'] = 'engagement'
                elif 'engagement_id' in cols:
                    values['engagement_id'] = eng_id
                
                valid_cols = [k for k in values.keys() if k in cols]
                valid_values = [values[k] for k in valid_cols]
                
                query = f"""
                    INSERT INTO sentiment_tracking ({', '.join(valid_cols)})
                    VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                """
                
                await conn.execute(query, *valid_values)
                populated['sentiment_tracking'] = populated.get('sentiment_tracking', 0) + 1
            except Exception as e:
                logger.debug(f"sentiment_tracking error: {e}")
        
        # 10. talent_skills
        logger.info("Populating talent_skills...")
        cols = await get_columns(conn, 'talent_skills')
        logger.info(f"  Columns: {list(cols.keys())}")
        
        if talent_ids and skill_ids:
            for talent_id in talent_ids[:5]:
                for skill_id in random.sample(skill_ids, min(3, len(skill_ids))):
                    try:
                        values = {
                            'talent_id': talent_id,
                            'created_at': datetime.now()
                        }
                        
                        # Check if uses skill_id or skill_name
                        if 'skill_id' in cols:
                            values['skill_id'] = skill_id
                        elif 'skill_name' in cols:
                            # Get skill name
                            skill_name = await conn.fetchval("SELECT name FROM skills WHERE id = $1", skill_id)
                            values['skill_name'] = skill_name
                        
                        # Check proficiency column name and type
                        if 'proficiency' in cols:
                            values['proficiency'] = random.randint(1, 10)
                        elif 'proficiency_level' in cols:
                            values['proficiency_level'] = random.randint(1, 10)
                        
                        valid_cols = [k for k in values.keys() if k in cols]
                        valid_values = [values[k] for k in valid_cols]
                        
                        query = f"""
                            INSERT INTO talent_skills ({', '.join(valid_cols)})
                            VALUES ({', '.join(f'${i+1}' for i in range(len(valid_cols)))})
                        """
                        
                        await conn.execute(query, *valid_values)
                        populated['talent_skills'] = populated.get('talent_skills', 0) + 1
                    except Exception as e:
                        if 'duplicate' not in str(e).lower():
                            logger.debug(f"talent_skills error: {e}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("REAL SCHEMA POPULATION COMPLETE!")
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
    asyncio.run(populate_real_schema())