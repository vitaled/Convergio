#!/usr/bin/env python3
"""
Comprehensive Backend Tests for Convergio
Tests all major functionality with gpt-4o-mini model
"""

import asyncio
import json
import os
from typing import Any, Dict
import httpx

# Read base URL from environment
BASE_URL = f"http://localhost:{os.getenv('BACKEND_PORT', '9000')}"

async def test_health_endpoints():
    """Test health check endpoints"""
    print("\n🏥 Testing: Health endpoints")
    
    async with httpx.AsyncClient() as client:
        # Basic health
        response = await client.get(f"{BASE_URL}/health/")
        assert response.status_code == 200
        health = response.json()
        print(f"✅ Basic health: {health['status']}")
        
        # System health
        response = await client.get(f"{BASE_URL}/health/system")
        assert response.status_code == 200
        system_health = response.json()
        db_status = system_health['checks']['database']['status']
        cache_status = system_health['checks']['cache']['status']
        print(f"✅ System health: Database={db_status}, Cache={cache_status}")
        
        # Agent health
        response = await client.get(f"{BASE_URL}/health/agents")
        assert response.status_code == 200
        agent_health = response.json()
        print(f"✅ Agent health: {agent_health['status']}, Count={agent_health.get('agent_count', 0)}")
    
    return True

async def test_api_status():
    """Test API status endpoint"""
    print("\n🔌 Testing: API status")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/system/api-status")
        assert response.status_code == 200
        status = response.json()
        
        print(f"✅ Backend: {status['backend']['connected']} - v{status['backend'].get('version', 'Unknown')}")
        print(f"✅ OpenAI: {status['openai']['connected']} - Model: {status['openai'].get('model', 'None')}")
        print(f"✅ Perplexity: {status['perplexity']['connected']}")
        
        # Check if OpenAI is configured with gpt-4o-mini
        assert status['openai']['connected'], "OpenAI should be connected"
        assert 'gpt-4o-mini' in status['openai'].get('model', ''), f"Model should be gpt-4o-mini, got {status['openai'].get('model')}"
    
    return status

async def test_agent_ecosystem():
    """Test agent management endpoint"""
    print("\n🤖 Testing: Agent Management")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/agent-management/agents")
        assert response.status_code == 200
        agents = response.json()
        
        assert isinstance(agents, list), "Expected agents to be a list"
        agent_count = len(agents)
        print(f"✅ Agent Management Status: healthy")
        print(f"   Total agents: {agent_count}")
        
        # Count agents by tier
        tiers = {}
        for agent in agents:
            tier = agent.get('tier', 'Unknown')
            tiers[tier] = tiers.get(tier, 0) + 1
        
        print(f"   Tier distribution: {tiers}")
        
        # Show some agents
        if agents:
            print("   Sample agents:")
            for agent in agents[:5]:
                print(f"     • {agent['name']}: {agent['role'][:100]}...")
    
    return {"status": "healthy", "agent_count": agent_count, "agents": agents}

