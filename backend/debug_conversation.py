#!/usr/bin/env python3
"""
Debug script to test agent conversation and capture the exact error
"""
import asyncio
import os
import sys
import traceback
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def debug_conversation():
    """Debug the agent conversation step by step"""
    print("🔍 Debugging Agent Conversation...")
    
    try:
        # 1. Initialize orchestrator
        print("\n1. Initializing orchestrator...")
        from src.agents.orchestrator import get_agent_orchestrator
        orchestrator = await get_agent_orchestrator()
        print("✅ Orchestrator initialized")
        
        # 2. Test simple conversation
        print("\n2. Starting conversation...")
        try:
            result = await orchestrator.orchestrate_conversation(
                message="Hello, provide a brief status update.",
                user_id="debug_user",
                conversation_id="debug_conv_001",
                context={"requires_approval": False}
            )
            
            print("\n✅ Conversation completed successfully!")
            print(f"Result type: {type(result)}")
            print(f"Result attributes: {dir(result)}")
            
            # Print result details
            if hasattr(result, 'response'):
                print(f"\nResponse: {result.response}")
            if hasattr(result, 'final_response'):
                print(f"Final Response: {result.final_response}")
            if hasattr(result, 'agents_used'):
                print(f"Agents Used: {result.agents_used}")
            if hasattr(result, 'turn_count'):
                print(f"Turn Count: {result.turn_count}")
            if hasattr(result, 'error'):
                print(f"Error: {result.error}")
                
            return result
            
        except Exception as conv_error:
            print(f"\n❌ Conversation failed: {conv_error}")
            print("\nFull traceback:")
            traceback.print_exc()
            
            # Try to get more details
            print("\n\nTrying to get more error details...")
            import structlog
            logger = structlog.get_logger()
            logger.error("Conversation debug error", error=str(conv_error), exc_info=True)
            
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Set environment to development for more logging
    os.environ["ENVIRONMENT"] = "development"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    asyncio.run(debug_conversation())