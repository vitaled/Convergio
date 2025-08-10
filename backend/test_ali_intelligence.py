#!/usr/bin/env python3
"""
Test Ali Intelligence System
"""

import asyncio
import json
import httpx

async def test_ali_intelligence():
    """Test Ali's intelligence endpoint"""
    
    print("=" * 80)
    print("TESTING ALI INTELLIGENCE SYSTEM")
    print("=" * 80)
    
    # Test different types of questions for Ali
    test_questions = [
        "What's the trend of MSFT in the last year?",
        "Analyze our Q4 performance",
        "Give me strategic recommendations for 2025",
        "hello",
        "Help me with project planning"
    ]
    
    for question in test_questions:
        print(f"\n🎯 Question for Ali: {question}")
        print("-" * 60)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://localhost:9000/api/v1/ali/intelligence',
                    json={
                        "message": question,
                        "context": {
                            "source": "test",
                            "role": "ceo",
                            "interface": "test_script"
                        },
                        "use_vector_search": True,
                        "use_database_insights": True,
                        "include_strategic_analysis": True
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Ali Response:")
                    print(f"   Response: {result.get('response', 'No response')[:200]}...")
                    print(f"   Data Sources: {result.get('data_sources_used', [])}")
                    print(f"   Confidence: {result.get('confidence_score', 'Unknown')}")
                    print(f"   Reasoning Chain: {len(result.get('reasoning_chain', []))} steps")
                    
                    if result.get('suggested_actions'):
                        print(f"   Actions: {len(result.get('suggested_actions', []))} suggestions")
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"   Response: {response.text[:500]}...")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_ali_intelligence())