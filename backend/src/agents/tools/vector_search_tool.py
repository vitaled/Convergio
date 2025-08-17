"""
🔍 Vector Search Tools for AutoGen Agents
Enables agents to perform semantic search on the vector database
"""

from typing import Any, Dict, List, Optional, Literal
import json
import asyncio
from datetime import datetime
import os

import structlog
from autogen_core.tools import BaseTool
from pydantic import BaseModel
import httpx

logger = structlog.get_logger()


class VectorSearchArgs(BaseModel):
    """Arguments for vector search"""
    query: str
    top_k: int = 5
    search_type: Literal["semantic", "hybrid", "keyword"] = "semantic"
    filters: Optional[Dict[str, Any]] = None


class VectorSearchTool(BaseTool):
    """
    Tool for performing semantic vector search on the knowledge base.
    Connects to the internal vector search API.
    """
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        super().__init__(
            args_type=VectorSearchArgs,
            return_type=str,
            name="vector_search",
            description="Perform semantic search on the knowledge base using vector embeddings"
        )
        self.base_url = base_url
    
    async def run(self, args: VectorSearchArgs, cancellation_token=None) -> str:
        """
        Perform vector search.
        
        Args:
            args: Search arguments
            cancellation_token: Optional cancellation token for AutoGen
        
        Returns:
            JSON string with search results
        """
        try:
            logger.info(f"🔍 Vector search: {args.query}", top_k=args.top_k, search_type=args.search_type)
            
            # Call the vector search API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/vector/search",
                    json={
                        "query": args.query,
                        "top_k": args.top_k,
                        "search_type": args.search_type,
                        "filters": args.filters or {}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format results for agent consumption
                    formatted_results = []
                    for i, result in enumerate(data.get("results", []), 1):
                        formatted_results.append({
                            "rank": i,
                            "title": result.get("title", "Untitled"),
                            "content": result.get("content", "")[:500] + ("..." if len(result.get("content", "")) > 500 else ""),
                            "similarity_score": result.get("similarity_score", 0.0),
                            "document_id": result.get("document_id"),
                            "metadata": result.get("metadata", {})
                        })
                    
                    return json.dumps({
                        "query": args.query,
                        "results_found": len(formatted_results),
                        "results": formatted_results,
                        "search_type": args.search_type,
                        "timestamp": datetime.now().isoformat()
                    }, indent=2)
                
                elif response.status_code == 404:
                    return json.dumps({
                        "error": "Vector search service not available",
                        "message": "The vector database is not running on port 9000",
                        "results": []
                    }, indent=2)
                
                else:
                    return json.dumps({
                        "error": f"Vector search failed with status {response.status_code}",
                        "message": response.text,
                        "results": []
                    }, indent=2)
                    
        except httpx.ConnectError:
            logger.warning("Vector search service not available")
            return json.dumps({
                "error": "Vector search service not available",
                "message": "Unable to connect to vector database on localhost:9000",
                "results": [],
                "fallback_suggestion": "Use database_query tool for document search instead"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Vector search error: {e}")
            return json.dumps({
                "error": str(e),
                "query": args.query,
                "results": []
            }, indent=2)


class DocumentEmbeddingArgs(BaseModel):
    """Arguments for document embedding"""
    text: str
    document_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentEmbeddingTool(BaseTool):
    """
    Tool for creating embeddings for documents.
    Useful for indexing new content.
    """
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        super().__init__(
            args_type=DocumentEmbeddingArgs,
            return_type=str,
            name="embed_document",
            description="Create vector embeddings for document text"
        )
        self.base_url = base_url
    
    async def run(self, args: DocumentEmbeddingArgs, cancellation_token=None) -> str:
        """
        Create document embedding.
        
        Args:
            args: Embedding arguments
            cancellation_token: Optional cancellation token for AutoGen
        
        Returns:
            JSON string with embedding result
        """
        try:
            logger.info(f"🔢 Creating embedding", text_length=len(args.text), doc_id=args.document_id)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/vector/embed",
                    json={
                        "text": args.text,
                        "document_id": args.document_id,
                        "metadata": args.metadata or {}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return json.dumps({
                        "status": "success",
                        "embedding_id": data.get("embedding_id"),
                        "document_id": args.document_id,
                        "text_length": len(args.text),
                        "embedding_dimensions": len(data.get("embedding", [])),
                        "timestamp": datetime.now().isoformat()
                    }, indent=2)
                
                else:
                    return json.dumps({
                        "status": "error",
                        "error": f"Embedding failed with status {response.status_code}",
                        "message": response.text
                    }, indent=2)
                    
        except httpx.ConnectError:
            return json.dumps({
                "status": "error",
                "error": "Vector service not available",
                "message": "Unable to connect to vector database on localhost:9000"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Embedding error: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2)


# Export vector tools
VECTOR_TOOLS = [
    VectorSearchTool(),
    DocumentEmbeddingTool()
]


def get_vector_tools(base_url: str = "http://localhost:9000") -> List[BaseTool]:
    """
    Get all vector-related tools for AutoGen 0.7.2 agents.
    
    Args:
        base_url: Base URL for vector service
    
    Returns:
        List of properly configured vector tools for AutoGen
    """
    return [
        VectorSearchTool(base_url),
        DocumentEmbeddingTool(base_url)
    ]