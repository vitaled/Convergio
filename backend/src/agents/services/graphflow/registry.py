"""
Workflow registry loading predefined workflows.
"""

import json
from typing import Dict
import structlog

from .definitions import BusinessWorkflow, WorkflowStep

logger = structlog.get_logger()


async def load_predefined_workflows() -> Dict[str, BusinessWorkflow]:
    """Return a dictionary of predefined workflows."""
    workflows: Dict[str, BusinessWorkflow] = {}

    strategic_workflow = BusinessWorkflow(
        workflow_id="strategic-analysis-001",
        name="Strategic Business Analysis",
        description="Comprehensive strategic analysis workflow for business decisions",
        steps=[
            WorkflowStep(
                step_id="initial-analysis",
                agent_name="ali_chief_of_staff",
                step_type="analysis",
                description="Initial strategic assessment and problem definition",
                inputs=["user_request", "context"],
                outputs=["strategic_assessment", "key_stakeholders"],
            ),
            WorkflowStep(
                step_id="financial-analysis",
                agent_name="amy_cfo",
                step_type="analysis",
                description="Financial impact analysis and budget considerations",
                inputs=["strategic_assessment"],
                outputs=["financial_impact", "budget_requirements"],
            ),
            WorkflowStep(
                step_id="technical-feasibility",
                agent_name="baccio_tech_architect",
                step_type="analysis",
                description="Technical feasibility and architecture assessment",
                inputs=["strategic_assessment"],
                outputs=["technical_feasibility", "architecture_recommendations"],
            ),
            WorkflowStep(
                step_id="risk-assessment",
                agent_name="luca_security_expert",
                step_type="validation",
                description="Risk analysis and mitigation strategies",
                inputs=["financial_impact", "technical_feasibility"],
                outputs=["risk_analysis", "mitigation_strategies"],
            ),
            WorkflowStep(
                step_id="final-recommendation",
                agent_name="ali_chief_of_staff",
                step_type="decision",
                description="Synthesize all analyses into actionable recommendations",
                inputs=["financial_impact", "technical_feasibility", "risk_analysis"],
                outputs=["final_recommendations", "implementation_plan"],
            ),
        ],
        entry_points=["initial-analysis"],
        exit_conditions={"final-recommendation": "recommendations_complete"},
        metadata={"category": "strategic", "complexity": "high", "estimated_duration": 1800},
    )

    onboarding_workflow = BusinessWorkflow(
        workflow_id="customer-onboarding-001",
        name="Customer Onboarding Process",
        description="Automated customer onboarding with multi-agent coordination",
        steps=[
            WorkflowStep(
                step_id="customer-intake",
                agent_name="andrea_customer_success_manager",
                step_type="analysis",
                description="Collect and analyze customer requirements",
                inputs=["customer_data", "requirements"],
                outputs=["customer_profile", "service_requirements"],
            ),
            WorkflowStep(
                step_id="technical-setup",
                agent_name="marco_devops_engineer",
                step_type="action",
                description="Configure technical infrastructure for customer",
                inputs=["customer_profile", "service_requirements"],
                outputs=["infrastructure_config", "access_credentials"],
            ),
            WorkflowStep(
                step_id="security-validation",
                agent_name="luca_security_expert",
                step_type="validation",
                description="Validate security setup and compliance",
                inputs=["infrastructure_config"],
                outputs=["security_clearance", "compliance_status"],
            ),
            WorkflowStep(
                step_id="onboarding-complete",
                agent_name="andrea_customer_success_manager",
                step_type="action",
                description="Finalize onboarding and customer handoff",
                inputs=["security_clearance", "access_credentials"],
                outputs=["onboarding_package", "next_steps"],
            ),
        ],
        entry_points=["customer-intake"],
        exit_conditions={"onboarding-complete": "customer_activated"},
        metadata={"category": "operations", "complexity": "medium", "estimated_duration": 900},
    )

    incident_workflow = BusinessWorkflow(
        workflow_id="incident-response-001",
        name="Security Incident Response",
        description="Automated incident response and resolution workflow",
        steps=[
            WorkflowStep(
                step_id="incident-triage",
                agent_name="luca_security_expert",
                step_type="analysis",
                description="Assess incident severity and impact",
                inputs=["incident_report", "system_status"],
                outputs=["severity_level", "impact_assessment"],
            ),
            WorkflowStep(
                step_id="technical-investigation",
                agent_name="baccio_tech_architect",
                step_type="analysis",
                description="Technical root cause analysis",
                inputs=["severity_level", "impact_assessment"],
                outputs=["root_cause", "technical_details"],
            ),
            WorkflowStep(
                step_id="communication-plan",
                agent_name="ali_chief_of_staff",
                step_type="action",
                description="Coordinate stakeholder communication",
                inputs=["severity_level", "impact_assessment"],
                outputs=["communication_plan", "stakeholder_updates"],
            ),
            WorkflowStep(
                step_id="resolution-implementation",
                agent_name="marco_devops_engineer",
                step_type="action",
                description="Implement technical resolution",
                inputs=["root_cause", "technical_details"],
                outputs=["resolution_steps", "system_recovery"],
            ),
            WorkflowStep(
                step_id="post-incident-review",
                agent_name="ali_chief_of_staff",
                step_type="validation",
                description="Post-incident analysis and process improvement",
                inputs=["resolution_steps", "communication_plan"],
                outputs=["incident_report", "process_improvements"],
            ),
        ],
        entry_points=["incident-triage"],
        exit_conditions={"post-incident-review": "incident_closed"},
        metadata={"category": "security", "complexity": "high", "estimated_duration": 3600},
    )

    workflows[strategic_workflow.workflow_id] = strategic_workflow
    workflows[onboarding_workflow.workflow_id] = onboarding_workflow
    workflows[incident_workflow.workflow_id] = incident_workflow

    logger.info("📋 Loaded %s predefined workflows", len(workflows))
    return workflows


