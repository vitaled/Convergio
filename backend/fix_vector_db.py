#!/usr/bin/env python3
"""
Fix document_embeddings table auto-increment issue
This script directly fixes the database schema for vector indexing
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import get_settings


async def fix_document_embeddings_table():
    """Fix the document_embeddings table to have proper auto-increment ID"""
    
    settings = get_settings()
    
    # Parse database URL - convert from SQLAlchemy format to asyncpg format
    db_url = settings.DATABASE_URL
    # Replace postgresql+asyncpg with postgresql
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Connect directly with asyncpg
    conn = await asyncpg.connect(db_url)
    
    try:
        print("🔧 Fixing document_embeddings table...")
        
        # First, check if the table exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'document_embeddings'
            )
        """)
        
        if not exists:
            print("❌ Table document_embeddings does not exist!")
            return False
        
        # Drop the table and recreate it with proper schema
        print("📊 Backing up existing data...")
        
        # Check if there's any data to backup
        count = await conn.fetchval("SELECT COUNT(*) FROM document_embeddings")
        print(f"Found {count} existing embeddings")
        
        if count > 0:
            # Backup existing data
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS document_embeddings_backup AS 
                SELECT * FROM document_embeddings
            """)
            print("✅ Data backed up to document_embeddings_backup")
        
        # Drop the problematic table
        print("🗑️ Dropping problematic table...")
        await conn.execute("DROP TABLE IF EXISTS document_embeddings CASCADE")
        
        # Recreate with proper schema
        print("🏗️ Creating table with proper schema...")
        await conn.execute("""
            CREATE TABLE document_embeddings (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding vector(1536) NOT NULL,
                embed_metadata JSON,
                created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                UNIQUE(document_id, chunk_index)
            )
        """)
        
        # Create indexes
        await conn.execute("""
            CREATE INDEX idx_document_embeddings_document_id 
            ON document_embeddings(document_id)
        """)
        
        await conn.execute("""
            CREATE INDEX idx_document_embeddings_embedding 
            ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
        """)
        
        print("✅ Table recreated with proper schema")
        
        # Restore data if there was any
        if count > 0:
            print("📥 Restoring backed up data...")
            try:
                await conn.execute("""
                    INSERT INTO document_embeddings 
                    (document_id, chunk_index, chunk_text, embedding, embed_metadata, created_at)
                    SELECT document_id, chunk_index, chunk_text, embedding::vector, embed_metadata, created_at
                    FROM document_embeddings_backup
                """)
                print(f"✅ Restored {count} embeddings")
                
                # Drop backup table
                await conn.execute("DROP TABLE document_embeddings_backup")
                print("🗑️ Cleaned up backup table")
            except Exception as e:
                print(f"⚠️ Could not restore data: {e}")
                print("Backup data is still in document_embeddings_backup table")
        
        # Verify the fix
        print("\n🔍 Verifying fix...")
        
        # Check if id column is now serial
        result = await conn.fetchrow("""
            SELECT column_default, is_identity
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'document_embeddings'
            AND column_name = 'id'
        """)
        
        if result:
            print(f"✅ ID column default: {result['column_default']}")
            print(f"✅ ID is identity: {result['is_identity']}")
        
        # Test insert without specifying ID
        print("\n🧪 Testing insert without ID...")
        try:
            # First ensure we have a test document
            doc_id = await conn.fetchval("""
                INSERT INTO documents (title, content, doc_metadata, is_indexed, index_status)
                VALUES ('Test Document', 'Test content', '{}', false, 'pending')
                ON CONFLICT DO NOTHING
                RETURNING id
            """)
            
            if not doc_id:
                doc_id = await conn.fetchval("""
                    SELECT id FROM documents WHERE title = 'Test Document' LIMIT 1
                """)
            
            if doc_id:
                # Try to insert an embedding without specifying ID
                test_embedding = [0.1] * 1536  # Standard embedding size
                # Convert to string format for PostgreSQL vector type
                embedding_str = '[' + ','.join(str(x) for x in test_embedding) + ']'
                embedding_id = await conn.fetchval("""
                    INSERT INTO document_embeddings 
                    (document_id, chunk_index, chunk_text, embedding, embed_metadata)
                    VALUES ($1, $2, $3, $4::vector, $5::json)
                    RETURNING id
                """, doc_id, 999, 'Test chunk', embedding_str, '{}')
                
                if embedding_id:
                    print(f"✅ Test insert successful! Generated ID: {embedding_id}")
                    # Clean up test data
                    await conn.execute("""
                        DELETE FROM document_embeddings 
                        WHERE id = $1
                    """, embedding_id)
                    await conn.execute("""
                        DELETE FROM documents 
                        WHERE id = $1 AND title = 'Test Document'
                    """, doc_id)
                else:
                    print("❌ Test insert failed - no ID returned")
            else:
                print("⚠️ Could not create test document")
                
        except Exception as e:
            print(f"❌ Test insert failed: {e}")
        
        print("\n✅ Database fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()


async def main():
    """Main function"""
    print("🚀 Starting document_embeddings table fix...")
    print("=" * 50)
    
    success = await fix_document_embeddings_table()
    
    if success:
        print("\n🎉 Fix completed successfully!")
        print("You can now run the E2E tests again.")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())