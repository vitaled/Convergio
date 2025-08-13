#!/usr/bin/env python3
"""
Populate Convergio database with comprehensive sample data
Creates realistic data for all tables with proper relationships
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
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

# Sample data generators
FIRST_NAMES = ["Marco", "Sofia", "Alessandro", "Giulia", "Lorenzo", "Chiara", "Matteo", "Emma", "Francesco", "Alice", 
                "Giovanni", "Sara", "Andrea", "Laura", "Luca", "Martina", "Davide", "Elena", "Giuseppe", "Valentina"]

LAST_NAMES = ["Rossi", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Ferrari", "Esposito", "Bruno", "Gallo",
              "Conti", "De Luca", "Costa", "Giordano", "Mancini", "Rizzo", "Lombardi", "Moretti", "Barbieri", "Fontana"]

COMPANIES = ["TechCorp Italia", "Digital Solutions", "Innovate Milano", "Future Systems", "Data Dynamics", 
             "Cloud Experts", "AI Innovations", "Software House Roma", "WebDev Torino", "Mobile First"]

SKILLS = ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "Kubernetes", "AWS", "Azure", 
          "Machine Learning", "Data Science", "DevOps", "Agile", "TypeScript", "Go", "Rust", "GraphQL", 
          "MongoDB", "Redis", "FastAPI", "Django", "Vue.js", "Angular", "Flutter", "Swift"]

DEPARTMENTS = ["Engineering", "Product", "Design", "Marketing", "Sales", "HR", "Finance", "Operations", "Data", "Security"]

PROJECT_TYPES = ["web_development", "data_analysis", "marketing_campaign", "business_strategy", "security_audit",
                 "system_architecture", "financial_planning", "product_launch", "mobile_app", "ai_integration"]

PROJECT_STATUSES = ["planning", "in_progress", "review", "completed", "on_hold"]

SENIORITY_LEVELS = ["Junior", "Mid-level", "Senior", "Lead", "Principal", "Staff", "Distinguished"]


class SampleDataGenerator:
    """Generate comprehensive sample data for Convergio"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.talent_ids = []
        self.project_ids = []
        self.conversation_ids = []
        self.document_ids = []
        
    async def populate_all(self):
        """Populate all tables with sample data"""
        try:
            logger.info("🚀 Starting database population...")
            
            # 1. Create talents
            await self.create_talents()
            
            # 2. Create projects
            await self.create_projects()
            
            # 3. Create conversations
            await self.create_conversations()
            
            # 4. Create documents and embeddings
            await self.create_documents_with_embeddings()
            
            # 5. Create memories
            await self.create_memories()
            
            # 6. Create engagement metrics
            await self.create_engagement_metrics()
            
            # 7. Create talent-project assignments
            await self.create_project_assignments()
            
            # 8. Create agent interactions
            await self.create_agent_interactions()
            
            logger.info("✅ Database population completed successfully!")
            
        except Exception as e:
            logger.error(f"Population failed: {e}")
            await self.session.rollback()
            raise
    
    async def create_talents(self, count: int = 15):
        """Create sample talents with comprehensive profiles"""
        logger.info(f"Creating {count} talents...")
        
        for i in range(count):
            talent_id = str(uuid.uuid4())
            self.talent_ids.append(talent_id)
            
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            
            talent_data = {
                'id': talent_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': f"{first_name.lower()}.{last_name.lower()}@{random.choice(COMPANIES).replace(' ', '').lower()}.com",
                'phone': f"+39 {random.randint(300, 399)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
                'location': random.choice(["Milano", "Roma", "Torino", "Napoli", "Bologna", "Firenze", "Venezia", "Genova"]),
                'department': random.choice(DEPARTMENTS),
                'role': f"{random.choice(SENIORITY_LEVELS)} {random.choice(['Developer', 'Engineer', 'Analyst', 'Manager', 'Specialist', 'Architect'])}",
                'skills': json.dumps(random.sample(SKILLS, random.randint(5, 12))),
                'experience_years': random.randint(1, 15),
                'bio': f"Experienced professional with {random.randint(3, 15)} years in the industry. "
                       f"Specializes in {', '.join(random.sample(SKILLS, 3))}. "
                       f"Passionate about technology and innovation.",
                'linkedin_url': f"https://linkedin.com/in/{first_name.lower()}{last_name.lower()}",
                'github_url': f"https://github.com/{first_name.lower()}{last_name.lower()}{random.randint(1, 99)}",
                'portfolio_url': f"https://{first_name.lower()}{last_name.lower()}.dev",
                'availability': random.choice(['immediate', '2_weeks', '1_month', '3_months', 'not_available']),
                'preferred_work_type': random.choice(['remote', 'hybrid', 'onsite']),
                'salary_expectation': random.randint(30000, 120000),
                'is_active': random.choice([True, True, True, False]),  # 75% active
                'rating': round(random.uniform(3.5, 5.0), 1),
                'total_projects': random.randint(0, 20),
                'completed_projects': random.randint(0, 15),
                'metadata': json.dumps({
                    'languages': random.sample(['Italian', 'English', 'Spanish', 'French', 'German'], random.randint(1, 3)),
                    'certifications': random.sample(['AWS Certified', 'Azure Expert', 'Google Cloud', 'PMP', 'Scrum Master'], random.randint(0, 3)),
                    'interests': random.sample(['AI/ML', 'Blockchain', 'IoT', 'Cloud', 'Security', 'DevOps'], random.randint(2, 4))
                }),
                'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365)),
                'updated_at': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
            }
            
            # Insert talent
            query = """
                INSERT INTO talents (
                    id, first_name, last_name, email, phone, location, department, role,
                    skills, experience_years, bio, linkedin_url, github_url, portfolio_url,
                    availability, preferred_work_type, salary_expectation, is_active,
                    rating, total_projects, completed_projects, metadata, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9::jsonb, $10, $11, $12, $13, $14,
                    $15, $16, $17, $18,
                    $19, $20, $21, $22::jsonb, $23, $24
                )
            """
            
            await self.session.execute(
                text(query),
                (
                    talent_data['id'], talent_data['first_name'], talent_data['last_name'],
                    talent_data['email'], talent_data['phone'], talent_data['location'],
                    talent_data['department'], talent_data['role'], talent_data['skills'],
                    talent_data['experience_years'], talent_data['bio'], talent_data['linkedin_url'],
                    talent_data['github_url'], talent_data['portfolio_url'], talent_data['availability'],
                    talent_data['preferred_work_type'], talent_data['salary_expectation'],
                    talent_data['is_active'], talent_data['rating'], talent_data['total_projects'],
                    talent_data['completed_projects'], talent_data['metadata'],
                    talent_data['created_at'], talent_data['updated_at']
                )
            )
        
        await self.session.commit()
        logger.info(f"✅ Created {count} talents")
    
    async def create_projects(self, count: int = 12):
        """Create sample projects with detailed information"""
        logger.info(f"Creating {count} projects...")
        
        for i in range(count):
            project_id = str(uuid.uuid4())
            self.project_ids.append(project_id)
            
            project_name = f"{random.choice(['Project', 'Initiative', 'Program'])} {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta'])} {random.randint(100, 999)}"
            
            start_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))
            duration_days = random.randint(30, 365)
            
            project_data = {
                'id': project_id,
                'name': project_name,
                'description': f"Strategic {random.choice(PROJECT_TYPES).replace('_', ' ')} project focused on "
                              f"delivering {random.choice(['innovative', 'cutting-edge', 'transformative', 'scalable'])} "
                              f"solutions for {random.choice(['customer engagement', 'operational efficiency', 'market expansion', 'digital transformation'])}.",
                'type': random.choice(PROJECT_TYPES),
                'status': random.choice(PROJECT_STATUSES),
                'priority': random.choice(['low', 'medium', 'high', 'critical']),
                'client_name': random.choice(COMPANIES),
                'budget': random.randint(10000, 500000),
                'spent_budget': random.randint(5000, 250000),
                'start_date': start_date,
                'end_date': start_date + timedelta(days=duration_days),
                'actual_end_date': start_date + timedelta(days=duration_days + random.randint(-30, 60)) if random.choice([True, False]) else None,
                'team_size': random.randint(3, 15),
                'progress_percentage': random.randint(0, 100),
                'requirements': json.dumps([
                    f"Requirement {j+1}: {random.choice(['Implement', 'Design', 'Develop', 'Integrate', 'Optimize'])} "
                    f"{random.choice(['system', 'feature', 'module', 'component', 'service'])}"
                    for j in range(random.randint(3, 8))
                ]),
                'deliverables': json.dumps([
                    f"{random.choice(['Technical', 'Business', 'User', 'System'])} "
                    f"{random.choice(['Documentation', 'Report', 'Analysis', 'Design', 'Implementation'])}"
                    for _ in range(random.randint(3, 6))
                ]),
                'risks': json.dumps([
                    {
                        'type': random.choice(['technical', 'budget', 'timeline', 'resource', 'external']),
                        'description': f"{random.choice(['Potential', 'Possible', 'Risk of'])} {random.choice(['delay', 'overrun', 'shortage', 'issue'])}",
                        'mitigation': f"{random.choice(['Monitor', 'Mitigate', 'Plan', 'Prepare'])} {random.choice(['closely', 'regularly', 'proactively'])}"
                    }
                    for _ in range(random.randint(2, 5))
                ]),
                'metadata': json.dumps({
                    'technologies': random.sample(SKILLS, random.randint(3, 8)),
                    'milestones': [f"Milestone {m+1}" for m in range(random.randint(3, 6))],
                    'stakeholders': random.sample(['CEO', 'CTO', 'Product Manager', 'Tech Lead', 'Client', 'Users'], random.randint(2, 4))
                }),
                'created_by': random.choice(self.talent_ids) if self.talent_ids else None,
                'created_at': start_date,
                'updated_at': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7))
            }
            
            # Insert project
            query = text("""
                INSERT INTO projects (
                    id, name, description, type, status, priority, client_name,
                    budget, spent_budget, start_date, end_date, actual_end_date,
                    team_size, progress_percentage, requirements, deliverables,
                    risks, metadata, created_by, created_at, updated_at
                ) VALUES (
                    :id, :name, :description, :type, :status, :priority, :client_name,
                    :budget, :spent_budget, :start_date, :end_date, :actual_end_date,
                    :team_size, :progress_percentage, :requirements::jsonb, :deliverables::jsonb,
                    :risks::jsonb, :metadata::jsonb, :created_by, :created_at, :updated_at
                )
            """)
            
            await self.session.execute(query, project_data)
        
        await self.session.commit()
        logger.info(f"✅ Created {count} projects")
    
    async def create_conversations(self, count: int = 20):
        """Create sample conversations with agents"""
        logger.info(f"Creating {count} conversations...")
        
        agent_names = ['ali_chief_of_staff', 'amy_cfo', 'baccio_tech_architect', 'davide_project_manager',
                      'diana_performance_dashboard', 'luca_security', 'sofia_social_media']
        
        for i in range(count):
            conversation_id = str(uuid.uuid4())
            self.conversation_ids.append(conversation_id)
            
            # Random conversation duration and complexity
            num_messages = random.randint(3, 15)
            agents_involved = random.sample(agent_names, random.randint(1, 4))
            
            messages = []
            for m in range(num_messages):
                messages.append({
                    'role': random.choice(['user', 'assistant']),
                    'content': f"Message {m+1}: {random.choice(['Question about', 'Analysis of', 'Update on', 'Request for'])} "
                              f"{random.choice(['project', 'budget', 'timeline', 'resources', 'performance'])}",
                    'agent': random.choice(agents_involved) if random.choice([True, False]) else None,
                    'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=num_messages-m)).isoformat()
                })
            
            conversation_data = {
                'id': conversation_id,
                'user_id': f"user_{random.randint(1, 100)}",
                'title': f"{random.choice(['Discussion', 'Analysis', 'Planning', 'Review'])} - "
                        f"{random.choice(['Project', 'Budget', 'Strategy', 'Performance'])} "
                        f"{random.choice(['Update', 'Review', 'Planning', 'Analysis'])}",
                'messages': json.dumps(messages),
                'agents_used': json.dumps(agents_involved),
                'turn_count': num_messages,
                'total_tokens': random.randint(500, 5000),
                'total_cost': round(random.uniform(0.01, 0.50), 4),
                'duration_seconds': random.randint(30, 300),
                'status': random.choice(['completed', 'completed', 'completed', 'in_progress', 'error']),
                'mode': random.choice(['autogen', 'streaming', 'graphflow']),
                'metadata': json.dumps({
                    'satisfaction_score': random.randint(1, 5),
                    'helpful': random.choice([True, True, True, False]),
                    'resolved': random.choice([True, True, False]),
                    'tags': random.sample(['urgent', 'technical', 'financial', 'strategic', 'operational'], random.randint(1, 3))
                }),
                'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
                'updated_at': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7))
            }
            
            # Insert conversation
            query = text("""
                INSERT INTO conversations (
                    id, user_id, title, messages, agents_used, turn_count,
                    total_tokens, total_cost, duration_seconds, status, mode,
                    metadata, created_at, updated_at
                ) VALUES (
                    :id, :user_id, :title, :messages::jsonb, :agents_used::jsonb, :turn_count,
                    :total_tokens, :total_cost, :duration_seconds, :status, :mode,
                    :metadata::jsonb, :created_at, :updated_at
                )
            """)
            
            await self.session.execute(query, conversation_data)
        
        await self.session.commit()
        logger.info(f"✅ Created {count} conversations")
    
    async def create_documents_with_embeddings(self, count: int = 15):
        """Create sample documents with embeddings"""
        logger.info(f"Creating {count} documents with embeddings...")
        
        document_types = ['technical_spec', 'project_plan', 'meeting_notes', 'requirements', 'design_doc',
                         'api_documentation', 'user_manual', 'financial_report', 'presentation', 'proposal']
        
        for i in range(count):
            document_id = str(uuid.uuid4())
            self.document_ids.append(document_id)
            
            doc_type = random.choice(document_types)
            
            # Create document
            document_data = {
                'id': document_id,
                'title': f"{doc_type.replace('_', ' ').title()} - {random.choice(['Q1', 'Q2', 'Q3', 'Q4'])} {random.randint(2024, 2025)}",
                'content': f"This is a comprehensive {doc_type.replace('_', ' ')} document containing detailed information about "
                          f"{random.choice(['system architecture', 'project requirements', 'financial metrics', 'technical implementation', 'strategic planning'])}. "
                          f"The document covers {random.choice(['analysis', 'design', 'implementation', 'testing', 'deployment'])} phases and includes "
                          f"{random.choice(['recommendations', 'best practices', 'guidelines', 'specifications', 'metrics'])}.",
                'type': doc_type,
                'source': random.choice(['upload', 'generated', 'imported', 'extracted']),
                'metadata': json.dumps({
                    'author': random.choice(FIRST_NAMES) + ' ' + random.choice(LAST_NAMES),
                    'department': random.choice(DEPARTMENTS),
                    'tags': random.sample(['important', 'draft', 'final', 'review', 'approved', 'confidential'], random.randint(1, 3)),
                    'version': f"{random.randint(1, 3)}.{random.randint(0, 9)}",
                    'file_size': f"{random.randint(100, 5000)} KB"
                }),
                'project_id': random.choice(self.project_ids) if self.project_ids and random.choice([True, False]) else None,
                'created_by': random.choice(self.talent_ids) if self.talent_ids else None,
                'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60)),
                'updated_at': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7))
            }
            
            # Insert document
            query = text("""
                INSERT INTO documents (
                    id, title, content, type, source, metadata,
                    project_id, created_by, created_at, updated_at
                ) VALUES (
                    :id, :title, :content, :type, :source, :metadata::jsonb,
                    :project_id, :created_by, :created_at, :updated_at
                )
            """)
            
            await self.session.execute(query, document_data)
            
            # Create embeddings for document chunks
            num_chunks = random.randint(1, 5)
            for chunk_idx in range(num_chunks):
                # Generate mock embedding (in production, use real embeddings)
                embedding = [random.random() for _ in range(1536)]  # OpenAI embedding dimension
                
                embedding_data = {
                    'id': str(uuid.uuid4()),
                    'document_id': document_id,
                    'chunk_index': chunk_idx,
                    'content': f"Chunk {chunk_idx + 1} of document: {document_data['content'][:200]}...",
                    'embedding': f"[{','.join(map(str, embedding))}]",
                    'metadata': json.dumps({
                        'chunk_size': random.randint(200, 500),
                        'overlap': 50,
                        'method': 'sliding_window'
                    }),
                    'created_at': document_data['created_at']
                }
                
                # Insert embedding
                query = text("""
                    INSERT INTO document_embeddings (
                        id, document_id, chunk_index, content, embedding, metadata, created_at
                    ) VALUES (
                        :id, :document_id, :chunk_index, :content, :embedding::vector, :metadata::jsonb, :created_at
                    )
                """)
                
                await self.session.execute(query, embedding_data)
        
        await self.session.commit()
        logger.info(f"✅ Created {count} documents with embeddings")
    
    async def create_memories(self, count: int = 30):
        """Create sample memories for the unified memory system"""
        logger.info(f"Creating {count} memories...")
        
        memory_types = ['conversation', 'context', 'knowledge', 'preferences', 'document']
        
        for i in range(count):
            memory_type = random.choice(memory_types)
            
            # Generate mock embedding
            embedding = [random.random() for _ in range(1536)]
            
            memory_data = {
                'id': str(uuid.uuid4()),
                'memory_type': memory_type,
                'content': f"Memory of type {memory_type}: {random.choice(['Important insight about', 'Key learning from', 'Observation regarding', 'Fact about'])} "
                          f"{random.choice(['project management', 'team dynamics', 'technical architecture', 'business strategy', 'user preferences'])}. "
                          f"This information is {random.choice(['critical', 'useful', 'relevant', 'important'])} for "
                          f"{random.choice(['future decisions', 'ongoing projects', 'team coordination', 'strategic planning'])}.",
                'embedding': f"[{','.join(map(str, embedding))}]",
                'metadata': json.dumps({
                    'source': random.choice(['conversation', 'document', 'analysis', 'user_input']),
                    'confidence': round(random.uniform(0.7, 1.0), 2),
                    'tags': random.sample(['important', 'actionable', 'reference', 'historical'], random.randint(1, 2))
                }),
                'user_id': f"user_{random.randint(1, 100)}" if random.choice([True, False]) else None,
                'agent_id': random.choice(['ali', 'amy', 'baccio', 'davide']) if random.choice([True, False]) else None,
                'conversation_id': random.choice(self.conversation_ids) if self.conversation_ids and random.choice([True, False]) else None,
                'document_id': random.choice(self.document_ids) if self.document_ids and memory_type == 'document' else None,
                'importance_score': round(random.uniform(0.3, 1.0), 2),
                'access_count': random.randint(0, 50),
                'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                'last_accessed': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7)),
                'expires_at': datetime.now(timezone.utc) + timedelta(days=random.randint(30, 365)) if random.choice([True, False]) else None
            }
            
            # Insert memory
            query = text("""
                INSERT INTO memories (
                    id, memory_type, content, embedding, metadata,
                    user_id, agent_id, conversation_id, document_id,
                    importance_score, access_count, created_at, last_accessed, expires_at
                ) VALUES (
                    :id, :memory_type::memory_type, :content, :embedding::vector, :metadata::jsonb,
                    :user_id, :agent_id, :conversation_id, :document_id,
                    :importance_score, :access_count, :created_at, :last_accessed, :expires_at
                )
            """)
            
            await self.session.execute(query, memory_data)
        
        await self.session.commit()
        logger.info(f"✅ Created {count} memories")
    
    async def create_engagement_metrics(self, count: int = 50):
        """Create sample engagement metrics"""
        logger.info(f"Creating {count} engagement metrics...")
        
        metric_types = ['page_view', 'click', 'conversion', 'session', 'interaction', 'download', 'share']
        sources = ['web', 'mobile', 'api', 'email', 'social']
        
        for i in range(count):
            metric_data = {
                'id': str(uuid.uuid4()),
                'user_id': f"user_{random.randint(1, 100)}",
                'event_type': random.choice(metric_types),
                'event_data': json.dumps({
                    'page': random.choice(['/dashboard', '/projects', '/talents', '/analytics', '/settings']),
                    'action': random.choice(['view', 'click', 'scroll', 'submit', 'download']),
                    'duration_seconds': random.randint(5, 300),
                    'source': random.choice(sources),
                    'device': random.choice(['desktop', 'mobile', 'tablet'])
                }),
                'session_id': f"session_{random.randint(1000, 9999)}",
                'timestamp': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30), 
                                                                    hours=random.randint(0, 23),
                                                                    minutes=random.randint(0, 59))
            }
            
            # Insert metric
            query = text("""
                INSERT INTO engagement_metrics (
                    id, user_id, event_type, event_data, session_id, timestamp
                ) VALUES (
                    :id, :user_id, :event_type, :event_data::jsonb, :session_id, :timestamp
                )
            """)
            
            await self.session.execute(query, metric_data)
        
        await self.session.commit()
        logger.info(f"✅ Created {count} engagement metrics")
    
    async def create_project_assignments(self):
        """Create talent-project assignments"""
        logger.info("Creating project assignments...")
        
        if not self.talent_ids or not self.project_ids:
            logger.warning("No talents or projects to assign")
            return
        
        assignments_created = 0
        roles = ['Developer', 'Designer', 'Analyst', 'Manager', 'Consultant', 'Architect', 'Lead']
        
        for project_id in self.project_ids:
            # Assign 3-8 talents to each project
            num_assignments = random.randint(3, min(8, len(self.talent_ids)))
            assigned_talents = random.sample(self.talent_ids, num_assignments)
            
            for talent_id in assigned_talents:
                assignment_data = {
                    'id': str(uuid.uuid4()),
                    'project_id': project_id,
                    'talent_id': talent_id,
                    'role': random.choice(roles),
                    'allocation_percentage': random.choice([25, 50, 75, 100]),
                    'start_date': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60)),
                    'end_date': datetime.now(timezone.utc) + timedelta(days=random.randint(30, 180)) if random.choice([True, False]) else None,
                    'is_active': random.choice([True, True, True, False]),
                    'performance_rating': round(random.uniform(3.0, 5.0), 1) if random.choice([True, False]) else None,
                    'metadata': json.dumps({
                        'hours_logged': random.randint(10, 200),
                        'tasks_completed': random.randint(5, 50),
                        'contribution_level': random.choice(['high', 'medium', 'low'])
                    }),
                    'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                    'updated_at': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 7))
                }
                
                # Insert assignment
                query = text("""
                    INSERT INTO project_assignments (
                        id, project_id, talent_id, role, allocation_percentage,
                        start_date, end_date, is_active, performance_rating,
                        metadata, created_at, updated_at
                    ) VALUES (
                        :id, :project_id, :talent_id, :role, :allocation_percentage,
                        :start_date, :end_date, :is_active, :performance_rating,
                        :metadata::jsonb, :created_at, :updated_at
                    )
                """)
                
                await self.session.execute(query, assignment_data)
                assignments_created += 1
        
        await self.session.commit()
        logger.info(f"✅ Created {assignments_created} project assignments")
    
    async def create_agent_interactions(self, count: int = 25):
        """Create sample agent interaction logs"""
        logger.info(f"Creating {count} agent interactions...")
        
        agent_names = ['ali_chief_of_staff', 'amy_cfo', 'baccio_tech_architect', 'davide_project_manager',
                      'diana_performance_dashboard', 'luca_security', 'sofia_social_media']
        
        interaction_types = ['query', 'analysis', 'report', 'recommendation', 'alert', 'update']
        
        for i in range(count):
            interaction_data = {
                'id': str(uuid.uuid4()),
                'agent_id': random.choice(agent_names),
                'user_id': f"user_{random.randint(1, 100)}",
                'interaction_type': random.choice(interaction_types),
                'request': f"{random.choice(['Please provide', 'I need', 'Can you give me', 'Show me'])} "
                          f"{random.choice(['analysis of', 'report on', 'update about', 'insights into'])} "
                          f"{random.choice(['project performance', 'financial metrics', 'team productivity', 'system health'])}",
                'response': f"Based on my analysis, {random.choice(['the data shows', 'I found that', 'the metrics indicate', 'the results suggest'])} "
                           f"{random.choice(['positive trends', 'areas for improvement', 'stable performance', 'significant changes'])} in "
                           f"{random.choice(['the requested area', 'key metrics', 'overall performance', 'critical indicators'])}.",
                'tokens_used': random.randint(100, 2000),
                'response_time_ms': random.randint(500, 5000),
                'success': random.choice([True, True, True, True, False]),  # 80% success
                'metadata': json.dumps({
                    'confidence': round(random.uniform(0.7, 1.0), 2),
                    'data_sources': random.sample(['database', 'api', 'cache', 'external'], random.randint(1, 3)),
                    'tools_used': random.sample(['web_search', 'query_talents', 'business_intelligence'], random.randint(1, 2))
                }),
                'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(0, 14),
                                                                    hours=random.randint(0, 23))
            }
            
            # Insert interaction
            query = text("""
                INSERT INTO agent_interactions (
                    id, agent_id, user_id, interaction_type, request, response,
                    tokens_used, response_time_ms, success, metadata, created_at
                ) VALUES (
                    :id, :agent_id, :user_id, :interaction_type, :request, :response,
                    :tokens_used, :response_time_ms, :success, :metadata::jsonb, :created_at
                )
            """)
            
            await self.session.execute(query, interaction_data)
        
        await self.session.commit()
        logger.info(f"✅ Created {count} agent interactions")


async def main():
    """Main function to populate the database"""
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        generator = SampleDataGenerator(session)
        
        # Check if we should clear existing data (default to 'n' for non-interactive)
        clear_data = os.getenv("CLEAR_DATA", "n").lower() == 'y'
        
        if clear_data:
            logger.info("Clearing existing data...")
            
            tables = [
                'agent_interactions',
                'project_assignments', 
                'engagement_metrics',
                'memories',
                'document_embeddings',
                'documents',
                'conversations',
                'projects',
                'talents'
            ]
            
            for table in tables:
                try:
                    await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                    logger.info(f"Cleared table: {table}")
                except Exception as e:
                    logger.warning(f"Could not clear table {table}: {e}")
            
            await session.commit()
        
        # Populate all tables
        await generator.populate_all()
    
    await engine.dispose()
    logger.info("🎉 Database population completed!")


if __name__ == "__main__":
    asyncio.run(main())