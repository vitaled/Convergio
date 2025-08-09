"""
Unit tests for per-turn token tracking with timeline
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from backend.src.agents.services.turn_token_tracker import (
    PerTurnTokenTracker,
    TurnTokenUsage,
    ConversationTokenTimeline,
    initialize_token_tracker,
    budget_monitor_callback
)
from autogen_agentchat.messages import TextMessage, ToolCallMessage, ToolResultMessage


class TestPerTurnTokenTracker:
    """Test per-turn token tracking functionality"""
    
    @pytest.fixture
    def token_tracker(self):
        """Create token tracker instance"""
        return PerTurnTokenTracker(budget_limit_usd=10.0)
    
    @pytest.fixture
    def mock_message(self):
        """Create mock message"""
        msg = Mock(spec=TextMessage)
        msg.content = "This is a test message with some content to track tokens."
        msg.source = "test_agent"
        return msg
    
    @pytest.fixture
    def mock_tool_message(self):
        """Create mock tool call message"""
        msg = Mock(spec=ToolCallMessage)
        msg.content = "Calling tool for analysis"
        msg.tool_calls = [Mock(name="analyze_data")]
        return msg
    
    def test_initialization(self, token_tracker):
        """Test tracker initialization"""
        assert token_tracker.budget_limit_usd == 10.0
        assert len(token_tracker.timelines) == 0
        assert len(token_tracker.token_callbacks) == 0
    
    def test_start_conversation(self, token_tracker):
        """Test starting a new conversation"""
        conversation_id = "test-conv-123"
        timeline = token_tracker.start_conversation(conversation_id, budget_limit_usd=5.0)
        
        assert timeline.conversation_id == conversation_id
        assert timeline.budget_limit_usd == 5.0
        assert timeline.budget_remaining_usd == 5.0
        assert len(timeline.turns) == 0
        assert conversation_id in token_tracker.timelines
    
    @pytest.mark.asyncio
    async def test_track_turn(self, token_tracker, mock_message):
        """Test tracking a single turn"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id)
        
        turn_usage = await token_tracker.track_turn(
            conversation_id=conversation_id,
            turn_number=1,
            agent_name="test_agent",
            message=mock_message,
            model="gpt-4",
            prompt_tokens=50,
            completion_tokens=100
        )
        
        assert turn_usage.turn_number == 1
        assert turn_usage.agent_name == "test_agent"
        assert turn_usage.prompt_tokens == 50
        assert turn_usage.completion_tokens == 100
        assert turn_usage.total_tokens == 150
        assert turn_usage.total_cost_usd > 0
        
        # Check timeline update
        timeline = token_tracker.get_timeline(conversation_id)
        assert len(timeline.turns) == 1
        assert timeline.total_tokens == 150
    
    @pytest.mark.asyncio
    async def test_token_estimation(self, token_tracker, mock_message):
        """Test automatic token estimation"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id)
        
        # Track without providing token counts
        turn_usage = await token_tracker.track_turn(
            conversation_id=conversation_id,
            turn_number=1,
            agent_name="test_agent",
            message=mock_message,
            model="gpt-4"
        )
        
        # Should have estimated tokens
        assert turn_usage.prompt_tokens > 0
        assert turn_usage.completion_tokens > 0
        assert turn_usage.total_tokens > 0
    
    @pytest.mark.asyncio
    async def test_cost_calculation(self, token_tracker):
        """Test cost calculation for different models"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id)
        
        models_to_test = [
            ("gpt-4", 1000, 1000),  # More expensive
            ("gpt-3.5-turbo", 1000, 1000),  # Cheaper
            ("claude-3-opus", 1000, 1000)  # Different pricing
        ]
        
        costs = []
        for model, prompt_tokens, completion_tokens in models_to_test:
            msg = Mock()
            msg.content = "Test"
            
            turn_usage = await token_tracker.track_turn(
                conversation_id=conversation_id,
                turn_number=len(costs) + 1,
                agent_name="test_agent",
                message=msg,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            costs.append(turn_usage.total_cost_usd)
        
        # GPT-4 should be more expensive than GPT-3.5
        assert costs[0] > costs[1]
    
    @pytest.mark.asyncio
    async def test_budget_tracking(self, token_tracker):
        """Test budget tracking and breach detection"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id, budget_limit_usd=0.01)  # Small budget
        
        # Track expensive turn
        msg = Mock()
        msg.content = "Test"
        
        await token_tracker.track_turn(
            conversation_id=conversation_id,
            turn_number=1,
            agent_name="test_agent",
            message=msg,
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=1000
        )
        
        timeline = token_tracker.get_timeline(conversation_id)
        
        # Should detect budget breach
        assert timeline.budget_remaining_usd < 0
        assert timeline.budget_breach_turn == 1
    
    @pytest.mark.asyncio
    async def test_agent_breakdown(self, token_tracker):
        """Test token usage breakdown by agent"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id)
        
        agents = ["agent_1", "agent_2", "agent_1"]  # Agent 1 speaks twice
        
        for i, agent in enumerate(agents):
            msg = Mock()
            msg.content = f"Message from {agent}"
            
            await token_tracker.track_turn(
                conversation_id=conversation_id,
                turn_number=i + 1,
                agent_name=agent,
                message=msg,
                model="gpt-4",
                prompt_tokens=100,
                completion_tokens=100
            )
        
        timeline = token_tracker.get_timeline(conversation_id)
        
        # Check agent breakdown
        assert "agent_1" in timeline.agent_token_usage
        assert "agent_2" in timeline.agent_token_usage
        assert timeline.agent_token_usage["agent_1"]["turns"] == 2
        assert timeline.agent_token_usage["agent_2"]["turns"] == 1
        assert timeline.agent_token_usage["agent_1"]["total_tokens"] == 400  # 2 turns * 200 tokens
    
    @pytest.mark.asyncio
    async def test_peak_usage_tracking(self, token_tracker):
        """Test tracking of peak token usage"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id)
        
        token_counts = [100, 500, 200, 300]  # Peak at turn 2
        
        for i, tokens in enumerate(token_counts):
            msg = Mock()
            msg.content = "Test"
            
            await token_tracker.track_turn(
                conversation_id=conversation_id,
                turn_number=i + 1,
                agent_name="test_agent",
                message=msg,
                model="gpt-4",
                prompt_tokens=tokens // 2,
                completion_tokens=tokens // 2
            )
        
        timeline = token_tracker.get_timeline(conversation_id)
        
        assert timeline.peak_turn_tokens == 500
        assert timeline.peak_turn_number == 2
    
    @pytest.mark.asyncio
    async def test_message_type_detection(self, token_tracker, mock_tool_message):
        """Test detection of different message types"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id)
        
        # Track tool call
        turn_usage = await token_tracker.track_turn(
            conversation_id=conversation_id,
            turn_number=1,
            agent_name="test_agent",
            message=mock_tool_message,
            model="gpt-4"
        )
        
        assert turn_usage.message_type == "tool_call"
        assert len(turn_usage.tool_calls) == 1
        assert turn_usage.tool_calls[0] == "analyze_data"
    
    @pytest.mark.asyncio
    async def test_callbacks(self, token_tracker):
        """Test callback registration and triggering"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id, budget_limit_usd=0.001)  # Tiny budget
        
        callback_events = []
        
        async def test_callback(event_type, conv_id, turn_usage, timeline):
            callback_events.append({
                "event": event_type,
                "turn": turn_usage.turn_number,
                "conv_id": conv_id
            })
        
        token_tracker.register_callback(test_callback)
        
        # Track turn that will breach budget
        msg = Mock()
        msg.content = "Test"
        
        await token_tracker.track_turn(
            conversation_id=conversation_id,
            turn_number=1,
            agent_name="test_agent",
            message=msg,
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=1000
        )
        
        # Should have triggered callbacks
        assert len(callback_events) >= 1
        assert any(e["event"] == "turn_complete" for e in callback_events)
        assert any(e["event"] == "budget_breach" for e in callback_events)
    
    def test_end_conversation(self, token_tracker):
        """Test ending a conversation"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id)
        
        timeline = token_tracker.end_conversation(conversation_id)
        
        assert timeline is not None
        assert timeline.end_time is not None
        assert timeline.conversation_id == conversation_id
    
    def test_get_turn_summary(self, token_tracker):
        """Test getting turn summary"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id, budget_limit_usd=10.0)
        
        summary = token_tracker.get_turn_summary(conversation_id)
        
        assert summary["conversation_id"] == conversation_id
        assert summary["total_turns"] == 0
        assert "budget_status" in summary
        assert summary["budget_status"]["limit"] == 10.0
    
    def test_export_timeline(self, token_tracker):
        """Test timeline export to JSON"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id)
        
        json_output = token_tracker.export_timeline(conversation_id)
        
        assert json_output is not None
        assert conversation_id in json_output
    
    @pytest.mark.asyncio
    async def test_simulate_budget_breach(self, token_tracker):
        """Test budget breach simulation"""
        conversation_id = "test-conv-123"
        token_tracker.start_conversation(conversation_id, budget_limit_usd=1.0)
        
        # Track some turns
        for i in range(3):
            msg = Mock()
            msg.content = "Test"
            
            await token_tracker.track_turn(
                conversation_id=conversation_id,
                turn_number=i + 1,
                agent_name="test_agent",
                message=msg,
                model="gpt-4",
                prompt_tokens=100,
                completion_tokens=100
            )
        
        # Simulate future usage
        breach_info = await token_tracker.simulate_budget_breach(
            conversation_id=conversation_id,
            turns_to_simulate=20
        )
        
        assert "current_cost_usd" in breach_info
        assert "projected_cost_usd" in breach_info
        assert "will_breach" in breach_info
        assert breach_info["simulated_turns"] == 20


class TestTokenTimeline:
    """Test conversation token timeline"""
    
    @pytest.mark.asyncio
    async def test_timeline_to_dict(self):
        """Test timeline serialization"""
        timeline = ConversationTokenTimeline(
            conversation_id="test-123",
            start_time=datetime.utcnow(),
            budget_limit_usd=10.0
        )
        
        # Add a turn
        turn = TurnTokenUsage(
            turn_number=1,
            agent_name="test_agent",
            message_type="text",
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150,
            prompt_cost_usd=0.001,
            completion_cost_usd=0.002,
            total_cost_usd=0.003,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=1),
            duration_ms=1000,
            message_length=100
        )
        timeline.turns.append(turn)
        
        # Serialize
        timeline_dict = timeline.to_dict()
        
        assert timeline_dict["conversation_id"] == "test-123"
        assert timeline_dict["total_turns"] == 1
        assert len(timeline_dict["timeline"]) == 1
        assert timeline_dict["budget"]["limit_usd"] == 10.0
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance metrics calculation"""
        timeline = ConversationTokenTimeline(
            conversation_id="test-123",
            start_time=datetime.utcnow()
        )
        
        # Add multiple turns
        for i in range(5):
            turn = TurnTokenUsage(
                turn_number=i + 1,
                agent_name=f"agent_{i % 2}",
                message_type="text",
                prompt_tokens=100,
                completion_tokens=100,
                total_tokens=200,
                prompt_cost_usd=0.001,
                completion_cost_usd=0.001,
                total_cost_usd=0.002,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(seconds=1),
                duration_ms=1000,
                message_length=100,
                tokens_per_second=200.0
            )
            timeline.turns.append(turn)
            timeline.total_tokens += turn.total_tokens
            timeline.total_cost_usd += turn.total_cost_usd
        
        # Calculate averages
        timeline.avg_tokens_per_turn = timeline.total_tokens / len(timeline.turns)
        timeline.avg_cost_per_turn = timeline.total_cost_usd / len(timeline.turns)
        
        assert timeline.avg_tokens_per_turn == 200
        assert timeline.avg_cost_per_turn == 0.002


class TestBudgetMonitoring:
    """Test budget monitoring callbacks"""
    
    @pytest.mark.asyncio
    async def test_budget_monitor_callback(self, caplog):
        """Test the budget monitor callback"""
        
        # Create mock data
        turn_usage = Mock()
        turn_usage.turn_number = 5
        
        timeline = Mock()
        timeline.budget_remaining_usd = -1.0
        timeline.budget_limit_usd = 10.0
        
        # Test budget breach
        await budget_monitor_callback(
            "budget_breach",
            "test-conv",
            turn_usage,
            timeline
        )
        
        # Should log critical message
        assert "BUDGET BREACHED" in caplog.text
        
        # Test high usage warning
        timeline.budget_remaining_usd = 1.5  # 85% used
        await budget_monitor_callback(
            "turn_complete",
            "test-conv",
            turn_usage,
            timeline
        )
        
        assert "Budget usage high" in caplog.text


class TestGlobalTokenTracker:
    """Test global token tracker functions"""
    
    def test_initialize_and_get_tracker(self):
        """Test global tracker initialization"""
        
        tracker = initialize_token_tracker(budget_limit_usd=20.0)
        assert tracker is not None
        assert tracker.budget_limit_usd == 20.0
        
        # Get should return same instance
        from backend.src.agents.services.turn_token_tracker import get_token_tracker
        same_tracker = get_token_tracker()
        assert same_tracker is tracker


if __name__ == "__main__":
    pytest.main([__file__, "-v"])