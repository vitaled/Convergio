"""
🌐 Web Search Tool for AutoGen Agents
Enables agents to search the internet for up-to-date information
Based on AutoGen documentation 2024-2025
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


class WebSearchArgs(BaseModel):
    """Arguments for web search"""
    query: str
    max_results: int = 5
    search_type: Literal["general", "news", "financial", "technical"] = "general"


class WebSearchTool(BaseTool):
    """
    Tool for searching the web for current information.
    Implements web search capabilities for AutoGen agents.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the web search tool.
        
        Args:
            api_key: API key for search service (Bing, Google, or Serper)
        """
        super().__init__(
            args_type=WebSearchArgs,
            return_type=str,
            name="web_search",
            description="Search the internet for current information, news, financial data, or technical documentation"
        )
        
        # Try to get API key from environment if not provided
        self.api_key = api_key or os.getenv("BING_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("SERPER_API_KEY")
        self.search_provider = self._determine_provider()
    
    def _determine_provider(self) -> str:
        """Determine which search provider to use based on available API keys"""
        if os.getenv("BING_API_KEY"):
            return "bing"
        elif os.getenv("SERPER_API_KEY"):
            return "serper"
        elif os.getenv("GOOGLE_API_KEY"):
            return "google"
        else:
            return "mock"  # Fallback to mock results for development
    
    async def run(self, args: WebSearchArgs, cancellation_token=None) -> str:
        """
        Perform a web search.
        
        Args:
            args: Search arguments containing query and options
            cancellation_token: Optional cancellation token for AutoGen
        
        Returns:
            JSON string with search results
        """
        try:
            logger.info(f"🔍 Web search: {args.query}", provider=self.search_provider)
            
            if self.search_provider == "bing":
                return await self._search_bing(args)
            elif self.search_provider == "serper":
                return await self._search_serper(args)
            elif self.search_provider == "google":
                return await self._search_google(args)
            else:
                return await self._mock_search(args)
                
        except Exception as e:
            logger.error(f"❌ Web search error: {e}")
            return json.dumps({
                "error": str(e),
                "results": []
            })
    
    async def _search_bing(self, args: WebSearchArgs) -> str:
        """Search using Bing Search API"""
        try:
            headers = {
                "Ocp-Apim-Subscription-Key": os.getenv("BING_API_KEY")
            }
            
            params = {
                "q": args.query,
                "count": args.max_results,
                "textDecorations": True,
                "textFormat": "HTML"
            }
            
            # Add search type specific parameters
            if args.search_type == "news":
                endpoint = "https://api.bing.microsoft.com/v7.0/news/search"
            else:
                endpoint = "https://api.bing.microsoft.com/v7.0/search"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Format results
                results = []
                if "webPages" in data:
                    for item in data["webPages"]["value"][:args.max_results]:
                        results.append({
                            "title": item.get("name"),
                            "url": item.get("url"),
                            "snippet": item.get("snippet"),
                            "date": item.get("dateLastCrawled")
                        })
                elif "value" in data:  # News results
                    for item in data["value"][:args.max_results]:
                        results.append({
                            "title": item.get("name"),
                            "url": item.get("url"),
                            "snippet": item.get("description"),
                            "date": item.get("datePublished")
                        })
                
                return json.dumps({
                    "query": args.query,
                    "results": results,
                    "source": "bing"
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return await self._mock_search(args)
    
    async def _search_serper(self, args: WebSearchArgs) -> str:
        """Search using Serper API (Google results)"""
        try:
            headers = {
                "X-API-KEY": os.getenv("SERPER_API_KEY"),
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": args.query,
                "num": args.max_results
            }
            
            # Add search type specific parameters
            if args.search_type == "news":
                payload["type"] = "news"
            elif args.search_type == "financial":
                payload["q"] += " stock market finance"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Format results
                results = []
                for item in data.get("organic", [])[:args.max_results]:
                    results.append({
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "snippet": item.get("snippet"),
                        "date": item.get("date")
                    })
                
                return json.dumps({
                    "query": args.query,
                    "results": results,
                    "source": "serper"
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return await self._mock_search(args)
    
    async def _search_google(self, args: WebSearchArgs) -> str:
        """Search using Google Custom Search API"""
        try:
            params = {
                "key": os.getenv("GOOGLE_API_KEY"),
                "cx": os.getenv("GOOGLE_CSE_ID"),  # Custom Search Engine ID
                "q": args.query,
                "num": args.max_results
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Format results
                results = []
                for item in data.get("items", [])[:args.max_results]:
                    results.append({
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "snippet": item.get("snippet"),
                        "date": None
                    })
                
                return json.dumps({
                    "query": args.query,
                    "results": results,
                    "source": "google"
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return await self._mock_search(args)
    
    async def _mock_search(self, args: WebSearchArgs) -> str:
        """Return mock search results for development/testing"""
        
        # Generate contextual mock results based on query
        mock_results = []
        
        if "msft" in args.query.lower() or "microsoft" in args.query.lower():
            mock_results = [
                {
                    "title": "Microsoft Stock (MSFT) - Latest Price & Analysis",
                    "url": "https://finance.yahoo.com/quote/MSFT",
                    "snippet": "Microsoft Corporation (MSFT) stock is trading at $425.50, up 2.3% today. Year-to-date performance shows +35% growth driven by AI and cloud services.",
                    "date": datetime.now().isoformat()
                },
                {
                    "title": "Microsoft Q4 2024 Earnings Beat Expectations",
                    "url": "https://www.cnbc.com/microsoft-earnings",
                    "snippet": "Microsoft reported Q4 revenue of $62.0 billion, up 16% year-over-year. Azure growth accelerated to 31% driven by AI workloads.",
                    "date": datetime.now().isoformat()
                }
            ]
        elif "autogen" in args.query.lower():
            mock_results = [
                {
                    "title": "AutoGen 0.4 Released - Microsoft Research",
                    "url": "https://microsoft.github.io/autogen",
                    "snippet": "AutoGen 0.4 introduces async architecture, MCP support, and WebSurfer agents for internet access. Major improvements in multi-agent orchestration.",
                    "date": datetime.now().isoformat()
                },
                {
                    "title": "Building Web-Enabled Agents with AutoGen",
                    "url": "https://github.com/microsoft/autogen",
                    "snippet": "Tutorial on implementing web search and browsing capabilities in AutoGen agents using WebSurferAgent and custom tools.",
                    "date": datetime.now().isoformat()
                }
            ]
        else:
            # Generic mock results
            mock_results = [
                {
                    "title": f"Latest information about {args.query}",
                    "url": f"https://example.com/search?q={args.query.replace(' ', '+')}",
                    "snippet": f"Recent developments and insights about {args.query}. This is mock data for development purposes.",
                    "date": datetime.now().isoformat()
                }
            ]
        
        return json.dumps({
            "query": args.query,
            "results": mock_results[:args.max_results],
            "source": "mock",
            "note": "Using mock data - configure BING_API_KEY, SERPER_API_KEY, or GOOGLE_API_KEY for real search"
        }, indent=2)


class WebBrowseArgs(BaseModel):
    """Arguments for web browsing"""
    url: str
    action: Literal["read", "summarize", "extract"] = "read"
    selector: Optional[str] = None  # CSS selector for specific content


class WebBrowseTool(BaseTool):
    """
    Tool for browsing web pages and extracting content.
    Simpler alternative to full WebSurferAgent.
    """
    
    def __init__(self):
        super().__init__(
            args_type=WebBrowseArgs,
            return_type=str,
            name="web_browse",
            description="Browse a web page to read content, summarize, or extract specific information"
        )
    
    async def run(self, args: WebBrowseArgs, cancellation_token=None) -> str:
        """
        Browse a web page and extract content.
        
        Args:
            args: Browse arguments containing URL and action
            cancellation_token: Optional cancellation token for AutoGen
        
        Returns:
            Extracted content or summary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(args.url, follow_redirects=True)
                response.raise_for_status()
                
                # For now, return raw HTML preview
                # In production, you'd use BeautifulSoup or similar to parse
                content = response.text[:1000]  # First 1000 chars
                
                return json.dumps({
                    "url": args.url,
                    "status": response.status_code,
                    "content_preview": content,
                    "action": args.action,
                    "note": "Full HTML parsing not implemented - use WebSurferAgent for advanced browsing"
                }, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Web browse error: {e}")
            return json.dumps({
                "error": str(e),
                "url": args.url
            })


# Export all web tools
WEB_TOOLS = [
    WebSearchTool(),
    WebBrowseTool()
]


def get_web_tools(api_key: Optional[str] = None) -> List[BaseTool]:
    """
    Get all web-related tools for AutoGen agents.
    
    Args:
        api_key: Optional API key for search services
    
    Returns:
        List of web tools
    """
    return [
        WebSearchTool(api_key),
        WebBrowseTool()
    ]