#!/usr/bin/env python3
"""
Complete database population script for all Convergio tables
Populates engagements, activities, OKRs and related tables
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
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
ENGAGEMENT_NAMES = [
    "Digital Transformation Initiative",
    "Cloud Migration Project",
    "AI Strategy Development",
    "Customer Experience Enhancement",
    "Data Analytics Platform",
    "Security Compliance Audit",
    "Mobile App Development",
    "Process Automation",
    "Marketing Campaign 2025",
    "Infrastructure Modernization"
]

ACTIVITY_NAMES = [
    "Requirements Gathering",
    "Technical Design",
    "Development Sprint 1",
    "Testing Phase",
    "User Training",
    "Documentation Review",
    "Stakeholder Meeting",
    "Performance Optimization",
    "Security Assessment",
    "Deployment Planning"
]

OKR_OBJECTIVES = [
    "Increase customer satisfaction",
    "Improve system performance",
    "Reduce operational costs",
    "Enhance team productivity",
    "Expand market reach",
    "Strengthen security posture",
    "Accelerate delivery times",
    "Improve code quality"
]

KEY_RESULTS = [
    "Achieve 95% uptime",
    "Reduce response time by 40%",
    "Increase user engagement by 25%",
    "Complete 100% of planned features",
    "Reduce bugs by 50%",
    "Improve test coverage to 80%",
    "Onboard 500 new users",
    "Reduce costs by 20%"
]


async def populate_database():
    """Populate all important tables in the database"""
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Starting complete database population...")
        
        # Get existing talents and clients
        talents = await conn.fetch("SELECT id FROM talents LIMIT 10")
        talent_ids = [t['id'] for t in talents]
        
        if not talent_ids:
            logger.error("No talents found! Please run populate_minimal.py first")
            return
        
        logger.info(f"Found {len(talent_ids)} existing talents")
        
        # ==================== CLIENTS ====================
        logger.info("Creating clients...")
        client_ids = []
        
        client_names = ["TechCorp", "InnovateSpa", "DataDynamics", "CloudExperts", "DigitalSolutions"]
        
        for name in client_names:
            result = await conn.fetchrow(
                """INSERT INTO clients (
                    name, industry, website, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5) 
                ON CONFLICT (name) DO UPDATE SET updated_at = $5
                RETURNING id""",
                name,
                random.choice(["Technology", "Finance", "Healthcare", "Retail", "Manufacturing"]),
                f"https://www.{name.lower()}.com",
                datetime.now(),
                datetime.now()
            )
            client_ids.append(result['id'])
        
        logger.info(f"✅ Created {len(client_ids)} clients")
        
        # ==================== ENGAGEMENTS ====================
        logger.info("Creating engagements...")
        engagement_ids = []
        
        for i, name in enumerate(ENGAGEMENT_NAMES):
            result = await conn.fetchrow(
                """INSERT INTO engagements (
                    name, client_id, start_date, end_date, 
                    budget, status, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
                RETURNING id""",
                name,
                random.choice(client_ids),
                datetime.now() - timedelta(days=random.randint(30, 180)),
                datetime.now() + timedelta(days=random.randint(30, 365)),
                random.randint(50000, 500000),
                random.choice(['Active', 'Planning', 'On Hold', 'Completed']),
                datetime.now(),
                datetime.now()
            )
            engagement_ids.append(result['id'])
            logger.info(f"Created engagement: {name}")
        
        logger.info(f"✅ Created {len(engagement_ids)} engagements")
        
        # ==================== ACTIVITIES ====================
        logger.info("Creating activities...")
        activity_ids = []
        
        for engagement_id in engagement_ids[:5]:  # Create activities for first 5 engagements
            for activity_name in random.sample(ACTIVITY_NAMES, random.randint(3, 6)):
                result = await conn.fetchrow(
                    """INSERT INTO activities (
                        name, engagement_id, assigned_to, 
                        start_date, end_date, status,
                        priority, estimated_hours, actual_hours,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) 
                    RETURNING id""",
                    activity_name,
                    engagement_id,
                    random.choice(talent_ids),
                    datetime.now() - timedelta(days=random.randint(1, 30)),
                    datetime.now() + timedelta(days=random.randint(1, 60)),
                    random.choice(['Not Started', 'In Progress', 'Completed', 'Blocked']),
                    random.choice(['Low', 'Medium', 'High', 'Critical']),
                    random.randint(8, 80),
                    random.randint(0, 60) if random.choice([True, False]) else None,
                    datetime.now(),
                    datetime.now()
                )
                activity_ids.append(result['id'])
        
        logger.info(f"✅ Created {len(activity_ids)} activities")
        
        # ==================== OKRs ====================
        logger.info("Creating OKRs...")
        okr_ids = []
        
        for objective in OKR_OBJECTIVES:
            result = await conn.fetchrow(
                """INSERT INTO okrs (
                    objective, quarter, year, owner_id,
                    status, progress, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
                RETURNING id""",
                objective,
                f"Q{random.randint(1, 4)}",
                2025,
                random.choice(talent_ids),
                random.choice(['Draft', 'Active', 'Completed', 'Cancelled']),
                random.randint(0, 100),
                datetime.now(),
                datetime.now()
            )
            okr_ids.append(result['id'])
            
            # Add key results for each OKR
            for kr in random.sample(KEY_RESULTS, random.randint(2, 4)):
                await conn.execute(
                    """INSERT INTO okrs (
                        objective, parent_id, quarter, year, owner_id,
                        status, progress, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT DO NOTHING""",
                    kr,
                    result['id'],
                    f"Q{random.randint(1, 4)}",
                    2025,
                    random.choice(talent_ids),
                    'Active',
                    random.randint(0, 100),
                    datetime.now(),
                    datetime.now()
                )
        
        logger.info(f"✅ Created {len(okr_ids)} OKRs with key results")
        
        # ==================== ACTIVITY ASSIGNMENTS ====================
        logger.info("Creating activity assignments...")
        assignment_count = 0
        
        for activity_id in activity_ids[:20]:  # Assign first 20 activities
            num_assignments = random.randint(1, 3)
            for _ in range(num_assignments):
                await conn.execute(
                    """INSERT INTO activity_assignments (
                        activity_id, talent_id, role, allocation_percentage,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT DO NOTHING""",
                    activity_id,
                    random.choice(talent_ids),
                    random.choice(['Lead', 'Contributor', 'Reviewer', 'Support']),
                    random.choice([25, 50, 75, 100]),
                    datetime.now(),
                    datetime.now()
                )
                assignment_count += 1
        
        logger.info(f"✅ Created {assignment_count} activity assignments")
        
        # ==================== MILESTONES ====================
        logger.info("Creating milestones...")
        milestone_count = 0
        
        for engagement_id in engagement_ids[:5]:
            for i in range(random.randint(2, 4)):
                await conn.execute(
                    """INSERT INTO milestones (
                        name, engagement_id, due_date, status,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT DO NOTHING""",
                    f"Milestone {i+1}",
                    engagement_id,
                    datetime.now() + timedelta(days=random.randint(30, 180)),
                    random.choice(['Pending', 'In Progress', 'Completed', 'Delayed']),
                    datetime.now(),
                    datetime.now()
                )
                milestone_count += 1
        
        logger.info(f"✅ Created {milestone_count} milestones")
        
        # ==================== STUDIOS ====================
        logger.info("Creating studios...")
        studio_names = ["Design Studio", "Engineering Hub", "Data Lab", "Innovation Center", "Product Team"]
        studio_count = 0
        
        for name in studio_names:
            try:
                await conn.execute(
                    """INSERT INTO studios (
                        name, studio_lead_id, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4)
                    ON CONFLICT (name) DO NOTHING""",
                    name,
                    random.choice(talent_ids),
                    datetime.now(),
                    datetime.now()
                )
                studio_count += 1
            except Exception as e:
                logger.debug(f"Skipping studio {name}: {e}")
        
        logger.info(f"✅ Created {studio_count} studios")
        
        # ==================== ENGAGEMENT UPDATES ====================
        logger.info("Creating engagement updates...")
        update_count = 0
        
        for engagement_id in engagement_ids[:5]:
            for _ in range(random.randint(2, 5)):
                await conn.execute(
                    """INSERT INTO engagement_updates (
                        engagement_id, update_text, posted_by,
                        created_at
                    ) VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING""",
                    engagement_id,
                    random.choice([
                        "Project is progressing well, on track for delivery",
                        "Completed user testing phase with positive feedback",
                        "Technical challenges resolved, moving to next phase",
                        "Client meeting scheduled for next week",
                        "Budget review completed, all metrics are green",
                        "Team expanded with two new developers",
                        "Security audit passed successfully",
                        "Performance improvements implemented"
                    ]),
                    random.choice(talent_ids),
                    datetime.now() - timedelta(days=random.randint(0, 30))
                )
                update_count += 1
        
        logger.info(f"✅ Created {update_count} engagement updates")
        
        # ==================== RISKS ====================
        logger.info("Creating risks...")
        risk_count = 0
        
        risk_descriptions = [
            "Timeline delay due to resource constraints",
            "Budget overrun risk due to scope changes",
            "Technical debt accumulation",
            "Key team member availability",
            "Third-party dependency delays",
            "Security vulnerabilities identified",
            "Performance issues under load",
            "Integration complexity higher than expected"
        ]
        
        for engagement_id in engagement_ids[:5]:
            for risk_desc in random.sample(risk_descriptions, random.randint(1, 3)):
                await conn.execute(
                    """INSERT INTO risks (
                        engagement_id, description, impact, probability,
                        mitigation_plan, status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT DO NOTHING""",
                    engagement_id,
                    risk_desc,
                    random.choice(['Low', 'Medium', 'High', 'Critical']),
                    random.choice(['Low', 'Medium', 'High']),
                    "Mitigation strategy in place with regular monitoring",
                    random.choice(['Open', 'Mitigated', 'Closed', 'Monitoring']),
                    datetime.now(),
                    datetime.now()
                )
                risk_count += 1
        
        logger.info(f"✅ Created {risk_count} risks")
        
        # ==================== SUMMARY ====================
        logger.info("\n" + "="*50)
        logger.info("🎉 DATABASE POPULATION COMPLETED!")
        logger.info("="*50)
        logger.info(f"✅ {len(client_ids)} Clients")
        logger.info(f"✅ {len(engagement_ids)} Engagements")
        logger.info(f"✅ {len(activity_ids)} Activities")
        logger.info(f"✅ {len(okr_ids)} OKRs")
        logger.info(f"✅ {assignment_count} Activity Assignments")
        logger.info(f"✅ {milestone_count} Milestones")
        logger.info(f"✅ {studio_count} Studios")
        logger.info(f"✅ {update_count} Engagement Updates")
        logger.info(f"✅ {risk_count} Risks")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Population failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(populate_database())