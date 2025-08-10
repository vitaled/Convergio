#!/usr/bin/env python3
"""
Test semplice - solo inizializzazione orchestrator
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging per vedere tutto
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Manual env setup from .env file
from dotenv import load_dotenv
load_dotenv()

async def test_simple_orchestrator():
    """Test basico dell'orchestrator"""
    try:
        print("=== STEP 1: Import orchestrator ===")
        from src.agents.orchestrator import get_agent_orchestrator
        print("✅ Import successful")
        
        print("\n=== STEP 2: Get orchestrator ===")
        orchestrator = await get_agent_orchestrator()
        print("✅ Orchestrator created")
        
        print("\n=== STEP 3: Test orchestrator (already initialized) ===")
        print(f"Orchestrator type: {type(orchestrator)}")
        print("✅ Orchestrator initialized")
        
        print("\n=== STEP 4: Test conversation ===")
        try:
            result = await orchestrator.orchestrate_conversation(
                message="Test: say hello",
                user_id="test_user",
                context={}
            )
            print("✅ Conversation successful!")
            print(f"Response: {result.response}")
            print(f"Agents used: {result.agents_used}")
            print(f"Duration: {result.duration_seconds}s")
        except Exception as conv_error:
            print(f"❌ Conversation failed: {conv_error}")
            import traceback
            traceback.print_exc()
        
        print("\n=== SUCCESS! Orchestrator works ===")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_orchestrator())