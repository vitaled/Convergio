#!/usr/bin/env python3
"""
🤝 CONVERGIO MULTI-AGENT CONVERSATION WORKFLOW TESTS
===================================================

Purpose: Test complex multi-agent conversation scenarios including:
- Sequential agent handoffs
- Parallel agent coordination
- Context preservation across agents
- Decision-making workflows
- Collaborative problem solving
- Error handling in multi-agent scenarios

Author: Convergio Test Suite
Last Updated: August 2025
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pytest
import httpx
from dataclasses import dataclass

# Setup paths
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from src.core.config import get_settings

# Configure logging
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)
TEST_NAME = Path(__file__).stem
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"{TEST_NAME}_{TIMESTAMP}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ConversationStep:
    """Single step in a multi-agent conversation."""
    agent_id: str
    message: str
    expected_capabilities: List[str]
    context_requirements: List[str]
    timeout_seconds: float = 30.0


@dataclass
class WorkflowResult:
    """Result of a multi-agent workflow test."""
    workflow_name: str
    total_steps: int
    completed_steps: int
    total_time_seconds: float
    agents_involved: List[str]
    context_preserved: bool
    success: bool
    errors: List[str]
    step_results: List[Dict[str, Any]]


class MultiAgentWorkflowTester:
    """
    Test suite for multi-agent conversation workflows.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "http://localhost:9000"
        self.session_id = f"workflow_test_{TIMESTAMP}"
        self.conversation_history: List[Dict[str, Any]] = []
    
    async def execute_conversation_step(
        self, 
        step: ConversationStep, 
        session_context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Execute a single conversation step."""
        try:
            logger.info(f"  💬 {step.agent_id}: {step.message[:50]}...")
            
            start_time = time.time()
            
            async with httpx.AsyncClient(base_url=self.base_url, timeout=step.timeout_seconds) as client:
                response = await client.post(
                    "/api/v1/agents/conversation",
                    json={
                        "message": step.message,
                        "agent": step.agent_id,
                        "session_id": self.session_id,
                        "context": {
                            **session_context,
                            "history": self.conversation_history[-5:],  # Last 5 messages
                            "workflow_test": True,
                            "step_requirements": {
                                "capabilities": step.expected_capabilities,
                                "context_needs": step.context_requirements
                            }
                        }
                    }
                )
                
                elapsed_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", data.get("content", ""))
                    
                    # Store in conversation history
                    history_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "agent": step.agent_id,
                        "user_message": step.message,
                        "agent_response": response_text,
                        "response_time": elapsed_time,
                        "metadata": data
                    }
                    self.conversation_history.append(history_entry)
                    
                    # Validate response
                    if len(response_text) < 10:
                        return False, {"error": "Response too short", "response": response_text}
                    
                    # Check if expected capabilities were demonstrated
                    capabilities_found = []
                    for capability in step.expected_capabilities:
                        if capability.lower() in response_text.lower():
                            capabilities_found.append(capability)
                    
                    result = {
                        "success": True,
                        "agent": step.agent_id,
                        "response": response_text,
                        "response_time": elapsed_time,
                        "capabilities_found": capabilities_found,
                        "response_length": len(response_text),
                        "metadata": data
                    }
                    
                    logger.info(f"    ✅ Response received ({elapsed_time:.1f}s, {len(response_text)} chars)")
                    return True, result
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"    ❌ {error_msg}")
                    return False, {"error": error_msg, "status_code": response.status_code}
                    
        except Exception as e:
            logger.error(f"    ❌ Exception: {e}")
            return False, {"error": str(e), "exception": type(e).__name__}
    
    async def test_sequential_workflow(self) -> WorkflowResult:
        """Test sequential agent handoff workflow."""
        logger.info("🔄 Testing Sequential Agent Workflow")
        
        # Define workflow: Strategic planning -> Financial analysis -> Technical implementation
        steps = [
            ConversationStep(
                agent_id="ali",
                message="We need to plan a new AI-powered feature for our platform. What strategic approach should we take?",
                expected_capabilities=["strategic planning", "vision"],
                context_requirements=["company_strategy"]
            ),
            ConversationStep(
                agent_id="amy",
                message="Based on the strategic direction Ali outlined, what would be the financial implications and budget requirements?",
                expected_capabilities=["financial analysis", "budgeting"],
                context_requirements=["previous_conversation", "strategic_context"]
            ),
            ConversationStep(
                agent_id="baccio",
                message="Given the strategic and financial constraints discussed, what technical architecture would you recommend?",
                expected_capabilities=["technical architecture", "implementation"],
                context_requirements=["strategic_context", "financial_constraints"]
            ),
            ConversationStep(
                agent_id="davide",
                message="Now that we have strategy, budget, and architecture, can you create a project plan with timelines?",
                expected_capabilities=["project management", "planning"],
                context_requirements=["all_previous_context"]
            )
        ]
        
        return await self.execute_workflow("Sequential Strategy-to-Implementation", steps)
    
    async def test_parallel_consultation_workflow(self) -> WorkflowResult:
        """Test parallel agent consultation workflow."""
        logger.info("🌍 Testing Parallel Consultation Workflow")
        
        # Define workflow: Multiple agents consulted in parallel about the same issue
        base_context = {
            "scenario": "We're considering implementing a new customer onboarding system",
            "requirements": "Must improve user experience while reducing support costs"
        }
        
        # Parallel consultation steps
        steps = [
            ConversationStep(
                agent_id="sara",
                message="From a UX perspective, what should we consider for a new customer onboarding system?",
                expected_capabilities=["user experience", "design"],
                context_requirements=["ux_principles"]
            ),
            ConversationStep(
                agent_id="luca",
                message="What security considerations should we have for the customer onboarding system?",
                expected_capabilities=["security", "compliance"],
                context_requirements=["security_framework"]
            ),
            ConversationStep(
                agent_id="andrea",
                message="How can we ensure the onboarding system improves customer success metrics?",
                expected_capabilities=["customer success", "metrics"],
                context_requirements=["customer_journey"]
            ),
            ConversationStep(
                agent_id="orchestrator",
                message="Based on the UX, security, and customer success perspectives, synthesize a comprehensive recommendation.",
                expected_capabilities=["synthesis", "coordination"],
                context_requirements=["all_expert_input"]
            )
        ]
        
        return await self.execute_workflow("Parallel Expert Consultation", steps, base_context)
    
    async def test_problem_solving_workflow(self) -> WorkflowResult:
        """Test collaborative problem-solving workflow."""
        logger.info("🧪 Testing Collaborative Problem-Solving Workflow")
        
        # Define workflow: Problem identification -> Analysis -> Solution -> Validation
        steps = [
            ConversationStep(
                agent_id="ava",
                message="Our customer churn rate has increased by 15% this quarter. What does the data tell us?",
                expected_capabilities=["data analysis", "insights"],
                context_requirements=["analytics_context"]
            ),
            ConversationStep(
                agent_id="behice",
                message="Based on the data analysis, what cultural or organizational factors might be contributing to churn?",
                expected_capabilities=["cultural analysis", "organizational insights"],
                context_requirements=["data_insights"]
            ),
            ConversationStep(
                agent_id="dave",
                message="Given the data and cultural insights, what change management strategy should we implement?",
                expected_capabilities=["change management", "strategy"],
                context_requirements=["problem_analysis"]
            ),
            ConversationStep(
                agent_id="diana",
                message="How can we set up dashboards to monitor the effectiveness of our churn reduction initiatives?",
                expected_capabilities=["performance monitoring", "dashboards"],
                context_requirements=["solution_context"]
            )
        ]
        
        return await self.execute_workflow("Collaborative Problem Solving", steps)
    
    async def test_escalation_workflow(self) -> WorkflowResult:
        """Test escalation and decision-making workflow."""
        logger.info("📨 Testing Escalation Workflow")
        
        # Define workflow: Specialist -> Manager -> Executive decision
        steps = [
            ConversationStep(
                agent_id="thor",
                message="We found a critical security vulnerability in our production system. What's the immediate assessment?",
                expected_capabilities=["security assessment", "risk analysis"],
                context_requirements=["security_context"]
            ),
            ConversationStep(
                agent_id="dan",
                message="Based on Thor's security assessment, what's the engineering management decision on handling this?",
                expected_capabilities=["engineering management", "decision making"],
                context_requirements=["technical_assessment"]
            ),
            ConversationStep(
                agent_id="ali",
                message="Given the security issue and engineering response plan, what's the executive decision and communication strategy?",
                expected_capabilities=["executive decision", "crisis management"],
                context_requirements=["full_situation_context"]
            )
        ]
        
        return await self.execute_workflow("Security Escalation", steps)
    
    async def test_creative_collaboration_workflow(self) -> WorkflowResult:
        """Test creative collaboration workflow."""
        logger.info("🎨 Testing Creative Collaboration Workflow")
        
        # Define workflow: Creative ideation -> Strategic validation -> Technical feasibility
        steps = [
            ConversationStep(
                agent_id="jony",
                message="We need a creative campaign for our new AI features. What innovative approaches should we consider?",
                expected_capabilities=["creative direction", "innovation"],
                context_requirements=["brand_context"]
            ),
            ConversationStep(
                agent_id="sofia",
                message="Evaluate Jony's creative concepts from a marketing strategy perspective. Which ones align with our goals?",
                expected_capabilities=["marketing strategy", "evaluation"],
                context_requirements=["creative_concepts"]
            ),
            ConversationStep(
                agent_id="riccardo",
                message="Transform the approved creative strategy into compelling storytelling for our audience.",
                expected_capabilities=["storytelling", "narrative"],
                context_requirements=["approved_strategy"]
            )
        ]
        
        return await self.execute_workflow("Creative Collaboration", steps)
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        steps: List[ConversationStep], 
        base_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """Execute a complete workflow and return results."""
        if base_context is None:
            base_context = {}
        
        start_time = time.time()
        errors = []
        step_results = []
        completed_steps = 0
        agents_involved = []
        
        logger.info(f"Starting workflow: {workflow_name} ({len(steps)} steps)")
        
        for i, step in enumerate(steps, 1):
            logger.info(f"Step {i}/{len(steps)}: {step.agent_id}")
            
            # Add step-specific context
            step_context = {
                **base_context,
                "workflow_name": workflow_name,
                "step_number": i,
                "total_steps": len(steps)
            }
            
            success, result = await self.execute_conversation_step(step, step_context)
            
            step_results.append({
                "step_number": i,
                "agent": step.agent_id,
                "success": success,
                "result": result
            })
            
            if success:
                completed_steps += 1
                if step.agent_id not in agents_involved:
                    agents_involved.append(step.agent_id)
            else:
                error_msg = f"Step {i} ({step.agent_id}) failed: {result.get('error', 'Unknown error')}"
                errors.append(error_msg)
                logger.error(f"  ❌ {error_msg}")
                # Continue with remaining steps even if one fails
        
        total_time = time.time() - start_time
        
        # Check context preservation (simple heuristic)
        context_preserved = self.check_context_preservation()
        
        workflow_result = WorkflowResult(
            workflow_name=workflow_name,
            total_steps=len(steps),
            completed_steps=completed_steps,
            total_time_seconds=total_time,
            agents_involved=agents_involved,
            context_preserved=context_preserved,
            success=completed_steps >= len(steps) * 0.7,  # 70% success rate
            errors=errors,
            step_results=step_results
        )
        
        # Log workflow summary
        status = "✅" if workflow_result.success else "❌"
        logger.info(f"{status} {workflow_name}: {completed_steps}/{len(steps)} steps completed ({total_time:.1f}s)")
        
        return workflow_result
    
    def check_context_preservation(self) -> bool:
        """Check if context is preserved across conversation steps."""
        if len(self.conversation_history) < 2:
            return True  # Not enough data to check
        
        # Simple heuristic: check if later responses reference earlier topics
        first_response = self.conversation_history[0]["agent_response"].lower()
        last_response = self.conversation_history[-1]["agent_response"].lower()
        
        # Extract key terms from first response
        first_words = set(word for word in first_response.split() if len(word) > 4)
        last_words = set(word for word in last_response.split() if len(word) > 4)
        
        # Check for overlap (indicating context preservation)
        overlap = len(first_words.intersection(last_words))
        
        # If there's reasonable overlap, context is likely preserved
        return overlap >= min(3, len(first_words) * 0.1)
    
    async def run_all_workflow_tests(self) -> Dict[str, Any]:
        """Run all multi-agent workflow tests."""
        logger.info("🚀 Starting Multi-Agent Workflow Test Suite")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Log file: {LOG_FILE}")
        logger.info("="*80)
        
        workflows = [
            self.test_sequential_workflow(),
            self.test_parallel_consultation_workflow(),
            self.test_problem_solving_workflow(),
            self.test_escalation_workflow(),
            self.test_creative_collaboration_workflow()
        ]
        
        start_time = time.time()
        
        # Execute workflows sequentially to avoid interference
        results = []
        for workflow_coro in workflows:
            try:
                result = await workflow_coro
                results.append(result)
                # Clear conversation history between workflows
                self.conversation_history.clear()
                # Use new session ID for each workflow
                self.session_id = f"workflow_test_{TIMESTAMP}_{len(results)}"
            except Exception as e:
                logger.error(f"Workflow failed with exception: {e}")
                results.append(WorkflowResult(
                    workflow_name=f"Failed Workflow {len(results) + 1}",
                    total_steps=0,
                    completed_steps=0,
                    total_time_seconds=0,
                    agents_involved=[],
                    context_preserved=False,
                    success=False,
                    errors=[str(e)],
                    step_results=[]
                ))
        
        total_time = time.time() - start_time
        
        # Generate summary
        summary = self.generate_workflow_summary(results, total_time)
        
        logger.info("="*80)
        logger.info("📊 MULTI-AGENT WORKFLOW TESTS COMPLETED")
        logger.info(f"Total time: {total_time:.1f}s")
        logger.info(f"Results saved to: {LOG_FILE}")
        logger.info("="*80)
        
        return summary
    
    def generate_workflow_summary(self, results: List[WorkflowResult], total_time: float) -> Dict[str, Any]:
        """Generate comprehensive workflow test summary."""
        total_workflows = len(results)
        successful_workflows = len([r for r in results if r.success])
        total_steps = sum(r.total_steps for r in results)
        completed_steps = sum(r.completed_steps for r in results)
        
        all_agents = set()
        for result in results:
            all_agents.update(result.agents_involved)
        
        context_preserved_count = len([r for r in results if r.context_preserved])
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_time_seconds": round(total_time, 2),
            "overview": {
                "total_workflows": total_workflows,
                "successful_workflows": successful_workflows,
                "success_rate": round((successful_workflows / total_workflows) * 100, 1) if total_workflows > 0 else 0,
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "step_completion_rate": round((completed_steps / total_steps) * 100, 1) if total_steps > 0 else 0,
                "unique_agents_involved": len(all_agents),
                "context_preservation_rate": round((context_preserved_count / total_workflows) * 100, 1) if total_workflows > 0 else 0
            },
            "workflow_results": [
                {
                    "name": r.workflow_name,
                    "success": r.success,
                    "completed_steps": f"{r.completed_steps}/{r.total_steps}",
                    "completion_rate": round((r.completed_steps / r.total_steps) * 100, 1) if r.total_steps > 0 else 0,
                    "time_seconds": round(r.total_time_seconds, 2),
                    "agents_involved": r.agents_involved,
                    "context_preserved": r.context_preserved,
                    "error_count": len(r.errors)
                }
                for r in results
            ],
            "agent_participation": {
                agent: len([r for r in results if agent in r.agents_involved])
                for agent in sorted(all_agents)
            },
            "detailed_results": [
                {
                    "workflow_name": r.workflow_name,
                    "total_steps": r.total_steps,
                    "completed_steps": r.completed_steps,
                    "total_time_seconds": r.total_time_seconds,
                    "agents_involved": r.agents_involved,
                    "context_preserved": r.context_preserved,
                    "success": r.success,
                    "errors": r.errors,
                    "step_results": r.step_results
                }
                for r in results
            ]
        }
        
        # Save detailed results
        results_file = LOG_DIR / f"workflow_test_results_{TIMESTAMP}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📋 Detailed results saved to: {results_file}")
        
        # Log summary
        logger.info(f"""\n📊 WORKFLOW TEST SUMMARY
=======================
Total Workflows: {total_workflows}
Successful: {successful_workflows} ({(successful_workflows/total_workflows)*100:.1f}%)
Total Steps: {total_steps}
Completed Steps: {completed_steps} ({(completed_steps/total_steps)*100:.1f}%)
Unique Agents: {len(all_agents)}
Context Preservation: {context_preserved_count}/{total_workflows} ({(context_preserved_count/total_workflows)*100:.1f}%)

Workflow Results:
{chr(10).join(f'  • {r.workflow_name}: {r.completed_steps}/{r.total_steps} steps (✅ {r.success})' for r in results)}
""")
        
        return summary


# Pytest integration
class TestMultiAgentWorkflows:
    """Pytest wrapper for multi-agent workflow tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sequential_workflow(self):
        """Test sequential agent workflow."""
        tester = MultiAgentWorkflowTester()
        result = await tester.test_sequential_workflow()
        
        assert result.success, f"Sequential workflow failed: {result.errors}"
        assert result.completed_steps >= result.total_steps * 0.7, "Too many steps failed"
        assert len(result.agents_involved) >= 3, "Not enough agents participated"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_parallel_consultation(self):
        """Test parallel consultation workflow."""
        tester = MultiAgentWorkflowTester()
        result = await tester.test_parallel_consultation_workflow()
        
        assert result.success, f"Parallel consultation failed: {result.errors}"
        assert result.completed_steps >= result.total_steps * 0.7, "Too many steps failed"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_problem_solving(self):
        """Test collaborative problem-solving workflow."""
        tester = MultiAgentWorkflowTester()
        result = await tester.test_problem_solving_workflow()
        
        assert result.success, f"Problem-solving workflow failed: {result.errors}"
        assert result.context_preserved, "Context was not preserved across agents"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_escalation_workflow(self):
        """Test escalation workflow."""
        tester = MultiAgentWorkflowTester()
        result = await tester.test_escalation_workflow()
        
        assert result.success, f"Escalation workflow failed: {result.errors}"
        assert "ali" in result.agents_involved, "Executive agent not involved in escalation"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_all_workflows_comprehensive(self):
        """Test all multi-agent workflows comprehensively."""
        tester = MultiAgentWorkflowTester()
        results = await tester.run_all_workflow_tests()
        
        # Assert overall success
        assert "error" not in results, f"Workflow tests failed: {results.get('error')}"
        assert results["overview"]["total_workflows"] > 0, "No workflows tested"
        
        # Assert reasonable success rate
        success_rate = results["overview"]["success_rate"]
        assert success_rate >= 60, f"Workflow success rate too low: {success_rate}% (expected ≥60%)"
        
        # Assert step completion rate
        step_completion_rate = results["overview"]["step_completion_rate"]
        assert step_completion_rate >= 70, f"Step completion rate too low: {step_completion_rate}% (expected ≥70%)"
        
        # Assert agent participation
        unique_agents = results["overview"]["unique_agents_involved"]
        assert unique_agents >= 8, f"Not enough agents participated: {unique_agents} (expected ≥8)"


def run_workflow_tests():
    """Execute the multi-agent workflow test suite."""
    logger.info("Starting Convergio Multi-Agent Workflow Test Suite")
    
    # Configure pytest
    pytest_args = [
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "--color=yes",
        "-m", "slow",  # Only run slow/comprehensive tests
        f"--junit-xml={LOG_DIR}/workflow_{TIMESTAMP}_junit.xml"
    ]
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    # Report results
    logger.info("="*80)
    if exit_code == 0:
        logger.info("✅ ALL WORKFLOW TESTS PASSED!")
    else:
        logger.error(f"❌ WORKFLOW TESTS FAILED (exit code: {exit_code})")
    logger.info(f"Test results saved to: {LOG_FILE}")
    logger.info("="*80)
    
    return exit_code


if __name__ == "__main__":
    import sys
    # Run the test suite directly
    tester = MultiAgentWorkflowTester()
    
    async def main():
        return await tester.run_all_workflow_tests()
    
    results = asyncio.run(main())
    
    # Exit with appropriate code
    if "error" in results:
        sys.exit(1)
    elif results["overview"]["success_rate"] < 60:
        sys.exit(1)
    else:
        sys.exit(0)
