#!/usr/bin/env python3
"""
Minimal database population script for Convergio
Matches actual database schema
"""

import asyncio
import random
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
import structlog
from passlib.context import CryptContext

logger = structlog.get_logger()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/convergio_db")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Sample data
FIRST_NAMES = ["Marco", "Sofia", "Alessandro", "Giulia", "Lorenzo", "Chiara", "Matteo", "Emma", "Francesco", "Alice"]
LAST_NAMES = ["Rossi", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Ferrari", "Esposito", "Bruno", "Gallo"]


async def populate_database():
    """Main function to populate the database"""
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        logger.info("🚀 Starting minimal database population...")
        
        # Create talents (matching actual schema)
        logger.info("Creating talents...")
        talent_ids = []
        
        for i in range(10):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            
            # Hash a default password
            password_hash = pwd_context.hash("password123")
            
            result = await conn.fetchrow(
                """INSERT INTO talents (
                    first_name, last_name, email, password_hash, is_admin,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7
                ) RETURNING id""",
                first_name,
                last_name,
                email,
                password_hash,
                False,
                datetime.now(),
                datetime.now()
            )
            
            talent_ids.append(result['id'])
            logger.info(f"Created talent: {first_name} {last_name} ({email})")
        
        logger.info(f"✅ Created {len(talent_ids)} talents")
        
        # Check what other tables exist
        tables_query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """
        tables = await conn.fetch(tables_query)
        
        logger.info("Available tables in database:")
        for table in tables:
            logger.info(f"  - {table['tablename']}")
        
        # Create studios if table exists
        if any(t['tablename'] == 'studios' for t in tables):
            logger.info("Creating studios...")
            
            studio_names = ["Design Studio", "Engineering Hub", "Product Lab", "Innovation Center", "Data Science Team"]
            
            for name in studio_names[:3]:
                await conn.execute(
                    """INSERT INTO studios (
                        name, description, studio_lead_id, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5
                    )""",
                    name,
                    f"A creative workspace focused on {name.lower()}",
                    random.choice(talent_ids),
                    datetime.now(),
                    datetime.now()
                )
            
            logger.info("✅ Created 3 studios")
        
        # Create talent_skills if table exists
        if any(t['tablename'] == 'talent_skills' for t in tables):
            logger.info("Creating talent skills...")
            
            skills = ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "AWS", "TypeScript"]
            
            for talent_id in talent_ids[:5]:
                # Add 2-4 skills per talent
                talent_skills = random.sample(skills, random.randint(2, 4))
                for skill in talent_skills:
                    await conn.execute(
                        """INSERT INTO talent_skills (
                            talent_id, skill_name, proficiency_level, created_at
                        ) VALUES (
                            $1, $2, $3, $4
                        ) ON CONFLICT DO NOTHING""",
                        talent_id,
                        skill,
                        random.choice(['beginner', 'intermediate', 'advanced', 'expert']),
                        datetime.now()
                    )
            
            logger.info("✅ Created talent skills")
        
        # Create conversations if table exists
        if any(t['tablename'] == 'conversations' for t in tables):
            logger.info("Creating conversations...")
            
            conversation_topics = [
                "Project Planning Discussion",
                "Technical Architecture Review",
                "Budget Analysis Meeting",
                "Performance Optimization Strategy",
                "Team Coordination Update"
            ]
            
            for topic in conversation_topics:
                await conn.execute(
                    """INSERT INTO conversations (
                        user_id, conversation_topic, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4
                    ) ON CONFLICT DO NOTHING""",
                    f"user_{random.randint(1, 100)}",
                    topic,
                    datetime.now(),
                    datetime.now()
                )
            
            logger.info("✅ Created conversations")
        
        logger.info("🎉 Minimal database population completed successfully!")
        
    except Exception as e:
        logger.error(f"Population failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(populate_database())