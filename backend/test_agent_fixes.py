#!/usr/bin/env python3
"""
Test script to validate all agent fixes
Tests:
1. Amy returns real data ($76.4B for Microsoft Q4 FY2025)
2. agents_used is properly populated
3. Single agent responds (not multiple)
4. Correct agent routing
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import structlog
# We'll need to create the orchestrator manually
from src.agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
from src.agents.services.cost_tracker import CostTracker
from src.agents.services.redis_state_manager import RedisStateManager
from src.agents.tools.autogen_tools import web_search

logger = structlog.get_logger()


async def test_web_search_tool():
    """Test 1: Verify web search returns real data"""
    print("\n" + "="*60)
    print("TEST 1: Web Search Tool with Perplexity")
    print("="*60)
    
    query = "Microsoft Q4 FY2025 revenue"
    result = await web_search(query)
    result_data = json.loads(result)
    
    print(f"Query: {query}")
    print(f"Result: {result_data.get('results', 'No results')[:300]}...")
    
    # Check if it contains the correct revenue
    if "76.4" in result or "seventy-six" in result.lower():
        print("✅ PASS: Web search returns correct Microsoft revenue ($76.4 billion)")
        return True
    else:
        print("❌ FAIL: Web search did not return correct revenue")
        return False


async def test_amy_with_financial_query():
    """Test 2: Amy CFO returns real financial data"""
    print("\n" + "="*60)
    print("TEST 2: Amy CFO with Financial Query")
    print("="*60)
    
    # Create orchestrator
    state_manager = RedisStateManager()
    cost_tracker = CostTracker()
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    await orchestrator.initialize()
    
    query = "What is Microsoft's Q4 FY2025 revenue?"
    result = await orchestrator.orchestrate_conversation(
        message=query,
        user_id="test_user",
        conversation_id="test_amy_001",
        context={"agent_name": "amy_cfo"}  # Direct to Amy
    )
    
    print(f"Query: {query}")
    print(f"Response: {result.response[:500]}...")
    print(f"Agents used: {result.agents_used}")
    
    # Check results
    success = True
    
    # Check if Amy was used
    if "amy_cfo" in result.agents_used or "amy" in str(result.agents_used).lower():
        print("✅ Amy CFO was used")
    else:
        print(f"❌ Amy CFO not in agents_used: {result.agents_used}")
        success = False
    
    # Check if response contains correct revenue
    if "76.4" in result.response or "seventy-six" in result.response.lower():
        print("✅ Response contains correct revenue ($76.4 billion)")
    else:
        print("❌ Response does not contain correct revenue")
        success = False
    
    return success


async def test_agent_tracking():
    """Test 3: Verify agents_used is populated correctly"""
    print("\n" + "="*60)
    print("TEST 3: Agent Tracking (agents_used)")
    print("="*60)
    
    # Create orchestrator
    state_manager = RedisStateManager()
    cost_tracker = CostTracker()
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    await orchestrator.initialize()
    
    # Test with a simple query
    query = "Hello, can you help me?"
    result = await orchestrator.orchestrate_conversation(
        message=query,
        user_id="test_user",
        conversation_id="test_tracking_001"
    )
    
    print(f"Query: {query}")
    print(f"Agents used: {result.agents_used}")
    print(f"Number of agents: {len(result.agents_used)}")
    
    if result.agents_used and len(result.agents_used) > 0:
        print(f"✅ PASS: agents_used is populated with {len(result.agents_used)} agent(s)")
        return True
    else:
        print("❌ FAIL: agents_used is empty")
        return False


async def test_single_agent_response():
    """Test 4: Verify only one agent responds to queries"""
    print("\n" + "="*60)
    print("TEST 4: Single Agent Response")
    print("="*60)
    
    # Create orchestrator
    state_manager = RedisStateManager()
    cost_tracker = CostTracker()
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    await orchestrator.initialize()
    
    test_cases = [
        ("What's our total revenue?", ["amy", "cfo", "diana"]),
        ("How many talents do we have?", ["ali", "davide"]),
        ("What's our security status?", ["luca"]),
    ]
    
    all_passed = True
    
    for query, expected_agents in test_cases:
        result = await orchestrator.orchestrate_conversation(
            message=query,
            user_id="test_user",
            conversation_id=f"test_single_{query[:10]}"
        )
        
        print(f"\nQuery: {query}")
        print(f"Agents used: {result.agents_used}")
        print(f"Expected one of: {expected_agents}")
        
        # Check single agent responded
        if len(result.agents_used) == 1:
            print(f"✅ Single agent responded: {result.agents_used[0]}")
            
            # Check if it's the right type of agent
            agent_name = result.agents_used[0].lower()
            if any(exp in agent_name for exp in expected_agents):
                print(f"✅ Correct agent type selected")
            else:
                print(f"⚠️ Unexpected agent selected (but still single response)")
        else:
            print(f"❌ Multiple agents responded: {result.agents_used}")
            all_passed = False
    
    return all_passed


async def test_routing_accuracy():
    """Test 5: Verify queries route to appropriate specialists"""
    print("\n" + "="*60)
    print("TEST 5: Agent Routing Accuracy")
    print("="*60)
    
    # Create orchestrator
    state_manager = RedisStateManager()
    cost_tracker = CostTracker()
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    await orchestrator.initialize()
    
    routing_tests = [
        {
            "query": "What's Microsoft's latest quarterly revenue?",
            "expected_agent": "amy",
            "reason": "Financial query should go to CFO"
        },
        {
            "query": "Show me the performance dashboard metrics",
            "expected_agent": "diana",
            "reason": "Dashboard query should go to Diana"
        },
        {
            "query": "What's our system architecture?",
            "expected_agent": "baccio",
            "reason": "Technical query should go to architect"
        },
        {
            "query": "Are there any security vulnerabilities?",
            "expected_agent": "luca",
            "reason": "Security query should go to Luca"
        }
    ]
    
    all_passed = True
    
    for test in routing_tests:
        result = await orchestrator.orchestrate_conversation(
            message=test["query"],
            user_id="test_user",
            conversation_id=f"test_routing_{test['expected_agent']}"
        )
        
        print(f"\nQuery: {test['query']}")
        print(f"Expected: {test['expected_agent']}")
        print(f"Actual: {result.agents_used}")
        print(f"Reason: {test['reason']}")
        
        if result.agents_used and any(test["expected_agent"] in agent.lower() for agent in result.agents_used):
            print(f"✅ Correctly routed to {test['expected_agent']}")
        else:
            print(f"❌ Not routed to expected agent")
            all_passed = False
    
    return all_passed


async def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("CONVERGIO AGENT FIXES VALIDATION SUITE")
    print("🚀"*30)
    
    results = {}
    
    # Run tests
    try:
        results["web_search"] = await test_web_search_tool()
    except Exception as e:
        print(f"❌ Web search test failed with error: {e}")
        results["web_search"] = False
    
    try:
        results["amy_financial"] = await test_amy_with_financial_query()
    except Exception as e:
        print(f"❌ Amy financial test failed with error: {e}")
        results["amy_financial"] = False
    
    try:
        results["agent_tracking"] = await test_agent_tracking()
    except Exception as e:
        print(f"❌ Agent tracking test failed with error: {e}")
        results["agent_tracking"] = False
    
    try:
        results["single_response"] = await test_single_agent_response()
    except Exception as e:
        print(f"❌ Single response test failed with error: {e}")
        results["single_response"] = False
    
    try:
        results["routing"] = await test_routing_accuracy()
    except Exception as e:
        print(f"❌ Routing test failed with error: {e}")
        results["routing"] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s}: {status}")
    
    total_passed = sum(1 for p in results.values() if p)
    total_tests = len(results)
    
    print("\n" + "="*60)
    print(f"TOTAL: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Agents are working correctly!")
        print("\nKey achievements:")
        print("✅ Amy returns real data ($76.4B for Microsoft)")
        print("✅ agents_used field is properly populated")
        print("✅ Single agent responds to queries")
        print("✅ Queries route to appropriate specialists")
    else:
        print("⚠️ Some tests failed. Review the output above for details.")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())