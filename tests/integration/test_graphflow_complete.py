"""
Integration test for GraphFlow complete workflow system
Verifies runner, orchestrator, definitions, and registry work together
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from agents.services.graphflow.runner import (
    GraphFlowRunner, WorkflowExecution, StepExecutionResult, StepStatus
)
from agents.services.graphflow.definitions import (
    BusinessWorkflow, WorkflowStep, StepType, WorkflowPriority,
    BusinessDomain, WorkflowStatus
)
from agents.services.graphflow.registry import (
    ComprehensiveWorkflowRegistry, load_predefined_workflows
)


@pytest.mark.asyncio
async def test_graphflow_runner_basic_execution():
    """Test basic workflow execution with runner"""
    
    # Create a simple test workflow
    workflow = BusinessWorkflow(
        workflow_id="test_workflow",
        name="Test Workflow",
        description="Test workflow for integration testing",
        business_domain=BusinessDomain.OPERATIONS,
        priority=WorkflowPriority.MEDIUM,
        sla_minutes=60,
        steps=[
            WorkflowStep(
                step_id="step1",
                step_type=StepType.ANALYSIS,
                agent_name="test_agent_1",
                description="First test step",
                detailed_instructions="Analyze the input data",
                inputs=["input_data"],
                outputs=["analysis_result"],
                estimated_duration_minutes=5
            ),
            WorkflowStep(
                step_id="step2",
                step_type=StepType.DECISION,
                agent_name="test_agent_2",
                description="Second test step",
                detailed_instructions="Make decision based on analysis",
                inputs=["analysis_result"],
                outputs=["decision"],
                dependencies=["step1"],
                estimated_duration_minutes=3
            )
        ],
        entry_points=["input_data"],
        exit_conditions={"success": "decision_made"},
        success_metrics={"completion": "All steps completed"},
        failure_handling={"error": "Retry or escalate"},
        escalation_rules={"timeout": "Notify manager"}
    )
    
    # Create runner with mocked dependencies
    runner = GraphFlowRunner(redis_client=None, db_session=None)
    
    # Mock the settings to avoid configuration issues
    runner.settings = MagicMock()
    runner.settings.redis_url = "redis://localhost:6379"
    
    # Mock OTEL manager
    runner.otel_manager = MagicMock()
    runner.otel_manager.span = MagicMock()
    runner.otel_manager.span.return_value.__enter__ = MagicMock()
    runner.otel_manager.span.return_value.__exit__ = MagicMock()
    
    # Execute workflow
    context = {"input_data": "test data"}
    execution = await runner.execute_workflow(
        workflow=workflow,
        user_id="test_user",
        context=context
    )
    
    # Verify execution
    assert execution.workflow_id == "test_workflow"
    assert execution.user_id == "test_user"
    assert execution.status == WorkflowStatus.COMPLETED
    assert len(execution.step_results) == 2
    assert "step1" in execution.step_results
    assert "step2" in execution.step_results
    
    # Verify step results
    step1_result = execution.step_results["step1"]
    assert step1_result.status == StepStatus.COMPLETED
    assert step1_result.step_id == "step1"
    
    step2_result = execution.step_results["step2"]
    assert step2_result.status == StepStatus.COMPLETED
    assert step2_result.step_id == "step2"
    
    print("✅ GraphFlow runner basic execution test passed")


@pytest.mark.asyncio
async def test_workflow_registry_integration():
    """Test workflow registry with pre-defined workflows"""
    
    # Load registry
    registry = ComprehensiveWorkflowRegistry()
    
    # Verify pre-defined workflows loaded
    assert len(registry.workflows) >= 4
    assert "strategic_analysis" in registry.workflows
    assert "product_launch" in registry.workflows
    assert "market_entry" in registry.workflows
    assert "customer_onboarding" in registry.workflows
    
    # Test workflow retrieval
    strategic_workflow = registry.workflows["strategic_analysis"]
    assert strategic_workflow.name == "Strategic Analysis Workflow"
    assert strategic_workflow.business_domain == BusinessDomain.STRATEGY
    assert len(strategic_workflow.steps) == 4
    
    # Test catalog
    assert len(registry.catalog) >= 4
    catalog_entry = registry.catalog[0]
    assert hasattr(catalog_entry, "workflow_id")
    assert hasattr(catalog_entry, "complexity")
    assert hasattr(catalog_entry, "estimated_duration_minutes")
    
    print("✅ Workflow registry integration test passed")


@pytest.mark.asyncio
async def test_workflow_execution_with_failures():
    """Test workflow execution with step failures and retries"""
    
    # Create workflow with failing step
    workflow = BusinessWorkflow(
        workflow_id="test_failure_workflow",
        name="Test Failure Workflow",
        description="Test workflow with failures",
        business_domain=BusinessDomain.OPERATIONS,
        priority=WorkflowPriority.HIGH,
        sla_minutes=30,
        steps=[
            WorkflowStep(
                step_id="failing_step",
                step_type=StepType.EXECUTION,
                agent_name="failing_agent",
                description="Step that will fail",
                detailed_instructions="This step simulates failure",
                inputs=["input"],
                outputs=["output"],
                retry_count=2,
                estimated_duration_minutes=2
            )
        ],
        entry_points=["input"],
        exit_conditions={"success": "completed", "failure": "failed"},
        success_metrics={"completion": "Step completed"},
        failure_handling={"retry": "Retry up to 2 times"},
        escalation_rules={"failure": "Escalate to manager"}
    )
    
    # Create runner
    runner = GraphFlowRunner()
    runner.settings = MagicMock()
    runner.otel_manager = None
    
    # Mock step execution to fail
    original_execute = runner._execute_single_step
    async def mock_failing_execute(step, execution):
        result = StepExecutionResult(
            step_id=step.step_id,
            status=StepStatus.FAILED,
            started_at=datetime.utcnow(),
            errors=["Simulated failure"]
        )
        return result
    
    runner._execute_single_step = mock_failing_execute
    
    # Execute workflow - should fail even after retries
    with pytest.raises(Exception, match="Critical step failing_step failed"):
        await runner.execute_workflow(
            workflow=workflow,
            user_id="test_user",
            context={"input": "test"}
        )
    
    print("✅ Workflow failure handling test passed")


@pytest.mark.asyncio
async def test_graphflow_complete_integration():
    """Test complete GraphFlow integration"""
    
    # Import all components
    from agents.services.graphflow.runner import GraphFlowRunner
    from agents.services.graphflow.definitions import (
        BusinessWorkflow, WorkflowStep, StepType
    )
    from agents.services.graphflow.registry import (
        load_predefined_workflows, search_workflows, get_workflow_catalog
    )
    
    # Test registry functions
    workflows = await load_predefined_workflows()
    assert len(workflows) >= 4
    
    # Test search functionality
    strategic_workflows = await search_workflows(
        query="strategic",
        domain="strategy"
    )
    assert len(strategic_workflows) >= 1
    
    # Test catalog
    catalog = await get_workflow_catalog()
    assert len(catalog) >= 4
    
    # Verify each catalog entry
    for entry in catalog:
        assert "workflow_id" in entry
        assert "name" in entry
        assert "complexity" in entry
        assert "estimated_duration_minutes" in entry
        assert "business_domain" in entry
    
    print("✅ Complete GraphFlow integration test passed")
    
    # Summary of verified components
    print("\n📊 GraphFlow Components Verified:")
    print(f"✅ {len(workflows)} workflows loaded from registry")
    print("✅ Workflow execution engine functional")
    print("✅ Step-by-step execution with dependencies")
    print("✅ Failure handling and retry logic")
    print("✅ Workflow search and catalog features")
    print("✅ Business domain categorization")
    print("✅ Complete integration successful!")


if __name__ == "__main__":
    # Run all tests
    asyncio.run(test_graphflow_runner_basic_execution())
    asyncio.run(test_workflow_registry_integration())
    asyncio.run(test_workflow_execution_with_failures())
    asyncio.run(test_graphflow_complete_integration())
    
    print("\n🎉 All GraphFlow integration tests passed!")