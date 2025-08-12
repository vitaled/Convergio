"""
Unified Vector Operations and Similarity Search
Centralizes all vector operations with pgvector optimization
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from .local_embeddings import get_local_embedding_provider

logger = structlog.get_logger()


class VectorOperations:
    """
    Centralized vector operations with pgvector optimization.
    Single source of truth for all similarity calculations.
    Includes automatic fallback to local embeddings when API unavailable.
    """
    
    @staticmethod
    async def create_embeddings_with_fallback(
        texts: List[str],
        batch_size: int = 100,
        use_cache: bool = True,
        prefer_local: bool = False
    ) -> List[List[float]]:
        """
        Create embeddings with automatic fallback to local model.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            use_cache: Whether to use cache
            prefer_local: If True, use local model by default
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        embeddings = []
        
        if prefer_local:
            # Use local model directly
            local_provider = get_local_embedding_provider()
            embeddings = await local_provider.create_batch_embeddings(
                texts, batch_size=32, use_cache=use_cache
            )
            logger.info(f"Created {len(embeddings)} embeddings using local model (preferred)")
        else:
            try:
                # Try AI client first
                from .ai_clients import batch_create_embeddings
                embeddings = await batch_create_embeddings(texts, batch_size=batch_size)
                logger.info(f"Created {len(embeddings)} embeddings using AI client")
                
            except Exception as e:
                logger.warning(f"AI client failed: {e}, falling back to local model")
                
                # Fallback to local embeddings
                local_provider = get_local_embedding_provider()
                embeddings = await local_provider.create_batch_embeddings(
                    texts, batch_size=32, use_cache=use_cache
                )
                logger.info(f"Created {len(embeddings)} embeddings using local model (fallback)")
                
        return embeddings
    
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
        threshold: float = 0.7,
        max_concurrent: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        Perform batch similarity search for multiple query vectors with optimized concurrency.
        
        Args:
            session: Database session
            query_vectors: List of query embedding vectors
            table_name: Table to search in
            vector_column: Column containing vectors
            limit_per_query: Maximum results per query
            threshold: Minimum similarity threshold
            max_concurrent: Maximum concurrent searches (default 10)
        
        Returns:
            List of result lists, one per query
        """
        
        if not query_vectors:
            return []
        
        # Import at function level to avoid circular imports
        import asyncio
        from asyncio import Semaphore
        
        # Create semaphore to limit concurrent operations
        semaphore = Semaphore(max_concurrent)
        
        async def search_with_semaphore(vec: List[float], index: int) -> Tuple[int, List[Dict[str, Any]]]:
            """Perform search with concurrency control"""
            async with semaphore:
                try:
                    result = await VectorOperations.similarity_search(
                        session, 
                        vec, 
                        table_name, 
                        vector_column,
                        limit_per_query, 
                        threshold
                    )
                    return (index, result)
                except Exception as e:
                    logger.error(f"Search failed for query {index}: {e}")
                    return (index, [])
        
        # Create tasks with index tracking for ordered results
        search_tasks = [
            search_with_semaphore(vec, i)
            for i, vec in enumerate(query_vectors)
        ]
        
        # Execute all searches concurrently with gather
        results_with_indices = await asyncio.gather(
            *search_tasks,
            return_exceptions=False  # Raise exceptions if any occur
        )
        
        # Sort results by original index to maintain order
        results_with_indices.sort(key=lambda x: x[0])
        batch_results = [result for _, result in results_with_indices]
        
        logger.info(
            f"✅ Batch vector search optimized: {len(query_vectors)} queries processed "
            f"(max concurrent: {max_concurrent})"
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
        
        # Get embeddings for all documents using centralized method with fallback
        texts = [doc.get('text', '') for doc in documents]
        
        if use_batch_embeddings:
            # Use batch processing with automatic fallback
            embeddings = await VectorOperations.create_embeddings_with_fallback(
                texts, 
                batch_size=100,
                use_cache=True,
                prefer_local=False  # Prefer API but fallback to local if needed
            )
        else:
            # Process individually (not recommended for performance)
            embeddings = []
            for text in texts:
                batch_result = await VectorOperations.create_embeddings_with_fallback(
                    [text],
                    batch_size=1,
                    use_cache=True,
                    prefer_local=False
                )
                if batch_result:
                    embeddings.append(batch_result[0])
        
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
        
        # Insert in chunks with optimized parallel processing
        total_inserted = 0
        import asyncio
        from asyncio import Semaphore
        
        # Limit concurrent database operations
        max_concurrent_inserts = 5
        semaphore = Semaphore(max_concurrent_inserts)
        
        async def insert_chunk(chunk_data: List[Dict], chunk_index: int) -> int:
            """Insert a single chunk with concurrency control"""
            async with semaphore:
                try:
                    # Build insert query
                    insert_query = f"""
                        INSERT INTO {table_name} 
                        (content, embedding, metadata, document_id, chunk_index)
                        VALUES 
                        (:content, :embedding::vector, :metadata, :document_id, :chunk_index)
                    """
                    
                    for row in chunk_data:
                        await session.execute(text(insert_query), row)
                    
                    await session.commit()
                    
                    logger.info(f"Chunk {chunk_index}: Indexed {len(chunk_data)} documents")
                    return len(chunk_data)
                    
                except Exception as e:
                    logger.error(f"Failed to index chunk {chunk_index}: {e}")
                    await session.rollback()
                    return 0
        
        # Create chunks and process them in parallel
        chunks = [
            insert_data[i:i + chunk_size]
            for i in range(0, len(insert_data), chunk_size)
        ]
        
        # Execute all chunk inserts concurrently
        insert_tasks = [
            insert_chunk(chunk, idx)
            for idx, chunk in enumerate(chunks)
        ]
        
        # Gather results
        results = await asyncio.gather(*insert_tasks, return_exceptions=False)
        total_inserted = sum(results)
        
        logger.info(f"✅ Vector indexing complete: {total_inserted}/{len(documents)} documents")
        
        return total_inserted
    
    @staticmethod
    async def batch_process_documents(
        documents: List[Dict[str, Any]],
        process_func,
        batch_size: int = 10,
        max_concurrent: int = 5
    ) -> List[Any]:
        """
        Generic batch processing with asyncio.gather optimization.
        
        Args:
            documents: List of documents to process
            process_func: Async function to process each document
            batch_size: Size of each batch
            max_concurrent: Maximum concurrent operations
            
        Returns:
            List of processed results
        """
        if not documents:
            return []
            
        import asyncio
        from asyncio import Semaphore
        
        semaphore = Semaphore(max_concurrent)
        
        async def process_with_semaphore(doc: Dict, index: int) -> Tuple[int, Any]:
            """Process document with concurrency control"""
            async with semaphore:
                try:
                    result = await process_func(doc)
                    return (index, result)
                except Exception as e:
                    logger.error(f"Processing failed for document {index}: {e}")
                    return (index, None)
        
        # Process in batches for better memory management
        all_results = []
        
        for batch_start in range(0, len(documents), batch_size):
            batch_end = min(batch_start + batch_size, len(documents))
            batch_docs = documents[batch_start:batch_end]
            
            # Create tasks for this batch
            batch_tasks = [
                process_with_semaphore(doc, batch_start + i)
                for i, doc in enumerate(batch_docs)
            ]
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=False)
            all_results.extend(batch_results)
            
            logger.debug(f"Processed batch {batch_start//batch_size + 1}: {len(batch_docs)} documents")
        
        # Sort by index and extract results
        all_results.sort(key=lambda x: x[0])
        final_results = [result for _, result in all_results]
        
        logger.info(f"✅ Batch processing complete: {len(documents)} documents processed")
        
        return final_results
    
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


async def create_embeddings_with_fallback(
    texts: List[str],
    batch_size: int = 100,
    use_cache: bool = True,
    prefer_local: bool = False
) -> List[List[float]]:
    """Convenience function for creating embeddings with fallback"""
    return await VectorOperations.create_embeddings_with_fallback(
        texts, batch_size, use_cache, prefer_local
    )