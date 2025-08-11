#!/usr/bin/env python
"""
Test all agents to ensure they work properly
"""

import asyncio
import json
import httpx
from typing import Dict, Any, List

# Agent test cases
TEST_QUERIES = {
    "ali-chief-of-staff": "A chi posso chiedere un consiglio di marketing?",
    "amy-cfo": "Quanto ha fatturato Microsoft nel Q4 FY2025?",
    "baccio-tech-architect": "What's the best architecture for a microservices system?",
    "sofia-marketing-strategist": "Come posso migliorare il brand positioning?",
    "luca-security-expert": "What are the OWASP top 10 vulnerabilities?",
    "giulia-hr-talent-acquisition": "How to improve employee retention?",
    "antonio-strategy-expert": "What's a good market entry strategy?",
    "omri-data-scientist": "How to implement a recommendation system?",
    "davide-project-manager": "How to manage project risks?",
    "sara-ux-ui-designer": "Best practices for mobile UX design?",
}

async def test_agent_direct(agent_name: str, query: str) -> Dict[str, Any]:
    """Test a single agent directly"""
    
    url = "http://localhost:9000/api/v1/agents/process"
    
    payload = {
        "agent_name": agent_name,
        "message": query,
        "conversation_id": f"test-{agent_name}",
        "debug_mode": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                return {
                    "agent": agent_name,
                    "success": True,
                    "response": response.json()
                }
            else:
                return {
                    "agent": agent_name,
                    "success": False,
                    "error": f"Status {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "agent": agent_name,
                "success": False,
                "error": str(e)
            }

async def test_orchestrator(query: str) -> Dict[str, Any]:
    """Test the main orchestrator"""
    
    url = "http://localhost:9000/api/v1/agents/orchestrate"
    
    payload = {
        "message": query,
        "user_id": "test-user",
        "conversation_id": "test-orchestrator"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                return {
                    "success": True,
                    "response": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Status {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

async def check_web_search_capability():
    """Test if web search is working"""
    
    # Test with a query that requires real-time data
    queries = [
        "What is Microsoft's Q4 FY2025 revenue?",
        "What's the current Tesla stock price?",
        "Latest news about Apple?"
    ]
    
    print("\n🌐 TESTING WEB SEARCH CAPABILITY")
    print("=" * 80)
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        result = await test_orchestrator(query)
        
        if result["success"]:
            response_text = result["response"].get("response", "")
            agents_used = result["response"].get("agents_used", [])
            
            # Check if response contains real data (not just repeating question)
            if query.lower() in response_text.lower() and len(response_text) < len(query) * 2:
                print(f"   ❌ Agent is just repeating the question!")
            elif "microsoft" in query.lower() and ("76" in response_text or "seventy" in response_text.lower()):
                print(f"   ✅ Got real Microsoft revenue data ($76.4B)")
            elif "i don't have" in response_text.lower() or "cannot access" in response_text.lower():
                print(f"   ⚠️ Agent cannot access web data")
            else:
                print(f"   ℹ️ Response preview: {response_text[:200]}...")
            
            print(f"   Agents used: {', '.join(agents_used)}")
        else:
            print(f"   ❌ Error: {result['error']}")

async def main():
    """Run all tests"""
    
    print("\n🤖 TESTING ALL CONVERGIO AGENTS")
    print("=" * 80)
    
    # Test ecosystem status
    print("\n📊 Checking ecosystem status...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:9000/api/v1/agents/ecosystem")
        ecosystem = response.json()
        print(f"   Status: {ecosystem['status']}")
        print(f"   Total agents: {ecosystem['total_agents']}")
        print(f"   Active agents: {ecosystem['active_agents']}")
    
    # Wait for initialization if needed
    if ecosystem['status'] == 'initializing':
        print("   ⏳ Waiting for agents to initialize...")
        await asyncio.sleep(5)
    
    # Test individual agents
    print("\n🧪 TESTING INDIVIDUAL AGENTS")
    print("=" * 80)
    
    for agent_name, query in TEST_QUERIES.items():
        print(f"\n🤖 Testing {agent_name}")
        print(f"   Query: {query}")
        
        result = await test_agent_direct(agent_name, query)
        
        if result["success"]:
            response_data = result["response"]
            
            # Check if it's a real response or just repetition
            if "result" in response_data and response_data["result"]:
                agent_response = response_data["result"].get("response", "")
                
                # Check for question repetition
                if query.lower() in agent_response.lower() and len(agent_response) < len(query) * 2:
                    print(f"   ❌ FAILURE: Agent is repeating the question!")
                    print(f"   Response: {agent_response[:200]}")
                else:
                    print(f"   ✅ SUCCESS: Agent responded properly")
                    print(f"   Response preview: {agent_response[:200]}...")
            else:
                print(f"   ⚠️ No result in response")
                print(f"   Response: {json.dumps(response_data, indent=2)[:500]}")
        else:
            print(f"   ❌ ERROR: {result['error'][:200]}")
    
    # Test web search capability
    await check_web_search_capability()
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())