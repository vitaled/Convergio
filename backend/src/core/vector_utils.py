"""
Unified Vector Operations and Similarity Search
Centralizes all vector operations with pgvector optimization
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class VectorOperations:
    """
    Centralized vector operations with pgvector optimization.
    Single source of truth for all similarity calculations.
    """
    
    @staticmethod
    def convert_to_pgvector(embedding: List[float]) -> str:
        """
        Convert embedding list to pgvector format string.
        
        Args:
            embedding: List of float values
        
        Returns:
            PostgreSQL vector string format '[0.1,0.2,...]'
        """
        if not embedding:
            return None
        
        # Ensure it's a list of floats
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        # Format for pgvector
        return f"[{','.join(map(str, embedding))}]"
    
    @staticmethod
    def normalize_vector(vector: List[float]) -> List[float]:
        """
        Normalize vector to unit length for cosine similarity.
        
        Args:
            vector: Input vector
        
        Returns:
            Normalized vector
        """
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return (np.array(vector) / norm).tolist()
    
    @staticmethod
    async def similarity_search(
        session: AsyncSession,
        query_vector: List[float],
        table_name: str = "document_embeddings",
        vector_column: str = "embedding",
        limit: int = 5,
        threshold: float = 0.7,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using pgvector with a single SQL query.
        NO NumPy recalculation - trust pgvector's native operators.
        
        Args:
            session: Database session
            query_vector: Query embedding vector
            table_name: Table to search in
            vector_column: Column containing vectors
            limit: Maximum results to return
            threshold: Minimum similarity threshold (0-1)
            metadata_filters: Optional filters on metadata columns
        
        Returns:
            List of results with similarity scores
        """
        
        # Convert to pgvector format
        query_vec_str = VectorOperations.convert_to_pgvector(query_vector)
        
        # Build base query using pgvector's <=> operator (cosine distance)
        # Note: <=> returns distance, so similarity = 1 - distance
        base_query = f"""
            SELECT 
                *,
                1 - ({vector_column} <=> :query_vec::vector) as similarity
            FROM {table_name}
            WHERE 1 - ({vector_column} <=> :query_vec::vector) > :threshold
        """
        
        # Add metadata filters if provided
        if metadata_filters:
            filter_conditions = []
            for key, value in metadata_filters.items():
                if isinstance(value, str):
                    filter_conditions.append(f"{key} = '{value}'")
                else:
                    filter_conditions.append(f"{key} = {value}")
            
            if filter_conditions:
                base_query += " AND " + " AND ".join(filter_conditions)
        
        # Add ordering and limit
        base_query += f"""
            ORDER BY {vector_column} <=> :query_vec::vector
            LIMIT :limit
        """
        
        try:
            # Execute query
            result = await session.execute(
                text(base_query),
                {
                    "query_vec": query_vec_str,
                    "threshold": threshold,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows:
                row_dict = dict(row._mapping)
                # Ensure similarity is included
                if 'similarity' not in row_dict:
                    row_dict['similarity'] = 1.0 - row_dict.get('distance', 0)
                results.append(row_dict)
            
            logger.info(
                f"✅ Vector search completed: {len(results)} results "
                f"(threshold: {threshold}, limit: {limit})"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    @staticmethod
    async def batch_similarity_search(
        session: AsyncSession,
        query_vectors: List[List[float]],
        table_name: str = "document_embeddings",
        vector_column: str = "embedding",
        limit_per_query: int = 5,
        threshold: float = 0.7
    ) -> List[List[Dict[str, Any]]]:
        """
        Perform batch similarity search for multiple query vectors.
        
        Args:
            session: Database session
            query_vectors: List of query embedding vectors
            table_name: Table to search in
            vector_column: Column containing vectors
            limit_per_query: Maximum results per query
            threshold: Minimum similarity threshold
        
        Returns:
            List of result lists, one per query
        """
        
        results = []
        
        # Process queries in parallel using asyncio
        import asyncio
        
        search_tasks = [
            VectorOperations.similarity_search(
                session, 
                vec, 
                table_name, 
                vector_column,
                limit_per_query, 
                threshold
            )
            for vec in query_vectors
        ]
        
        batch_results = await asyncio.gather(*search_tasks)
        
        logger.info(
            f"✅ Batch vector search completed: {len(query_vectors)} queries processed"
        )
        
        return batch_results
    
    @staticmethod
    async def index_vectors(
        session: AsyncSession,
        documents: List[Dict[str, Any]],
        table_name: str = "document_embeddings",
        chunk_size: int = 100,
        use_batch_embeddings: bool = True
    ) -> int:
        """
        Index multiple documents with their embeddings.
        Uses batch embedding API for efficiency.
        
        Args:
            session: Database session
            documents: List of documents with 'text' and optional 'metadata'
            table_name: Table to insert into
            chunk_size: Batch size for insertion
            use_batch_embeddings: Whether to use batch API
        
        Returns:
            Number of documents indexed
        """
        
        if not documents:
            return 0
        
        # Get embeddings for all documents
        if use_batch_embeddings:
            from .ai_clients import batch_create_embeddings
            
            texts = [doc.get('text', '') for doc in documents]
            embeddings = await batch_create_embeddings(texts, batch_size=100)
        else:
            # Fallback to individual embeddings (not recommended)
            from .ai_clients import get_embedding
            embeddings = []
            for doc in documents:
                emb = await get_embedding(doc.get('text', ''))
                embeddings.append(emb)
        
        # Prepare batch insert data
        insert_data = []
        for i, doc in enumerate(documents):
            if i < len(embeddings) and embeddings[i]:
                insert_data.append({
                    'content': doc.get('text', ''),
                    'embedding': VectorOperations.convert_to_pgvector(embeddings[i]),
                    'metadata': doc.get('metadata', {}),
                    'document_id': doc.get('document_id'),
                    'chunk_index': doc.get('chunk_index', 0)
                })
        
        # Insert in chunks
        total_inserted = 0
        for i in range(0, len(insert_data), chunk_size):
            chunk = insert_data[i:i + chunk_size]
            
            try:
                # Build insert query
                insert_query = f"""
                    INSERT INTO {table_name} 
                    (content, embedding, metadata, document_id, chunk_index)
                    VALUES 
                    (:content, :embedding::vector, :metadata, :document_id, :chunk_index)
                """
                
                for row in chunk:
                    await session.execute(text(insert_query), row)
                
                await session.commit()
                total_inserted += len(chunk)
                
                logger.info(f"Indexed {len(chunk)} documents (total: {total_inserted})")
                
            except Exception as e:
                logger.error(f"Failed to index chunk: {e}")
                await session.rollback()
        
        logger.info(f"✅ Vector indexing complete: {total_inserted}/{len(documents)} documents")
        
        return total_inserted
    
    @staticmethod
    def compute_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.
        Used only for in-memory comparisons, not for DB queries.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Cosine similarity score (0-1)
        """
        if not vec1 or not vec2:
            return 0.0
        
        # Convert to numpy arrays
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # Compute cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    @staticmethod
    async def create_hnsw_index(
        session: AsyncSession,
        table_name: str = "document_embeddings",
        vector_column: str = "embedding",
        m: int = 16,
        ef_construction: int = 64
    ) -> bool:
        """
        Create HNSW index for fast similarity search.
        
        Args:
            session: Database session
            table_name: Table name
            vector_column: Vector column name
            m: HNSW parameter (default 16)
            ef_construction: HNSW parameter (default 64)
        
        Returns:
            Success status
        """
        try:
            index_name = f"idx_{table_name}_{vector_column}_hnsw"
            
            # Create HNSW index for fast cosine similarity search
            create_index_query = f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name}
                USING hnsw ({vector_column} vector_cosine_ops)
                WITH (m = {m}, ef_construction = {ef_construction})
            """
            
            await session.execute(text(create_index_query))
            await session.commit()
            
            logger.info(f"✅ HNSW index created: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create HNSW index: {e}")
            await session.rollback()
            return False


# Convenience functions for backward compatibility
async def similarity_search(
    session: AsyncSession,
    query_vector: List[float],
    limit: int = 5,
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Convenience function for similarity search"""
    return await VectorOperations.similarity_search(
        session, query_vector, limit=limit, threshold=threshold
    )


def convert_to_pgvector(embedding: List[float]) -> str:
    """Convenience function for pgvector conversion"""
    return VectorOperations.convert_to_pgvector(embedding)