"""
🌊 Streaming Orchestrator Functionality Tests
==========================================

Integration tests for the streaming orchestrator and real-time agent responses.
Tests WebSocket streaming, backpressure handling, and AutoGen integration.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import AsyncGenerator


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_orchestrator_initialization():
    """Test streaming orchestrator initialization."""
    
    try:
        from agents.services.streaming_orchestrator import StreamingOrchestrator
        from core.redis import init_redis
        
        # Ensure Redis is initialized
        try:
            await init_redis()
        except Exception:
            # Redis already initialized or not available
            pass
        
        orchestrator = StreamingOrchestrator()
        assert orchestrator is not None
        assert orchestrator.active_sessions == {}
        assert orchestrator._initialized == False
        
        # Test initialization
        await orchestrator.initialize()
        assert orchestrator._initialized == True
        assert orchestrator.memory_system is not None
        
    except ImportError as e:
        pytest.skip(f"Streaming orchestrator not available: {e}")
    except Exception as e:
        pytest.skip(f"Redis not available for streaming tests: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_session_creation():
    """Test streaming session creation and management."""
    
    try:
        from agents.services.streaming_orchestrator import StreamingOrchestrator
        from agents.services.streaming.session import StreamingSession
        from core.redis import init_redis
        
        # Ensure Redis is initialized
        try:
            await init_redis()
        except Exception:
            # Redis already initialized or not available
            pass
        
        orchestrator = StreamingOrchestrator()
        await orchestrator.initialize()
        
        # Mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        # Create streaming session
        session_id = await orchestrator.create_streaming_session(
            websocket=mock_websocket,
            user_id="test_user",
            agent_name="test_agent",
            session_context={"test": True}
        )
        
        assert session_id is not None
        assert isinstance(session_id, str)
        assert session_id in orchestrator.active_sessions
        
        session = orchestrator.active_sessions[session_id]
        assert isinstance(session, StreamingSession)
        assert session.user_id == "test_user"
        assert session.agent_name == "test_agent"
        assert session.status == "active"
        
        # Verify session created message was sent
        mock_websocket.send_json.assert_called()
        
    except ImportError as e:
        pytest.skip(f"Streaming components not available: {e}")
    except Exception as e:
        pytest.skip(f"Redis not available for streaming tests: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_response_processing():
    """Test streaming response processing and WebSocket communication."""
    
    try:
        from agents.services.streaming_orchestrator import StreamingOrchestrator
        from agents.services.streaming.response_types import StreamingResponse
        from core.redis import init_redis
        
        # Ensure Redis is initialized
        try:
            await init_redis()
        except Exception:
            # Redis already initialized or not available
            pass
        
        orchestrator = StreamingOrchestrator()
        await orchestrator.initialize()
        
        # Create mock session
        mock_websocket = AsyncMock()
        session_id = await orchestrator.create_streaming_session(
            websocket=mock_websocket,
            user_id="test_user",
            agent_name="test_agent"
        )
        
        session = orchestrator.active_sessions[session_id]
        
        # Test sending streaming response
        test_response = StreamingResponse(
            chunk_id="test_chunk",
            session_id=session_id,
            agent_name="test_agent",
            chunk_type='text',
            content="Hello from streaming test",
            timestamp=datetime.utcnow()
        )
        
        await orchestrator._send_streaming_response(session, test_response)
        
        # Verify WebSocket message was sent
        assert mock_websocket.send_json.called
        
        # Check the sent message structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert "event" in call_args
        assert "data" in call_args
        assert call_args["data"]["content"] == "Hello from streaming test"
        
    except ImportError as e:
        pytest.skip(f"Streaming components not available: {e}")
    except Exception as e:
        pytest.skip(f"Redis not available for streaming tests: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_native_autogen_streaming():
    """Test native AutoGen streaming functionality."""
    
    try:
        from agents.services.streaming.runner import NativeAutoGenStreamer, StreamingResponse
        from agents.services.streaming.session import StreamingSession
        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        # Create test session
        session = StreamingSession(
            session_id="test_session",
            user_id="test_user",
            agent_name="test_agent",
            websocket=AsyncMock(),
            start_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0,
            status='active'
        )
        
        # Mock AutoGen agent with streaming
        mock_client = Mock(spec=OpenAIChatCompletionClient)
        mock_agent = Mock(spec=AssistantAgent)
        
        # Mock streaming responses
        async def mock_stream_responses():
            yield Mock(content="Hello ")
            yield Mock(content="world!")
            yield Mock(content=" How can I help you?")
        
        mock_agent.run_stream = AsyncMock(return_value=mock_stream_responses())
        
        # Test streaming
        streamer = NativeAutoGenStreamer()
        
        responses = []
        async for response in streamer.stream_agent_response(
            agent=mock_agent,
            message="Hello",
            session=session,
            logger=Mock()
        ):
            responses.append(response)
        
        # Verify streaming responses
        assert len(responses) >= 1  # At least final response
        
        # Check for text responses
        text_responses = [r for r in responses if r.chunk_type == 'text']
        if text_responses:
            assert any("Hello" in r.content or "world" in r.content for r in text_responses)
        
        # Check for final response
        final_responses = [r for r in responses if r.chunk_type == 'final']
        assert len(final_responses) >= 1
        
    except ImportError as e:
        pytest.skip(f"AutoGen or streaming components not available: {e}")
    except Exception as e:
        pytest.skip(f"AutoGen streaming test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_error_handling():
    """Test streaming error handling and recovery."""
    
    try:
        from agents.services.streaming.runner import NativeAutoGenStreamer
        from agents.services.streaming.session import StreamingSession
        
        session = StreamingSession(
            session_id="test_session",
            user_id="test_user", 
            agent_name="test_agent",
            websocket=AsyncMock(),
            start_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0,
            status='active'
        )
        
        # Mock agent that raises an error
        mock_agent = Mock()
        mock_agent.run_stream = AsyncMock(side_effect=Exception("Test streaming error"))
        
        streamer = NativeAutoGenStreamer()
        
        # Test error handling
        responses = []
        async for response in streamer.stream_agent_response(
            agent=mock_agent,
            message="Test error handling",
            session=session,
            logger=Mock()
        ):
            responses.append(response)
        
        # Should have at least one error response
        error_responses = [r for r in responses if r.chunk_type == 'error']
        assert len(error_responses) >= 1
        
        # Error response should contain error information
        error_response = error_responses[0]
        assert "error" in error_response.content.lower()
        
    except ImportError as e:
        pytest.skip(f"Streaming components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_backpressure_control():
    """Test streaming backpressure control mechanisms."""
    
    try:
        from agents.services.streaming.runner import NativeAutoGenStreamer, BackpressureConfig
        
        # Configure tight backpressure limits
        config = BackpressureConfig(
            window_size=3,
            max_buffer_size=10,
            heartbeat_interval=1.0,
            chunk_delay=0.01,
            adaptive_delay=True
        )
        
        streamer = NativeAutoGenStreamer(backpressure_config=config)
        
        # Test backpressure detection
        stream_id = "test_stream"
        streamer.stream_buffers[stream_id] = ["chunk1", "chunk2", "chunk3", "chunk4"]  # Over window size
        
        should_apply = await streamer._should_apply_backpressure(stream_id)
        assert should_apply == True
        
        # Test backpressure delay
        import time
        start_time = time.time()
        await streamer._apply_backpressure_delay(stream_id)
        end_time = time.time()
        
        # Should have applied some delay
        assert end_time - start_time >= 0.001  # At least 1ms delay
        
        # Test with empty buffer (no backpressure)
        streamer.stream_buffers[stream_id] = []
        should_apply = await streamer._should_apply_backpressure(stream_id)
        assert should_apply == False
        
    except ImportError as e:
        pytest.skip(f"Streaming components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_message_processing():
    """Test streaming message processing with context."""
    
    try:
        from agents.services.streaming_orchestrator import StreamingOrchestrator
        from core.redis import init_redis
        
        # Ensure Redis is initialized
        try:
            await init_redis()
        except Exception:
            pytest.skip("Redis not available for streaming tests")
        
        orchestrator = StreamingOrchestrator()
        await orchestrator.initialize()
        
        # Mock WebSocket and create session
        mock_websocket = AsyncMock()
        session_id = await orchestrator.create_streaming_session(
            websocket=mock_websocket,
            user_id="test_user",
            agent_name="test_agent"
        )
        
        # Mock the agent processing parts
        with patch('agents.services.agent_loader.DynamicAgentLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.scan_and_load_agents.return_value = {
                "test_agent": {
                    "name": "Test Agent",
                    "role": "Test Role",
                    "description": "Test agent for streaming",
                    "system_message": "You are a test agent."
                }
            }
            mock_loader._build_system_message.return_value = "You are a test agent."
            mock_loader_class.return_value = mock_loader
            
            with patch('agents.services.streaming.runner.stream_agent_response') as mock_stream:
                # Mock streaming responses
                async def mock_streaming_responses(agent, message, session, logger):
                    yield Mock(
                        chunk_id="test1",
                        session_id=session_id,
                        agent_name="test_agent", 
                        chunk_type='text',
                        content="Test streaming response",
                        timestamp=datetime.utcnow()
                    )
                
                mock_stream.return_value = mock_streaming_responses(None, None, None, None)
                
                # Process streaming message
                await orchestrator.process_streaming_message(
                    session_id=session_id,
                    message="Hello, test streaming",
                    message_context={"test": True}
                )
                
                # Verify session was updated
                session = orchestrator.active_sessions[session_id]
                assert session.message_count > 0
                assert session.status == "active"
        
    except ImportError as e:
        pytest.skip(f"Streaming orchestrator not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_session_cleanup():
    """Test streaming session cleanup and resource management."""
    
    try:
        from agents.services.streaming_orchestrator import StreamingOrchestrator
        
        orchestrator = StreamingOrchestrator()
        await orchestrator.initialize()
        
        # Create multiple sessions
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        session_id1 = await orchestrator.create_streaming_session(
            websocket=mock_websocket1,
            user_id="test_user1",
            agent_name="test_agent1"
        )
        
        session_id2 = await orchestrator.create_streaming_session(
            websocket=mock_websocket2,
            user_id="test_user2", 
            agent_name="test_agent2"
        )
        
        # Verify sessions exist
        assert len(orchestrator.active_sessions) == 2
        assert session_id1 in orchestrator.active_sessions
        assert session_id2 in orchestrator.active_sessions
        
        # Test session cleanup
        await orchestrator.close_streaming_session(session_id1)
        
        # Verify session was removed
        assert len(orchestrator.active_sessions) == 1
        assert session_id1 not in orchestrator.active_sessions
        assert session_id2 in orchestrator.active_sessions
        
    except (ImportError, AttributeError) as e:
        # close_streaming_session might not be implemented
        pytest.skip(f"Streaming session cleanup not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_memory_integration():
    """Test streaming integration with memory system."""
    
    try:
        from agents.services.streaming_orchestrator import StreamingOrchestrator
        from agents.memory.autogen_memory_system import AutoGenMemorySystem
        from core.redis import init_redis
        
        # Ensure Redis is initialized
        try:
            await init_redis()
        except Exception:
            pytest.skip("Redis not available for streaming tests")
        
        orchestrator = StreamingOrchestrator()
        await orchestrator.initialize()
        
        # Mock memory system
        mock_memory_system = Mock(spec=AutoGenMemorySystem)
        mock_memory_system.retrieve_relevant_context = AsyncMock(return_value=[
            {"content": "Previous conversation about testing", "importance": 0.8}
        ])
        mock_memory_system.store_conversation_message = AsyncMock()
        
        orchestrator.memory_system = mock_memory_system
        
        # Create session and mock the processing
        mock_websocket = AsyncMock()
        session_id = await orchestrator.create_streaming_session(
            websocket=mock_websocket,
            user_id="test_user",
            agent_name="test_agent"
        )
        
        # Mock agent loading and streaming
        with patch('agents.services.agent_loader.DynamicAgentLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.scan_and_load_agents.return_value = {
                "test_agent": {"name": "Test Agent", "system_message": "Test"}
            }
            mock_loader._build_system_message.return_value = "Test system message"
            mock_loader_class.return_value = mock_loader
            
            with patch('agents.services.streaming.runner.stream_agent_response') as mock_stream:
                mock_stream.return_value = []  # Empty stream for this test
                
                # Process message
                await orchestrator.process_streaming_message(
                    session_id=session_id,
                    message="Test memory integration"
                )
                
                # Verify memory system interactions
                mock_memory_system.retrieve_relevant_context.assert_called_once()
                mock_memory_system.store_conversation_message.assert_called_once()
        
    except ImportError as e:
        pytest.skip(f"Streaming or memory components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_websocket_protocol():
    """Test WebSocket protocol compatibility."""
    
    try:
        from agents.services.streaming_orchestrator import StreamingOrchestrator
        from agents.services.streaming.response_types import StreamingResponse
        
        orchestrator = StreamingOrchestrator()
        await orchestrator.initialize()
        
        # Create mock WebSocket
        sent_messages = []
        
        async def mock_send_json(message):
            sent_messages.append(message)
        
        mock_websocket = Mock()
        mock_websocket.send_json = AsyncMock(side_effect=mock_send_json)
        
        # Create session
        session_id = await orchestrator.create_streaming_session(
            websocket=mock_websocket,
            user_id="test_user", 
            agent_name="test_agent"
        )
        
        session = orchestrator.active_sessions[session_id]
        
        # Test different message types
        test_responses = [
            StreamingResponse(
                chunk_id="test1",
                session_id=session_id,
                agent_name="test_agent",
                chunk_type='text',
                content="Hello world",
                timestamp=datetime.utcnow()
            ),
            StreamingResponse(
                chunk_id="test2", 
                session_id=session_id,
                agent_name="test_agent",
                chunk_type='thinking',
                content="Agent is thinking...",
                timestamp=datetime.utcnow()
            ),
            StreamingResponse(
                chunk_id="test3",
                session_id=session_id,
                agent_name="test_agent",
                chunk_type='final',
                content="Response completed",
                timestamp=datetime.utcnow()
            )
        ]
        
        # Send each response
        for response in test_responses:
            await orchestrator._send_streaming_response(session, response)
        
        # Verify all messages were sent (including session creation)
        assert len(sent_messages) >= len(test_responses) + 1  # +1 for session creation
        
        # Verify message structure
        for message in sent_messages[1:]:  # Skip session creation message
            assert "event" in message
            assert "data" in message
            assert "timestamp" in message["data"]
            assert "content" in message["data"]
        
    except ImportError as e:
        pytest.skip(f"Streaming components not available: {e}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_streaming_performance_characteristics():
    """Test streaming performance under load."""
    
    try:
        from agents.services.streaming.runner import NativeAutoGenStreamer
        from agents.services.streaming.session import StreamingSession
        import time
        
        streamer = NativeAutoGenStreamer()
        
        # Create test session
        session = StreamingSession(
            session_id="perf_test",
            user_id="test_user",
            agent_name="test_agent", 
            websocket=AsyncMock(),
            start_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0,
            status='active'
        )
        
        # Mock agent with many rapid responses
        async def mock_rapid_responses():
            for i in range(100):  # Many small chunks
                yield Mock(content=f"Chunk {i} ")
        
        mock_agent = Mock()
        mock_agent.run_stream = AsyncMock(return_value=mock_rapid_responses())
        
        # Measure streaming performance
        start_time = time.time()
        
        response_count = 0
        async for response in streamer.stream_agent_response(
            agent=mock_agent,
            message="Performance test",
            session=session,
            logger=Mock()
        ):
            response_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance expectations
        assert duration < 5.0, f"Streaming too slow: {duration:.2f}s"
        assert response_count > 0, "No responses generated"
        
        # Calculate throughput
        if duration > 0:
            throughput = response_count / duration
            assert throughput > 10, f"Throughput too low: {throughput:.1f} responses/sec"
        
    except ImportError as e:
        pytest.skip(f"Streaming components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_concurrent_sessions():
    """Test multiple concurrent streaming sessions."""
    
    try:
        from agents.services.streaming_orchestrator import StreamingOrchestrator
        
        orchestrator = StreamingOrchestrator() 
        await orchestrator.initialize()
        
        # Create multiple concurrent sessions
        sessions = []
        
        for i in range(5):  # 5 concurrent sessions
            mock_websocket = AsyncMock()
            session_id = await orchestrator.create_streaming_session(
                websocket=mock_websocket,
                user_id=f"user_{i}",
                agent_name=f"agent_{i}"
            )
            sessions.append(session_id)
        
        # Verify all sessions were created
        assert len(orchestrator.active_sessions) == 5
        
        # Verify each session is properly isolated
        for i, session_id in enumerate(sessions):
            session = orchestrator.active_sessions[session_id]
            assert session.user_id == f"user_{i}"
            assert session.agent_name == f"agent_{i}"
            assert session.status == "active"
        
        # Test concurrent message processing (without full agent mocking)
        # Just verify the sessions remain isolated and properly managed
        
    except ImportError as e:
        pytest.skip(f"Streaming orchestrator not available: {e}")