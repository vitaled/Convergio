#!/usr/bin/env python3
"""
Test script for cost tracking functionality
"""

import asyncio
import json
import uuid
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger()

BASE_URL = "http://localhost:9000/api/v1"

async def test_cost_tracking():
    """Test the complete cost tracking flow"""
    
    print("🧪 Testing Cost Tracking System\n")
    
    # Generate unique session and conversation IDs
    session_id = f"test-session-{uuid.uuid4().hex[:8]}"
    conversation_id = f"test-conv-{uuid.uuid4().hex[:8]}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # Test 1: Check current pricing
        print("1️⃣ Testing pricing endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/cost-management/pricing/current")
            if response.status_code == 200:
                pricing_data = response.json()
                print(f"✅ Pricing data retrieved: {len(pricing_data.get('providers', {}))} providers")
                
                # Show OpenAI pricing
                openai_models = pricing_data.get('providers', {}).get('openai', [])
                if openai_models:
                    gpt4o = next((m for m in openai_models if m['model'] == 'gpt-4o'), None)
                    if gpt4o:
                        print(f"   GPT-4o: ${gpt4o['input_price_per_1k']}/${gpt4o['output_price_per_1k']} per 1K tokens")
            else:
                print(f"❌ Pricing endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing pricing: {e}")
        
        # Test 2: Get initial realtime overview
        print("\n2️⃣ Testing realtime cost overview...")
        try:
            response = await client.get(f"{BASE_URL}/cost-management/realtime/current")
            if response.status_code == 200:
                initial_data = response.json()
                print(f"✅ Initial cost overview: ${initial_data.get('total_cost_usd', 0):.4f} total")
                print(f"   Today: ${initial_data.get('today_cost_usd', 0):.4f}")
                print(f"   Status: {initial_data.get('status', 'unknown')}")
            else:
                print(f"❌ Realtime overview failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing realtime overview: {e}")
        
        # Test 3: Record test interactions
        print("\n3️⃣ Recording test interactions...")
        
        test_interactions = [
            {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "provider": "openai",
                "model": "gpt-4o",
                "input_tokens": 100,
                "output_tokens": 150,
                "agent_id": "ali_chief_of_staff",
                "agent_name": "Ali",
                "request_type": "chat",
                "response_time_ms": 1200,
                "metadata": {"test": "cost_tracking_test_1"}
            },
            {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "input_tokens": 200,
                "output_tokens": 300,
                "agent_id": "amy_cfo",
                "agent_name": "Amy",
                "request_type": "chat",
                "response_time_ms": 800,
                "metadata": {"test": "cost_tracking_test_2"}
            },
            {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "provider": "perplexity",
                "model": "sonar-pro",
                "input_tokens": 50,
                "output_tokens": 100,
                "agent_id": "baccio_tech_architect",
                "agent_name": "Baccio",
                "request_type": "search",
                "response_time_ms": 600,
                "metadata": {"test": "cost_tracking_test_3"}
            }
        ]
        
        recorded_costs = []
        for i, interaction in enumerate(test_interactions, 1):
            try:
                response = await client.post(f"{BASE_URL}/cost-management/interactions", json=interaction)
                if response.status_code == 200:
                    result = response.json()
                    cost = result.get('cost_breakdown', {}).get('total_cost_usd', 0)
                    recorded_costs.append(cost)
                    print(f"✅ Interaction {i}: {interaction['provider']}/{interaction['model']} - ${cost:.6f}")
                    print(f"   Session total: ${result.get('session_total', 0):.6f}")
                else:
                    print(f"❌ Interaction {i} failed: {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ Error recording interaction {i}: {e}")
        
        # Test 4: Check updated realtime overview
        print("\n4️⃣ Checking updated cost overview...")
        try:
            await asyncio.sleep(1)  # Give database time to update
            response = await client.get(f"{BASE_URL}/cost-management/realtime/current")
            if response.status_code == 200:
                updated_data = response.json()
                print(f"✅ Updated cost overview: ${updated_data.get('total_cost_usd', 0):.6f} total")
                print(f"   Today: ${updated_data.get('today_cost_usd', 0):.6f}")
                
                # Show provider breakdown
                providers = updated_data.get('provider_breakdown', {})
                if providers:
                    print("   Provider breakdown:")
                    for provider, cost in providers.items():
                        print(f"     {provider}: ${cost:.6f}")
                        
                # Show model breakdown
                models = updated_data.get('model_breakdown', {})
                if models:
                    print("   Model breakdown:")
                    for model, cost in list(models.items())[:3]:  # Show top 3
                        print(f"     {model}: ${cost:.6f}")
            else:
                print(f"❌ Updated overview failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error checking updated overview: {e}")
        
        # Test 5: Get session details
        print("\n5️⃣ Testing session cost details...")
        try:
            response = await client.get(f"{BASE_URL}/cost-management/sessions/{session_id}")
            if response.status_code == 200:
                session_data = response.json()
                print(f"✅ Session details: ${session_data.get('total_cost_usd', 0):.6f} total")
                print(f"   Interactions: {session_data.get('total_interactions', 0)}")
                print(f"   Tokens: {session_data.get('total_tokens', 0):,}")
                
                # Show API calls
                api_calls = session_data.get('api_calls', [])
                print(f"   API calls recorded: {len(api_calls)}")
                
            else:
                print(f"❌ Session details failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting session details: {e}")
        
        # Test 6: Get agent cost details
        print("\n6️⃣ Testing agent cost details...")
        try:
            response = await client.get(f"{BASE_URL}/cost-management/agents/ali_chief_of_staff/costs?days=1")
            if response.status_code == 200:
                agent_data = response.json()
                print(f"✅ Ali cost data: ${agent_data.get('total_cost_usd', 0):.6f} total")
                print(f"   Calls: {agent_data.get('total_calls', 0)}")
                print(f"   Avg per call: ${agent_data.get('avg_cost_per_call', 0):.6f}")
                
                # Show model breakdown
                models = agent_data.get('model_breakdown', [])
                for model_data in models:
                    print(f"   {model_data['provider']}/{model_data['model']}: ${model_data['total_cost']:.6f}")
                    
            else:
                print(f"❌ Agent costs failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting agent costs: {e}")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"Session ID: {session_id}")
        print(f"Total test cost: ${sum(recorded_costs):.6f}")
        print(f"Test interactions: {len([c for c in recorded_costs if c > 0])}")
        
        print("\n✅ Cost tracking system test completed!")

if __name__ == "__main__":
    asyncio.run(test_cost_tracking())