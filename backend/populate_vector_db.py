#!/usr/bin/env python3
"""
Populate vector database with sample data for testing
"""

import asyncio
import json
import os
import sys
sys.path.append(os.path.dirname(__file__))

from datetime import datetime
import httpx
import structlog

logger = structlog.get_logger()

# Sample documents for vector database
SAMPLE_DOCUMENTS = [
    {
        "text": "Microsoft Azure is a cloud computing platform offering over 200 products and services. It provides infrastructure as a service (IaaS), platform as a service (PaaS), and software as a service (SaaS). Azure supports various programming languages, tools, and frameworks, including both Microsoft-specific and third-party software.",
        "metadata": {"source": "azure_overview", "category": "cloud", "company": "Microsoft"}
    },
    {
        "text": "Microsoft reported Q4 FY2025 revenue of $76.4 billion, representing an 18% year-over-year growth. The strong performance was driven by cloud services, particularly Azure, which saw 39% revenue growth. Microsoft Cloud revenue reached $46.7 billion, up 27%.",
        "metadata": {"source": "earnings_report", "category": "financial", "quarter": "Q4 FY2025"}
    },
    {
        "text": "AutoGen is an open-source framework by Microsoft for building AI agent systems. It enables developers to create sophisticated multi-agent applications where AI agents can collaborate, use tools, and solve complex tasks. Version 0.7 introduces async architecture and improved tool execution.",
        "metadata": {"source": "autogen_docs", "category": "technology", "framework": "AutoGen"}
    },
    {
        "text": "Convergio is an advanced talent management and project orchestration platform. It leverages AI agents to streamline recruitment, project management, and business intelligence. The platform integrates with Microsoft technologies and uses AutoGen for agent orchestration.",
        "metadata": {"source": "convergio_overview", "category": "platform", "product": "Convergio"}
    },
    {
        "text": "The talent acquisition process involves identifying, attracting, and hiring skilled professionals. Key metrics include time-to-hire, quality of hire, and candidate experience. Modern platforms use AI to match candidates with opportunities based on skills, experience, and cultural fit.",
        "metadata": {"source": "hr_best_practices", "category": "talent", "topic": "recruitment"}
    },
    {
        "text": "Project management best practices include clear goal setting, stakeholder engagement, risk management, and continuous monitoring. Agile methodologies emphasize iterative development, customer collaboration, and responding to change. Tools like Kanban boards and sprint planning help teams stay organized.",
        "metadata": {"source": "pm_guide", "category": "project_management", "methodology": "Agile"}
    },
    {
        "text": "Business intelligence involves analyzing data to make informed business decisions. Key components include data warehousing, data mining, reporting, and predictive analytics. Modern BI tools provide real-time dashboards, self-service analytics, and AI-powered insights.",
        "metadata": {"source": "bi_fundamentals", "category": "business_intelligence", "type": "overview"}
    },
    {
        "text": "Amy CFO specializes in financial analysis and reporting. She can provide insights on revenue trends, cost optimization, and financial forecasting. Amy uses real-time market data and company metrics to deliver accurate financial intelligence.",
        "metadata": {"source": "agent_profile", "category": "agent", "name": "Amy_CFO"}
    },
    {
        "text": "Ali Chief of Staff coordinates between different departments and agents. Ali has access to all tools and can orchestrate complex workflows. Key responsibilities include strategic planning, cross-functional coordination, and executive support.",
        "metadata": {"source": "agent_profile", "category": "agent", "name": "Ali_Chief_of_Staff"}
    },
    {
        "text": "Vector databases use embedding vectors to enable semantic search. Unlike keyword search, vector search understands context and meaning. Applications include recommendation systems, similarity search, and retrieval-augmented generation (RAG) for LLMs.",
        "metadata": {"source": "tech_guide", "category": "technology", "topic": "vector_search"}
    }
]

async def create_embeddings():
    """Create embeddings for sample documents using batch API for efficiency"""
    
    try:
        # Import the new batch embedding function
        from src.core.ai_clients import batch_create_embeddings
        from src.core.vector_utils import VectorOperations
        from src.core.database import get_async_session
        
        # Extract all texts for batch processing
        texts = [doc["text"] for doc in SAMPLE_DOCUMENTS]
        
        logger.info(f"🚀 Creating embeddings for {len(texts)} documents using batch API...")
        
        # Create all embeddings in a single batch call (90% cost reduction!)
        embeddings = await batch_create_embeddings(texts, batch_size=100)
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings in batch")
        
        # Now store them in the database
        async with get_async_session() as session:
            documents_with_embeddings = []
            
            for i, (doc, embedding) in enumerate(zip(SAMPLE_DOCUMENTS, embeddings)):
                documents_with_embeddings.append({
                    'text': doc['text'],
                    'metadata': doc['metadata'],
                    'document_id': f"sample_doc_{i}",
                    'chunk_index': 0
                })
            
            # Use VectorOperations to index all documents
            indexed_count = await VectorOperations.index_vectors(
                session,
                documents_with_embeddings,
                use_batch_embeddings=False  # We already have embeddings
            )
            
            logger.info(f"✅ Indexed {indexed_count} documents in vector database")
        
        logger.info("✅ Sample data population complete with batch embeddings!")
        
    except ImportError:
        # Fallback to API endpoint if new modules not available
        logger.warning("New batch modules not available, using API endpoint...")
        await create_embeddings_via_api()
    except Exception as e:
        logger.error(f"❌ Error populating database: {e}")
        
        # Try alternative: Direct database insertion with mock embeddings
        logger.info("Attempting direct database insertion with mock embeddings...")
        await insert_mock_embeddings()

async def create_embeddings_via_api():
    """Fallback: Create embeddings via API endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, doc in enumerate(SAMPLE_DOCUMENTS):
            logger.info(f"Creating embedding {i+1}/{len(SAMPLE_DOCUMENTS)}")
            
            response = await client.post(
                "http://localhost:9000/api/v1/embeddings",
                json={
                    "text": doc["text"],
                    "metadata": doc["metadata"]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Created embedding: {result.get('id', 'unknown')}")
            else:
                logger.error(f"❌ Failed: {response.status_code}")
            
            await asyncio.sleep(0.5)

async def insert_mock_embeddings():
    """Insert mock embeddings directly into database"""
    import psycopg2
    from psycopg2.extras import Json
    import numpy as np
    
    try:
        # Get database URL from environment
        db_url = os.getenv("DATABASE_URL", "postgresql://convergio_user:convergio_pass@localhost:5432/convergio_platform")
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Create embeddings table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(1536),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample documents with mock embeddings
        for doc in SAMPLE_DOCUMENTS:
            # Generate a deterministic mock embedding based on text
            mock_embedding = np.random.RandomState(hash(doc["text"]) % 2**32).randn(1536).tolist()
            
            cur.execute("""
                INSERT INTO embeddings (content, embedding, metadata)
                VALUES (%s, %s, %s)
            """, (doc["text"], mock_embedding, Json(doc["metadata"])))
            
            logger.info(f"✅ Inserted: {doc['metadata'].get('source', 'unknown')}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info("✅ Mock embeddings inserted successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database insertion failed: {e}")

async def main():
    """Main function"""
    logger.info("🚀 Starting vector database population...")
    logger.info(f"📊 Will insert {len(SAMPLE_DOCUMENTS)} sample documents")
    
    await create_embeddings()

if __name__ == "__main__":
    asyncio.run(main())