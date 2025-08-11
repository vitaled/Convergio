#!/usr/bin/env python
"""
Test Amy CFO with Intelligent Tool Executor
Verify that Amy correctly uses web search for financial queries
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.tools.intelligent_tool_executor import execute_intelligent_query


async def test_amy_scenarios():
    """Test Amy CFO scenarios with intelligent routing"""
    
    print("\n" + "="*80)
    print("🎩 TESTING AMY CFO WITH INTELLIGENT TOOL EXECUTOR")
    print("="*80)
    
    # Amy's typical queries
    amy_queries = [
        {
            "query": "What is Microsoft's Q4 FY2025 revenue?",
            "expected_tool": "web_search",
            "expected_answer": "$76.4 billion"  # The correct answer
        },
        {
            "query": "What are Apple's latest quarterly earnings?",
            "expected_tool": "web_search",
            "expected_answer": "real-time data"
        },
        {
            "query": "Calculate the ROI if we invest $1M with 15% annual return over 5 years",
            "expected_tool": "ai_chat",
            "expected_answer": "calculation"
        },
        {
            "query": "What is EBITDA and how is it calculated?",
            "expected_tool": "ai_chat",
            "expected_answer": "definition"
        }
    ]
    
    for scenario in amy_queries:
        print(f"\n📊 Query: {scenario['query']}")
        print(f"   Expected tool: {scenario['expected_tool']}")
        
        # Execute the query
        result = await execute_intelligent_query(scenario['query'])
        
        # Check routing
        tools_used = result.get('tools_used', [])
        if scenario['expected_tool'] in tools_used:
            print(f"   ✅ Correct tool used: {tools_used}")
        else:
            print(f"   ❌ Wrong tool used: {tools_used} (expected {scenario['expected_tool']})")
        
        # Check response
        responses = result.get('responses', {})
        if responses:
            tool_key = tools_used[0] if tools_used else None
            if tool_key and tool_key in responses:
                response_data = responses[tool_key]
                
                if tool_key == 'web_search':
                    # Check if we got real data from Perplexity
                    if 'results' in response_data:
                        print(f"   📈 Web search results received")
                        print(f"   Content preview: {str(response_data['results'])[:200]}...")
                        
                        # Check for the expected revenue figure
                        if 'Microsoft' in scenario['query'] and '$76' in str(response_data['results']):
                            print(f"   ✅ CORRECT: Found Microsoft Q4 FY2025 revenue (~$76.4B)")
                        elif 'error' in response_data:
                            print(f"   ⚠️ Error: {response_data['error']}")
                    else:
                        print(f"   ⚠️ No results in web search response")
                        
                elif tool_key == 'ai_chat':
                    if 'response' in response_data:
                        print(f"   💬 AI chat response received")
                        print(f"   Response preview: {response_data['response'][:200]}...")
                    elif 'error' in response_data:
                        print(f"   ⚠️ Error: {response_data['error']}")
    
    print("\n" + "="*80)
    print("📊 FINANCIAL DATA VERIFICATION")
    print("="*80)
    
    # Specific test for Microsoft revenue
    print("\n🔍 Testing Microsoft Q4 FY2025 Revenue Query...")
    ms_result = await execute_intelligent_query("What is Microsoft's Q4 FY2025 revenue?")
    
    if 'web_search' in ms_result.get('tools_used', []):
        print("✅ Correctly used web search")
        
        web_response = ms_result['responses'].get('web_search', {})
        if web_response and 'results' in web_response:
            results_str = str(web_response['results'])
            
            # Check for the correct figure
            if any(x in results_str.lower() for x in ['76.4', '76,4', 'seventy-six']):
                print("✅ FOUND CORRECT REVENUE: $76.4 billion")
                print("✅ Amy CFO is now returning REAL data, not fake!")
            elif any(x in results_str.lower() for x in ['60', 'sixty']):
                print("❌ STILL GETTING FAKE DATA: ~$60 billion")
                print("❌ This is the invented data, not real!")
            else:
                print(f"🔍 Revenue data found: {results_str[:500]}")
    else:
        print("❌ Did not use web search - would return fake data!")
    
    print("\n✅ Test completed!")


async def test_intelligent_decision_making():
    """Test the decision-making logic"""
    
    print("\n" + "="*80)
    print("🧠 TESTING INTELLIGENT DECISION MAKING")
    print("="*80)
    
    from src.agents.tools.smart_tool_selector import SmartToolSelector
    
    selector = SmartToolSelector()
    
    # Test various query types
    test_cases = [
        ("Microsoft Q4 FY2025 earnings", True, "financial + time-sensitive"),
        ("What is a P/E ratio?", False, "general knowledge"),
        ("Tesla stock price today", True, "real-time market data"),
        ("How to calculate NPV", False, "general knowledge"),
        ("Latest Fed interest rate decision", True, "current news"),
        ("Explain compound interest", False, "general knowledge"),
    ]
    
    for query, should_search, reason in test_cases:
        analysis = selector.analyze_query(query)
        decision = selector.should_use_web_search(query, threshold=0.7)
        
        status = "✅" if decision == should_search else "❌"
        print(f"\n📝 Query: {query}")
        print(f"   Expected web search: {should_search} ({reason})")
        print(f"   Decision: {decision} {status}")
        print(f"   Confidence: {analysis['confidence']:.0%}")
        print(f"   Reason: {analysis['reason']}")


if __name__ == "__main__":
    print("\n🚀 Starting Amy CFO Intelligent Tool Test...")
    
    # Check if Perplexity is configured
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("\n⚠️ WARNING: PERPLEXITY_API_KEY not set")
        print("Amy won't be able to get real financial data!")
        print("She will fall back to general AI knowledge\n")
    else:
        print("✅ Perplexity API configured - Amy can access real data!\n")
    
    # Run tests
    asyncio.run(test_amy_scenarios())
    asyncio.run(test_intelligent_decision_making())