#!/usr/bin/env python3
"""
Detailed investigation of agent conversation timeout issue
"""
import asyncio
import os
import sys
import time
import traceback
from pathlib import Path
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def investigate_conversation():
    """Investigate why agent conversation times out"""
    print("🔍 Investigating Agent Conversation Timeout Issue...")
    
    try:
        # 1. Initialize orchestrator with detailed logging
        print("\n1. Initializing orchestrator with debug logging...")
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        # Enable all AutoGen and OpenAI logging
        for logger_name in ['autogen', 'autogen.agentchat', 'autogen_core', 'autogen_ext', 
                           'openai', 'httpx', 'src.agents']:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
        
        from src.agents.orchestrator import get_agent_orchestrator
        
        print("Getting orchestrator instance...")
        orchestrator = await get_agent_orchestrator()
        print(f"✅ Orchestrator initialized with {len(orchestrator.agents)} agents")
        
        # 2. Check orchestrator configuration
        print("\n2. Orchestrator configuration:")
        print(f"  - Max turns: {orchestrator.max_turns}")
        print(f"  - Selector mode: {orchestrator.selector_mode}")
        print(f"  - Agent count: {len(orchestrator.agents)}")
        
        # Print first 5 agents
        for i, agent in enumerate(list(orchestrator.agents.values())[:5]):
            print(f"  - Agent {i+1}: {agent.name}")
        
        # 3. Test with minimal conversation
        print("\n3. Starting MINIMAL conversation test...")
        
        # Use a very simple message that should complete quickly
        simple_message = "Say hello and provide your name only."
        
        print(f"Message: '{simple_message}'")
        print("Starting timer...")
        
        start_time = time.time()
        
        try:
            # Add timeout wrapper
            result = await asyncio.wait_for(
                orchestrator.orchestrate_conversation(
                    message=simple_message,
                    user_id="debug_user",
                    conversation_id="debug_minimal_001",
                    context={"requires_approval": False}
                ),
                timeout=30.0  # 30 second timeout for minimal test
            )
            
            elapsed = time.time() - start_time
            print(f"\n✅ Conversation completed in {elapsed:.2f} seconds!")
            
            # Analyze result
            print("\n4. Result analysis:")
            print(f"  - Type: {type(result)}")
            
            if hasattr(result, '__dict__'):
                print("  - Attributes:")
                for key, value in result.__dict__.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"    - {key}: {value[:100]}...")
                    else:
                        print(f"    - {key}: {value}")
            
            return result
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"\n❌ Conversation TIMED OUT after {elapsed:.2f} seconds")
            
            # Try to understand why
            print("\n5. Timeout analysis:")
            
            # Check if group chat is stuck
            if hasattr(orchestrator, 'group_chat'):
                gc = orchestrator.group_chat
                print(f"  - Group chat type: {type(gc)}")
                
                if hasattr(gc, '_message_thread'):
                    print(f"  - Message thread length: {len(gc._message_thread) if gc._message_thread else 0}")
                
                if hasattr(gc, '_agent_names'):
                    print(f"  - Agent names in chat: {gc._agent_names}")
                    
                if hasattr(gc, 'messages'):
                    print(f"  - Messages in chat: {len(gc.messages) if gc.messages else 0}")
            
            # Check if selector is the issue
            if hasattr(orchestrator, 'selector'):
                print(f"  - Selector type: {type(orchestrator.selector)}")
            
            raise
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ Conversation failed after {elapsed:.2f} seconds")
            print(f"Error: {e}")
            print("\nFull traceback:")
            traceback.print_exc()
            
            # Additional debugging
            print("\n6. Error context:")
            print(f"  - Error type: {type(e).__name__}")
            print(f"  - Error message: {str(e)}")
            
            # Check for specific AutoGen errors
            if "run_stream" in str(e):
                print("  ⚠️ Detected run_stream API issue")
            elif "cancellation_token" in str(e):
                print("  ⚠️ Detected cancellation_token issue")
            elif "model" in str(e).lower():
                print("  ⚠️ Detected model configuration issue")
            
            raise
            
    except Exception as e:
        print(f"\n❌ Investigation failed: {e}")
        traceback.print_exc()

async def test_direct_groupchat():
    """Test group chat directly without orchestrator"""
    print("\n\n🔬 Testing GroupChat directly...")
    
    try:
        from src.agents.services.groupchat.initializer import GroupChatInitializer
        from src.agents.business.loader import load_business_agents
        
        # Load agents
        print("Loading business agents...")
        agents = await load_business_agents()
        print(f"Loaded {len(agents)} agents")
        
        # Initialize group chat
        print("Initializing group chat...")
        initializer = GroupChatInitializer(agents=agents)
        
        # Check initialization
        print(f"Group chat type: {type(initializer.group_chat)}")
        print(f"Selector type: {type(initializer.selector) if hasattr(initializer, 'selector') else 'No selector'}")
        
        # Try to run a simple task
        print("\nTrying direct task execution...")
        
        from autogen_agentchat.task import TextMentionTermination
        from autogen_agentchat.messages import TextMessage
        
        # Create a simple task
        task = "Say hello"
        
        # Check if we need to use run_stream with keyword argument
        print("Attempting to run task...")
        
        try:
            # Try with keyword argument (correct for AutoGen 0.7.2)
            async for message in initializer.group_chat.run_stream(task=task):
                print(f"Message: {message}")
                break  # Just get first message
                
        except TypeError as e:
            print(f"TypeError: {e}")
            if "positional argument" in str(e):
                print("⚠️ run_stream API issue detected")
                # Try without stream
                try:
                    result = await initializer.group_chat.run(task=task)
                    print(f"Non-stream result: {result}")
                except Exception as e2:
                    print(f"Non-stream also failed: {e2}")
            
    except Exception as e:
        print(f"Direct test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Set environment for maximum logging
    os.environ["ENVIRONMENT"] = "development"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    print("=" * 60)
    print("AGENT CONVERSATION TIMEOUT INVESTIGATION")
    print("=" * 60)
    
    # Run investigation
    asyncio.run(investigate_conversation())
    
    # Also test direct group chat
    asyncio.run(test_direct_groupchat())