#!/usr/bin/env python
"""
Populate database with test data for dashboard
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_async_session, init_db
from src.models.talent import Talent
from src.models.engagement import Engagement, EngagementStatus
from src.models.project import Project, ProjectStatus


async def populate_test_data():
    """Add test data to database"""
    
    # Initialize database
    await init_db()
    
    async with get_async_session() as session:
        try:
            # Create test talents
            talents = [
                Talent(
                    name="Alice Johnson",
                    email="alice@example.com",
                    phone="+1234567890",
                    skills=["Python", "React", "AWS"],
                    location="San Francisco",
                    rate=150.0,
                    experience_years=5,
                    linkedin_url="https://linkedin.com/in/alice",
                    github_url="https://github.com/alice",
                    availability_status="available",
                    resume_url="https://example.com/alice-resume.pdf"
                ),
                Talent(
                    name="Bob Smith",
                    email="bob@example.com",
                    phone="+1234567891",
                    skills=["Java", "Spring", "Kubernetes"],
                    location="New York",
                    rate=175.0,
                    experience_years=7,
                    linkedin_url="https://linkedin.com/in/bob",
                    github_url="https://github.com/bob",
                    availability_status="available",
                    resume_url="https://example.com/bob-resume.pdf"
                ),
                Talent(
                    name="Carol Davis",
                    email="carol@example.com",
                    phone="+1234567892",
                    skills=["Data Science", "ML", "Python"],
                    location="Austin",
                    rate=200.0,
                    experience_years=6,
                    linkedin_url="https://linkedin.com/in/carol",
                    availability_status="busy",
                    resume_url="https://example.com/carol-resume.pdf"
                ),
                Talent(
                    name="David Wilson",
                    email="david@example.com",
                    phone="+1234567893",
                    skills=["DevOps", "AWS", "Terraform"],
                    location="Seattle",
                    rate=160.0,
                    experience_years=4,
                    availability_status="available"
                ),
                Talent(
                    name="Emma Martinez",
                    email="emma@example.com",
                    phone="+1234567894",
                    skills=["UI/UX", "Figma", "React"],
                    location="Los Angeles",
                    rate=140.0,
                    experience_years=3,
                    availability_status="available"
                )
            ]
            
            for talent in talents:
                session.add(talent)
            
            await session.flush()
            
            # Create test projects
            projects = [
                Project(
                    name="E-Commerce Platform Redesign",
                    description="Complete redesign of our e-commerce platform with modern UI/UX",
                    status=ProjectStatus.ACTIVE,
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now() + timedelta(days=60),
                    budget=500000.0,
                    client_name="TechCorp Inc",
                    required_skills=["React", "Python", "AWS", "UI/UX"]
                ),
                Project(
                    name="AI Customer Service Bot",
                    description="Implement AI-powered customer service chatbot",
                    status=ProjectStatus.ACTIVE,
                    start_date=datetime.now() - timedelta(days=15),
                    end_date=datetime.now() + timedelta(days=75),
                    budget=250000.0,
                    client_name="ServicePro LLC",
                    required_skills=["Python", "ML", "NLP", "AWS"]
                ),
                Project(
                    name="Mobile Banking App",
                    description="Develop secure mobile banking application",
                    status=ProjectStatus.PLANNING,
                    start_date=datetime.now() + timedelta(days=15),
                    end_date=datetime.now() + timedelta(days=120),
                    budget=750000.0,
                    client_name="FirstBank",
                    required_skills=["React Native", "Java", "Security", "DevOps"]
                ),
                Project(
                    name="Data Analytics Dashboard",
                    description="Build real-time analytics dashboard for business metrics",
                    status=ProjectStatus.COMPLETED,
                    start_date=datetime.now() - timedelta(days=90),
                    end_date=datetime.now() - timedelta(days=10),
                    budget=150000.0,
                    client_name="DataViz Corp",
                    required_skills=["Python", "React", "D3.js", "PostgreSQL"]
                ),
                Project(
                    name="Cloud Migration Initiative",
                    description="Migrate on-premise infrastructure to AWS cloud",
                    status=ProjectStatus.ACTIVE,
                    start_date=datetime.now() - timedelta(days=45),
                    end_date=datetime.now() + timedelta(days=45),
                    budget=350000.0,
                    client_name="LegacySystems Inc",
                    required_skills=["AWS", "DevOps", "Terraform", "Kubernetes"]
                )
            ]
            
            for project in projects:
                session.add(project)
            
            await session.flush()
            
            # Create test engagements
            engagements = [
                Engagement(
                    talent_id=talents[0].id,
                    project_id=projects[0].id,
                    role="Senior Frontend Developer",
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now() + timedelta(days=60),
                    status=EngagementStatus.ACTIVE,
                    hourly_rate=150.0,
                    hours_per_week=40
                ),
                Engagement(
                    talent_id=talents[2].id,
                    project_id=projects[1].id,
                    role="ML Engineer",
                    start_date=datetime.now() - timedelta(days=15),
                    end_date=datetime.now() + timedelta(days=75),
                    status=EngagementStatus.ACTIVE,
                    hourly_rate=200.0,
                    hours_per_week=40
                ),
                Engagement(
                    talent_id=talents[3].id,
                    project_id=projects[4].id,
                    role="DevOps Lead",
                    start_date=datetime.now() - timedelta(days=45),
                    end_date=datetime.now() + timedelta(days=45),
                    status=EngagementStatus.ACTIVE,
                    hourly_rate=160.0,
                    hours_per_week=40
                ),
                Engagement(
                    talent_id=talents[1].id,
                    project_id=projects[0].id,
                    role="Backend Developer",
                    start_date=datetime.now() - timedelta(days=25),
                    end_date=datetime.now() + timedelta(days=60),
                    status=EngagementStatus.ACTIVE,
                    hourly_rate=175.0,
                    hours_per_week=40
                ),
                Engagement(
                    talent_id=talents[4].id,
                    project_id=projects[3].id,
                    role="UI/UX Designer",
                    start_date=datetime.now() - timedelta(days=90),
                    end_date=datetime.now() - timedelta(days=10),
                    status=EngagementStatus.COMPLETED,
                    hourly_rate=140.0,
                    hours_per_week=30
                )
            ]
            
            for engagement in engagements:
                session.add(engagement)
            
            # Commit all data
            await session.commit()
            
            print("✅ Test data populated successfully!")
            print(f"   - {len(talents)} talents added")
            print(f"   - {len(projects)} projects added")
            print(f"   - {len(engagements)} engagements added")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error populating test data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(populate_test_data())