"""
Smoke tests for tool execution
Verifies that tools actually execute and return real data
"""

import asyncio
import os
import pytest
import json
from unittest.mock import patch

# Add parent directory to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.agents.tools.convergio_tools import (
    VectorSearchTool, VectorSearchArgs,
    TalentsQueryTool, TalentsQueryArgs,
    BusinessIntelligenceTool, BusinessIntelligenceArgs,
    EngagementAnalyticsTool, EngagementAnalyticsArgs
)
from src.agents.tools.web_search_tool import WebSearchTool, WebSearchArgs
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


class TestToolExecution:
    """Test suite for verifying tool execution"""
    
    @pytest.mark.asyncio
    async def test_web_search_tool_execution(self):
        """Test that WebSearchTool executes with real provider"""
        tool = WebSearchTool()
        
        # Check provider configuration
        health = tool.provider_health()
        
        if health['configured']:
            # If Perplexity is configured, verify real search
            args = WebSearchArgs(query="Microsoft Azure cloud", max_results=2)
            result = await tool.run(args)
            
            # Parse result
            data = json.loads(result)
            
            # Verify real data returned
            assert 'error' not in data or data['error'] is None
            assert 'results' in data
            assert data.get('source') == 'perplexity'
            
            # Verify content is not mock
            results_str = str(data.get('results', ''))
            assert 'mock' not in results_str.lower()
            assert len(results_str) > 100  # Real results are detailed
        else:
            # If no provider configured, verify error message
            args = WebSearchArgs(query="test query")
            result = await tool.run(args)
            data = json.loads(result)
            
            assert 'error' in data
            assert 'PERPLEXITY_API_KEY' in data['error']
            
    @pytest.mark.asyncio
    async def test_vector_search_tool_execution(self):
        """Test that VectorSearchTool executes without errors"""
        tool = VectorSearchTool()
        
        # Test embedding and search
        args = VectorSearchArgs(query="project management best practices", top_k=3)
        result = await tool.run(args)
        
        # Should return a string result (even if no data found)
        assert isinstance(result, str)
        
        # Should not have unhandled errors
        assert 'Error performing vector search' not in result or 'No relevant results found' in result
        
    @pytest.mark.asyncio
    async def test_talents_query_tool_execution(self):
        """Test that TalentsQueryTool executes"""
        tool = TalentsQueryTool()
        
        # Test different query types
        for query_type in ["count", "skills", "all"]:
            args = TalentsQueryArgs(query_type=query_type)
            result = await tool.run(args)
            
            # Should return a string result
            assert isinstance(result, str)
            
            # Parse if JSON
            if result.startswith('{'):
                data = json.loads(result)
                # Should have some structure
                assert isinstance(data, dict)
                
    @pytest.mark.asyncio
    async def test_business_intelligence_tool_execution(self):
        """Test that BusinessIntelligenceTool executes"""
        tool = BusinessIntelligenceTool()
        
        # Test overview
        args = BusinessIntelligenceArgs(focus_area="overview")
        result = await tool.run(args)
        
        # Should return JSON string
        assert isinstance(result, str)
        data = json.loads(result)
        
        # Should have report structure
        assert 'business_intelligence_report' in data
        assert 'generated_at' in data['business_intelligence_report']
        
    @pytest.mark.asyncio
    async def test_engagement_analytics_tool_execution(self):
        """Test that EngagementAnalyticsTool executes"""
        tool = EngagementAnalyticsTool()
        
        # Test summary
        args = EngagementAnalyticsArgs(analysis_type="summary")
        result = await tool.run(args)
        
        # Should return a result
        assert isinstance(result, str)
        
        # If JSON, verify structure
        if result.startswith('{'):
            data = json.loads(result)
            assert isinstance(data, dict)
            
    @pytest.mark.asyncio
    async def test_autogen_agent_tool_execution(self):
        """Test that AutoGen agents execute tools correctly"""
        
        # Skip if no OpenAI key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not configured")
            
        client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create agent with web search tool
        tool = WebSearchTool()
        agent = AssistantAgent(
            name="test_agent",
            model_client=client,
            system_message="You are a test agent that uses tools.",
            tools=[tool]
        )
        
        # Test tool execution through agent
        result = await agent.run(task="Search for Python programming tutorials")
        
        # Verify result has messages
        assert hasattr(result, 'messages')
        assert len(result.messages) > 0
        
        # Check for tool execution events
        tool_executed = False
        for msg in result.messages:
            msg_str = str(msg)
            if 'ToolCallRequestEvent' in msg_str or 'ToolCallExecutionEvent' in msg_str:
                tool_executed = True
                break
                
        # If Perplexity is configured, tool should execute
        if tool.provider_health()['configured']:
            assert tool_executed, "Tool should have been executed"
            
    @pytest.mark.asyncio
    async def test_no_smart_fallbacks(self):
        """Test that smart fallbacks are disabled"""
        from src.agents.utils.config import get_settings
        
        settings = get_settings()
        
        # Verify fallbacks are disabled
        assert settings.smart_fallback_enabled == False
        assert settings.fake_internal_data_enabled == False
        
        # Test AgentIntelligence doesn't use fallbacks
        from src.agents.services.agent_intelligence import AgentIntelligence
        
        ai = AgentIntelligence("test_agent")
        
        # Test with a longer, clearer message to avoid clarification request
        test_message = "What is the company revenue for last quarter? Please provide exact numbers."
        
        # Without API key, should return error, not fallback
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            response = await ai.generate_intelligent_response(
                test_message,
                context={}
            )
            
            # Should indicate error or unavailable, not provide fake data
            # Also not provide placeholder data like "$52.9B"
            assert not any(fake_indicator in response for fake_indicator in [
                "$52.9B", "$25.9B", "$14.9B", "[placeholder]"
            ]), f"Response should not contain fake data: {response}"


if __name__ == "__main__":
    # Run tests
    asyncio.run(TestToolExecution().test_web_search_tool_execution())
    asyncio.run(TestToolExecution().test_vector_search_tool_execution())
    asyncio.run(TestToolExecution().test_talents_query_tool_execution())
    asyncio.run(TestToolExecution().test_business_intelligence_tool_execution())
    asyncio.run(TestToolExecution().test_engagement_analytics_tool_execution())
    asyncio.run(TestToolExecution().test_no_smart_fallbacks())
    print("✅ All smoke tests passed!")