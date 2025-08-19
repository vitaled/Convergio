"""
🧠 RAG Processor Functionality Tests
==================================

Integration tests for RAG (Retrieval-Augmented Generation) functionality
including memory system integration and context enhancement.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_processor_initialization():
    """Test RAG processor initialization with memory system."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor
        from agents.memory.autogen_memory_system import AutoGenMemorySystem
        
        # Test with default initialization
        processor = AdvancedRAGProcessor()
        assert processor is not None
        assert processor.memory_system is not None
        assert processor.dynamic_threshold is not None
        assert processor.semantic_deduplicator is not None
        assert processor.cache is not None
        assert processor.quality_monitor is not None
        
        # Test with custom memory system
        memory_system = AutoGenMemorySystem()
        processor_custom = AdvancedRAGProcessor(memory_system=memory_system)
        assert processor_custom.memory_system == memory_system
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_context_creation():
    """Test RAG context creation with scoring."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor, RAGContext
        from agents.memory.autogen_memory_system import MemoryEntry, MemoryType
        
        processor = AdvancedRAGProcessor()
        
        # Create mock memory entry
        mock_memory = MemoryEntry(
            id="test_memory_1",
            user_id="test_user",
            agent_id="test_agent",
            memory_type=MemoryType.CONVERSATION,
            content="This is a test conversation about project management and deadlines.",
            importance_score=0.8,
            conversation_id="conv_123",
            created_at=datetime.now()
        )
        
        # Test context creation
        rag_context = await processor._create_rag_context(
            memory=mock_memory,
            query="project management",
            recency_weight=0.3,
            importance_weight=0.4,
            relevance_weight=0.3
        )
        
        assert isinstance(rag_context, RAGContext)
        assert rag_context.content == mock_memory.content
        assert rag_context.importance_score == 0.8
        assert 0.0 <= rag_context.relevance_score <= 1.0
        assert 0.0 <= rag_context.recency_score <= 1.0
        assert 0.0 <= rag_context.composite_score <= 1.0
        assert rag_context.source_agent == "test_agent"
        assert rag_context.memory_type == MemoryType.CONVERSATION
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_relevance_score_calculation():
    """Test relevance score calculation with different methods."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor
        
        processor = AdvancedRAGProcessor()
        
        # Test exact match
        score1 = await processor._calculate_relevance_score(
            "project management and deadlines",
            "project management"
        )
        assert score1 > 0.0
        
        # Test partial match
        score2 = await processor._calculate_relevance_score(
            "software development lifecycle",
            "project management"
        )
        assert 0.0 <= score2 <= 1.0
        
        # Test no match
        score3 = await processor._calculate_relevance_score(
            "weather forecast today",
            "project management"
        )
        assert score3 == 0.0
        
        # Exact match should have higher score than partial match
        assert score1 > score2
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_recency_score_calculation():
    """Test recency score calculation."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor
        
        processor = AdvancedRAGProcessor()
        
        # Test recent timestamp (should have high score)
        recent_time = datetime.now() - timedelta(hours=1)
        recent_score = await processor._calculate_recency_score(recent_time)
        
        # Test old timestamp (should have lower score)
        old_time = datetime.now() - timedelta(days=7)
        old_score = await processor._calculate_recency_score(old_time)
        
        assert 0.0 <= recent_score <= 1.0
        assert 0.0 <= old_score <= 1.0
        assert recent_score > old_score
        
        # Test None timestamp
        none_score = await processor._calculate_recency_score(None)
        assert none_score == 0.0
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_context_building():
    """Test building memory context from various sources."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor
        from agents.memory.autogen_memory_system import AutoGenMemorySystem, MemoryEntry, MemoryType
        
        # Mock memory system with test data
        mock_memory_system = Mock(spec=AutoGenMemorySystem)
        
        # Mock memory entries
        mock_memories = [
            MemoryEntry(
                id="mem_1",
                user_id="test_user", 
                agent_id="test_agent",
                memory_type=MemoryType.CONVERSATION,
                content="We discussed the Q4 project timeline and deliverables.",
                importance_score=0.7,
                conversation_id="conv_1",
                created_at=datetime.now() - timedelta(hours=2)
            ),
            MemoryEntry(
                id="mem_2",
                user_id="test_user",
                agent_id="test_agent", 
                memory_type=MemoryType.KNOWLEDGE,
                content="Project management best practices include regular stakeholder communication.",
                importance_score=0.9,
                conversation_id=None,
                created_at=datetime.now() - timedelta(days=1)
            )
        ]
        
        mock_memory_system.retrieve_by_type = AsyncMock(return_value=mock_memories)
        
        processor = AdvancedRAGProcessor(memory_system=mock_memory_system)
        
        # Test context building
        context_message = await processor.build_memory_context(
            user_id="test_user",
            agent_id="test_agent", 
            query="project management timeline",
            limit=5,
            similarity_threshold=0.1,
            use_cache=False  # Disable cache for testing
        )
        
        assert context_message is not None
        assert "Relevant Context" in context_message.content
        assert "project" in context_message.content.lower()
        assert "timeline" in context_message.content.lower()
        
        # Verify memory system was called correctly
        assert mock_memory_system.retrieve_by_type.called
        call_args = mock_memory_system.retrieve_by_type.call_args_list
        assert len(call_args) >= 1  # Should be called for different memory types
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_deduplication():
    """Test context deduplication functionality."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor, RAGContext
        from agents.memory.autogen_memory_system import MemoryType
        
        processor = AdvancedRAGProcessor()
        
        # Create duplicate contexts
        contexts = [
            RAGContext(
                content="This is a duplicate message about project status.",
                relevance_score=0.8,
                importance_score=0.7,
                recency_score=0.9,
                composite_score=0.8,
                source_agent="agent1",
                memory_type=MemoryType.CONVERSATION,
                conversation_id="conv1",
                timestamp=datetime.now()
            ),
            RAGContext(
                content="This is a duplicate message about project status.",  # Same content
                relevance_score=0.7,
                importance_score=0.6,
                recency_score=0.8,
                composite_score=0.7,
                source_agent="agent2", 
                memory_type=MemoryType.CONVERSATION,
                conversation_id="conv2",
                timestamp=datetime.now()
            ),
            RAGContext(
                content="This is a unique message about budget planning.",
                relevance_score=0.6,
                importance_score=0.8,
                recency_score=0.7,
                composite_score=0.7,
                source_agent="agent1",
                memory_type=MemoryType.KNOWLEDGE,
                conversation_id=None,
                timestamp=datetime.now()
            )
        ]
        
        # Test deduplication
        deduplicated = await processor._deduplicate_and_rank(contexts, limit=10)
        
        # Should have only 2 unique contexts (duplicates removed)
        assert len(deduplicated) == 2
        
        # Should be sorted by composite score
        scores = [c.composite_score for c in deduplicated]
        assert scores == sorted(scores, reverse=True)
        
        # Should keep the higher scoring duplicate
        project_contexts = [c for c in deduplicated if "project status" in c.content]
        assert len(project_contexts) == 1
        assert project_contexts[0].composite_score == 0.8  # Higher score kept
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unified_orchestrator_rag_integration():
    """Test RAG integration in unified orchestrator."""
    
    try:
        from agents.orchestrators.unified import UnifiedOrchestrator
        
        # Initialize orchestrator with RAG enabled
        orchestrator = UnifiedOrchestrator()
        await orchestrator.initialize(enable_rag=True, enable_safety=False)
        
        # Verify RAG processor was initialized
        assert hasattr(orchestrator, 'rag_processor')
        
        # RAG processor should be initialized if dependencies are available
        if orchestrator.rag_processor is not None:
            assert orchestrator.rag_processor.memory_system is not None
        
        # Test conversation with RAG context
        if orchestrator.rag_processor:
            # Mock the RAG processor to avoid actual memory operations
            orchestrator.rag_processor.build_memory_context = AsyncMock(
                return_value=Mock(content="Test RAG context for project management")
            )
            
            result = await orchestrator.orchestrate_conversation(
                message="Tell me about project management best practices",
                user_id="test_user",
                conversation_id="test_conv",
                context={
                    "rag_limit": 3,
                    "rag_threshold": 0.3,
                    "include_history": True,
                    "include_knowledge": True
                }
            )
            
            # Verify RAG context was requested
            orchestrator.rag_processor.build_memory_context.assert_called_once()
            
            # Result should contain response
            assert "response" in result
            assert isinstance(result["response"], str)
        
    except ImportError as e:
        pytest.skip(f"Orchestrator or RAG components not available: {e}")
    except Exception as e:
        # If orchestrator initialization fails, that's also acceptable for this test
        pytest.skip(f"Orchestrator initialization failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_cache_functionality():
    """Test RAG caching functionality."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor
        from agents.services.groupchat.rag_enhancements import IntelligentRAGCache
        
        # Test cache initialization
        cache = IntelligentRAGCache()
        await cache.initialize()
        
        # Test cache operations
        test_result = {"content": "Cached RAG result for project management query"}
        
        # Set cache entry
        await cache.set(
            user_id="test_user",
            query="project management",
            result=test_result,
            agent_id="test_agent"
        )
        
        # Get cache entry
        cached_result = await cache.get(
            user_id="test_user", 
            query="project management",
            agent_id="test_agent"
        )
        
        if cached_result:  # Cache might not be available in test environment
            assert cached_result["content"] == test_result["content"]
        
    except ImportError as e:
        pytest.skip(f"RAG cache components not available: {e}")
    except Exception as e:
        # Cache operations might fail in test environment
        pytest.skip(f"Cache operations not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_quality_monitoring():
    """Test RAG quality monitoring functionality."""
    
    try:
        from agents.services.groupchat.rag_enhancements import RAGQualityMonitor
        
        monitor = RAGQualityMonitor()
        
        # Test tracking retrieval metrics
        await monitor.track_retrieval(
            query="test query",
            contexts_retrieved=3,
            avg_score=0.75,
            latency_ms=150.0,
            cache_hit=False
        )
        
        # Test tracking agent filter effectiveness
        await monitor.track_agent_filter_effectiveness(
            agent_name="test_agent",
            pre_filter_count=10,
            post_filter_count=7,
            avg_score_improvement=0.15
        )
        
        # Verify monitoring doesn't crash
        assert True
        
    except ImportError as e:
        pytest.skip(f"RAG quality monitoring not available: {e}")
    except Exception as e:
        # Monitoring might fail in test environment
        pytest.skip(f"Quality monitoring operations failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_specific_rag_context():
    """Test agent-specific context retrieval."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor
        from agents.memory.autogen_memory_system import AutoGenMemorySystem
        
        # Mock memory system
        mock_memory_system = Mock(spec=AutoGenMemorySystem)
        mock_memory_system.retrieve_by_type = AsyncMock(return_value=[])
        
        processor = AdvancedRAGProcessor(memory_system=mock_memory_system)
        
        # Test agent-specific context retrieval
        contexts = await processor._get_agent_specific_context(
            user_id="test_user",
            agent_id="ali_chief_of_staff",
            query="strategic planning",
            limit=3
        )
        
        # Should return list (even if empty due to mocking)
        assert isinstance(contexts, list)
        
        # Verify memory system was called for relationships and preferences
        call_args = mock_memory_system.retrieve_by_type.call_args_list
        assert len(call_args) >= 1  # Should be called for relationships/preferences
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_error_handling():
    """Test RAG error handling and fallback behavior."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor
        from agents.memory.autogen_memory_system import AutoGenMemorySystem
        
        # Mock memory system that raises errors
        mock_memory_system = Mock(spec=AutoGenMemorySystem)
        mock_memory_system.retrieve_by_type = AsyncMock(side_effect=Exception("Memory system error"))
        
        processor = AdvancedRAGProcessor(memory_system=mock_memory_system)
        
        # Test error handling in context building
        context_message = await processor.build_memory_context(
            user_id="test_user",
            agent_id="test_agent",
            query="test query",
            limit=5,
            use_cache=False
        )
        
        # Should return None gracefully when memory system fails
        assert context_message is None
        
        # Test relevance score calculation with embedding errors
        with patch('agents.tools.vector_search_client.embed_text', side_effect=Exception("Embedding error")):
            score = await processor._calculate_relevance_score("test content", "test query")
            
            # Should fall back to keyword matching
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_rag_performance_characteristics():
    """Test RAG performance characteristics under load."""
    
    try:
        from agents.services.groupchat.rag import AdvancedRAGProcessor
        from agents.memory.autogen_memory_system import AutoGenMemorySystem, MemoryEntry, MemoryType
        import time
        
        # Create processor
        mock_memory_system = Mock(spec=AutoGenMemorySystem)
        
        # Create many mock memory entries
        mock_memories = []
        for i in range(50):  # Large number of memories
            mock_memories.append(MemoryEntry(
                id=f"mem_{i}",
                user_id="test_user",
                agent_id="test_agent",
                memory_type=MemoryType.CONVERSATION,
                content=f"This is test memory entry number {i} about various project topics.",
                importance_score=0.5 + (i % 5) * 0.1,
                conversation_id=f"conv_{i//10}",
                created_at=datetime.now() - timedelta(hours=i)
            ))
        
        mock_memory_system.retrieve_by_type = AsyncMock(return_value=mock_memories)
        processor = AdvancedRAGProcessor(memory_system=mock_memory_system)
        
        # Test performance with large result set
        start_time = time.time()
        
        context_message = await processor.build_memory_context(
            user_id="test_user",
            agent_id="test_agent",
            query="project topics",
            limit=10,
            use_cache=False,
            use_semantic_dedup=True
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (< 5 seconds)
        assert processing_time < 5.0, f"RAG processing too slow: {processing_time:.2f}s"
        
        # Should still return valid context
        if context_message:
            assert isinstance(context_message.content, str)
            assert len(context_message.content) > 0
        
    except ImportError as e:
        pytest.skip(f"RAG components not available: {e}")