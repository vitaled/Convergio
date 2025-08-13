#!/usr/bin/env python3
"""
Simple database population script for Convergio
Uses direct SQL execution for compatibility
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

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/convergio_db")

# Sample data
FIRST_NAMES = ["Marco", "Sofia", "Alessandro", "Giulia", "Lorenzo", "Chiara", "Matteo", "Emma", "Francesco", "Alice"]
LAST_NAMES = ["Rossi", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Ferrari", "Esposito", "Bruno", "Gallo"]
COMPANIES = ["TechCorp Italia", "Digital Solutions", "Innovate Milano", "Future Systems", "Data Dynamics"]
SKILLS = ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "Kubernetes", "AWS", "Azure", 
          "Machine Learning", "Data Science", "DevOps", "Agile", "TypeScript", "Go"]
DEPARTMENTS = ["Engineering", "Product", "Design", "Marketing", "Sales", "HR", "Finance", "Operations", "Data"]
PROJECT_TYPES = ["web_development", "data_analysis", "marketing_campaign", "business_strategy", "security_audit"]


async def populate_database():
    """Main function to populate the database"""
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
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
                
                await session.execute(
                    text("""INSERT INTO talents (
                        id, first_name, last_name, email, phone, location, department, role,
                        skills, experience_years, bio, is_active, rating, metadata,
                        created_at, updated_at
                    ) VALUES (
                        :id, :first_name, :last_name, :email, :phone, :location, :department, :role,
                        :skills::jsonb, :experience_years, :bio, :is_active, :rating, :metadata::jsonb,
                        :created_at, :updated_at
                    )"""), {
                        'id': talent_id,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': f"{first_name.lower()}.{last_name.lower()}@example.com",
                        'phone': f"+39 {random.randint(300, 399)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
                        'location': random.choice(["Milano", "Roma", "Torino", "Napoli"]),
                        'department': random.choice(DEPARTMENTS),
                        'role': f"{random.choice(['Junior', 'Senior', 'Lead'])} Developer",
                        'skills': skills,
                        'experience_years': random.randint(1, 10),
                        'bio': f"Experienced {first_name} with passion for technology",
                        'is_active': True,
                        'rating': round(random.uniform(3.5, 5.0), 1),
                        'metadata': metadata,
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                )
            
            await session.commit()
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
                
                await session.execute(
                    text("""INSERT INTO projects (
                        id, name, description, type, status, priority, client_name,
                        budget, team_size, progress_percentage, requirements, deliverables,
                        risks, metadata, created_at, updated_at
                    ) VALUES (
                        :id, :name, :description, :type, :status, :priority, :client_name,
                        :budget, :team_size, :progress_percentage, :requirements::jsonb, :deliverables::jsonb,
                        :risks::jsonb, :metadata::jsonb, :created_at, :updated_at
                    )"""), {
                        'id': project_id,
                        'name': f"Project {random.choice(['Alpha', 'Beta', 'Gamma'])} {i+1}",
                        'description': f"Strategic project for digital transformation",
                        'type': random.choice(PROJECT_TYPES),
                        'status': random.choice(['planning', 'in_progress', 'completed']),
                        'priority': random.choice(['low', 'medium', 'high']),
                        'client_name': random.choice(COMPANIES),
                        'budget': random.randint(10000, 100000),
                        'team_size': random.randint(3, 10),
                        'progress_percentage': random.randint(0, 100),
                        'requirements': requirements,
                        'deliverables': deliverables,
                        'risks': risks,
                        'metadata': metadata,
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                )
            
            await session.commit()
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
                
                await session.execute(
                    text("""INSERT INTO conversations (
                        id, user_id, title, messages, agents_used, turn_count,
                        total_tokens, total_cost, duration_seconds, status, mode,
                        metadata, created_at, updated_at
                    ) VALUES (
                        :id, :user_id, :title, :messages::jsonb, :agents_used::jsonb, :turn_count,
                        :total_tokens, :total_cost, :duration_seconds, :status, :mode,
                        :metadata::jsonb, :created_at, :updated_at
                    )"""), {
                        'id': conversation_id,
                        'user_id': f"user_{random.randint(1, 10)}",
                        'title': f"Discussion about {random.choice(['Project', 'Budget', 'Strategy'])}",
                        'messages': messages,
                        'agents_used': agents_used,
                        'turn_count': 3,
                        'total_tokens': random.randint(500, 2000),
                        'total_cost': round(random.uniform(0.01, 0.10), 4),
                        'duration_seconds': random.randint(30, 180),
                        'status': 'completed',
                        'mode': 'autogen',
                        'metadata': metadata,
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                )
            
            await session.commit()
            logger.info(f"✅ Created {len(conversation_ids)} conversations")
            
            # Create documents (without embeddings for simplicity)
            logger.info("Creating documents...")
            document_ids = []
            for i in range(10):
                document_id = str(uuid.uuid4())
                document_ids.append(document_id)
                
                metadata = json.dumps({
                    'author': f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                    'tags': ['important', 'draft']
                })
                
                await session.execute(
                    text("""INSERT INTO documents (
                        id, title, content, type, source, metadata,
                        project_id, created_at, updated_at
                    ) VALUES (
                        :id, :title, :content, :type, :source, :metadata::jsonb,
                        :project_id, :created_at, :updated_at
                    )"""), {
                        'id': document_id,
                        'title': f"Document {i+1} - Technical Specification",
                        'content': f"This is the content of document {i+1} containing important project information.",
                        'type': 'technical_spec',
                        'source': 'generated',
                        'metadata': metadata,
                        'project_id': random.choice(project_ids) if random.choice([True, False]) else None,
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                )
            
            await session.commit()
            logger.info(f"✅ Created {len(document_ids)} documents")
            
            # Create project assignments
            logger.info("Creating project assignments...")
            assignments_created = 0
            for project_id in project_ids[:5]:  # Assign to first 5 projects
                num_talents = random.randint(2, 4)
                assigned_talents = random.sample(talent_ids, min(num_talents, len(talent_ids)))
                
                for talent_id in assigned_talents:
                    metadata = json.dumps({'hours_logged': random.randint(10, 100)})
                    
                    await session.execute(
                        text("""INSERT INTO project_assignments (
                            id, project_id, talent_id, role, allocation_percentage,
                            start_date, is_active, metadata, created_at, updated_at
                        ) VALUES (
                            :id, :project_id, :talent_id, :role, :allocation_percentage,
                            :start_date, :is_active, :metadata::jsonb, :created_at, :updated_at
                        )"""), {
                            'id': str(uuid.uuid4()),
                            'project_id': project_id,
                            'talent_id': talent_id,
                            'role': random.choice(['Developer', 'Designer', 'Manager']),
                            'allocation_percentage': random.choice([50, 75, 100]),
                            'start_date': datetime.now(timezone.utc),
                            'is_active': True,
                            'metadata': metadata,
                            'created_at': datetime.now(timezone.utc),
                            'updated_at': datetime.now(timezone.utc)
                        }
                    )
                    assignments_created += 1
            
            await session.commit()
            logger.info(f"✅ Created {assignments_created} project assignments")
            
            # Create agent interactions
            logger.info("Creating agent interactions...")
            for i in range(10):
                metadata = json.dumps({'confidence': round(random.uniform(0.7, 1.0), 2)})
                
                await session.execute(
                    text("""INSERT INTO agent_interactions (
                        id, agent_id, user_id, interaction_type, request, response,
                        tokens_used, response_time_ms, success, metadata, created_at
                    ) VALUES (
                        :id, :agent_id, :user_id, :interaction_type, :request, :response,
                        :tokens_used, :response_time_ms, :success, :metadata::jsonb, :created_at
                    )"""), {
                        'id': str(uuid.uuid4()),
                        'agent_id': random.choice(agent_names),
                        'user_id': f"user_{random.randint(1, 10)}",
                        'interaction_type': random.choice(['query', 'analysis', 'report']),
                        'request': f"Request {i+1}: Please analyze the project data",
                        'response': f"Response {i+1}: Based on my analysis, the project is on track",
                        'tokens_used': random.randint(100, 1000),
                        'response_time_ms': random.randint(500, 3000),
                        'success': True,
                        'metadata': metadata,
                        'created_at': datetime.now(timezone.utc)
                    }
                )
            
            await session.commit()
            logger.info("✅ Created 10 agent interactions")
            
            logger.info("🎉 Database population completed successfully!")
            
        except Exception as e:
            logger.error(f"Population failed: {e}")
            await session.rollback()
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(populate_database())