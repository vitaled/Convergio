#!/usr/bin/env python3
"""
Populate database tables via API endpoints
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
import httpx
import structlog

logger = structlog.get_logger()

API_BASE_URL = "http://localhost:8055"


async def populate_via_api():
    """Populate tables using API endpoints"""
    
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        populated = {}
        
        # First, check which endpoints are available
        logger.info("Fetching API documentation...")
        try:
            response = await client.get("/openapi.json")
            if response.status_code == 200:
                openapi = response.json()
                paths = openapi.get("paths", {})
                logger.info(f"Found {len(paths)} API endpoints")
                
                # List available endpoints
                endpoints = []
                for path, methods in paths.items():
                    for method in methods:
                        if method in ["post", "put"]:
                            endpoints.append((method.upper(), path))
                
                logger.info("Available POST/PUT endpoints:")
                for method, path in sorted(endpoints):
                    logger.info(f"  {method} {path}")
                
                # Try to populate via available endpoints
                
                # 1. Try chat sessions endpoint
                if "/chat" in str(paths) or "/sessions" in str(paths):
                    logger.info("Attempting to create chat sessions...")
                    for i in range(3):
                        try:
                            response = await client.post(
                                "/api/chat/sessions",
                                json={
                                    "user_id": 1,
                                    "message": f"Test message {i+1}"
                                }
                            )
                            if response.status_code in [200, 201]:
                                populated['chat_sessions'] = populated.get('chat_sessions', 0) + 1
                                logger.info(f"✅ Created chat session {i+1}")
                        except Exception as e:
                            logger.debug(f"Failed chat session: {e}")
                
                # 2. Try LLM models endpoint
                if "/llm" in str(paths) or "/models" in str(paths):
                    logger.info("Attempting to create LLM models...")
                    models = [
                        {"model_name": "gpt-4", "display_name": "GPT-4", "provider_id": 1},
                        {"model_name": "claude-3", "display_name": "Claude 3", "provider_id": 1},
                    ]
                    for model in models:
                        try:
                            response = await client.post(
                                "/api/llm/models",
                                json=model
                            )
                            if response.status_code in [200, 201]:
                                populated['llm_models'] = populated.get('llm_models', 0) + 1
                                logger.info(f"✅ Created LLM model: {model['model_name']}")
                        except Exception as e:
                            logger.debug(f"Failed LLM model: {e}")
                
                # 3. Try skills endpoint for talent_skills
                if "/talents" in str(paths) or "/skills" in str(paths):
                    logger.info("Attempting to assign skills to talents...")
                    for talent_id in range(1, 4):
                        for skill_id in range(1, 4):
                            try:
                                response = await client.post(
                                    f"/api/talents/{talent_id}/skills",
                                    json={
                                        "skill_id": skill_id,
                                        "proficiency": random.randint(1, 10)
                                    }
                                )
                                if response.status_code in [200, 201]:
                                    populated['talent_skills'] = populated.get('talent_skills', 0) + 1
                                    logger.info(f"✅ Assigned skill {skill_id} to talent {talent_id}")
                            except Exception as e:
                                logger.debug(f"Failed talent skill: {e}")
                
                # 4. Try engagement tags
                if "/engagements" in str(paths):
                    logger.info("Attempting to add engagement tags...")
                    tags = ["urgent", "priority", "review", "strategic"]
                    for eng_id in range(1, 4):
                        for tag in random.sample(tags, 2):
                            try:
                                response = await client.post(
                                    f"/api/engagements/{eng_id}/tags",
                                    json={"tag": tag}
                                )
                                if response.status_code in [200, 201]:
                                    populated['engagement_tags'] = populated.get('engagement_tags', 0) + 1
                                    logger.info(f"✅ Added tag '{tag}' to engagement {eng_id}")
                            except Exception as e:
                                logger.debug(f"Failed engagement tag: {e}")
                
                # 5. Try knowledge base
                if "/knowledge" in str(paths) or "/kb" in str(paths):
                    logger.info("Attempting to create knowledge base articles...")
                    articles = [
                        {"title": "Getting Started", "content": "Welcome guide", "tags": ["intro", "guide"]},
                        {"title": "API Reference", "content": "API documentation", "tags": ["api", "docs"]},
                        {"title": "Best Practices", "content": "Best practices guide", "tags": ["guide", "tips"]},
                    ]
                    for article in articles:
                        try:
                            response = await client.post(
                                "/api/knowledge",
                                json=article
                            )
                            if response.status_code in [200, 201]:
                                populated['knowledge_base'] = populated.get('knowledge_base', 0) + 1
                                logger.info(f"✅ Created KB article: {article['title']}")
                        except Exception as e:
                            logger.debug(f"Failed KB article: {e}")
                
                # 6. Try initiatives
                if "/initiatives" in str(paths):
                    logger.info("Attempting to create initiatives...")
                    initiatives = [
                        {"name": "Cloud Migration", "description": "Migrate to cloud", "owner_id": 1, "initiative_type_id": 1},
                        {"name": "Cost Optimization", "description": "Reduce costs", "owner_id": 2, "initiative_type_id": 2},
                    ]
                    for init in initiatives:
                        try:
                            response = await client.post(
                                "/api/initiatives",
                                json=init
                            )
                            if response.status_code in [200, 201]:
                                populated['initiatives'] = populated.get('initiatives', 0) + 1
                                logger.info(f"✅ Created initiative: {init['name']}")
                        except Exception as e:
                            logger.debug(f"Failed initiative: {e}")
                
                # 7. Try sentiment tracking
                if "/sentiment" in str(paths) or "/analytics" in str(paths):
                    logger.info("Attempting to create sentiment tracking...")
                    for i in range(5):
                        try:
                            response = await client.post(
                                "/api/sentiment",
                                json={
                                    "target_id": i + 1,
                                    "target_type": "engagement",
                                    "sentiment_score": round(random.uniform(-1, 1), 2),
                                    "confidence": round(random.uniform(0.5, 1), 2)
                                }
                            )
                            if response.status_code in [200, 201]:
                                populated['sentiment_tracking'] = populated.get('sentiment_tracking', 0) + 1
                                logger.info(f"✅ Created sentiment tracking {i+1}")
                        except Exception as e:
                            logger.debug(f"Failed sentiment: {e}")
                
                # Try generic endpoints based on table names
                empty_tables = [
                    "fiscal_periods", "kudos_categories", "mcp_agent_bindings"
                ]
                
                for table in empty_tables:
                    # Try various endpoint patterns
                    endpoint_patterns = [
                        f"/api/{table}",
                        f"/api/{table.replace('_', '-')}",
                        f"/api/{table.replace('_', '/')}",
                        f"/{table}",
                        f"/{table.replace('_', '-')}"
                    ]
                    
                    for endpoint in endpoint_patterns:
                        if endpoint in str(paths):
                            logger.info(f"Found endpoint: {endpoint}")
                            # Try to POST sample data
                            try:
                                sample_data = generate_sample_data(table)
                                response = await client.post(endpoint, json=sample_data)
                                if response.status_code in [200, 201]:
                                    populated[table] = populated.get(table, 0) + 1
                                    logger.info(f"✅ Created {table} via {endpoint}")
                                    break
                            except Exception as e:
                                logger.debug(f"Failed {table} at {endpoint}: {e}")
                
                # Summary
                logger.info("\n" + "="*60)
                logger.info("API POPULATION RESULTS:")
                if populated:
                    for table, count in sorted(populated.items()):
                        logger.info(f"✅ {table}: {count} rows")
                    logger.info(f"Total rows inserted: {sum(populated.values())}")
                else:
                    logger.warning("❌ No tables were populated via API")
                    logger.info("This might mean:")
                    logger.info("  1. API endpoints don't match table names")
                    logger.info("  2. Authentication is required")
                    logger.info("  3. Different data format is expected")
                logger.info("="*60)
                
            else:
                logger.error(f"Failed to fetch OpenAPI spec: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error connecting to API: {e}")
            logger.info("Make sure the API is running on http://localhost:8055")


def generate_sample_data(table_name):
    """Generate sample data based on table name"""
    if "fiscal" in table_name:
        return {
            "name": "Q1 2025",
            "year": 2025,
            "quarter": 1,
            "start_date": "2025-01-01",
            "end_date": "2025-03-31"
        }
    elif "kudos" in table_name:
        return {
            "name": "Teamwork",
            "description": "Great teamwork",
            "icon": "👥"
        }
    elif "mcp" in table_name:
        return {
            "mcp_server_id": 1,
            "agent_id": "agent-1",
            "configuration": {"enabled": True}
        }
    else:
        return {"name": f"Sample {table_name}"}


if __name__ == "__main__":
    asyncio.run(populate_via_api())