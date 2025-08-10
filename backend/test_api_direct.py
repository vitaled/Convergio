#!/usr/bin/env python3
"""
Test diretto dell'endpoint API per il debugging
"""

import asyncio
import json
import httpx

async def test_api_direct():
    """Test diretto dell'endpoint conversation"""
    
    url = "http://localhost:9000/api/v1/agents/conversation"
    
    payload = {
        "message": "Test: say hello",
        "user_id": "test_user",
        "context": {"requires_approval": False}
    }
    
    print(f"=== CALLING API DIRECTLY ===")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            print(f"\n=== RESPONSE ===")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"Response JSON: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response Text: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_direct())