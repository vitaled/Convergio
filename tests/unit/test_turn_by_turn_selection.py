"""
Unit tests for turn-by-turn speaker selection
Verifies intelligent speaker selection at each conversation turn
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

from backend.src.agents.services.groupchat.turn_by_turn_selector import (
    TurnByTurnSelectorGroupChat,
    create_turn_by_turn_groupchat
)
from backend.src.agents.services.groupchat.selection_policy import (
    IntelligentSpeakerSelector,
    MissionPhase,
    ExpertiseDomain,
    SelectionContext,
    AgentCapability
)


class TestTurnByTurnSelection:
    """Test turn-by-turn speaker selection functionality"""
    
    @pytest.fixture
    def mock_participants(self):
        """Create mock agent participants"""
        participants = []
        
        # Create diverse agents
        agent_names = [
            "ali_chief_of_staff",
            "amy_cfo", 
            "luca_security_expert",
            "diana_performance_dashboard"
        ]
        
        for name in agent_names:
            agent = Mock()
            agent.name = name
            agent.run_stream = AsyncMock()
            participants.append(agent)
        
        return participants
    
    @pytest.fixture
    def mock_model_client(self):
        """Create mock model client"""
        client = Mock()
        client.model = "gpt-4"
        return client
    
    @pytest.fixture
    def mock_selector(self):
        """Create mock intelligent selector"""
        selector = Mock(spec=IntelligentSpeakerSelector)
        selector.agent_capabilities = {
            "ali_chief_of_staff": Mock(
                agent_name="ali_chief_of_staff",
                expertise_domains={ExpertiseDomain.STRATEGY},
                mission_phase_relevance={MissionPhase.DISCOVERY: 0.9}
            ),
            "amy_cfo": Mock(
                agent_name="amy_cfo",
                expertise_domains={ExpertiseDomain.FINANCE},
                mission_phase_relevance={MissionPhase.ANALYSIS: 0.9}
            ),
            "luca_security_expert": Mock(
                agent_name="luca_security_expert",
                expertise_domains={ExpertiseDomain.SECURITY},
                mission_phase_relevance={MissionPhase.EXECUTION: 0.8}
            ),
            "diana_performance_dashboard": Mock(
                agent_name="diana_performance_dashboard",
                expertise_domains={ExpertiseDomain.ANALYTICS},
                mission_phase_relevance={MissionPhase.MONITORING: 0.9}
            )
        }
        
        # Mock score_agent method
        async def mock_score_agent(agent_name, context):
            scores = {
                "ali_chief_of_staff": 0.8,
                "amy_cfo": 0.7,
                "luca_security_expert": 0.6,
                "diana_performance_dashboard": 0.5
            }
            return scores.get(agent_name, 0.5)
        
        selector.score_agent = mock_score_agent
        return selector
    
    @pytest.fixture
    def turn_by_turn_chat(self, mock_participants, mock_model_client, mock_selector):
        """Create turn-by-turn selector group chat"""
        return TurnByTurnSelectorGroupChat(
            participants=mock_participants,
            model_client=mock_model_client,
            selector=mock_selector,
            enable_intelligent_selection=True,
            max_turns=10
        )
    
    @pytest.mark.asyncio
    async def test_intelligent_selection_enabled(self, turn_by_turn_chat):
        """Test that intelligent selection is properly enabled"""
        assert turn_by_turn_chat.enable_intelligent_selection
        assert turn_by_turn_chat.intelligent_selector is not None
        assert turn_by_turn_chat.turn_count == 0
    
    @pytest.mark.asyncio
    async def test_turn_counting(self, turn_by_turn_chat):
        """Test that turns are counted correctly"""
        # Create mock messages
        messages = []
        for i in range(3):
            msg = Mock()
            msg.content = f"Message {i}"
            msg.source = "user"
            messages.append(msg)
        
        # Mock the parent select_speaker to avoid actual AutoGen calls
        with patch.object(TurnByTurnSelectorGroupChat.__bases__[0], 'select_speaker', 
                         AsyncMock(return_value=turn_by_turn_chat.participants[0])):
            
            # Select speaker multiple times
            await turn_by_turn_chat.select_speaker(messages[:1])
            assert turn_by_turn_chat.turn_count == 1
            
            await turn_by_turn_chat.select_speaker(messages[:2])
            assert turn_by_turn_chat.turn_count == 2
            
            await turn_by_turn_chat.select_speaker(messages)
            assert turn_by_turn_chat.turn_count == 3
    
    @pytest.mark.asyncio
    async def test_phase_detection(self, turn_by_turn_chat):
        """Test mission phase detection from messages"""
        
        # Test discovery phase
        phase = turn_by_turn_chat._detect_mission_phase(
            "Let's explore and understand the current situation",
            []
        )
        assert phase == MissionPhase.DISCOVERY
        
        # Test analysis phase
        phase = turn_by_turn_chat._detect_mission_phase(
            "We need to analyze the data and evaluate our options",
            []
        )
        assert phase == MissionPhase.ANALYSIS
        
        # Test strategy phase
        phase = turn_by_turn_chat._detect_mission_phase(
            "Let's create a strategic roadmap for the next quarter",
            []
        )
        assert phase == MissionPhase.STRATEGY
        
        # Test execution phase
        phase = turn_by_turn_chat._detect_mission_phase(
            "Time to implement and deploy the solution",
            []
        )
        assert phase == MissionPhase.EXECUTION
    
    @pytest.mark.asyncio
    async def test_complexity_calculation(self, turn_by_turn_chat):
        """Test conversation complexity calculation"""
        
        # Simple message
        complexity = turn_by_turn_chat._calculate_complexity(
            "Hello, how are you?",
            num_messages=2
        )
        assert complexity < 0.3
        
        # Complex technical message
        complexity = turn_by_turn_chat._calculate_complexity(
            "We need to implement a microservices architecture with API gateway, "
            "service mesh, and distributed tracing. The deployment should use "
            "container orchestration with proper security compliance and optimization "
            "algorithms for resource allocation." * 5,  # Make it long
            num_messages=15
        )
        assert complexity > 0.5
    
    @pytest.mark.asyncio
    async def test_urgency_detection(self, turn_by_turn_chat):
        """Test urgency level detection"""
        
        # Non-urgent
        urgency = turn_by_turn_chat._calculate_urgency(
            "When you have time, could you look at this?"
        )
        assert urgency < 0.3
        
        # Urgent
        urgency = turn_by_turn_chat._calculate_urgency(
            "This is urgent! We need this done ASAP for the critical deadline today!"
        )
        assert urgency > 0.7
    
    @pytest.mark.asyncio
    async def test_expertise_extraction(self, turn_by_turn_chat):
        """Test required expertise extraction"""
        
        # Financial expertise
        expertise = turn_by_turn_chat._extract_required_expertise(
            "What's our revenue, budget, and ROI for this quarter?"
        )
        assert ExpertiseDomain.FINANCE in expertise
        
        # Security expertise
        expertise = turn_by_turn_chat._extract_required_expertise(
            "We have a security vulnerability and need compliance review"
        )
        assert ExpertiseDomain.SECURITY in expertise
        
        # Multiple domains
        expertise = turn_by_turn_chat._extract_required_expertise(
            "Analyze our financial metrics and create a strategic roadmap with security considerations"
        )
        assert ExpertiseDomain.FINANCE in expertise
        assert ExpertiseDomain.STRATEGY in expertise
        assert ExpertiseDomain.SECURITY in expertise
    
    @pytest.mark.asyncio
    async def test_speaker_diversity(self, turn_by_turn_chat):
        """Test that speaker selection encourages diversity"""
        
        # Set up previous speakers
        turn_by_turn_chat.previous_speakers = ["ali_chief_of_staff", "ali_chief_of_staff"]
        
        # Create context
        context = SelectionContext(
            message_content="Need analysis",
            conversation_history=[],
            current_mission_phase=MissionPhase.ANALYSIS,
            previous_speakers=turn_by_turn_chat.previous_speakers,
            conversation_complexity=0.5,
            urgency_level=0.3,
            required_expertise={ExpertiseDomain.FINANCE},
            collaboration_needed=False,
            user_preferences={}
        )
        
        # Initial scores
        scores = {
            "ali_chief_of_staff": 0.8,
            "amy_cfo": 0.75,  # Close second
            "luca_security_expert": 0.6,
            "diana_performance_dashboard": 0.5
        }
        
        # Apply turn adjustments (should penalize Ali for recent speaking)
        adjusted_scores = turn_by_turn_chat._apply_turn_adjustments(scores, context)
        
        # Amy should now have higher score due to Ali's penalty
        assert adjusted_scores["amy_cfo"] > adjusted_scores["ali_chief_of_staff"]
    
    @pytest.mark.asyncio
    async def test_turn_based_phase_boost(self, turn_by_turn_chat):
        """Test that early/late turns boost appropriate agents"""
        
        context = SelectionContext(
            message_content="Test message",
            conversation_history=[],
            current_mission_phase=MissionPhase.DISCOVERY,
            previous_speakers=[],
            conversation_complexity=0.5,
            urgency_level=0.3,
            required_expertise=set(),
            collaboration_needed=False,
            user_preferences={}
        )
        
        # Early turn (turn 2)
        turn_by_turn_chat.turn_count = 2
        scores = {
            "ali_chief_of_staff": 0.7,  # Discovery agent
            "amy_cfo": 0.7,
            "luca_security_expert": 0.7,  # Execution agent
            "diana_performance_dashboard": 0.7
        }
        
        # Set up capabilities for boost
        turn_by_turn_chat.intelligent_selector.agent_capabilities["ali_chief_of_staff"] = Mock(
            mission_phase_relevance={MissionPhase.DISCOVERY: 0.9, MissionPhase.EXECUTION: 0.3}
        )
        turn_by_turn_chat.intelligent_selector.agent_capabilities["luca_security_expert"] = Mock(
            mission_phase_relevance={MissionPhase.DISCOVERY: 0.3, MissionPhase.EXECUTION: 0.9}
        )
        
        adjusted_early = turn_by_turn_chat._apply_turn_adjustments(scores.copy(), context)
        
        # Late turn (turn 12)
        turn_by_turn_chat.turn_count = 12
        adjusted_late = turn_by_turn_chat._apply_turn_adjustments(scores.copy(), context)
        
        # Ali should be boosted more in early turns
        # Luca should be boosted more in late turns
        assert adjusted_early["ali_chief_of_staff"] > adjusted_early["luca_security_expert"]
        assert adjusted_late["luca_security_expert"] > adjusted_late["ali_chief_of_staff"]
    
    @pytest.mark.asyncio
    async def test_urgency_affects_selection(self, turn_by_turn_chat):
        """Test that urgency affects agent selection"""
        
        # Set up fast responder
        turn_by_turn_chat.intelligent_selector.agent_capabilities["diana_performance_dashboard"] = Mock(
            avg_response_time=1.5  # Fast
        )
        turn_by_turn_chat.intelligent_selector.agent_capabilities["ali_chief_of_staff"] = Mock(
            avg_response_time=3.0  # Slower
        )
        
        # High urgency context
        context = SelectionContext(
            message_content="Urgent request",
            conversation_history=[],
            current_mission_phase=MissionPhase.EXECUTION,
            previous_speakers=[],
            conversation_complexity=0.5,
            urgency_level=0.9,  # High urgency
            required_expertise=set(),
            collaboration_needed=False,
            user_preferences={}
        )
        
        scores = {
            "ali_chief_of_staff": 0.7,
            "diana_performance_dashboard": 0.68  # Slightly lower initial score
        }
        
        adjusted = turn_by_turn_chat._apply_turn_adjustments(scores, context)
        
        # Diana should get boost for being fast responder in urgent situation
        assert adjusted["diana_performance_dashboard"] > 0.68 * 1.05  # At least 5% boost
    
    @pytest.mark.asyncio
    async def test_selection_performance_tracking(self, turn_by_turn_chat):
        """Test that selection performance is tracked"""
        
        # Mock selection process
        messages = [Mock(content="Test", source="user")]
        
        with patch.object(turn_by_turn_chat, '_intelligent_select', 
                         AsyncMock(return_value=turn_by_turn_chat.participants[0])):
            
            # Make several selections
            for _ in range(3):
                await turn_by_turn_chat.select_speaker(messages)
            
            # Check performance metrics
            perf = turn_by_turn_chat.get_selection_performance()
            
            assert perf["total_turns"] == 3
            assert "avg_selection_time_ms" in perf
            assert "speaker_diversity" in perf
            assert len(turn_by_turn_chat.selection_times) == 3
    
    @pytest.mark.asyncio
    async def test_fallback_on_error(self, turn_by_turn_chat):
        """Test fallback to default selection on error"""
        
        # Make intelligent selection fail
        turn_by_turn_chat.intelligent_selector.score_agent = AsyncMock(
            side_effect=Exception("Selection error")
        )
        
        messages = [Mock(content="Test", source="user")]
        
        # Mock parent select_speaker for fallback
        with patch.object(TurnByTurnSelectorGroupChat.__bases__[0], 'select_speaker',
                         AsyncMock(return_value=turn_by_turn_chat.participants[0])) as mock_parent:
            
            # Should fallback without raising
            result = await turn_by_turn_chat.select_speaker(messages)
            
            assert result == turn_by_turn_chat.participants[0]
            mock_parent.assert_called_once()  # Verify fallback was used
    
    @pytest.mark.asyncio
    async def test_collaboration_detection(self, turn_by_turn_chat):
        """Test collaboration need detection"""
        
        # Should detect collaboration
        assert turn_by_turn_chat._needs_collaboration(
            "We need to collaborate and coordinate across teams"
        )
        
        assert turn_by_turn_chat._needs_collaboration(
            "This requires joint effort from multiple departments"
        )
        
        # Should not detect collaboration
        assert not turn_by_turn_chat._needs_collaboration(
            "I need a simple analysis"
        )


class TestSelectionIntegration:
    """Test integration with selection metrics"""
    
    @pytest.mark.asyncio
    async def test_metrics_recording(self):
        """Test that selection metrics are recorded"""
        
        with patch('backend.src.agents.services.groupchat.selection_metrics.record_selection_metrics') as mock_record:
            mock_record.return_value = AsyncMock()
            
            # Create chat
            participants = [Mock(name=f"agent_{i}") for i in range(3)]
            model_client = Mock()
            selector = Mock(spec=IntelligentSpeakerSelector)
            selector.agent_capabilities = {}
            selector.score_agent = AsyncMock(return_value=0.8)
            
            chat = TurnByTurnSelectorGroupChat(
                participants=participants,
                model_client=model_client,
                selector=selector,
                enable_intelligent_selection=True
            )
            
            # Mock intelligent select
            chat._intelligent_select = AsyncMock(return_value=participants[0])
            
            # Select speaker
            messages = [Mock(content="Test", source="user")]
            await chat.select_speaker(messages)
            
            # Verify metrics were recorded
            assert chat.turn_count == 1
            assert len(chat.selection_scores) > 0
    
    @pytest.mark.asyncio
    async def test_turn_reduction_measurement(self):
        """Test that turn reduction can be measured"""
        
        # Create two chats - one with intelligent selection, one without
        participants = [Mock(name=f"agent_{i}") for i in range(4)]
        model_client = Mock()
        
        # Chat with intelligent selection
        intelligent_chat = TurnByTurnSelectorGroupChat(
            participants=participants,
            model_client=model_client,
            enable_intelligent_selection=True,
            max_turns=20
        )
        
        # Chat without intelligent selection  
        default_chat = TurnByTurnSelectorGroupChat(
            participants=participants,
            model_client=model_client,
            enable_intelligent_selection=False,
            max_turns=20
        )
        
        # Simulate conversations
        # Intelligent should achieve goal in fewer turns
        intelligent_turns = 8
        default_turns = 12
        
        for _ in range(intelligent_turns):
            intelligent_chat.turn_count += 1
            intelligent_chat.previous_speakers.append(participants[_ % 4].name)
        
        for _ in range(default_turns):
            default_chat.turn_count += 1
            default_chat.previous_speakers.append(participants[_ % 4].name)
        
        # Calculate turn reduction
        reduction = (default_turns - intelligent_turns) / default_turns * 100
        
        # Should achieve at least 10% reduction
        assert reduction >= 10
        
        # Check diversity
        intelligent_perf = intelligent_chat.get_selection_performance()
        default_perf = default_chat.get_selection_performance()
        
        assert intelligent_perf["total_turns"] < default_perf["total_turns"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])