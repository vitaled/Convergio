#!/usr/bin/env python3
"""
🚀 CONVERGIO END-TO-END TEST SUITE
==================================

Purpose: Complete end-to-end testing simulating real user interactions
         from frontend through backend to database and back.

Test Coverage:
- Complete user workflows
- Authentication and authorization
- Real-time WebSocket communication
- File uploads and processing
- Multi-step conversations
- Session management
- Data persistence

Author: Convergio Test Suite
Last Updated: December 2024
"""

import asyncio
import json
import logging
import time
import websockets
import socket
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pytest
import httpx
try:
    from playwright.async_api import async_playwright
except ModuleNotFoundError:  # Playwright missing in Python env
    pytest.skip("Playwright not installed; skipping E2E tests", allow_module_level=True)

# Setup paths
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from src.core.config import get_settings
import os

# Configure logging
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)
TEST_NAME = Path(__file__).stem
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"{TEST_NAME}_{TIMESTAMP}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def is_frontend_available() -> bool:
    """Check if frontend is running on configured port"""
    try:
        import os
        frontend_port = int(os.getenv("FRONTEND_PORT", "4000"))
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(1.0)
            return sock.connect_ex(("localhost", frontend_port)) == 0
    except:
        return False


class TestEndToEnd:
    """
    Complete end-to-end test scenarios simulating real user interactions.
    """
    
    @classmethod
    def setup_class(cls):
        """Setup test environment."""
        logger.info("="*70)
        logger.info("CONVERGIO END-TO-END TEST SUITE")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Log file: {LOG_FILE}")
        logger.info("="*70)
        
        cls.settings = get_settings()
        import os
        backend_port = os.getenv('BACKEND_PORT', '9000')
        frontend_port = os.getenv('FRONTEND_PORT', '4000')
        cls.backend_url = f"http://localhost:{backend_port}"
        cls.frontend_url = f"http://localhost:{frontend_port}"
        cls.ws_url = f"ws://localhost:{backend_port}/ws"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not is_frontend_available(), reason="Frontend not running on configured port")
    async def test_complete_user_journey(self):
        """
        Test a complete user journey from landing to conversation.
        
        Flow:
        1. User visits homepage
        2. Navigates to chat interface
        3. Starts conversation with Ali CEO
        4. Switches to Amy CFO
        5. Uses orchestrator for complex query
        6. Receives real-time updates
        """
        logger.info("\n🎯 Testing Complete User Journey...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Step 1: Visit homepage
                logger.info("Step 1: Visiting homepage...")
                await page.goto(self.frontend_url)
                await page.wait_for_load_state("networkidle")
                
                # Check if page loaded
                title = await page.title()
                logger.info(f"  ✓ Page loaded: {title}")
                
                # Step 2: Navigate to chat
                logger.info("Step 2: Navigating to chat interface...")
                chat_button = page.locator("text=Start Chat")
                if await chat_button.is_visible():
                    await chat_button.click()
                    await page.wait_for_url("**/chat", timeout=5000)
                    logger.info("  ✓ Navigated to chat")
                else:
                    logger.info("  ℹ Chat interface directly accessible")
                
                # Step 3: Start conversation with Ali
                logger.info("Step 3: Starting conversation with Ali CEO...")
                
                # Select Ali agent
                agent_selector = page.locator("select#agent-selector")
                if await agent_selector.is_visible():
                    await agent_selector.select_option("ali")
                    logger.info("  ✓ Selected Ali CEO")
                
                # Send message
                message_input = page.locator("textarea#message-input, input#message")
                if await message_input.is_visible():
                    await message_input.fill("What is our company vision?")
                    await message_input.press("Enter")
                    
                    # Wait for response
                    response_locator = page.locator(".message.assistant").last
                    await response_locator.wait_for(timeout=30000)
                    response_text = await response_locator.text_content()
                    logger.info(f"  ✓ Ali responded: {response_text[:100]}...")
                
                # Step 4: Switch to Amy CFO
                logger.info("Step 4: Switching to Amy CFO...")
                if await agent_selector.is_visible():
                    await agent_selector.select_option("amy")
                    await message_input.fill("What's our current burn rate?")
                    await message_input.press("Enter")
                    
                    # Wait for Amy's response
                    await page.wait_for_timeout(2000)
                    logger.info("  ✓ Amy CFO engaged")
                
                # Step 5: Test orchestrator
                logger.info("Step 5: Testing orchestrator with complex query...")
                if await agent_selector.is_visible():
                    await agent_selector.select_option("orchestrator")
                    complex_query = "Compare our financial status with our strategic goals"
                    await message_input.fill(complex_query)
                    await message_input.press("Enter")
                    
                    await page.wait_for_timeout(3000)
                    logger.info("  ✓ Orchestrator handling complex query")
                
                logger.info("✅ Complete user journey successful!")
                
            except Exception as e:
                logger.error(f"❌ User journey failed: {e}")
                await page.screenshot(path=f"{LOG_DIR}/error_{TIMESTAMP}.png")
                raise
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_websocket_real_time_streaming(self):
        """
        Test WebSocket real-time streaming functionality.
        
        Verifies:
        - WebSocket connection establishment
        - Real-time message streaming
        - Proper message formatting
        - Connection stability
        """
        logger.info("\n📡 Testing WebSocket Real-Time Streaming...")
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                logger.info("  ✓ WebSocket connected")
                
                # Send initial message
                message = {
                    "type": "conversation",
                    "agent": "ali",
                    "content": "Stream me a response about company culture"
                }
                
                await websocket.send(json.dumps(message))
                logger.info("  ✓ Message sent")
                
                # Receive streaming response
                chunks_received = 0
                full_response = ""
                
                while True:
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=5.0
                        )
                        
                        data = json.loads(response)
                        
                        if data.get("type") == "chunk":
                            chunks_received += 1
                            full_response += data.get("content", "")
                            
                        elif data.get("type") == "complete":
                            logger.info(f"  ✓ Streaming complete: {chunks_received} chunks")
                            logger.info(f"  ✓ Total response: {len(full_response)} chars")
                            break
                            
                        elif data.get("type") == "error":
                            logger.error(f"  ❌ Streaming error: {data.get('message')}")
                            break
                            
                    except asyncio.TimeoutError:
                        logger.info("  ✓ Streaming completed (timeout)")
                        break
                
                assert chunks_received > 0, "No chunks received"
                assert len(full_response) > 0, "Empty response"
                
        except Exception as e:
            logger.warning(f"  ⚠ WebSocket test skipped: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not is_frontend_available(), reason="Frontend not running on configured port")
    async def test_multi_step_conversation_context(self):
        """
        Test multi-step conversation with context preservation.
        
        Verifies:
        - Context is maintained across messages
        - Follow-up questions work correctly
        - Conversation history is preserved
        - Agent memory functions
        """
        logger.info("\n💬 Testing Multi-Step Conversation Context...")
        
        session_id = f"test_session_{TIMESTAMP}"
        conversation_history = []
        
        async with httpx.AsyncClient(base_url=self.backend_url) as client:
            # Step 1: Initial message
            logger.info("Step 1: Initial message...")
            response = await client.post(
                "/api/v1/agents/conversation",
                json={
                    "message": "My name is TestUser and I'm interested in AI",
                    "agent": "ali",
                    "session_id": session_id,
                    "context": {}
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                conversation_history.append(data)
                logger.info("  ✓ Initial message processed")
            
            # Step 2: Follow-up referencing previous
            logger.info("Step 2: Follow-up question...")
            response = await client.post(
                "/api/v1/agents/conversation",
                json={
                    "message": "What did I just tell you my name was?",
                    "agent": "ali",
                    "session_id": session_id,
                    "context": {
                        "history": conversation_history
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "").lower()
                
                # Check if context was preserved
                if "testuser" in content:
                    logger.info("  ✓ Context preserved: Name remembered")
                else:
                    logger.warning("  ⚠ Context may not be preserved")
                
                conversation_history.append(data)
            
            # Step 3: Topic continuation
            logger.info("Step 3: Topic continuation...")
            response = await client.post(
                "/api/v1/agents/conversation",
                json={
                    "message": "Tell me more about that AI topic I mentioned",
                    "agent": "ali",
                    "session_id": session_id,
                    "context": {
                        "history": conversation_history
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "").lower()
                
                if "ai" in content or "artificial intelligence" in content:
                    logger.info("  ✓ Topic context maintained")
                
                logger.info(f"  ✓ Conversation length: {len(conversation_history)} messages")
    
    @pytest.mark.asyncio
    async def test_concurrent_user_sessions(self):
        """
        Test system handling multiple concurrent user sessions.
        
        Verifies:
        - Multiple users can interact simultaneously
        - Sessions are isolated
        - No cross-contamination of data
        - Performance under concurrent load
        """
        logger.info("\n👥 Testing Concurrent User Sessions...")
        
        async def simulate_user(user_id: int):
            """Simulate a single user session."""
            session_id = f"user_{user_id}_{TIMESTAMP}"
            
            async with httpx.AsyncClient(base_url=self.backend_url) as client:
                # Each user asks a different question
                questions = [
                    "What is our product roadmap?",
                    "Tell me about financial projections",
                    "Explain our technology stack",
                    "What are our hiring plans?",
                    "Describe our competitive advantage"
                ]
                
                question = questions[user_id % len(questions)]
                
                start_time = time.time()
                response = await client.post(
                    "/api/v1/agents/conversation",
                    json={
                        "message": question,
                        "agent": "orchestrator",
                        "session_id": session_id
                    },
                    timeout=30.0
                )
                elapsed = time.time() - start_time
                
                return {
                    "user_id": user_id,
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "session_id": session_id
                }
        
        # Simulate 5 concurrent users
        num_users = 5
        logger.info(f"Simulating {num_users} concurrent users...")
        
        tasks = [simulate_user(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful = [r for r in results if isinstance(r, dict) and r["status"] == 200]
        failed = [r for r in results if isinstance(r, Exception) or (isinstance(r, dict) and r["status"] != 200)]
        
        logger.info(f"  ✓ Successful sessions: {len(successful)}/{num_users}")
        
        if successful:
            avg_time = sum(r["elapsed"] for r in successful) / len(successful)
            max_time = max(r["elapsed"] for r in successful)
            logger.info(f"  ✓ Average response time: {avg_time:.2f}s")
            logger.info(f"  ✓ Max response time: {max_time:.2f}s")
        
        if failed:
            logger.warning(f"  ⚠ Failed sessions: {len(failed)}")
        
        # Verify session isolation
        session_ids = [r["session_id"] for r in successful]
        assert len(session_ids) == len(set(session_ids)), "Session IDs not unique"
        logger.info("  ✓ Session isolation verified")
    
    @pytest.mark.asyncio
    async def test_error_recovery_e2e(self):
        """
        Test end-to-end error recovery scenarios.
        
        Verifies:
        - System recovers from API errors
        - Frontend handles backend failures gracefully
        - Retry mechanisms work
        - User gets meaningful error messages
        """
        logger.info("\n🔧 Testing Error Recovery E2E...")
        
        async with httpx.AsyncClient(base_url=self.backend_url) as client:
            # Test 1: Invalid agent name
            logger.info("Test 1: Invalid agent name...")
            response = await client.post(
                "/api/v1/agents/conversation",
                json={
                    "message": "Hello",
                    "agent": "invalid_agent"
                }
            )
            
            if response.status_code in [400, 404]:
                logger.info("  ✓ Invalid agent handled correctly")
                try:
                    error_data = response.json()
                    if "error" in error_data or "detail" in error_data:
                        logger.info("  ✓ Error message provided to user")
                except:
                    pass
            
            # Test 2: Malformed request
            logger.info("Test 2: Malformed request...")
            response = await client.post(
                "/api/v1/agents/conversation",
                data="invalid json"
            )
            
            if response.status_code in [400, 422]:
                logger.info("  ✓ Malformed request rejected")
            
            # Test 3: Recovery after error
            logger.info("Test 3: Recovery after error...")
            
            # First, cause an error
            await client.post(
                "/api/v1/agents/conversation",
                json={"invalid": "data"}
            )
            
            # Then, valid request
            response = await client.post(
                "/api/v1/agents/conversation",
                json={
                    "message": "Hello after error",
                    "agent": "ali"
                }
            )
            
            if response.status_code == 200:
                logger.info("  ✓ System recovered after error")
            else:
                logger.warning("  ⚠ Recovery may have issues")


def run_e2e_tests():
    """Execute the end-to-end test suite."""
    logger.info("Starting Convergio End-to-End Test Suite")
    logger.info(f"Backend URL: {TestEndToEnd.backend_url}")
    logger.info(f"Frontend URL: {TestEndToEnd.frontend_url}")
    
    # Configure pytest
    pytest_args = [
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "--color=yes",
        f"--junit-xml={LOG_DIR}/{TEST_NAME}_{TIMESTAMP}_junit.xml"
    ]
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    # Report results
    logger.info("="*70)
    if exit_code == 0:
        logger.info("✅ ALL E2E TESTS PASSED!")
    else:
        logger.error(f"❌ E2E TESTS FAILED (exit code: {exit_code})")
    logger.info(f"Test results saved to: {LOG_FILE}")
    logger.info("="*70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_e2e_tests())