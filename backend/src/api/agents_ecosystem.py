"""
Agent Ecosystem Health Check API
Provides real-time health status of agents and their tools
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import os
import httpx
import structlog

from src.agents.tools.web_search_tool import WebSearchTool
from src.agents.tools.convergio_tools import VectorSearchTool
from src.agents.utils.config import get_settings

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
logger = structlog.get_logger()
settings = get_settings()


@router.get("/ecosystem")
async def get_ecosystem_health() -> Dict[str, Any]:
    """
    Get comprehensive health status of the agent ecosystem
    """
    
    health_report = {
        "status": "healthy",
        "agents": [],
        "tools": {},
        "database": {},
        "ai_models": {},
        "message": "Agent ecosystem operational"
    }
    
    try:
        # Check web search tool
        web_tool = WebSearchTool()
        web_health = web_tool.provider_health()
        health_report["tools"]["web_search"] = {
            "configured": web_health["configured"],
            "provider": web_health["provider"],
            "status": "healthy" if web_health["configured"] else "not_configured"
        }
        
        # Check vector search tool
        try:
            vector_tool = VectorSearchTool()
            health_report["tools"]["vector_search"] = {
                "available": True,
                "status": "healthy"
            }
        except Exception as e:
            health_report["tools"]["vector_search"] = {
                "available": False,
                "status": "error",
                "error": str(e)
            }
        
        # Check database connectivity
        try:
            async with httpx.AsyncClient() as client:
                db_response = await client.get("http://localhost:9000/api/v1/talents", timeout=2.0)
                health_report["database"] = {
                    "healthy": db_response.status_code == 200,
                    "status": "connected" if db_response.status_code == 200 else "error"
                }
        except Exception:
            health_report["database"] = {
                "healthy": False,
                "status": "disconnected"
            }
        
        # Check AI models configuration
        health_report["ai_models"] = {
            "openai": {
                "configured": bool(os.getenv("OPENAI_API_KEY")),
                "model": settings.default_ai_model
            },
            "perplexity": {
                "configured": bool(os.getenv("PERPLEXITY_API_KEY"))
            }
        }
        
        # List available agents
        agents_list = [
            {"name": "ali_chief_of_staff", "status": "available", "capabilities": ["all_tools", "orchestration"]},
            {"name": "amy_cfo", "status": "available", "capabilities": ["web_search", "financial_analysis"]},
            {"name": "davide_project_manager", "status": "available", "capabilities": ["project_management", "database"]},
            {"name": "diana_performance_dashboard", "status": "available", "capabilities": ["analytics", "reporting"]},
        ]
        health_report["agents"] = agents_list
        
        # Determine overall health
        if not health_report["tools"]["web_search"]["configured"]:
            health_report["status"] = "degraded"
            health_report["message"] = "Web search not configured - limited agent capabilities"
        
        if not health_report["database"]["healthy"]:
            health_report["status"] = "degraded"
            health_report["message"] = "Database connection issues - some features unavailable"
            
        if not health_report["ai_models"]["openai"]["configured"]:
            health_report["status"] = "unhealthy"
            health_report["message"] = "No AI model configured - agents cannot operate"
        
        return health_report
        
    except Exception as e:
        logger.error("Ecosystem health check failed", error=str(e))
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "agents": [],
            "tools": {},
            "database": {},
            "ai_models": {}
        }


@router.get("/health/{agent_name}")
async def get_agent_health(agent_name: str) -> Dict[str, Any]:
    """
    Get health status of a specific agent
    """
    
    # Check if agent exists
    known_agents = [
        "ali_chief_of_staff",
        "amy_cfo", 
        "davide_project_manager",
        "diana_performance_dashboard",
        "chris_tech_advisor",
        "emma_data_analyst"
    ]
    
    if agent_name not in known_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    # Get ecosystem health
    ecosystem = await get_ecosystem_health()
    
    # Build agent-specific health
    agent_health = {
        "name": agent_name,
        "status": "healthy",
        "tools_available": [],
        "issues": []
    }
    
    # Check tools based on agent role
    if agent_name == "ali_chief_of_staff":
        # Ali needs all tools
        if ecosystem["tools"]["web_search"]["configured"]:
            agent_health["tools_available"].append("web_search")
        else:
            agent_health["issues"].append("Web search not configured")
            
        if ecosystem["tools"]["vector_search"]["available"]:
            agent_health["tools_available"].append("vector_search")
        else:
            agent_health["issues"].append("Vector search unavailable")
            
        if ecosystem["database"]["healthy"]:
            agent_health["tools_available"].append("database")
        else:
            agent_health["issues"].append("Database disconnected")
            
    elif agent_name in ["amy_cfo", "chris_tech_advisor"]:
        # Financial/tech agents need web search
        if ecosystem["tools"]["web_search"]["configured"]:
            agent_health["tools_available"].append("web_search")
        else:
            agent_health["issues"].append("Web search not configured - cannot fetch market data")
            agent_health["status"] = "degraded"
    
    elif agent_name in ["davide_project_manager", "diana_performance_dashboard"]:
        # PM/Dashboard agents need database
        if ecosystem["database"]["healthy"]:
            agent_health["tools_available"].append("database")
        else:
            agent_health["issues"].append("Database unavailable - cannot access project data")
            agent_health["status"] = "unhealthy"
    
    # Check AI model
    if not ecosystem["ai_models"]["openai"]["configured"]:
        agent_health["status"] = "unhealthy"
        agent_health["issues"].append("No AI model configured")
    
    # Set overall status
    if len(agent_health["issues"]) > 2:
        agent_health["status"] = "unhealthy"
    elif len(agent_health["issues"]) > 0:
        agent_health["status"] = "degraded"
    
    return agent_health