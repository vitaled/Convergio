"""
AutoGen Bench Scenarios - Comprehensive benchmark tests for Convergio AutoGen implementation
Tests strategic Q&A, analytics synthesis, routing complexity, and performance benchmarking.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import pytest
import structlog
from unittest.mock import AsyncMock, MagicMock, patch

# Import AutoGen components
from backend.src.agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
from backend.src.agents.services.cost_tracker import CostTracker
from backend.src.agents.services.redis_state_manager import RedisStateManager
from backend.src.agents.services.groupchat.selection_policy import MissionPhase
from backend.src.agents.services.groupchat.types import GroupChatResult

logger = structlog.get_logger()


class BenchmarkScenario(Enum):
    """Types of benchmark scenarios"""
    STRATEGIC_QA = "strategic_qa"
    ANALYTICS_SYNTHESIS = "analytics_synthesis"
    ROUTING_COMPLEXITY = "routing_complexity"
    PERFORMANCE_STRESS = "performance_stress"
    COST_EFFICIENCY = "cost_efficiency"
    MEMORY_COHERENCE = "memory_coherence"
    WORKFLOW_EXECUTION = "workflow_execution"
    MULTI_AGENT_COLLABORATION = "multi_agent_collaboration"


@dataclass
class BenchmarkResult:
    """Comprehensive benchmark result tracking"""
    scenario: BenchmarkScenario
    scenario_name: str
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Performance metrics
    total_turns: int = 0
    agents_used: List[str] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    
    # Cost metrics
    total_cost_usd: float = 0.0
    cost_per_turn: float = 0.0
    total_tokens: int = 0
    tokens_per_turn: float = 0.0
    model_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Quality metrics
    answer_quality_score: float = 0.0  # 0.0-1.0
    routing_accuracy: float = 0.0  # 0.0-1.0
    coherence_score: float = 0.0  # 0.0-1.0
    task_completion_rate: float = 0.0  # 0.0-1.0
    
    # Test outcomes
    passed: bool = False
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Detailed logs
    conversation_log: List[Dict[str, Any]] = field(default_factory=list)
    agent_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.response_times:
            self.avg_response_time = sum(self.response_times) / len(self.response_times)
            sorted_times = sorted(self.response_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            self.p95_response_time = sorted_times[p95_idx] if p95_idx < len(sorted_times) else 0
            self.p99_response_time = sorted_times[p99_idx] if p99_idx < len(sorted_times) else 0
        
        if self.total_turns > 0:
            self.cost_per_turn = self.total_cost_usd / self.total_turns
            self.tokens_per_turn = self.total_tokens / self.total_turns


class AutoGenBenchmarkSuite:
    """Comprehensive AutoGen benchmark test suite"""
    
    def __init__(self, orchestrator: ModernGroupChatOrchestrator):
        self.orchestrator = orchestrator
        self.results: List[BenchmarkResult] = []
        
    async def run_scenario(
        self,
        scenario: BenchmarkScenario,
        test_cases: List[Dict[str, Any]]
    ) -> BenchmarkResult:
        """Run a complete benchmark scenario"""
        
        result = BenchmarkResult(
            scenario=scenario,
            scenario_name=scenario.value,
            description=self._get_scenario_description(scenario),
            start_time=datetime.utcnow()
        )
        
        try:
            logger.info(f"🚀 Starting benchmark scenario: {scenario.value}")
            
            for i, test_case in enumerate(test_cases):
                logger.info(f"  Running test case {i+1}/{len(test_cases)}: {test_case.get('name', 'unnamed')}")
                
                case_result = await self._run_test_case(scenario, test_case)
                
                # Aggregate metrics
                result.total_turns += case_result.get("turns", 0)
                result.agents_used.extend(case_result.get("agents_used", []))
                result.response_times.append(case_result.get("response_time", 0))
                result.total_cost_usd += case_result.get("cost", 0)
                result.total_tokens += case_result.get("tokens", 0)
                
                # Update quality scores
                result.answer_quality_score += case_result.get("quality_score", 0)
                result.routing_accuracy += case_result.get("routing_score", 0)
                result.coherence_score += case_result.get("coherence_score", 0)
                
                # Log conversation
                result.conversation_log.append(case_result)
                
                # Check for failures
                if not case_result.get("passed", False):
                    result.failures.append(f"Test case {i+1}: {case_result.get('error', 'Unknown failure')}")
            
            # Calculate averages
            num_cases = len(test_cases)
            if num_cases > 0:
                result.answer_quality_score /= num_cases
                result.routing_accuracy /= num_cases
                result.coherence_score /= num_cases
                result.task_completion_rate = (num_cases - len(result.failures)) / num_cases
            
            result.passed = len(result.failures) == 0
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            
            # Calculate final metrics
            result.calculate_metrics()
            
            logger.info(f"✅ Completed scenario {scenario.value}: {'PASSED' if result.passed else 'FAILED'}")
            logger.info(f"   Duration: {result.duration_seconds:.2f}s, Cost: ${result.total_cost_usd:.4f}")
            
        except Exception as e:
            logger.error(f"❌ Scenario {scenario.value} failed with exception: {str(e)}")
            result.failures.append(f"Scenario exception: {str(e)}")
            result.passed = False
            
        self.results.append(result)
        return result
    
    async def _run_test_case(
        self,
        scenario: BenchmarkScenario,
        test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run individual test case within scenario"""
        
        start_time = time.time()
        
        try:
            # Execute test based on scenario type
            if scenario == BenchmarkScenario.STRATEGIC_QA:
                result = await self._run_strategic_qa_test(test_case)
            elif scenario == BenchmarkScenario.ANALYTICS_SYNTHESIS:
                result = await self._run_analytics_synthesis_test(test_case)
            elif scenario == BenchmarkScenario.ROUTING_COMPLEXITY:
                result = await self._run_routing_complexity_test(test_case)
            elif scenario == BenchmarkScenario.PERFORMANCE_STRESS:
                result = await self._run_performance_stress_test(test_case)
            elif scenario == BenchmarkScenario.COST_EFFICIENCY:
                result = await self._run_cost_efficiency_test(test_case)
            elif scenario == BenchmarkScenario.MEMORY_COHERENCE:
                result = await self._run_memory_coherence_test(test_case)
            elif scenario == BenchmarkScenario.WORKFLOW_EXECUTION:
                result = await self._run_workflow_execution_test(test_case)
            elif scenario == BenchmarkScenario.MULTI_AGENT_COLLABORATION:
                result = await self._run_multi_agent_collaboration_test(test_case)
            else:
                result = {"passed": False, "error": f"Unknown scenario: {scenario}"}
            
            response_time = time.time() - start_time
            result["response_time"] = response_time
            
            return result
            
        except Exception as e:
            logger.error(f"Test case failed: {str(e)}")
            return {
                "passed": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    async def _run_strategic_qa_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test strategic Q&A capabilities"""
        
        message = test_case.get("message", "What is our strategic positioning in the market?")
        expected_agents = test_case.get("expected_agents", ["ali_chief_of_staff", "domik_mckinsey_strategic_decision_maker"])
        
        # Run conversation
        result = await self.orchestrator.orchestrate_conversation(
            message=message,
            user_id="bench_user",
            conversation_id=f"bench_strategic_{datetime.utcnow().timestamp()}",
            context={"mission_phase": MissionPhase.STRATEGY.value}
        )
        
        # Evaluate results
        agents_matched = all(agent in result.agents_used for agent in expected_agents)
        quality_score = self._evaluate_strategic_answer_quality(result.final_response, test_case.get("expected_keywords", []))
        
        return {
            "passed": agents_matched and quality_score > 0.7,
            "turns": len(result.chat_history),
            "agents_used": result.agents_used,
            "cost": result.cost_breakdown.get("total_cost", 0),
            "tokens": result.cost_breakdown.get("total_tokens", 0),
            "quality_score": quality_score,
            "routing_score": 1.0 if agents_matched else 0.5,
            "coherence_score": self._evaluate_coherence(result.chat_history),
            "response": result.final_response
        }
    
    async def _run_analytics_synthesis_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test analytics synthesis capabilities"""
        
        message = test_case.get("message", "Synthesize our Q3 performance metrics and provide insights")
        expected_agents = test_case.get("expected_agents", ["diana_performance_dashboard", "amy_cfo"])
        
        # Run conversation
        result = await self.orchestrator.orchestrate_conversation(
            message=message,
            user_id="bench_user",
            conversation_id=f"bench_analytics_{datetime.utcnow().timestamp()}",
            context={"mission_phase": MissionPhase.MONITORING.value}
        )
        
        # Evaluate synthesis quality
        has_metrics = any(keyword in result.final_response.lower() for keyword in ["metric", "kpi", "performance", "trend"])
        has_insights = any(keyword in result.final_response.lower() for keyword in ["insight", "analysis", "recommend", "suggest"])
        quality_score = (0.5 if has_metrics else 0) + (0.5 if has_insights else 0)
        
        return {
            "passed": quality_score > 0.7,
            "turns": len(result.chat_history),
            "agents_used": result.agents_used,
            "cost": result.cost_breakdown.get("total_cost", 0),
            "tokens": result.cost_breakdown.get("total_tokens", 0),
            "quality_score": quality_score,
            "routing_score": 1.0 if any(agent in result.agents_used for agent in expected_agents) else 0.5,
            "coherence_score": self._evaluate_coherence(result.chat_history),
            "response": result.final_response
        }
    
    async def _run_routing_complexity_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test complex routing scenarios"""
        
        messages = test_case.get("messages", [
            "I need help with budget planning",
            "Also, what are the security implications?",
            "And how does this align with our strategy?"
        ])
        
        expected_agents_sequence = test_case.get("expected_sequence", [
            "amy_cfo",
            "luca_security_expert",
            "ali_chief_of_staff"
        ])
        
        all_agents_used = []
        total_cost = 0
        total_tokens = 0
        
        for i, message in enumerate(messages):
            result = await self.orchestrator.orchestrate_conversation(
                message=message,
                user_id="bench_user",
                conversation_id=f"bench_routing_{datetime.utcnow().timestamp()}",
                context={"turn": i}
            )
            
            all_agents_used.extend(result.agents_used)
            total_cost += result.cost_breakdown.get("total_cost", 0)
            total_tokens += result.cost_breakdown.get("total_tokens", 0)
        
        # Calculate routing accuracy
        routing_score = sum(
            1 for expected in expected_agents_sequence
            if expected in all_agents_used
        ) / len(expected_agents_sequence)
        
        return {
            "passed": routing_score > 0.7,
            "turns": len(messages),
            "agents_used": all_agents_used,
            "cost": total_cost,
            "tokens": total_tokens,
            "quality_score": 0.8,  # Default for routing tests
            "routing_score": routing_score,
            "coherence_score": 0.8  # Default for routing tests
        }
    
    async def _run_performance_stress_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test performance under stress conditions"""
        
        num_conversations = test_case.get("num_conversations", 10)
        parallel = test_case.get("parallel", True)
        max_response_time = test_case.get("max_response_time_seconds", 5.0)
        
        async def run_single_conversation(idx: int):
            start = time.time()
            result = await self.orchestrator.orchestrate_conversation(
                message=f"Performance test message {idx}",
                user_id="bench_user",
                conversation_id=f"bench_perf_{idx}_{datetime.utcnow().timestamp()}"
            )
            duration = time.time() - start
            return duration, result
        
        if parallel:
            # Run conversations in parallel
            tasks = [run_single_conversation(i) for i in range(num_conversations)]
            results = await asyncio.gather(*tasks)
        else:
            # Run conversations sequentially
            results = []
            for i in range(num_conversations):
                result = await run_single_conversation(i)
                results.append(result)
        
        response_times = [r[0] for r in results]
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        return {
            "passed": max_time < max_response_time,
            "turns": num_conversations,
            "agents_used": [],
            "cost": sum(r[1].cost_breakdown.get("total_cost", 0) for r in results),
            "tokens": sum(r[1].cost_breakdown.get("total_tokens", 0) for r in results),
            "quality_score": 1.0 if max_time < max_response_time else 0.5,
            "routing_score": 1.0,
            "coherence_score": 1.0,
            "avg_response_time": avg_time,
            "max_response_time": max_time
        }
    
    async def _run_cost_efficiency_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test cost efficiency optimizations"""
        
        message = test_case.get("message", "Simple query that should use efficient model")
        max_cost = test_case.get("max_cost_usd", 0.01)
        preferred_model = test_case.get("preferred_model", "gpt-4o-mini")
        
        # Run conversation
        result = await self.orchestrator.orchestrate_conversation(
            message=message,
            user_id="bench_user",
            conversation_id=f"bench_cost_{datetime.utcnow().timestamp()}",
            context={"optimize_cost": True}
        )
        
        actual_cost = result.cost_breakdown.get("total_cost", 0)
        model_used = result.cost_breakdown.get("model", "unknown")
        
        efficiency_score = 1.0 if actual_cost <= max_cost else (max_cost / actual_cost)
        
        return {
            "passed": actual_cost <= max_cost,
            "turns": len(result.chat_history),
            "agents_used": result.agents_used,
            "cost": actual_cost,
            "tokens": result.cost_breakdown.get("total_tokens", 0),
            "quality_score": efficiency_score,
            "routing_score": 1.0,
            "coherence_score": 1.0,
            "model_used": model_used,
            "efficiency_score": efficiency_score
        }
    
    async def _run_memory_coherence_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test memory and context coherence"""
        
        conversation_turns = test_case.get("turns", [
            {"message": "My name is John and I work in finance", "expected": ["john", "finance"]},
            {"message": "What did I tell you about my job?", "expected": ["finance"]},
            {"message": "What's my name?", "expected": ["john"]}
        ])
        
        conversation_id = f"bench_memory_{datetime.utcnow().timestamp()}"
        coherence_scores = []
        total_cost = 0
        total_tokens = 0
        
        for turn in conversation_turns:
            result = await self.orchestrator.orchestrate_conversation(
                message=turn["message"],
                user_id="bench_user",
                conversation_id=conversation_id
            )
            
            # Check if expected keywords are in response
            response_lower = result.final_response.lower()
            matches = sum(1 for keyword in turn["expected"] if keyword.lower() in response_lower)
            coherence = matches / len(turn["expected"]) if turn["expected"] else 1.0
            coherence_scores.append(coherence)
            
            total_cost += result.cost_breakdown.get("total_cost", 0)
            total_tokens += result.cost_breakdown.get("total_tokens", 0)
        
        avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0
        
        return {
            "passed": avg_coherence > 0.7,
            "turns": len(conversation_turns),
            "agents_used": [],
            "cost": total_cost,
            "tokens": total_tokens,
            "quality_score": avg_coherence,
            "routing_score": 1.0,
            "coherence_score": avg_coherence,
            "coherence_details": coherence_scores
        }
    
    async def _run_workflow_execution_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test workflow execution capabilities"""
        
        workflow_id = test_case.get("workflow_id", "strategic_analysis")
        workflow_input = test_case.get("input", {"business_context": "Test context", "strategic_question": "Test question"})
        expected_steps = test_case.get("expected_steps", ["initial_context", "market_analysis"])
        
        # Mock workflow execution through conversation
        result = await self.orchestrator.orchestrate_conversation(
            message=f"Execute workflow: {workflow_id} with input: {json.dumps(workflow_input)}",
            user_id="bench_user",
            conversation_id=f"bench_workflow_{datetime.utcnow().timestamp()}",
            context={"workflow_id": workflow_id, "workflow_input": workflow_input}
        )
        
        # Check if expected workflow steps were mentioned
        response_lower = result.final_response.lower()
        steps_found = sum(1 for step in expected_steps if step in response_lower or step.replace("_", " ") in response_lower)
        completion_rate = steps_found / len(expected_steps) if expected_steps else 1.0
        
        return {
            "passed": completion_rate > 0.7,
            "turns": len(result.chat_history),
            "agents_used": result.agents_used,
            "cost": result.cost_breakdown.get("total_cost", 0),
            "tokens": result.cost_breakdown.get("total_tokens", 0),
            "quality_score": completion_rate,
            "routing_score": 1.0,
            "coherence_score": 1.0,
            "workflow_completion": completion_rate
        }
    
    async def _run_multi_agent_collaboration_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test multi-agent collaboration scenarios"""
        
        message = test_case.get("message", "I need a comprehensive analysis including strategy, finance, and security perspectives")
        min_agents = test_case.get("min_agents", 3)
        expected_collaboration = test_case.get("expected_agents", ["ali_chief_of_staff", "amy_cfo", "luca_security_expert"])
        
        # Run conversation requiring collaboration
        result = await self.orchestrator.orchestrate_conversation(
            message=message,
            user_id="bench_user",
            conversation_id=f"bench_collab_{datetime.utcnow().timestamp()}",
            context={"require_collaboration": True}
        )
        
        # Evaluate collaboration
        unique_agents = list(set(result.agents_used))
        collaboration_score = len(unique_agents) / max(min_agents, 1)
        expected_coverage = sum(1 for agent in expected_collaboration if agent in unique_agents) / len(expected_collaboration)
        
        return {
            "passed": len(unique_agents) >= min_agents and expected_coverage > 0.6,
            "turns": len(result.chat_history),
            "agents_used": result.agents_used,
            "cost": result.cost_breakdown.get("total_cost", 0),
            "tokens": result.cost_breakdown.get("total_tokens", 0),
            "quality_score": expected_coverage,
            "routing_score": collaboration_score,
            "coherence_score": self._evaluate_coherence(result.chat_history),
            "unique_agents": unique_agents,
            "collaboration_score": collaboration_score
        }
    
    def _evaluate_strategic_answer_quality(self, response: str, expected_keywords: List[str]) -> float:
        """Evaluate quality of strategic answers"""
        if not expected_keywords:
            expected_keywords = ["strategy", "analysis", "market", "competitive", "opportunity", "risk"]
        
        response_lower = response.lower()
        matches = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
        
        # Also check for structure and depth
        has_structure = any(marker in response for marker in ["1.", "2.", "•", "-"])
        has_depth = len(response) > 500
        
        base_score = matches / len(expected_keywords)
        structure_bonus = 0.1 if has_structure else 0
        depth_bonus = 0.1 if has_depth else 0
        
        return min(1.0, base_score + structure_bonus + depth_bonus)
    
    def _evaluate_coherence(self, chat_history: List[Dict[str, Any]]) -> float:
        """Evaluate conversation coherence"""
        if len(chat_history) < 2:
            return 1.0
        
        # Simple coherence check: responses should reference previous context
        coherence_scores = []
        for i in range(1, len(chat_history)):
            current = str(chat_history[i].get("content", "")).lower()
            previous = str(chat_history[i-1].get("content", "")).lower()
            
            # Check for contextual references
            has_reference = any(word in current for word in ["as mentioned", "regarding", "following", "based on"])
            
            # Check for topic continuity (shared keywords)
            prev_words = set(previous.split())
            curr_words = set(current.split())
            overlap = len(prev_words & curr_words) / max(len(prev_words), len(curr_words), 1)
            
            score = 0.5 if has_reference else 0
            score += overlap * 0.5
            coherence_scores.append(score)
        
        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 1.0
    
    def _get_scenario_description(self, scenario: BenchmarkScenario) -> str:
        """Get description for scenario"""
        descriptions = {
            BenchmarkScenario.STRATEGIC_QA: "Tests strategic Q&A with proper agent routing and quality responses",
            BenchmarkScenario.ANALYTICS_SYNTHESIS: "Tests analytics synthesis and data interpretation capabilities",
            BenchmarkScenario.ROUTING_COMPLEXITY: "Tests complex routing scenarios with multiple agents",
            BenchmarkScenario.PERFORMANCE_STRESS: "Tests system performance under stress conditions",
            BenchmarkScenario.COST_EFFICIENCY: "Tests cost optimization and efficient model selection",
            BenchmarkScenario.MEMORY_COHERENCE: "Tests memory and context coherence across turns",
            BenchmarkScenario.WORKFLOW_EXECUTION: "Tests GraphFlow workflow execution capabilities",
            BenchmarkScenario.MULTI_AGENT_COLLABORATION: "Tests multi-agent collaboration scenarios"
        }
        return descriptions.get(scenario, "Unknown scenario")
    
    def generate_report(self) -> str:
        """Generate comprehensive benchmark report"""
        
        report = ["=" * 80]
        report.append("AUTOGEN BENCHMARK REPORT")
        report.append("=" * 80]
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append("")
        
        # Summary
        total_scenarios = len(self.results)
        passed_scenarios = sum(1 for r in self.results if r.passed)
        total_cost = sum(r.total_cost_usd for r in self.results)
        total_duration = sum(r.duration_seconds for r in self.results)
        
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Scenarios: {total_scenarios}")
        report.append(f"Passed: {passed_scenarios}/{total_scenarios} ({passed_scenarios/total_scenarios*100:.1f}%)")
        report.append(f"Total Cost: ${total_cost:.4f}")
        report.append(f"Total Duration: {total_duration:.2f}s")
        report.append("")
        
        # Detailed results per scenario
        for result in self.results:
            report.append(f"SCENARIO: {result.scenario_name}")
            report.append("-" * 40)
            report.append(f"Description: {result.description}")
            report.append(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
            report.append(f"Duration: {result.duration_seconds:.2f}s")
            report.append(f"Total Turns: {result.total_turns}")
            report.append(f"Total Cost: ${result.total_cost_usd:.4f}")
            report.append(f"Cost per Turn: ${result.cost_per_turn:.4f}")
            report.append(f"Avg Response Time: {result.avg_response_time:.3f}s")
            report.append(f"P95 Response Time: {result.p95_response_time:.3f}s")
            report.append(f"P99 Response Time: {result.p99_response_time:.3f}s")
            report.append("")
            
            report.append("Quality Metrics:")
            report.append(f"  Answer Quality: {result.answer_quality_score:.2%}")
            report.append(f"  Routing Accuracy: {result.routing_accuracy:.2%}")
            report.append(f"  Coherence Score: {result.coherence_score:.2%}")
            report.append(f"  Task Completion: {result.task_completion_rate:.2%}")
            report.append("")
            
            if result.failures:
                report.append("Failures:")
                for failure in result.failures:
                    report.append(f"  - {failure}")
                report.append("")
            
            if result.warnings:
                report.append("Warnings:")
                for warning in result.warnings:
                    report.append(f"  - {warning}")
                report.append("")
        
        # Performance comparison
        report.append("PERFORMANCE COMPARISON")
        report.append("-" * 40)
        
        if self.results:
            best_cost = min(r.cost_per_turn for r in self.results if r.cost_per_turn > 0)
            worst_cost = max(r.cost_per_turn for r in self.results if r.cost_per_turn > 0)
            best_time = min(r.avg_response_time for r in self.results if r.avg_response_time > 0)
            worst_time = max(r.avg_response_time for r in self.results if r.avg_response_time > 0)
            
            report.append(f"Best Cost per Turn: ${best_cost:.4f}")
            report.append(f"Worst Cost per Turn: ${worst_cost:.4f}")
            report.append(f"Best Avg Response Time: {best_time:.3f}s")
            report.append(f"Worst Avg Response Time: {worst_time:.3f}s")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


# Benchmark test definitions
STRATEGIC_QA_TESTS = [
    {
        "name": "Market Positioning",
        "message": "What is our competitive positioning in the enterprise AI market?",
        "expected_agents": ["domik_mckinsey_strategic_decision_maker", "ali_chief_of_staff"],
        "expected_keywords": ["market", "competitive", "positioning", "strategy", "analysis"]
    },
    {
        "name": "Growth Strategy",
        "message": "How should we approach international expansion into Asian markets?",
        "expected_agents": ["ali_chief_of_staff", "domik_mckinsey_strategic_decision_maker"],
        "expected_keywords": ["expansion", "market entry", "strategy", "risk", "opportunity"]
    },
    {
        "name": "Strategic Priorities",
        "message": "What should be our top 3 strategic priorities for next quarter?",
        "expected_agents": ["ali_chief_of_staff"],
        "expected_keywords": ["priorities", "strategic", "focus", "objectives", "goals"]
    }
]

ANALYTICS_SYNTHESIS_TESTS = [
    {
        "name": "Performance Metrics",
        "message": "Synthesize our Q3 performance across all business units",
        "expected_agents": ["diana_performance_dashboard", "amy_cfo"],
        "expected_keywords": ["performance", "metrics", "kpi", "analysis", "trend"]
    },
    {
        "name": "Financial Analysis",
        "message": "Analyze revenue trends and provide cost optimization recommendations",
        "expected_agents": ["amy_cfo", "diana_performance_dashboard"],
        "expected_keywords": ["revenue", "cost", "optimization", "trend", "recommendation"]
    }
]

ROUTING_COMPLEXITY_TESTS = [
    {
        "name": "Multi-Domain Query",
        "messages": [
            "I need help with budget planning for Q4",
            "What are the security implications of our cloud migration?",
            "How does this align with our overall strategy?"
        ],
        "expected_sequence": ["amy_cfo", "luca_security_expert", "ali_chief_of_staff"]
    },
    {
        "name": "Cross-Functional Request",
        "messages": [
            "Design a workflow for customer onboarding",
            "Include financial tracking requirements",
            "Ensure compliance with security policies"
        ],
        "expected_sequence": ["wanda_workflow_orchestrator", "amy_cfo", "luca_security_expert"]
    }
]

PERFORMANCE_STRESS_TESTS = [
    {
        "name": "Parallel Load Test",
        "num_conversations": 10,
        "parallel": True,
        "max_response_time_seconds": 5.0
    },
    {
        "name": "Sequential Throughput",
        "num_conversations": 5,
        "parallel": False,
        "max_response_time_seconds": 3.0
    }
]

COST_EFFICIENCY_TESTS = [
    {
        "name": "Simple Query Optimization",
        "message": "What time is it?",
        "max_cost_usd": 0.001,
        "preferred_model": "gpt-4o-mini"
    },
    {
        "name": "Moderate Query Optimization",
        "message": "Summarize our company mission in one paragraph",
        "max_cost_usd": 0.01,
        "preferred_model": "gpt-4o-mini"
    }
]

MEMORY_COHERENCE_TESTS = [
    {
        "name": "Context Retention",
        "turns": [
            {"message": "My name is Alice and I manage the product team", "expected": ["alice", "product"]},
            {"message": "What team do I manage?", "expected": ["product"]},
            {"message": "What's my name again?", "expected": ["alice"]}
        ]
    },
    {
        "name": "Multi-Turn Context",
        "turns": [
            {"message": "We're planning to launch three new products: Alpha, Beta, and Gamma", "expected": ["alpha", "beta", "gamma"]},
            {"message": "Which product should we prioritize?", "expected": ["alpha", "beta", "gamma"]},
            {"message": "What were those products I mentioned?", "expected": ["alpha", "beta", "gamma"]}
        ]
    }
]

WORKFLOW_EXECUTION_TESTS = [
    {
        "name": "Strategic Analysis Workflow",
        "workflow_id": "strategic_analysis",
        "input": {
            "business_context": "Enterprise AI platform",
            "strategic_question": "Market expansion strategy"
        },
        "expected_steps": ["initial_context", "market_analysis", "financial_analysis", "strategic_synthesis"]
    },
    {
        "name": "Product Launch Workflow",
        "workflow_id": "product_launch",
        "input": {
            "product_concept": "AI assistant tool",
            "target_market": "Enterprise customers"
        },
        "expected_steps": ["product_validation", "gtm_strategy", "financial_planning"]
    }
]

MULTI_AGENT_COLLABORATION_TESTS = [
    {
        "name": "Strategic Planning Session",
        "message": "Develop a comprehensive strategic plan including market analysis, financial projections, and risk assessment",
        "min_agents": 3,
        "expected_agents": ["ali_chief_of_staff", "domik_mckinsey_strategic_decision_maker", "amy_cfo", "luca_security_expert"]
    },
    {
        "name": "Operational Excellence Review",
        "message": "Review our operational efficiency across workflows, performance metrics, and coordination patterns",
        "min_agents": 3,
        "expected_agents": ["wanda_workflow_orchestrator", "diana_performance_dashboard", "xavier_coordination_patterns"]
    }
]


async def run_full_benchmark_suite(orchestrator: ModernGroupChatOrchestrator) -> str:
    """Run complete benchmark suite and generate report"""
    
    suite = AutoGenBenchmarkSuite(orchestrator)
    
    # Run all benchmark scenarios
    scenarios = [
        (BenchmarkScenario.STRATEGIC_QA, STRATEGIC_QA_TESTS),
        (BenchmarkScenario.ANALYTICS_SYNTHESIS, ANALYTICS_SYNTHESIS_TESTS),
        (BenchmarkScenario.ROUTING_COMPLEXITY, ROUTING_COMPLEXITY_TESTS),
        (BenchmarkScenario.PERFORMANCE_STRESS, PERFORMANCE_STRESS_TESTS),
        (BenchmarkScenario.COST_EFFICIENCY, COST_EFFICIENCY_TESTS),
        (BenchmarkScenario.MEMORY_COHERENCE, MEMORY_COHERENCE_TESTS),
        (BenchmarkScenario.WORKFLOW_EXECUTION, WORKFLOW_EXECUTION_TESTS),
        (BenchmarkScenario.MULTI_AGENT_COLLABORATION, MULTI_AGENT_COLLABORATION_TESTS)
    ]
    
    for scenario, test_cases in scenarios:
        await suite.run_scenario(scenario, test_cases)
    
    # Generate and return report
    return suite.generate_report()


# Export for pytest integration
__all__ = [
    "AutoGenBenchmarkSuite",
    "BenchmarkScenario",
    "BenchmarkResult",
    "run_full_benchmark_suite",
    "STRATEGIC_QA_TESTS",
    "ANALYTICS_SYNTHESIS_TESTS",
    "ROUTING_COMPLEXITY_TESTS",
    "PERFORMANCE_STRESS_TESTS",
    "COST_EFFICIENCY_TESTS",
    "MEMORY_COHERENCE_TESTS",
    "WORKFLOW_EXECUTION_TESTS",
    "MULTI_AGENT_COLLABORATION_TESTS"
]