#!/usr/bin/env python3
"""
Database population script matching the actual Convergio schema
"""

import asyncio
import json
import random
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
import structlog

logger = structlog.get_logger()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/convergio_db")

# Sample data
CLIENT_NAMES = [
    "TechCorp Italia", "InnovateSpa", "DataDynamics Solutions", 
    "CloudExperts", "Digital Transformation Co", "AI Innovations",
    "Future Systems", "Smart Analytics", "Cyber Security Plus", "Mobile First"
]

ENGAGEMENT_TITLES = [
    "Digital Transformation Roadmap",
    "Cloud Migration Strategy",
    "AI Implementation Plan",
    "Customer Experience Enhancement",
    "Data Analytics Platform Development",
    "Security Compliance Audit",
    "Mobile Application Suite",
    "Process Automation Initiative",
    "Marketing Campaign Optimization",
    "Infrastructure Modernization Project"
]

ACTIVITY_TITLES = [
    "Requirements Analysis and Documentation",
    "System Architecture Design",
    "Development Sprint Planning",
    "Quality Assurance Testing",
    "User Training Program",
    "Technical Documentation Review",
    "Stakeholder Alignment Meeting",
    "Performance Optimization Sprint",
    "Security Assessment Phase",
    "Deployment and Rollout Planning"
]

OKR_OBJECTIVES = [
    "Increase customer satisfaction by 30%",
    "Improve system performance and reliability",
    "Reduce operational costs by 25%",
    "Enhance team productivity and collaboration",
    "Expand market reach to new segments",
    "Strengthen security and compliance posture",
    "Accelerate product delivery times",
    "Improve code quality and maintainability"
]


