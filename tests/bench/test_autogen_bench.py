"""
AutoGen Bench Test Suite - Pytest integration for benchmark scenarios
Runs comprehensive benchmark tests and generates CI artifacts.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import structlog

from tests.bench.autogen_bench_scenarios import (
    AutoGenBenchmarkSuite,
    BenchmarkScenario,
    run_full_benchmark_suite,
    STRATEGIC_QA_TESTS,
    ANALYTICS_SYNTHESIS_TESTS,
    ROUTING_COMPLEXITY_TESTS,
    PERFORMANCE_STRESS_TESTS,
    COST_EFFICIENCY_TESTS,
    MEMORY_COHERENCE_TESTS,
    WORKFLOW_EXECUTION_TESTS,
    MULTI_AGENT_COLLABORATION_TESTS
)

logger = structlog.get_logger()


@pytest.fixture
async def mock_orchestrator():
    """Create mock orchestrator for testing"""
    from backend.src.agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
    from backend.src.agents.services.groupchat.types import GroupChatResult
    
    orchestrator = AsyncMock(spec=ModernGroupChatOrchestrator)
    
    # Mock successful response
    mock_result = MagicMock(spec=GroupChatResult)
    mock_result.final_response = "This is a strategic analysis with market insights and competitive positioning."
    mock_result.agents_used = ["ali_chief_of_staff", "domik_mckinsey_strategic_decision_maker"]
    mock_result.chat_history = [
        {"role": "user", "content": "What is our strategy?"},
        {"role": "assistant", "content": "Based on market analysis..."}
    ]
    mock_result.cost_breakdown = {
        "total_cost": 0.005,
        "total_tokens": 150,
        "model": "gpt-4o-mini"
    }
    mock_result.duration_seconds = 1.5
    
    orchestrator.orchestrate_conversation.return_value = mock_result
    orchestrator.is_healthy.return_value = True
    
    return orchestrator


@pytest.fixture
def benchmark_output_dir(tmp_path):
    """Create temporary directory for benchmark outputs"""
    output_dir = tmp_path / "benchmark_results"
    output_dir.mkdir(exist_ok=True)
    return output_dir


class TestAutoGenBenchmark:
    """Test suite for AutoGen benchmark scenarios"""
    
    @pytest.mark.asyncio
    async def test_strategic_qa_scenario(self, mock_orchestrator):
        """Test strategic Q&A benchmark scenario"""
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        result = await suite.run_scenario(
            BenchmarkScenario.STRATEGIC_QA,
            STRATEGIC_QA_TESTS[:1]  # Run first test only
        )
        
        assert result.scenario == BenchmarkScenario.STRATEGIC_QA
        assert result.passed == True
        assert result.total_turns > 0
        assert result.total_cost_usd > 0
        assert result.answer_quality_score > 0.5
        assert len(result.agents_used) > 0
    
    @pytest.mark.asyncio
    async def test_analytics_synthesis_scenario(self, mock_orchestrator):
        """Test analytics synthesis benchmark scenario"""
        # Mock analytics-specific response
        mock_result = MagicMock()
        mock_result.final_response = "Performance metrics show 25% growth with KPI improvements and trend analysis."
        mock_result.agents_used = ["diana_performance_dashboard", "amy_cfo"]
        mock_result.chat_history = [{"role": "assistant", "content": "Metrics analysis..."}]
        mock_result.cost_breakdown = {"total_cost": 0.004, "total_tokens": 120, "model": "gpt-4o-mini"}
        mock_orchestrator.orchestrate_conversation.return_value = mock_result
        
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        result = await suite.run_scenario(
            BenchmarkScenario.ANALYTICS_SYNTHESIS,
            ANALYTICS_SYNTHESIS_TESTS[:1]
        )
        
        assert result.scenario == BenchmarkScenario.ANALYTICS_SYNTHESIS
        assert result.passed == True
        assert "diana_performance_dashboard" in result.agents_used or "amy_cfo" in result.agents_used
    
    @pytest.mark.asyncio
    async def test_routing_complexity_scenario(self, mock_orchestrator):
        """Test routing complexity benchmark scenario"""
        # Mock different agents for different messages
        responses = [
            {"agents": ["amy_cfo"], "response": "Budget planning response"},
            {"agents": ["luca_security_expert"], "response": "Security analysis"},
            {"agents": ["ali_chief_of_staff"], "response": "Strategic alignment"}
        ]
        
        call_count = 0
        def mock_conversation(*args, **kwargs):
            nonlocal call_count
            mock_result = MagicMock()
            mock_result.agents_used = responses[call_count]["agents"]
            mock_result.final_response = responses[call_count]["response"]
            mock_result.chat_history = []
            mock_result.cost_breakdown = {"total_cost": 0.003, "total_tokens": 100}
            call_count += 1
            return mock_result
        
        mock_orchestrator.orchestrate_conversation.side_effect = mock_conversation
        
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        result = await suite.run_scenario(
            BenchmarkScenario.ROUTING_COMPLEXITY,
            ROUTING_COMPLEXITY_TESTS[:1]
        )
        
        assert result.scenario == BenchmarkScenario.ROUTING_COMPLEXITY
        assert result.routing_accuracy > 0.5
        assert len(result.agents_used) >= 3
    
    @pytest.mark.asyncio
    async def test_performance_stress_scenario(self, mock_orchestrator):
        """Test performance stress benchmark scenario"""
        # Mock fast responses
        mock_result = MagicMock()
        mock_result.final_response = "Quick response"
        mock_result.agents_used = ["ali_chief_of_staff"]
        mock_result.chat_history = []
        mock_result.cost_breakdown = {"total_cost": 0.002, "total_tokens": 50}
        mock_orchestrator.orchestrate_conversation.return_value = mock_result
        
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        # Reduce test load for unit tests
        test_case = {
            "name": "Light Load Test",
            "num_conversations": 3,
            "parallel": True,
            "max_response_time_seconds": 10.0
        }
        
        result = await suite.run_scenario(
            BenchmarkScenario.PERFORMANCE_STRESS,
            [test_case]
        )
        
        assert result.scenario == BenchmarkScenario.PERFORMANCE_STRESS
        assert result.passed == True
        assert result.avg_response_time < 10.0
    
    @pytest.mark.asyncio
    async def test_cost_efficiency_scenario(self, mock_orchestrator):
        """Test cost efficiency benchmark scenario"""
        # Mock efficient response
        mock_result = MagicMock()
        mock_result.final_response = "Simple answer"
        mock_result.agents_used = ["ali_chief_of_staff"]
        mock_result.chat_history = []
        mock_result.cost_breakdown = {
            "total_cost": 0.0005,  # Very low cost
            "total_tokens": 20,
            "model": "gpt-4o-mini"
        }
        mock_orchestrator.orchestrate_conversation.return_value = mock_result
        
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        result = await suite.run_scenario(
            BenchmarkScenario.COST_EFFICIENCY,
            COST_EFFICIENCY_TESTS[:1]
        )
        
        assert result.scenario == BenchmarkScenario.COST_EFFICIENCY
        assert result.passed == True
        assert result.cost_per_turn < 0.01
    
    @pytest.mark.asyncio
    async def test_memory_coherence_scenario(self, mock_orchestrator):
        """Test memory coherence benchmark scenario"""
        # Mock coherent responses
        responses = [
            "I understand your name is Alice and you manage the product team",
            "You manage the product team as mentioned",
            "Your name is Alice"
        ]
        
        call_count = 0
        def mock_conversation(*args, **kwargs):
            nonlocal call_count
            mock_result = MagicMock()
            mock_result.final_response = responses[call_count] if call_count < len(responses) else "Default"
            mock_result.agents_used = ["ali_chief_of_staff"]
            mock_result.chat_history = []
            mock_result.cost_breakdown = {"total_cost": 0.003, "total_tokens": 100}
            call_count += 1
            return mock_result
        
        mock_orchestrator.orchestrate_conversation.side_effect = mock_conversation
        
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        result = await suite.run_scenario(
            BenchmarkScenario.MEMORY_COHERENCE,
            MEMORY_COHERENCE_TESTS[:1]
        )
        
        assert result.scenario == BenchmarkScenario.MEMORY_COHERENCE
        assert result.coherence_score > 0.5
    
    @pytest.mark.asyncio
    async def test_workflow_execution_scenario(self, mock_orchestrator):
        """Test workflow execution benchmark scenario"""
        # Mock workflow response
        mock_result = MagicMock()
        mock_result.final_response = """
        Executing strategic analysis workflow:
        - Initial context established
        - Market analysis completed
        - Financial analysis performed
        - Strategic synthesis generated
        """
        mock_result.agents_used = ["wanda_workflow_orchestrator", "ali_chief_of_staff"]
        mock_result.chat_history = []
        mock_result.cost_breakdown = {"total_cost": 0.008, "total_tokens": 250}
        mock_orchestrator.orchestrate_conversation.return_value = mock_result
        
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        result = await suite.run_scenario(
            BenchmarkScenario.WORKFLOW_EXECUTION,
            WORKFLOW_EXECUTION_TESTS[:1]
        )
        
        assert result.scenario == BenchmarkScenario.WORKFLOW_EXECUTION
        assert result.passed == True
        assert result.quality_score > 0.5
    
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration_scenario(self, mock_orchestrator):
        """Test multi-agent collaboration benchmark scenario"""
        # Mock collaborative response
        mock_result = MagicMock()
        mock_result.final_response = "Comprehensive analysis with multiple perspectives"
        mock_result.agents_used = [
            "ali_chief_of_staff",
            "domik_mckinsey_strategic_decision_maker",
            "amy_cfo",
            "luca_security_expert"
        ]
        mock_result.chat_history = []
        mock_result.cost_breakdown = {"total_cost": 0.012, "total_tokens": 400}
        mock_orchestrator.orchestrate_conversation.return_value = mock_result
        
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        result = await suite.run_scenario(
            BenchmarkScenario.MULTI_AGENT_COLLABORATION,
            MULTI_AGENT_COLLABORATION_TESTS[:1]
        )
        
        assert result.scenario == BenchmarkScenario.MULTI_AGENT_COLLABORATION
        assert result.passed == True
        assert len(set(result.agents_used)) >= 3
    
    @pytest.mark.asyncio
    async def test_generate_benchmark_report(self, mock_orchestrator):
        """Test benchmark report generation"""
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        # Run a simple scenario
        await suite.run_scenario(
            BenchmarkScenario.STRATEGIC_QA,
            STRATEGIC_QA_TESTS[:1]
        )
        
        # Generate report
        report = suite.generate_report()
        
        assert "AUTOGEN BENCHMARK REPORT" in report
        assert "SUMMARY" in report
        assert "SCENARIO: strategic_qa" in report
        assert "Status:" in report
        assert "Quality Metrics:" in report
    
    @pytest.mark.asyncio
    async def test_save_benchmark_artifacts(self, mock_orchestrator, benchmark_output_dir):
        """Test saving benchmark artifacts for CI"""
        suite = AutoGenBenchmarkSuite(mock_orchestrator)
        
        # Run scenarios
        await suite.run_scenario(BenchmarkScenario.STRATEGIC_QA, STRATEGIC_QA_TESTS[:1])
        await suite.run_scenario(BenchmarkScenario.COST_EFFICIENCY, COST_EFFICIENCY_TESTS[:1])
        
        # Generate report
        report = suite.generate_report()
        
        # Save report
        report_path = benchmark_output_dir / f"benchmark_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path.write_text(report)
        
        # Save JSON results
        results_data = []
        for result in suite.results:
            results_data.append({
                "scenario": result.scenario.value,
                "passed": result.passed,
                "duration_seconds": result.duration_seconds,
                "total_cost_usd": result.total_cost_usd,
                "quality_score": result.answer_quality_score,
                "routing_accuracy": result.routing_accuracy,
                "coherence_score": result.coherence_score
            })
        
        json_path = benchmark_output_dir / "benchmark_results.json"
        json_path.write_text(json.dumps(results_data, indent=2))
        
        assert report_path.exists()
        assert json_path.exists()
        assert len(results_data) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_benchmark_suite_integration():
    """Integration test for full benchmark suite (skip in CI)"""
    pytest.skip("Full benchmark suite requires real orchestrator")
    
    # This would run with real orchestrator in integration environment
    from backend.src.agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
    from backend.src.agents.services.cost_tracker import CostTracker
    from backend.src.agents.services.redis_state_manager import RedisStateManager
    
    # Initialize real components
    state_manager = RedisStateManager()
    cost_tracker = CostTracker(state_manager)
    orchestrator = ModernGroupChatOrchestrator(state_manager, cost_tracker)
    
    await orchestrator.initialize()
    
    # Run full suite
    report = await run_full_benchmark_suite(orchestrator)
    
    # Save report
    output_dir = Path("benchmark_results")
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / f"full_benchmark_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
    report_path.write_text(report)
    
    assert "AUTOGEN BENCHMARK REPORT" in report
    print(f"Benchmark report saved to: {report_path}")


@pytest.mark.parametrize("scenario,test_cases", [
    (BenchmarkScenario.STRATEGIC_QA, STRATEGIC_QA_TESTS),
    (BenchmarkScenario.ANALYTICS_SYNTHESIS, ANALYTICS_SYNTHESIS_TESTS),
    (BenchmarkScenario.ROUTING_COMPLEXITY, ROUTING_COMPLEXITY_TESTS),
])
@pytest.mark.asyncio
async def test_benchmark_scenarios_parametrized(mock_orchestrator, scenario, test_cases):
    """Parametrized test for different benchmark scenarios"""
    suite = AutoGenBenchmarkSuite(mock_orchestrator)
    
    # Run only first test case for speed
    result = await suite.run_scenario(scenario, test_cases[:1])
    
    assert result.scenario == scenario
    assert result.duration_seconds > 0
    assert result.total_cost_usd >= 0
    
    # Scenario should have some result
    assert result.passed or len(result.failures) > 0


def test_benchmark_result_metrics_calculation():
    """Test benchmark result metrics calculation"""
    from tests.bench.autogen_bench_scenarios import BenchmarkResult
    
    result = BenchmarkResult(
        scenario=BenchmarkScenario.STRATEGIC_QA,
        scenario_name="strategic_qa",
        description="Test scenario",
        start_time=datetime.utcnow()
    )
    
    # Add test data
    result.response_times = [1.0, 2.0, 3.0, 4.0, 5.0]
    result.total_turns = 5
    result.total_cost_usd = 0.025
    result.total_tokens = 500
    
    # Calculate metrics
    result.calculate_metrics()
    
    assert result.avg_response_time == 3.0
    assert result.cost_per_turn == 0.005
    assert result.tokens_per_turn == 100
    assert result.p95_response_time > 0
    assert result.p99_response_time > 0


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=tests.bench",
        "--cov-report=term-missing",
        "--asyncio-mode=auto"
    ])