async def test_ali_intelligence():
    """Test Ali Intelligence endpoint with simple query"""
    print("\n🧠 Testing: Ali Intelligence (CEO assistant)")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/ali/intelligence",
            json={
                "query": "What is 2+2?",
                "context": {"test": True}
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ali responded: {result.get('response', '')[:100]}...")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
        else:
            print(f"⚠️ Ali Intelligence not available: {response.text}")
    
    return response.status_code == 200

async def test_vector_search():
    """Test vector search functionality"""
    print("\n🔍 Testing: Vector search")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create embedding - This will call OpenAI API and incur costs
        response = await client.post(
            f"{BASE_URL}/api/v1/vector/embeddings",
            json={"text": "Microsoft Q4 earnings"}
        )
        
        if response.status_code == 200:
            embedding_result = response.json()
            print(f"✅ Created embedding")
            print(f"   Model: {embedding_result.get('model', 'Unknown')}")
            print(f"   Dimension: {len(embedding_result.get('embedding', []))}")
            
            # Track OpenAI API cost
            print("💰 Cost incurred: OpenAI embedding API call")
        else:
            print(f"⚠️ Embeddings creation failed: {response.text}")
        
        # Test search
        response = await client.post(
            f"{BASE_URL}/api/v1/vector/search",
            json={
                "query": "financial earnings",
                "table": "documents",
                "limit": 5
            }
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Vector search returned {len(results.get('results', []))} results")
        else:
            print(f"⚠️ Vector search failed: {response.text}")
    
    return True

async def test_cost_management():
    """Test cost management endpoints"""
    print("\n💰 Testing: Cost management")
    async with httpx.AsyncClient() as client:
        # Get current costs
        response = await client.get(f"{BASE_URL}/api/v1/cost-management/realtime/current")
        
        if response.status_code == 200:
            costs = response.json()
            print(f"✅ Cost tracking active:")
            print(f"   Total cost: ${costs.get('total_cost_usd', 0):.4f}")
            print(f"   Total tokens: {costs.get('total_tokens', 0)}")
            print(f"   Interactions: {costs.get('total_interactions', 0)}")
            print(f"   Provider breakdown: {costs.get('provider_breakdown', {})}")
            
            # Get optimization suggestions if endpoint exists
            try:
                response = await client.get(f"{BASE_URL}/api/v1/cost-management/optimization-suggestions")
                if response.status_code == 200:
                    suggestions = response.json()
                    print(f"✅ Got {len(suggestions.get('suggestions', []))} optimization suggestions")
            except Exception as e:
                print(f"ℹ️ Optimization endpoint not available: {e}")
        else:
            print(f"⚠️ Cost management not available: {response.text}")
    
    return True

async def test_workflow_catalog(test_client):
    """Test workflow catalog"""
    print("\n📋 Testing: Workflow catalog")
    response = test_client.get("/api/v1/workflows/catalog")
    
    if response.status_code == 200:
        catalog = response.json()
        workflows = catalog.get('workflows', [])
        print(f"✅ Found {len(workflows)} workflow templates:")
        for wf in workflows:
            print(f"   • {wf['name']}: {wf['description'][:50]}...")
    else:
        print(f"⚠️ Workflow catalog not available: {response.text}")

    return True

async def test_agent_signatures(test_client):
    """Test agent signature generation and verification"""
    print("\n🔐 Testing: Agent signatures")
    # Generate signature
    response = test_client.post(
        "/api/v1/agent-signatures/generate",
        json={
            "agent_id": "amy_cfo",
            "message": "Test financial analysis"
        }
    )

    if response.status_code == 200:
        sig_data = response.json()
        print(f"✅ Signature generated for amy_cfo")
        print(f"   Signature: {sig_data['signature'][:40]}...")
        
        # Verify signature
        response = test_client.post(
            "/api/v1/agent-signatures/verify",
            json={
                "agent_id": "amy_cfo",
                "message": "Test financial analysis",
                "signature": sig_data['signature']
            }
        )
        
        if response.status_code == 200:
            verify = response.json()
            print(f"✅ Signature verification: {verify['valid']}")
            assert verify['valid'], "Signature should be valid"
    else:
        print(f"⚠️ Signature generation failed: {response.text}")

    return True

async def test_database_maintenance(test_client):
    """Test database maintenance endpoints"""
    print("\n🔧 Testing: Database maintenance")
    response = test_client.get("/api/v1/admin/maintenance/status")

    if response.status_code == 200:
        status = response.json()
        print(f"✅ Maintenance scheduler: {status['scheduler_running']}")
        print(f"   Next VACUUM: {status.get('next_vacuum', 'Not scheduled')}")
        print(f"   Next analysis: {status.get('next_analysis', 'Not scheduled')}")
    else:
        print(f"⚠️ Maintenance status not available: {response.text}")

    return True

async def test_talent_management(test_client):
    """Test talent management endpoints"""
    print("\n👥 Testing: Talent management")
    # List talents
    response = test_client.get("/api/v1/talents")

    if response.status_code == 200:
        talents = response.json()
        print(f"✅ Found {len(talents)} talents")
        if talents:
            for talent in talents[:3]:
                print(f"   • {talent.get('name', 'Unknown')}: {talent.get('role', 'Unknown')}")
    else:
        print(f"⚠️ Talents API not available: {response.text}")

    return True

async def test_openai_model(test_client):
    """Test OpenAI model configuration"""
    print("\n🤖 Testing: OpenAI Model (gpt-4o-mini)")
    
    import os
    model = os.getenv('OPENAI_MODEL', 'Not set')
    api_key = os.getenv('OPENAI_API_KEY', '')
    
    print(f"   Environment model: {model}")
    print(f"   API key present: {'Yes' if api_key else 'No'}")
    
    if api_key:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=api_key)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello, gpt-4o-mini is working!' in 5 words or less."}
                ],
                max_tokens=20
            )
            
            content = response.choices[0].message.content
            print(f"✅ Direct OpenAI test: {content}")
            assert content, "Should have response content"
            
        except Exception as e:
            print(f"❌ OpenAI direct test failed: {e}")
            return False
    
    return True

async def main():
    """Run all comprehensive backend tests"""
    print("=" * 60)
    print("🚀 CONVERGIO COMPREHENSIVE BACKEND TESTS")
    print("   Model: gpt-4o-mini")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = test_client.get("/health/")
        if response.status_code != 200:
                print("❌ Backend is not running! Please start it first.")
                return
    except Exception as e:
        print(f"❌ Cannot connect to backend at {BASE_URL}: {e}")
        return
    
    print("✅ Backend is running\n")
    
    # Track test results
    results = []
    
    try:
        # Run all tests
        tests = [
            ("Health Endpoints", test_health_endpoints),
            ("API Status", test_api_status),
            ("OpenAI Model", test_openai_model),
            ("Agent Ecosystem", test_agent_ecosystem),
            ("Ali Intelligence", test_ali_intelligence),
            ("Vector Search", test_vector_search),
            ("Cost Management", test_cost_management),
            ("Workflow Catalog", test_workflow_catalog),
            ("Agent Signatures", test_agent_signatures),
            ("Database Maintenance", test_database_maintenance),
            ("Talent Management", test_talent_management),
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, "✅ PASSED" if result else "⚠️ PARTIAL"))
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                results.append((test_name, "❌ FAILED"))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        for test_name, status in results:
            print(f"{status} {test_name}")
        
        passed = sum(1 for _, s in results if "PASSED" in s)
        total = len(results)
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL TESTS PASSED!")
        elif passed > total * 0.7:
            print("⚠️ MOST TESTS PASSED (some issues)")
        else:
            print("❌ SIGNIFICANT TEST FAILURES")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())