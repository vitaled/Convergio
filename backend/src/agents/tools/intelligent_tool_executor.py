"""
Intelligent Tool Executor
Integrates Smart Tool Selector with AutoGen tool execution
Automatically decides when to use web search vs regular AI chat
"""

import json
import structlog
from typing import Any, Dict, List, Optional
from autogen_core.tools import BaseTool

from .smart_tool_selector import SmartToolSelector
from .web_search_tool import WebSearchTool
from .vector_search_client import VectorSearchClient
from ..ai_clients import get_ai_client_manager

logger = structlog.get_logger()


class IntelligentToolExecutor:
    """
    Executes tools intelligently based on query analysis.
    Automatically routes queries to appropriate tools.
    """
    
    def __init__(self):
        """Initialize with available tools"""
        self.selector = SmartToolSelector()
        self.web_search = WebSearchTool()
        self.vector_client = None  # Initialize only when needed
        self.ai_manager = get_ai_client_manager()
        
        # Track tool usage for metrics
        self.tool_usage = {
            "web_search": 0,
            "vector_search": 0,
            "database": 0,
            "ai_chat": 0
        }
    
    async def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Execute a query using the most appropriate tool(s).
        
        Args:
            query: The user query
            context: Optional context for the query
            threshold: Confidence threshold for tool selection
        
        Returns:
            Response with results and metadata
        """
        
        # Analyze the query
        analysis = self.selector.analyze_query(query)
        
        logger.info(
            "🧠 Query Analysis",
            query=query[:100],
            needs_web=analysis["needs_web_search"],
            confidence=f"{analysis['confidence']:.0%}",
            suggested_tools=analysis["suggested_tools"]
        )
        
        results = {
            "query": query,
            "analysis": analysis,
            "tools_used": [],
            "responses": {}
        }
        
        # Execute based on analysis
        if analysis["needs_web_search"] and analysis["confidence"] >= threshold:
            # Use web search for current/real-time info
            logger.info("🌐 Using web search for real-time data")
            self.tool_usage["web_search"] += 1
            
            web_result = await self._execute_web_search(query)
            results["tools_used"].append("web_search")
            results["responses"]["web_search"] = web_result
            
        elif "database_query" in analysis["suggested_tools"]:
            # Query internal database
            logger.info("📊 Using database query for internal data")
            self.tool_usage["database"] += 1
            
            db_result = await self._execute_database_query(query, context)
            results["tools_used"].append("database_query")
            results["responses"]["database"] = db_result
            
        elif "vector_search" in analysis["suggested_tools"]:
            # Use vector search for semantic search
            logger.info("🔍 Using vector search for semantic matching")
            self.tool_usage["vector_search"] += 1
            
            vector_result = await self._execute_vector_search(query)
            results["tools_used"].append("vector_search")
            results["responses"]["vector_search"] = vector_result
            
        else:
            # Use regular AI chat for general knowledge
            logger.info("💬 Using AI chat for general knowledge")
            self.tool_usage["ai_chat"] += 1
            
            chat_result = await self._execute_ai_chat(query, context)
            results["tools_used"].append("ai_chat")
            results["responses"]["ai_chat"] = chat_result
        
        # Log metrics
        logger.info(
            "📈 Tool Usage Metrics",
            web_search=self.tool_usage["web_search"],
            vector_search=self.tool_usage["vector_search"],
            database=self.tool_usage["database"],
            ai_chat=self.tool_usage["ai_chat"]
        )
        
        return results
    
    async def _execute_web_search(self, query: str) -> Dict[str, Any]:
        """Execute web search using Perplexity"""
        try:
            from web_search_tool import WebSearchArgs
            
            args = WebSearchArgs(
                query=query,
                max_results=5,
                search_type="general"
            )
            
            result = await self.web_search.run(args)
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"error": str(e)}
    
    async def _execute_database_query(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute database query for internal data"""
        try:
            # This would use the actual database tools
            # For now, return a placeholder
            return {
                "source": "database",
                "query": query,
                "message": "Database query would be executed here",
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {"error": str(e)}
    
    async def _execute_vector_search(self, query: str) -> Dict[str, Any]:
        """Execute vector search for semantic matching"""
        try:
            # Initialize vector client if needed
            if self.vector_client is None:
                try:
                    self.vector_client = VectorSearchClient()
                except Exception as init_error:
                    logger.warning(f"Could not initialize vector client: {init_error}")
                    return {
                        "source": "vector_search",
                        "query": query,
                        "error": "Vector search not configured",
                        "fallback": "Using AI chat instead"
                    }
            
            results = await self.vector_client.search(
                query=query,
                top_k=5
            )
            
            return {
                "source": "vector_search",
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {"error": str(e)}
    
    async def _execute_ai_chat(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute regular AI chat for general knowledge"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer based on your training knowledge."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            # Add context if provided
            if context:
                messages[0]["content"] += f"\n\nContext: {json.dumps(context)}"
            
            response = await self.ai_manager.chat_completion(
                messages=messages,
                provider="openai",
                temperature=0.7
            )
            
            return {
                "source": "ai_chat",
                "query": query,
                "response": response,
                "model": "gpt-4o-mini"
            }
            
        except Exception as e:
            logger.error(f"AI chat failed: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tool usage metrics"""
        total = sum(self.tool_usage.values())
        
        if total == 0:
            return {
                "total_queries": 0,
                "usage": self.tool_usage,
                "percentages": {}
            }
        
        percentages = {
            tool: (count / total) * 100
            for tool, count in self.tool_usage.items()
        }
        
        return {
            "total_queries": total,
            "usage": self.tool_usage,
            "percentages": percentages
        }
    
    def reset_metrics(self):
        """Reset usage metrics"""
        self.tool_usage = {
            "web_search": 0,
            "vector_search": 0,
            "database": 0,
            "ai_chat": 0
        }


# Global instance
_intelligent_executor = None


def get_intelligent_executor() -> IntelligentToolExecutor:
    """Get singleton intelligent executor"""
    global _intelligent_executor
    if _intelligent_executor is None:
        _intelligent_executor = IntelligentToolExecutor()
    return _intelligent_executor


# Convenience function for AutoGen integration
async def execute_intelligent_query(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Execute a query intelligently, automatically selecting the right tool.
    
    This is the main entry point for AutoGen agents to use intelligent tool selection.
    """
    executor = get_intelligent_executor()
    return await executor.execute_query(query, context, threshold)