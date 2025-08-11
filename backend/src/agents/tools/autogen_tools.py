"""
AutoGen Tool Functions
Properly formatted tool functions for AutoGen 0.7+
"""

import json
import os
from typing import Literal
import httpx
import structlog

logger = structlog.get_logger()


async def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for current information using Perplexity.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
    
    Returns:
        JSON string with search results
    """
    try:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            return json.dumps({
                "error": "PERPLEXITY_API_KEY not set",
                "results": []
            })
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Use Perplexity's sonar model for web search
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful search assistant. Provide accurate, current information from the web."
                },
                {
                    "role": "user",
                    "content": f"Search the web for: {query}. Provide the top {max_results} most relevant results."
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info(f"✅ Web search completed: {query[:50]}")
            
            return json.dumps({
                "query": query,
                "results": content,
                "source": "perplexity"
            }, indent=2)
            
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return json.dumps({
            "error": str(e),
            "results": []
        })


async def query_talents(query_type: Literal["count", "departments", "skills", "all"] = "count") -> str:
    """
    Query talent information from Convergio database.
    
    Args:
        query_type: Type of query (count, departments, skills, all)
    
    Returns:
        Talent information as JSON string
    """
    try:
        async with httpx.AsyncClient() as client:
            if query_type == "count":
                r = await client.get("http://localhost:9000/api/v1/talents")
                r.raise_for_status()
                talents = r.json()
                total = len(talents) if isinstance(talents, list) else len(talents.get("data", []))
                return f"Total talents in database: {total}"
            
            elif query_type == "all":
                response = await client.get("http://localhost:9000/api/v1/talents")
                if response.status_code == 200:
                    talents = response.json()
                    summary = {
                        "total_talents": len(talents),
                        "active_talents": len([t for t in talents if t.get("is_active", True)]),
                        "departments": list(set([t.get("department", "Unknown") for t in talents]))
                    }
                    return json.dumps(summary, indent=2)
            
            return "No data found for the specified query type"
            
    except Exception as e:
        logger.error(f"Talents query failed: {e}")
        return f"Error querying talents: {str(e)}"


async def business_intelligence(focus_area: Literal["overview", "talents", "performance"] = "overview") -> str:
    """
    Get business intelligence analysis from Convergio data.
    
    Args:
        focus_area: Area to focus on (overview, talents, performance)
    
    Returns:
        Business intelligence report as JSON string
    """
    try:
        report = {
            "business_intelligence_report": {
                "focus_area": focus_area
            }
        }
        
        if focus_area in ["overview", "talents"]:
            talents_data = await query_talents("all")
            report["talent_analysis"] = talents_data
        
        if focus_area in ["overview", "performance"]:
            report["performance_metrics"] = {
                "status": "Dashboard metrics available",
                "note": "Use web_search for real-time financial data"
            }
        
        return json.dumps(report, indent=2)
        
    except Exception as e:
        logger.error(f"Business intelligence failed: {e}")
        return f"Error generating business intelligence: {str(e)}"


# Tool functions for different agent types
def get_amy_tools():
    """Tools for Amy CFO - financial focus"""
    return [web_search, business_intelligence, query_talents]


def get_ali_tools():
    """Tools for Ali Chief of Staff - all tools"""
    return [web_search, query_talents, business_intelligence]


def get_data_analysis_tools():
    """Tools for data analysis agents"""
    return [query_talents, business_intelligence]


def get_market_strategy_tools():
    """Tools for market/strategy agents"""
    return [web_search, business_intelligence]


def get_default_tools():
    """Default tools for all agents"""
    return [web_search, query_talents]