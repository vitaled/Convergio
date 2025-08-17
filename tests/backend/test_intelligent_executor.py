"""
Test Intelligent Tool Executor
Verifies that queries are routed to the correct tools
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools.intelligent_tool_executor import (
    get_intelligent_executor,
    execute_intelligent_query
)


async def test_intelligent_routing():
    """Test that different queries are routed correctly"""
    
    test_queries = [
        # Should use web search
        ("What is Microsoft's Q4 FY2025 revenue?", "web_search"),
        ("Latest Tesla stock price", "web_search"),
        ("Current weather in New York", "web_search"),
        ("Apple earnings announcement today", "web_search"),
        
        # Should use AI chat (general knowledge)
        ("Explain how machine learning works", "ai_chat"),
        ("What is the difference between TCP and UDP?", "ai_chat"),
        ("Best practices for Python programming", "ai_chat"),
        
        # Should use database
        ("How many talents do we have in our database?", "database"),
        ("Show me our current projects", "database"),
        
        # Should use vector search
        ("Find similar documents about AI", "vector_search"),
        ("Search for related content on machine learning", "vector_search"),
    ]
    
    executor = get_intelligent_executor()
    
    print("\n" + "="*80)
    print("🧪 TESTING INTELLIGENT QUERY ROUTING")
    print("="*80)
    
    for query, expected_tool in test_queries:
        print(f"\n📝 Query: {query}")
        print(f"   Expected: {expected_tool}")
        
        # Analyze without executing (for testing)
        analysis = executor.selector.analyze_query(query)
        
        # Determine which tool would be used
        if analysis["needs_web_search"] and analysis["confidence"] >= 0.7:
            actual_tool = "web_search"
        elif "database_query" in analysis["suggested_tools"]:
            actual_tool = "database"
        elif "vector_search" in analysis["suggested_tools"]:
            actual_tool = "vector_search"
        else:
            actual_tool = "ai_chat"
        
        status = "✅" if actual_tool == expected_tool else "❌"
        print(f"   Actual: {actual_tool} {status}")
        print(f"   Confidence: {analysis['confidence']:.0%}")
        print(f"   Reason: {analysis['reason']}")
        
        if actual_tool != expected_tool:
            print(f"   ⚠️ MISMATCH: Expected {expected_tool}, got {actual_tool}")
    
    print("\n" + "="*80)
    print("📊 TOOL SELECTION METRICS")
    print("="*80)
    
    # Test actual execution with a few queries
    print("\n🔄 Testing actual execution...")
    
    # Test web search (requires PERPLEXITY_API_KEY)
    if os.getenv("PERPLEXITY_API_KEY"):
        print("\n1. Testing web search...")
        result = await execute_intelligent_query(
            "What is Microsoft's Q4 FY2025 revenue?"
        )
        print(f"   Tools used: {result['tools_used']}")
        print(f"   Has response: {'web_search' in result['responses']}")
    else:
        print("\n⚠️ Skipping web search test (PERPLEXITY_API_KEY not set)")
    
    # Test AI chat (should always work with OpenAI)
    print("\n2. Testing AI chat...")
    result = await execute_intelligent_query(
        "Explain what a REST API is in simple terms"
    )
    print(f"   Tools used: {result['tools_used']}")
    print(f"   Has response: {'ai_chat' in result['responses']}")
    
    # Get final metrics
    metrics = executor.get_metrics()
    print("\n📈 Final Usage Metrics:")
    print(f"   Total queries: {metrics['total_queries']}")
    for tool, count in metrics['usage'].items():
        if count > 0:
            print(f"   {tool}: {count} ({metrics['percentages'][tool]:.1f}%)")
    
    print("\n✅ Intelligent executor test completed!")


async def test_specific_scenarios():
    """Test specific real-world scenarios"""
    
    print("\n" + "="*80)
    print("🎯 TESTING SPECIFIC SCENARIOS")
    print("="*80)
    
    scenarios = [
        {
            "name": "Financial Query (Amy CFO)",
            "query": "What was Microsoft's revenue in Q4 FY2025?",
            "expected": "web_search",
            "reason": "Current financial data needs real-time lookup"
        },
        {
            "name": "Technical Explanation",
            "query": "How does a neural network learn?",
            "expected": "ai_chat",
            "reason": "General knowledge question"
        },
        {
            "name": "Company News",
            "query": "Latest news about Apple's new product announcements",
            "expected": "web_search",
            "reason": "Current news requires web search"
        },
        {
            "name": "Internal Data",
            "query": "How many employees are in our talent database?",
            "expected": "database",
            "reason": "Internal company data"
        }
    ]
    
    executor = get_intelligent_executor()
    
    for scenario in scenarios:
        print(f"\n🔍 Scenario: {scenario['name']}")
        print(f"   Query: {scenario['query']}")
        print(f"   Expected: {scenario['expected']}")
        print(f"   Reason: {scenario['reason']}")
        
        analysis = executor.selector.analyze_query(scenario['query'])
        print(f"   Analysis:")
        print(f"     - Needs web: {analysis['needs_web_search']}")
        print(f"     - Confidence: {analysis['confidence']:.0%}")
        print(f"     - Query type: {analysis['query_type']}")
        print(f"     - Suggested tools: {analysis['suggested_tools']}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_intelligent_routing())
    asyncio.run(test_specific_scenarios())