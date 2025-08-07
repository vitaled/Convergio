"""
🔧 Convergio Custom AutoGen Tools
Advanced tools that integrate AutoGen agents with Convergio backend APIs
"""

from typing import Any, Dict, List, Optional, Literal
import json
import asyncio
from datetime import datetime

import structlog
from autogen_core.tools import BaseTool
from pydantic import BaseModel
import httpx

from .backend_api_client import (
    query_talents_count, 
    query_engagements_summary, 
    query_dashboard_stats, 
    query_skills_overview
)
from .vector_search_client import search_similar, embed_text

logger = structlog.get_logger()


class TalentsQueryArgs(BaseModel):
    query_type: Literal["count", "departments", "skills", "all"] = "count"


class TalentsQueryTool(BaseTool):
    """Tool for querying talent information from Convergio database"""
    
    def __init__(self):
        super().__init__(
            args_type=TalentsQueryArgs,
            return_type=str,
            name="query_talents",
            description="Query talent information from the Convergio database. Returns talent count, departments, skills overview."
        )
    
    async def run(self, args: TalentsQueryArgs) -> str:
        """
        Query talent information
        
        Args:
            args: Query arguments containing query_type
        """
        try:
            if args.query_type == "count":
                result = await query_talents_count()
                return f"Total talents: {result.get('total', 0)}"
            
            elif args.query_type == "skills":
                result = await query_skills_overview()
                return f"Skills overview: {json.dumps(result, indent=2)}"
            
            elif args.query_type == "all":
                # Get comprehensive talent information
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:9000/api/v1/talents")
                    if response.status_code == 200:
                        talents = response.json()
                        summary = {
                            "total_talents": len(talents),
                            "active_talents": len([t for t in talents if t.get("is_active", True)]),
                            "admins": len([t for t in talents if t.get("is_admin", False)]),
                            "departments": list(set([t.get("department", "Unknown") for t in talents])),
                            "recent_talents": [t for t in talents[-3:]]  # Last 3
                        }
                        return json.dumps(summary, indent=2)
            
            return "No data found for the specified query type"
            
        except Exception as e:
            logger.error("❌ TalentsQueryTool error", error=str(e))
            return f"Error querying talents: {str(e)}"


class VectorSearchArgs(BaseModel):
    query: str
    top_k: int = 5


class VectorSearchTool(BaseTool):
    """Tool for semantic search using vector embeddings"""
    
    def __init__(self):
        super().__init__(
            args_type=VectorSearchArgs,
            return_type=str,
            name="vector_search",
            description="Perform semantic search across Convergio knowledge base using vector embeddings"
        )
    
    async def run(self, args: VectorSearchArgs) -> str:
        """
        Perform vector search
        
        Args:
            args: Search arguments containing query and top_k
        """
        try:
            # Embed the query
            query_embedding = await embed_text(args.query)
            
            # Search for similar content
            results = await search_similar(query_embedding, top_k=args.top_k)
            
            if not results:
                return f"No relevant results found for: {args.query}"
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(f"{i}. {result.get('content', 'No content')[:200]}...")
            
            return f"Vector search results for '{args.query}':\n" + "\n".join(formatted_results)
            
        except Exception as e:
            logger.error("❌ VectorSearchTool error", error=str(e))
            return f"Error performing vector search: {str(e)}"


class EngagementAnalyticsArgs(BaseModel):
    analysis_type: Literal["summary", "dashboard", "trends"] = "summary"


class EngagementAnalyticsTool(BaseTool):
    """Tool for analyzing engagement data and business metrics"""
    
    def __init__(self):
        super().__init__(
            args_type=EngagementAnalyticsArgs,
            return_type=str,
            name="engagement_analytics",
            description="Analyze engagement data, business metrics, and dashboard statistics"
        )
    
    async def run(self, args: EngagementAnalyticsArgs) -> str:
        """
        Analyze engagements and business metrics
        
        Args:
            args: Analysis arguments containing analysis_type
        """
        try:
            if args.analysis_type == "summary":
                result = await query_engagements_summary()
                return f"Engagement summary: {json.dumps(result, indent=2)}"
            
            elif args.analysis_type == "dashboard":
                result = await query_dashboard_stats()
                return f"Dashboard stats: {json.dumps(result, indent=2)}"
            
            elif args.analysis_type == "trends":
                # Get trend data from multiple sources
                summary = await query_engagements_summary()
                dashboard = await query_dashboard_stats()
                
                trends = {
                    "engagement_trends": summary,
                    "performance_metrics": dashboard,
                    "analysis_date": datetime.now().isoformat(),
                    "key_insights": [
                        "Engagement metrics collected",
                        "Dashboard performance tracked",
                        "Real-time analytics available"
                    ]
                }
                return json.dumps(trends, indent=2)
            
            return "No analytics data available for the specified type"
            
        except Exception as e:
            logger.error("❌ EngagementAnalyticsTool error", error=str(e))
            return f"Error analyzing engagements: {str(e)}"


class BusinessIntelligenceArgs(BaseModel):
    focus_area: Literal["overview", "talents", "performance", "insights"] = "overview"


class BusinessIntelligenceTool(BaseTool):
    """Advanced business intelligence tool combining multiple data sources"""
    
    def __init__(self):
        super().__init__(
            args_type=BusinessIntelligenceArgs,
            return_type=str,
            name="business_intelligence",
            description="Comprehensive business intelligence analysis combining talents, engagements, and performance data"
        )
        self.talents_tool = TalentsQueryTool()
        self.analytics_tool = EngagementAnalyticsTool()
        self.vector_tool = VectorSearchTool()
    
    async def run(self, args: BusinessIntelligenceArgs) -> str:
        """
        Generate business intelligence report
        
        Args:
            args: Business intelligence arguments containing focus_area
        """
        try:
            report = {
                "business_intelligence_report": {
                    "generated_at": datetime.now().isoformat(),
                    "focus_area": args.focus_area
                }
            }
            
            if args.focus_area == "overview" or args.focus_area == "talents":
                talents_data = await self.talents_tool.run(TalentsQueryArgs(query_type="all"))
                report["talent_analysis"] = talents_data
            
            if args.focus_area == "overview" or args.focus_area == "performance":
                performance_data = await self.analytics_tool.run(EngagementAnalyticsArgs(analysis_type="dashboard"))
                report["performance_metrics"] = performance_data
            
            if args.focus_area == "insights":
                # Generate insights using vector search
                insights_query = f"business insights {args.focus_area} performance metrics trends"
                insights = await self.vector_tool.run(VectorSearchArgs(query=insights_query))
                report["ai_insights"] = insights
            
            return json.dumps(report, indent=2)
            
        except Exception as e:
            logger.error("❌ BusinessIntelligenceTool error", error=str(e))
            return f"Error generating business intelligence: {str(e)}"


# Export available tools
CONVERGIO_TOOLS = [
    TalentsQueryTool(),
    VectorSearchTool(),
    EngagementAnalyticsTool(),
    BusinessIntelligenceTool(),
]