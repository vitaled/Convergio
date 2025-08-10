#!/usr/bin/env python3
"""
Standalone test to debug AutoGen model issues with gpt-4o-mini
"""

import os
import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import CreateResult, ModelInfo
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Read API key from .env file manually
def get_api_key():
    env_path = "/Users/roberdan/GitHub/convergio/backend/.env"
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("OPENAI_API_KEY="):
                value = line.split('=', 1)[1]
                # Strip quotes if present
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                return value
    raise ValueError("OPENAI_API_KEY not found in .env")

async def test_model_configurations():
    """Test different model configurations with AutoGen"""
    api_key = get_api_key()
    
    # Test configurations
    test_configs = [
        {
            "name": "gpt-4o-mini without model_info",
            "config": {
                "model": "gpt-4o-mini",
                "api_key": api_key,
            }
        },
        {
            "name": "gpt-4o-mini with model_info",
            "config": {
                "model": "gpt-4o-mini",
                "api_key": api_key,
                "model_info": {
                    "vision": False,
                    "function_calling": True,
                    "json_output": True,
                    "family": "openai",
                    "structured_output": True,
                }
            }
        },
        {
            "name": "gpt-4o-mini with TypedDict ModelInfo",
            "config": {
                "model": "gpt-4o-mini",
                "api_key": api_key,
                "model_info": ModelInfo(
                    vision=False,
                    function_calling=True,
                    json_output=True,
                    family="openai",
                    structured_output=True,
                )
            }
        },
    ]
    
    for test in test_configs:
        print(f"\n{'='*60}")
        print(f"Testing: {test['name']}")
        print(f"Model: {test['config']['model']}")
        print(f"Has model_info: {'model_info' in test['config']}")
        
        try:
            # Create client
            client = OpenAIChatCompletionClient(**test['config'])
            print(f"✅ Client created successfully")
            
            # Try to make a simple call
            messages = [
                {"role": "user", "content": "Say 'test' and nothing else"}
            ]
            
            result = await client.create(
                messages=messages,
                extra_create_args={"max_tokens": 10, "temperature": 0.1}
            )
            
            if isinstance(result, CreateResult):
                print(f"✅ API call successful")
                print(f"Response: {result.content}")
            else:
                print(f"❌ Unexpected result type: {type(result)}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

async def test_direct_openai():
    """Test direct OpenAI API call to verify the model works"""
    import openai
    
    api_key = get_api_key()
    client = openai.OpenAI(api_key=api_key)
    
    print(f"\n{'='*60}")
    print("Testing direct OpenAI API call with gpt-4o-mini")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'test' and nothing else"}
            ],
            max_tokens=10,
            temperature=0.1
        )
        print(f"✅ Direct OpenAI call successful")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Direct OpenAI call failed: {e}")

if __name__ == "__main__":
    print("Testing AutoGen with gpt-4o-mini model")
    print("="*60)
    
    # First test direct OpenAI
    asyncio.run(test_direct_openai())
    
    # Then test AutoGen configurations
    asyncio.run(test_model_configurations())