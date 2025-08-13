#!/usr/bin/env python3
"""
Final working database population script for Convergio
Uses raw SQL for maximum compatibility
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
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
FIRST_NAMES = ["Marco", "Sofia", "Alessandro", "Giulia", "Lorenzo", "Chiara", "Matteo", "Emma", "Francesco", "Alice"]
LAST_NAMES = ["Rossi", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Ferrari", "Esposito", "Bruno", "Gallo"]
COMPANIES = ["TechCorp Italia", "Digital Solutions", "Innovate Milano", "Future Systems", "Data Dynamics"]
SKILLS = ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "Kubernetes", "AWS", "Azure", 
          "Machine Learning", "Data Science", "DevOps", "Agile", "TypeScript", "Go"]
DEPARTMENTS = ["Engineering", "Product", "Design", "Marketing", "Sales", "HR", "Finance", "Operations", "Data"]
PROJECT_TYPES = ["web_development", "data_analysis", "marketing_campaign", "business_strategy", "security_audit"]


async def populate_database():
    """Main function to populate the database using asyncpg"""
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Starting database population...")
        
        # Create talents
        logger.info("Creating talents...")
        talent_ids = []
        for i in range(10):
            talent_id = str(uuid.uuid4())
            talent_ids.append(talent_id)
            
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            skills = json.dumps(random.sample(SKILLS, random.randint(3, 7)))
            metadata = json.dumps({
                'languages': ['Italian', 'English'],
                'interests': ['AI/ML', 'Cloud']
            })
            
            await conn.execute(
                """INSERT INTO talents (
                    id, first_name, last_name, email, phone, location, department, role,
                    skills, experience_years, bio, is_active, rating, metadata,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9::jsonb, $10, $11, $12, $13, $14::jsonb,
                    $15, $16
                )""",
                talent_id,
                first_name,
                last_name,
                f"{first_name.lower()}.{last_name.lower()}@example.com",
                f"+39 {random.randint(300, 399)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
                random.choice(["Milano", "Roma", "Torino", "Napoli"]),
                random.choice(DEPARTMENTS),
                f"{random.choice(['Junior', 'Senior', 'Lead'])} Developer",
                skills,
                random.randint(1, 10),
                f"Experienced {first_name} with passion for technology",
                True,
                round(random.uniform(3.5, 5.0), 1),
                metadata,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            )
        
        logger.info(f"✅ Created {len(talent_ids)} talents")
        
        # Create projects
        logger.info("Creating projects...")
        project_ids = []
        for i in range(10):
            project_id = str(uuid.uuid4())
            project_ids.append(project_id)
            
            requirements = json.dumps([f"Requirement {j+1}" for j in range(3)])
            deliverables = json.dumps([f"Deliverable {j+1}" for j in range(3)])
            risks = json.dumps([{'type': 'technical', 'description': 'Technical risk'}])
            metadata = json.dumps({'technologies': random.sample(SKILLS, 3)})
            
            await conn.execute(
                """INSERT INTO projects (
                    id, name, description, type, status, priority, client_name,
                    budget, team_size, progress_percentage, requirements, deliverables,
                    risks, metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7,
                    $8, $9, $10, $11::jsonb, $12::jsonb,
                    $13::jsonb, $14::jsonb, $15, $16
                )""",
                project_id,
                f"Project {random.choice(['Alpha', 'Beta', 'Gamma'])} {i+1}",
                f"Strategic project for digital transformation",
                random.choice(PROJECT_TYPES),
                random.choice(['planning', 'in_progress', 'completed']),
                random.choice(['low', 'medium', 'high']),
                random.choice(COMPANIES),
                random.randint(10000, 100000),
                random.randint(3, 10),
                random.randint(0, 100),
                requirements,
                deliverables,
                risks,
                metadata,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            )
        
        logger.info(f"✅ Created {len(project_ids)} projects")
        
        # Create conversations
        logger.info("Creating conversations...")
        conversation_ids = []
        agent_names = ['ali_chief_of_staff', 'amy_cfo', 'baccio_tech_architect', 'davide_project_manager']
        
        for i in range(10):
            conversation_id = str(uuid.uuid4())
            conversation_ids.append(conversation_id)
            
            messages = json.dumps([
                {
                    'role': 'user',
                    'content': f'Question {j+1} about the project',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                } for j in range(3)
            ])
            agents_used = json.dumps(random.sample(agent_names, 2))
            metadata = json.dumps({'satisfaction_score': random.randint(3, 5)})
            
            await conn.execute(
                """INSERT INTO conversations (
                    id, user_id, title, messages, agents_used, turn_count,
                    total_tokens, total_cost, duration_seconds, status, mode,
                    metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4::jsonb, $5::jsonb, $6,
                    $7, $8, $9, $10, $11,
                    $12::jsonb, $13, $14
                )""",
                conversation_id,
                f"user_{random.randint(1, 10)}",
                f"Discussion about {random.choice(['Project', 'Budget', 'Strategy'])}",
                messages,
                agents_used,
                3,
                random.randint(500, 2000),
                round(random.uniform(0.01, 0.10), 4),
                random.randint(30, 180),
                'completed',
                'autogen',
                metadata,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            )
        
        logger.info(f"✅ Created {len(conversation_ids)} conversations")
        
        # Create documents
        logger.info("Creating documents...")
        document_ids = []
        for i in range(10):
            document_id = str(uuid.uuid4())
            document_ids.append(document_id)
            
            metadata = json.dumps({
                'author': f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                'tags': ['important', 'draft']
            })
            
            await conn.execute(
                """INSERT INTO documents (
                    id, title, content, type, source, metadata,
                    project_id, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6::jsonb,
                    $7, $8, $9
                )""",
                document_id,
                f"Document {i+1} - Technical Specification",
                f"This is the content of document {i+1} containing important project information.",
                'technical_spec',
                'generated',
                metadata,
                random.choice(project_ids) if random.choice([True, False]) else None,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            )
        
        logger.info(f"✅ Created {len(document_ids)} documents")
        
        # Create project assignments
        logger.info("Creating project assignments...")
        assignments_created = 0
        for project_id in project_ids[:5]:  # Assign to first 5 projects
            num_talents = random.randint(2, 4)
            assigned_talents = random.sample(talent_ids, min(num_talents, len(talent_ids)))
            
            for talent_id in assigned_talents:
                metadata = json.dumps({'hours_logged': random.randint(10, 100)})
                
                await conn.execute(
                    """INSERT INTO project_assignments (
                        id, project_id, talent_id, role, allocation_percentage,
                        start_date, is_active, metadata, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5,
                        $6, $7, $8::jsonb, $9, $10
                    )""",
                    str(uuid.uuid4()),
                    project_id,
                    talent_id,
                    random.choice(['Developer', 'Designer', 'Manager']),
                    random.choice([50, 75, 100]),
                    datetime.now(timezone.utc),
                    True,
                    metadata,
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc)
                )
                assignments_created += 1
        
        logger.info(f"✅ Created {assignments_created} project assignments")
        
        # Create agent interactions
        logger.info("Creating agent interactions...")
        for i in range(10):
            metadata = json.dumps({'confidence': round(random.uniform(0.7, 1.0), 2)})
            
            await conn.execute(
                """INSERT INTO agent_interactions (
                    id, agent_id, user_id, interaction_type, request, response,
                    tokens_used, response_time_ms, success, metadata, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10::jsonb, $11
                )""",
                str(uuid.uuid4()),
                random.choice(agent_names),
                f"user_{random.randint(1, 10)}",
                random.choice(['query', 'analysis', 'report']),
                f"Request {i+1}: Please analyze the project data",
                f"Response {i+1}: Based on my analysis, the project is on track",
                random.randint(100, 1000),
                random.randint(500, 3000),
                True,
                metadata,
                datetime.now(timezone.utc)
            )
        
        logger.info("✅ Created 10 agent interactions")
        
        # Create engagement metrics
        logger.info("Creating engagement metrics...")
        for i in range(10):
            event_data = json.dumps({
                'page': random.choice(['/dashboard', '/projects', '/talents']),
                'action': random.choice(['view', 'click', 'scroll']),
                'duration_seconds': random.randint(5, 300)
            })
            
            await conn.execute(
                """INSERT INTO engagement_metrics (
                    id, user_id, event_type, event_data, session_id, timestamp
                ) VALUES (
                    $1, $2, $3, $4::jsonb, $5, $6
                )""",
                str(uuid.uuid4()),
                f"user_{random.randint(1, 10)}",
                random.choice(['page_view', 'click', 'interaction']),
                event_data,
                f"session_{random.randint(1000, 9999)}",
                datetime.now(timezone.utc)
            )
        
        logger.info("✅ Created 10 engagement metrics")
        
        logger.info("🎉 Database population completed successfully!")
        
    except Exception as e:
        logger.error(f"Population failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(populate_database())