async def populate_database():
    """Populate database with sample data matching actual schema"""
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Starting database population with correct schema...")
        
        # Get existing talents
        talents = await conn.fetch("SELECT id, first_name, last_name FROM talents LIMIT 10")
        talent_ids = [t['id'] for t in talents]
        
        if not talent_ids:
            logger.error("No talents found! Please run populate_minimal.py first")
            return
        
        logger.info(f"Found {len(talent_ids)} existing talents")
        
        # ==================== CLIENTS ====================
        logger.info("Creating clients...")
        client_ids = []
        
        for name in CLIENT_NAMES:
            email = f"contact@{name.lower().replace(' ', '').replace('.', '')}.com"
            
            try:
                result = await conn.fetchrow(
                    """INSERT INTO clients (
                        name, email, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4) 
                    RETURNING id""",
                    name,
                    email,
                    datetime.now(),
                    datetime.now()
                )
                if result:
                    client_ids.append(result['id'])
                    logger.info(f"Created client: {name}")
            except Exception as e:
                logger.debug(f"Could not create client {name}: {e}")
        
        logger.info(f"✅ Created {len(client_ids)} clients")
        
        # ==================== ENGAGEMENTS ====================
        logger.info("Creating engagements...")
        engagement_ids = []
        
        for title in ENGAGEMENT_TITLES:
            description = f"""
            This engagement focuses on {title.lower()}. 
            Key objectives include:
            - Deliver high-quality solutions
            - Meet all project milestones
            - Ensure stakeholder satisfaction
            - Maintain budget and timeline constraints
            
            Expected outcomes:
            - Improved operational efficiency
            - Enhanced user experience
            - Measurable business value
            """
            
            result = await conn.fetchrow(
                """INSERT INTO engagements (
                    title, description, created_at, updated_at
                ) VALUES ($1, $2, $3, $4) 
                RETURNING id""",
                title,
                description,
                datetime.now(),
                datetime.now()
            )
            if result:
                engagement_ids.append(result['id'])
                logger.info(f"Created engagement: {title}")
        
        logger.info(f"✅ Created {len(engagement_ids)} engagements")
        
        # ==================== ACTIVITIES ====================
        logger.info("Creating activities...")
        activity_ids = []
        
        for title in ACTIVITY_TITLES:
            description = f"""
            Activity: {title}
            
            This activity involves detailed work on {title.lower()}.
            
            Key deliverables:
            - Complete analysis and documentation
            - Stakeholder review and approval
            - Implementation of recommendations
            - Quality assurance and testing
            
            Success criteria:
            - All requirements met
            - Deliverables approved by stakeholders
            - Timeline adhered to
            - Quality standards maintained
            """
            
            result = await conn.fetchrow(
                """INSERT INTO activities (
                    title, description, created_at, updated_at
                ) VALUES ($1, $2, $3, $4) 
                RETURNING id""",
                title,
                description,
                datetime.now(),
                datetime.now()
            )
            if result:
                activity_ids.append(result['id'])
                logger.info(f"Created activity: {title}")
        
        logger.info(f"✅ Created {len(activity_ids)} activities")
        
        # ==================== OKRs ====================
        logger.info("Creating OKRs...")
        okr_count = 0
        
        for objective in OKR_OBJECTIVES:
            key_results = [
                {"description": "Measure progress on key metric 1", "target": 100, "current": random.randint(0, 100)},
                {"description": "Achieve target for metric 2", "target": 50, "current": random.randint(0, 50)},
                {"description": "Complete milestone 3", "target": 1, "current": random.choice([0, 1])}
            ]
            
            try:
                result = await conn.fetchrow(
                    """INSERT INTO okrs (
                        objective, key_results, visibility, okr_scope,
                        entity_id, created_by_id, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
                    RETURNING id""",
                    objective,
                    json.dumps(key_results),
                    'public',
                    'company',
                    1,  # Default entity
                    random.choice(talent_ids),
                    datetime.now(),
                    datetime.now()
                )
                if result:
                    okr_count += 1
                    logger.info(f"Created OKR: {objective[:50]}...")
            except Exception as e:
                logger.debug(f"Could not create OKR: {e}")
        
        logger.info(f"✅ Created {okr_count} OKRs")
        
        # ==================== STUDIOS (if not already created) ====================
        logger.info("Creating studios...")
        studio_names = ["Design Lab", "Engineering Center", "Data Science Hub", "Innovation Studio", "Product Team"]
        studio_count = 0
        
        for name in studio_names:
            try:
                result = await conn.fetchrow(
                    """INSERT INTO studios (
                        name, studio_lead_id, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4)
                    RETURNING id""",
                    name,
                    random.choice(talent_ids),
                    datetime.now(),
                    datetime.now()
                )
                if result:
                    studio_count += 1
                    logger.info(f"Created studio: {name}")
            except Exception as e:
                logger.debug(f"Skipping studio {name}: {e}")
        
        logger.info(f"✅ Created {studio_count} studios")
        
        # ==================== CREWS ====================
        logger.info("Creating crews...")
        crew_names = ["Alpha Team", "Beta Squad", "Gamma Force", "Delta Unit", "Epsilon Group"]
        crew_count = 0
        
        for name in crew_names:
            try:
                result = await conn.fetchrow(
                    """INSERT INTO crews (
                        name, description, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4)
                    RETURNING id""",
                    name,
                    f"Elite team focused on high-priority projects",
                    datetime.now(),
                    datetime.now()
                )
                if result:
                    crew_count += 1
                    logger.info(f"Created crew: {name}")
            except Exception as e:
                logger.debug(f"Skipping crew {name}: {e}")
        
        logger.info(f"✅ Created {crew_count} crews")
        
        # ==================== ORGANIZATIONS ====================
        logger.info("Creating organizations...")
        org_names = ["Convergio HQ", "Innovation Division", "Customer Success", "Technical Operations", "Strategic Initiatives"]
        org_count = 0
        
        for name in org_names:
            try:
                result = await conn.fetchrow(
                    """INSERT INTO organizations (
                        name, description, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4)
                    RETURNING id""",
                    name,
                    f"Organization unit: {name}",
                    datetime.now(),
                    datetime.now()
                )
                if result:
                    org_count += 1
                    logger.info(f"Created organization: {name}")
            except Exception as e:
                logger.debug(f"Organization might already exist: {name}")
        
        logger.info(f"✅ Created {org_count} organizations")
        
        # ==================== SUMMARY ====================
        logger.info("\n" + "="*60)
        logger.info("🎉 DATABASE POPULATION COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info(f"✅ {len(client_ids)} Clients created")
        logger.info(f"✅ {len(engagement_ids)} Engagements created")
        logger.info(f"✅ {len(activity_ids)} Activities created")
        logger.info(f"✅ {okr_count} OKRs created")
        logger.info(f"✅ {studio_count} Studios created")
        logger.info(f"✅ {crew_count} Crews created")
        logger.info(f"✅ {org_count} Organizations created")
        logger.info("="*60)
        
        # Show sample queries to verify data
        logger.info("\nVerifying data...")
        
        client_count = await conn.fetchval("SELECT COUNT(*) FROM clients")
        engagement_count = await conn.fetchval("SELECT COUNT(*) FROM engagements")
        activity_count = await conn.fetchval("SELECT COUNT(*) FROM activities")
        okr_count_total = await conn.fetchval("SELECT COUNT(*) FROM okrs")
        
        logger.info(f"📊 Total records in database:")
        logger.info(f"   - Clients: {client_count}")
        logger.info(f"   - Engagements: {engagement_count}")
        logger.info(f"   - Activities: {activity_count}")
        logger.info(f"   - OKRs: {okr_count_total}")
        
    except Exception as e:
        logger.error(f"Population failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(populate_database())