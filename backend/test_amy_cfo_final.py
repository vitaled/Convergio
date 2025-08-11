#!/usr/bin/env python3
"""
Final test for Amy CFO with real data
"""

import asyncio
import os
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.agents.tools.web_search_tool import WebSearchTool

async def test_amy_cfo():
    """Test Amy CFO returns correct Microsoft Q4 FY2025 revenue"""
    
    # Set Perplexity API key
    os.environ['PERPLEXITY_API_KEY'] = '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'
    
    print("🧪 Testing Amy CFO with real web search...")
    print("=" * 60)
    
    # Create OpenAI client
    client = OpenAIChatCompletionClient(
        model='gpt-4o',
        api_key=os.environ.get('OPENAI_API_KEY')
    )
    
    # Create web search tool
    tool = WebSearchTool()
    print(f"✅ Web search provider: {tool.provider_health()}")
    
    # Create Amy CFO agent
    amy = AssistantAgent(
        name='amy_cfo',
        model_client=client,
        system_message="""You are Amy, the Chief Financial Officer. 
        You provide accurate, up-to-date financial data and analysis.
        Always use web search to get the latest financial information.
        Be precise with numbers and cite your sources.""",
        tools=[tool]
    )
    
    # Test question
    question = "What was Microsoft's Q4 FY2025 revenue reported in July 2025?"
    print(f"\n📊 Question: {question}")
    print("-" * 60)
    
    # Get response
    result = await amy.run(task=question)
    
    # Extract the final answer
    if hasattr(result, 'messages'):
        for msg in result.messages:
            if hasattr(msg, 'content') and msg.content:
                content = str(msg.content)
                # Skip tool call messages
                if 'FunctionCall' in content or 'FunctionExecutionResult' in content:
                    continue
                # Skip the question echo
                if content == question:
                    continue
                    
                print(f"\n💬 Amy's Answer:")
                print(content)
                
                # Verify the correct answer is present
                if "$76.4 billion" in content or "76.4 billion" in content:
                    print("\n✅ SUCCESS! Amy returned the correct revenue: $76.4 billion")
                    return True
                else:
                    print("\n❌ FAILED! Amy did not return the correct revenue ($76.4 billion)")
                    return False
    
    print("\n❌ No response from Amy")
    return False

if __name__ == "__main__":
    success = asyncio.run(test_amy_cfo())
    exit(0 if success else 1)