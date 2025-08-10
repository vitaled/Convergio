#!/usr/bin/env python3
"""Simple test of AutoGen with gpt-4o-mini"""

import asyncio
import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Manual env setup to avoid quote issues
os.environ['DEFAULT_AI_MODEL'] = 'gpt-4o-mini'
# OpenAI API key loaded from .env file

async def test_direct():
    """Test initializing and using the client directly"""
    from src.agents.services.groupchat.initializer import initialize_model_client
    
    print("Initializing model client...")
    client = initialize_model_client()
    print(f"Client initialized")
    
    # Try a simple create call
    from autogen_agentchat.messages import TextMessage
    
    try:
        print("Making API call...")
        result = await client.create(
            messages=[TextMessage(content="Say 'test' and nothing else", source="user")]
        )
        print(f"✅ Success! Response: {result.content}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct())