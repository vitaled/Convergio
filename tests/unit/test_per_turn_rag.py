"""
Unit tests for per-turn RAG injection
Verifies that context is injected at each turn when feature is enabled
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from backend.src.agents.services.groupchat.per_turn_rag import (
    PerTurnRAGInjector,
    RAGEnhancedGroupChat
)
from backend.src.agents.services.groupchat.rag import AdvancedRAGProcessor


class TestPerTurnRAGInjector:
    """Test per-turn RAG injection functionality"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings"""
        settings = Mock()
        settings.rag_in_loop_enabled = True
        settings.rag_max_facts = 5
        settings.rag_similarity_threshold = 0.7
        return settings
    
    @pytest.fixture
    def mock_memory_system(self):
        """Create mock memory system"""
        memory = Mock()
        memory.store_conversation = AsyncMock()
        memory.retrieve_memories = AsyncMock(return_value=[])
        return memory
    
    @pytest.fixture
    def mock_rag_processor(self, mock_memory_system, mock_settings):
        """Create mock RAG processor"""
        processor = Mock(spec=AdvancedRAGProcessor)
        processor.build_memory_context = AsyncMock()
        processor.build_memory_context.return_value = Mock(
            content="Relevant facts:\n- Fact 1\n- Fact 2"
        )
        return processor
    
    @pytest.fixture
    def rag_injector(self, mock_rag_processor, mock_memory_system, mock_settings):
        """Create RAG injector instance"""
        return PerTurnRAGInjector(
            rag_processor=mock_rag_processor,
            memory_system=mock_memory_system,
            settings=mock_settings
        )
    
    @pytest.mark.asyncio
    async def test_inject_context_when_enabled(self, rag_injector, mock_settings):
        """Test context injection when RAG is enabled"""
        # Arrange
        conversation_id = "test-conv-123"
        user_id = "user-456"
        agent_name = "ali_chief_of_staff"
        turn_number = 3
        current_message = "What's our strategy for Q2?"
        conversation_history = [
            {"turn": 1, "agent": "user", "content": "Let's discuss strategy"},
            {"turn": 2, "agent": "ali", "content": "I'll analyze our options"}
        ]
        
        # Act
        enhanced_message = await rag_injector.inject_context_for_turn(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_name=agent_name,
            turn_number=turn_number,
            current_message=current_message,
            conversation_history=conversation_history
        )
        
        # Assert
        assert current_message in enhanced_message
        assert "📌 Relevant Context:" in enhanced_message
        assert "Fact 1" in enhanced_message
        assert "Fact 2" in enhanced_message
        assert "🎯 Focus Area:" in enhanced_message
        
        # Verify RAG processor was called
        rag_injector.rag_processor.build_memory_context.assert_called_once()
        call_args = rag_injector.rag_processor.build_memory_context.call_args
        assert call_args[1]["user_id"] == user_id
        assert call_args[1]["agent_id"] == agent_name
    
    @pytest.mark.asyncio
    async def test_no_injection_when_disabled(self, rag_injector, mock_settings):
        """Test no context injection when RAG is disabled"""
        # Arrange
        mock_settings.rag_in_loop_enabled = False
        current_message = "What's our strategy for Q2?"
        
        # Act
        enhanced_message = await rag_injector.inject_context_for_turn(
            conversation_id="test-conv-123",
            user_id="user-456",
            agent_name="ali_chief_of_staff",
            turn_number=1,
            current_message=current_message,
            conversation_history=[]
        )
        
        # Assert
        assert enhanced_message == current_message
        rag_injector.rag_processor.build_memory_context.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_context_caching(self, rag_injector):
        """Test that context is cached to avoid redundant calls"""
        # Arrange
        conversation_id = "test-conv-123"
        user_id = "user-456"
        agent_name = "ali_chief_of_staff"
        turn_number = 3
        current_message = "What's our strategy?"
        
        # Act - First call
        enhanced1 = await rag_injector.inject_context_for_turn(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_name=agent_name,
            turn_number=turn_number,
            current_message=current_message,
            conversation_history=[]
        )
        
        # Act - Second call with same parameters (should use cache)
        enhanced2 = await rag_injector.inject_context_for_turn(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_name=agent_name,
            turn_number=turn_number,
            current_message=current_message,
            conversation_history=[]
        )
        
        # Assert
        assert enhanced1 == enhanced2
        # RAG processor should only be called once due to caching
        assert rag_injector.rag_processor.build_memory_context.call_count == 1
    
    @pytest.mark.asyncio
    async def test_turn_specific_weights(self, rag_injector):
        """Test that weights adjust based on turn number"""
        # Arrange
        conversation_id = "test-conv-123"
        user_id = "user-456"
        agent_name = "ali_chief_of_staff"
        
        # Act - Early turn (turn 2)
        await rag_injector.inject_context_for_turn(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_name=agent_name,
            turn_number=2,
            current_message="Early message",
            conversation_history=[]
        )
        
        early_call = rag_injector.rag_processor.build_memory_context.call_args
        
        # Clear cache and mock
        rag_injector.context_cache.clear()
        rag_injector.rag_processor.build_memory_context.reset_mock()
        
        # Act - Later turn (turn 5)
        await rag_injector.inject_context_for_turn(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_name=agent_name,
            turn_number=5,
            current_message="Later message",
            conversation_history=[]
        )
        
        later_call = rag_injector.rag_processor.build_memory_context.call_args
        
        # Assert - Recency weight should be higher for later turns
        assert early_call[1]["recency_weight"] == 0.3
        assert later_call[1]["recency_weight"] == 0.4
        
        # Include conversation history should be True for later turns
        assert early_call[1]["include_conversation_history"] == False  # Turn 2
        assert later_call[1]["include_conversation_history"] == True   # Turn 5
    
    @pytest.mark.asyncio
    async def test_agent_specific_context(self, rag_injector):
        """Test that agent-specific context is included"""
        # Arrange
        agents_to_test = [
            ("ali_chief_of_staff", "strategic alignment and coordination"),
            ("amy_cfo", "financial implications and budgeting"),
            ("luca_security_expert", "security and compliance")
        ]
        
        for agent_name, expected_focus in agents_to_test:
            # Clear cache for each test
            rag_injector.context_cache.clear()
            
            # Act
            enhanced_message = await rag_injector.inject_context_for_turn(
                conversation_id="test-conv",
                user_id="user-456",
                agent_name=agent_name,
                turn_number=1,
                current_message="Test message",
                conversation_history=[]
            )
            
            # Assert
            assert expected_focus in enhanced_message
            assert "🎯 Focus Area:" in enhanced_message
    
    def test_turn_history_tracking(self, rag_injector):
        """Test that turn history is tracked correctly"""
        # Arrange
        conversation_id = "test-conv-123"
        
        # Act - Track multiple turns
        rag_injector._track_turn(
            conversation_id=conversation_id,
            turn_number=1,
            agent_name="ali",
            context={"facts": ["f1", "f2"], "history": [], "insights": ["i1"]}
        )
        
        rag_injector._track_turn(
            conversation_id=conversation_id,
            turn_number=2,
            agent_name="amy",
            context={"facts": ["f3"], "history": ["h1"], "insights": []}
        )
        
        # Act - Get metrics
        metrics = rag_injector.get_turn_metrics(conversation_id)
        
        # Assert
        assert metrics["total_turns"] == 2
        assert metrics["unique_agents"] == 2
        assert metrics["avg_facts_per_turn"] == 1.5  # (2 + 1) / 2
        assert metrics["avg_history_per_turn"] == 0.5  # (0 + 1) / 2
        assert metrics["turns_with_insights"] == 1
    
    def test_cache_clearing(self, rag_injector):
        """Test cache clearing functionality"""
        # Arrange
        conversation_id1 = "conv-1"
        conversation_id2 = "conv-2"
        
        # Add some cache entries
        rag_injector.context_cache["key1_conv-1"] = {
            "enhanced_message": "test1",
            "timestamp": datetime.utcnow()
        }
        rag_injector.context_cache["key2_conv-2"] = {
            "enhanced_message": "test2",
            "timestamp": datetime.utcnow()
        }
        
        rag_injector.turn_history[conversation_id1] = [{"turn": 1}]
        rag_injector.turn_history[conversation_id2] = [{"turn": 1}]
        
        # Act - Clear specific conversation
        rag_injector.clear_cache(conversation_id1)
        
        # Assert
        assert "key1_conv-1" not in rag_injector.context_cache
        assert "key2_conv-2" in rag_injector.context_cache
        assert conversation_id1 not in rag_injector.turn_history
        assert conversation_id2 in rag_injector.turn_history
        
        # Act - Clear all
        rag_injector.clear_cache()
        
        # Assert
        assert len(rag_injector.context_cache) == 0
        assert len(rag_injector.turn_history) == 0


class TestRAGEnhancedGroupChat:
    """Test RAG-enhanced GroupChat"""
    
    @pytest.fixture
    def mock_rag_injector(self):
        """Create mock RAG injector"""
        injector = Mock(spec=PerTurnRAGInjector)
        injector.inject_context_for_turn = AsyncMock()
        injector.inject_context_for_turn.return_value = "Enhanced message with context"
        return injector
    
    @pytest.fixture
    def mock_participants(self):
        """Create mock participants"""
        participants = []
        for i in range(3):
            agent = Mock()
            agent.name = f"agent_{i}"
            participants.append(agent)
        return participants
    
    @pytest.fixture
    def mock_model_client(self):
        """Create mock model client"""
        client = Mock()
        client.model = "gpt-4"
        return client
    
    @pytest.mark.asyncio
    async def test_rag_enhanced_groupchat_creation(self, mock_participants, mock_model_client, mock_rag_injector):
        """Test RAGEnhancedGroupChat creation"""
        # Act
        group_chat = RAGEnhancedGroupChat(
            participants=mock_participants,
            model_client=mock_model_client,
            rag_injector=mock_rag_injector
        )
        
        # Assert
        assert group_chat.rag_injector == mock_rag_injector
        assert group_chat.turn_count == 0
        assert group_chat.conversation_id is not None
        assert group_chat.user_id == "default"
    
    @pytest.mark.asyncio
    async def test_run_stream_with_rag_injection(self, mock_participants, mock_model_client, mock_rag_injector):
        """Test that run_stream injects context at each turn"""
        # Arrange
        group_chat = RAGEnhancedGroupChat(
            participants=mock_participants,
            model_client=mock_model_client,
            rag_injector=mock_rag_injector
        )
        
        # Create mock messages to simulate stream
        mock_messages = []
        for i in range(3):
            msg = Mock()
            msg.source = f"agent_{i}"
            msg.content = f"Message {i}"
            mock_messages.append(msg)
        
        # Mock the parent run_stream to return our messages
        async def mock_run_stream(task):
            for msg in mock_messages:
                yield msg
        
        with patch.object(RAGEnhancedGroupChat.__bases__[0], 'run_stream', mock_run_stream):
            # Act
            messages_received = []
            async for message in group_chat.run_stream(
                task="Test task",
                conversation_id="test-conv",
                user_id="test-user"
            ):
                messages_received.append(message)
            
            # Assert
            assert len(messages_received) == 3
            assert group_chat.turn_count == 3
            assert group_chat.conversation_id == "test-conv"
            assert group_chat.user_id == "test-user"
            
            # Verify RAG injection was called for each message
            assert mock_rag_injector.inject_context_for_turn.call_count == 3
            
            # Verify enhanced content was set
            for msg in messages_received:
                assert msg.content == "Enhanced message with context"
    
    @pytest.mark.asyncio
    async def test_run_stream_without_rag_injector(self, mock_participants, mock_model_client):
        """Test that run_stream works without RAG injector"""
        # Arrange
        group_chat = RAGEnhancedGroupChat(
            participants=mock_participants,
            model_client=mock_model_client,
            rag_injector=None  # No RAG injector
        )
        
        # Create mock messages
        mock_messages = []
        for i in range(2):
            msg = Mock()
            msg.source = f"agent_{i}"
            msg.content = f"Original message {i}"
            mock_messages.append(msg)
        
        # Mock the parent run_stream
        async def mock_run_stream(task):
            for msg in mock_messages:
                yield msg
        
        with patch.object(RAGEnhancedGroupChat.__bases__[0], 'run_stream', mock_run_stream):
            # Act
            messages_received = []
            async for message in group_chat.run_stream(task="Test task"):
                messages_received.append(message)
            
            # Assert - Messages should pass through unchanged
            assert len(messages_received) == 2
            for i, msg in enumerate(messages_received):
                assert msg.content == f"Original message {i}"


class TestFeatureFlagIntegration:
    """Test per-turn RAG with feature flag integration"""
    
    @pytest.mark.asyncio
    async def test_rag_enabled_by_feature_flag(self):
        """Test that per-turn RAG is controlled by feature flag"""
        from backend.src.agents.utils.feature_flags import (
            FeatureFlagManager,
            FeatureFlagName,
            RolloutStrategy
        )
        
        # Arrange
        flag_manager = FeatureFlagManager()
        
        # Test with flag OFF
        flag_manager.update_flag(
            FeatureFlagName.RAG_IN_LOOP,
            enabled=False
        )
        
        mock_settings = Mock()
        mock_settings.rag_in_loop_enabled = flag_manager.is_enabled(FeatureFlagName.RAG_IN_LOOP)
        
        mock_memory = Mock()
        mock_rag_processor = Mock()
        
        injector = PerTurnRAGInjector(
            rag_processor=mock_rag_processor,
            memory_system=mock_memory,
            settings=mock_settings
        )
        
        # Act
        result = await injector.inject_context_for_turn(
            conversation_id="test",
            user_id="user",
            agent_name="ali",
            turn_number=1,
            current_message="Test message",
            conversation_history=[]
        )
        
        # Assert - Should return original message when disabled
        assert result == "Test message"
        
        # Test with flag ON
        flag_manager.update_flag(
            FeatureFlagName.RAG_IN_LOOP,
            enabled=True
        )
        mock_settings.rag_in_loop_enabled = flag_manager.is_enabled(FeatureFlagName.RAG_IN_LOOP)
        
        mock_rag_processor.build_memory_context = AsyncMock()
        mock_rag_processor.build_memory_context.return_value = Mock(
            content="Context: Important facts"
        )
        
        injector2 = PerTurnRAGInjector(
            rag_processor=mock_rag_processor,
            memory_system=mock_memory,
            settings=mock_settings
        )
        
        # Act
        result2 = await injector2.inject_context_for_turn(
            conversation_id="test",
            user_id="user",
            agent_name="ali",
            turn_number=1,
            current_message="Test message",
            conversation_history=[]
        )
        
        # Assert - Should enhance message when enabled
        assert "Test message" in result2
        assert "📌 Relevant Context:" in result2
    
    @pytest.mark.asyncio
    async def test_percentage_rollout(self):
        """Test per-turn RAG with percentage-based rollout"""
        from backend.src.agents.utils.feature_flags import (
            FeatureFlagManager,
            FeatureFlagName,
            RolloutStrategy
        )
        
        # Arrange
        flag_manager = FeatureFlagManager()
        flag_manager.update_flag(
            FeatureFlagName.RAG_IN_LOOP,
            enabled=True,
            strategy=RolloutStrategy.PERCENTAGE,
            percentage=50.0  # 50% rollout
        )
        
        # Test with multiple users
        enabled_count = 0
        total_users = 100
        
        for i in range(total_users):
            user_id = f"user_{i}"
            is_enabled = flag_manager.is_enabled(
                FeatureFlagName.RAG_IN_LOOP,
                user_id=user_id
            )
            if is_enabled:
                enabled_count += 1
        
        # Assert - Should be roughly 50% (with some variance)
        assert 40 <= enabled_count <= 60  # Allow 10% variance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])