"""
GraphFlow Workflow Generator - NL to Workflow conversion
Generates AutoGen workflows from natural language descriptions
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import json
import uuid
import structlog

from src.agents.security.ai_security_guardian import AISecurityGuardian
from src.core.ai_clients import get_autogen_client

logger = structlog.get_logger()


class WorkflowStep(BaseModel):
    """Single step in a workflow"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    agent: str  # Agent responsible for this step
    tools: List[str] = []  # Tools needed for this step
    inputs: List[str] = []  # IDs of steps that provide input
    outputs: Dict[str, str] = {}  # Output schema
    conditions: Optional[Dict[str, Any]] = None  # Conditional execution
    approval_required: bool = False
    timeout_seconds: int = 300
    retry_count: int = 3


class BusinessWorkflow(BaseModel):
    """Complete workflow definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "system"
    version: str = "1.0.0"
    
    steps: List[WorkflowStep] = []
    entry_point: str  # ID of first step
    exit_points: List[str] = []  # IDs of final steps
    
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    is_template: bool = False
    is_active: bool = True
    
    estimated_duration_seconds: int = 0
    estimated_cost: float = 0.0
    
    # Safety and compliance
    safety_validated: bool = False
    compliance_tags: List[str] = []


class WorkflowGenerationRequest(BaseModel):
    """Request to generate a workflow from natural language"""
    prompt: str
    domain: Optional[str] = None  # IT, Marketing, Legal, Finance, HR
    complexity: str = "medium"  # simple, medium, complex
    max_steps: int = 10
    require_approval: bool = False
    safety_check: bool = True


class WorkflowGenerator:
    """Service for generating workflows from natural language"""
    
    def __init__(self):
        self.security_guardian = AISecurityGuardian()
        self.model_client = None
        self.workflow_templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, BusinessWorkflow]:
        """Load predefined workflow templates"""
        templates = {}
        
        # Strategic Analysis Template
        templates["strategic_analysis"] = BusinessWorkflow(
            id="strategic_analysis_template",
            name="Strategic Analysis Workflow",
            description="Multi-agent strategic analysis for business decisions",
            is_template=True,
            steps=[
                WorkflowStep(
                    id="market_research",
                    name="Market Research",
                    description="Gather market intelligence and competitor data",
                    agent="sofia_marketing",
                    tools=["web_search", "database_query"],
                    outputs={"market_data": "json"}
                ),
                WorkflowStep(
                    id="financial_analysis",
                    name="Financial Analysis",
                    description="Analyze financial implications and ROI",
                    agent="amy_cfo",
                    tools=["database_query", "calculator"],
                    inputs=["market_research"],
                    outputs={"financial_report": "json"}
                ),
                WorkflowStep(
                    id="strategic_planning",
                    name="Strategic Planning",
                    description="Develop strategic recommendations",
                    agent="ali_chief_of_staff",
                    tools=["ai_analysis"],
                    inputs=["market_research", "financial_analysis"],
                    outputs={"strategy_document": "markdown"},
                    approval_required=True
                )
            ],
            entry_point="market_research",
            exit_points=["strategic_planning"],
            estimated_duration_seconds=1800,
            estimated_cost=2.50
        )
        
        # Product Launch Template
        templates["product_launch"] = BusinessWorkflow(
            id="product_launch_template",
            name="Product Launch Workflow",
            description="Coordinate product launch across multiple teams",
            is_template=True,
            steps=[
                WorkflowStep(
                    id="product_review",
                    name="Product Review",
                    description="Final product quality and feature review",
                    agent="luke_program_manager",
                    tools=["database_query"],
                    outputs={"product_status": "json"}
                ),
                WorkflowStep(
                    id="marketing_prep",
                    name="Marketing Preparation",
                    description="Prepare marketing materials and campaigns",
                    agent="sofia_marketing",
                    tools=["content_generator", "web_search"],
                    inputs=["product_review"],
                    outputs={"marketing_assets": "json"}
                ),
                WorkflowStep(
                    id="legal_review",
                    name="Legal Review",
                    description="Legal compliance and terms review",
                    agent="bria_legal",
                    tools=["document_analyzer"],
                    inputs=["product_review", "marketing_prep"],
                    outputs={"legal_approval": "boolean"},
                    approval_required=True
                ),
                WorkflowStep(
                    id="launch_execution",
                    name="Launch Execution",
                    description="Execute the product launch",
                    agent="ali_chief_of_staff",
                    tools=["notification", "database_update"],
                    inputs=["legal_review"],
                    outputs={"launch_status": "json"}
                )
            ],
            entry_point="product_review",
            exit_points=["launch_execution"],
            estimated_duration_seconds=7200,
            estimated_cost=5.00
        )
        
        # Customer Onboarding Template
        templates["customer_onboarding"] = BusinessWorkflow(
            id="customer_onboarding_template",
            name="Customer Onboarding Workflow",
            description="Automated customer onboarding process",
            is_template=True,
            steps=[
                WorkflowStep(
                    id="account_setup",
                    name="Account Setup",
                    description="Create customer account and initial configuration",
                    agent="marco_devops",
                    tools=["database_update", "api_call"],
                    outputs={"account_id": "string"}
                ),
                WorkflowStep(
                    id="contract_generation",
                    name="Contract Generation",
                    description="Generate and send customer contract",
                    agent="bria_legal",
                    tools=["document_generator", "email"],
                    inputs=["account_setup"],
                    outputs={"contract_id": "string"}
                ),
                WorkflowStep(
                    id="training_schedule",
                    name="Training Schedule",
                    description="Schedule customer training sessions",
                    agent="harper_hr",
                    tools=["calendar", "email"],
                    inputs=["account_setup"],
                    outputs={"training_dates": "json"}
                ),
                WorkflowStep(
                    id="welcome_package",
                    name="Welcome Package",
                    description="Send welcome materials and documentation",
                    agent="lee_writer",
                    tools=["content_generator", "email"],
                    inputs=["account_setup", "training_schedule"],
                    outputs={"package_sent": "boolean"}
                )
            ],
            entry_point="account_setup",
            exit_points=["contract_generation", "welcome_package"],
            estimated_duration_seconds=3600,
            estimated_cost=1.50
        )
        
        return templates
    
    async def generate_workflow(
        self,
        request: WorkflowGenerationRequest
    ) -> Tuple[BusinessWorkflow, Dict[str, Any]]:
        """
        Generate a workflow from natural language description
        
        Returns:
            Tuple of (workflow, metadata) where metadata includes safety check results
        """
        metadata = {
            "generation_time": datetime.utcnow().isoformat(),
            "safety_checked": False,
            "safety_passed": False,
            "violations": []
        }
        
        # Safety check if enabled
        if request.safety_check:
            safety_result = await self.security_guardian.validate_prompt(
                request.prompt,
                user_id="workflow_generator"
            )
            
            metadata["safety_checked"] = True
            metadata["safety_passed"] = safety_result.execution_authorized
            metadata["violations"] = safety_result.violations
            
            if not safety_result.execution_authorized:
                raise ValueError(f"Safety check failed: {', '.join(safety_result.violations)}")
        
        # Check if we can use a template
        template = self._match_template(request.prompt)
        if template:
            workflow = template.model_copy()
            workflow.id = str(uuid.uuid4())
            workflow.is_template = False
            workflow.created_at = datetime.utcnow()
            workflow.description = f"Generated from: {request.prompt}"
            workflow.safety_validated = metadata["safety_passed"]
            
            logger.info(f"Used template for workflow generation: {template.name}")
            return workflow, metadata
        
        # Generate custom workflow using AI
        workflow = await self._generate_custom_workflow(request)
        workflow.safety_validated = metadata["safety_passed"]
        
        logger.info(f"Generated custom workflow: {workflow.name}")
        return workflow, metadata
    
    def _match_template(self, prompt: str) -> Optional[BusinessWorkflow]:
        """Match prompt to existing templates"""
        prompt_lower = prompt.lower()
        
        # Simple keyword matching for templates
        if any(keyword in prompt_lower for keyword in ["strategic", "strategy", "analysis", "market"]):
            return self.workflow_templates.get("strategic_analysis")
        elif any(keyword in prompt_lower for keyword in ["product", "launch", "release"]):
            return self.workflow_templates.get("product_launch")
        elif any(keyword in prompt_lower for keyword in ["customer", "onboarding", "setup"]):
            return self.workflow_templates.get("customer_onboarding")
        
        return None
    
    async def _generate_custom_workflow(
        self,
        request: WorkflowGenerationRequest
    ) -> BusinessWorkflow:
        """Generate a custom workflow using AI"""
        
        if not self.model_client:
            self.model_client = get_model_client()
        
        # Prepare prompt for AI
        system_prompt = """You are a workflow designer for the Convergio platform.
        Generate a workflow definition as JSON based on the user's description.
        
        Available agents: ali_chief_of_staff, amy_cfo, sofia_marketing, bria_legal, 
        marco_devops, luke_program_manager, harper_hr, lee_writer, omri_data_scientist,
        dan_engineering, luca_security, natalie_designer, jenny_accessibility
        
        Available tools: web_search, database_query, document_generator, email,
        api_call, calculator, ai_analysis, content_generator
        
        Return a JSON object with:
        - name: workflow name
        - description: workflow description
        - steps: array of step objects with (id, name, description, agent, tools, inputs, outputs)
        - entry_point: ID of first step
        - exit_points: array of final step IDs
        """
        
        user_prompt = f"""Create a workflow for: {request.prompt}
        Domain: {request.domain or 'General'}
        Complexity: {request.complexity}
        Max steps: {request.max_steps}
        Require approval: {request.require_approval}"""
        
        try:
            response = await self.model_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format="json"
            )
            
            workflow_data = json.loads(response)
            
            # Convert to BusinessWorkflow
            steps = []
            for step_data in workflow_data.get("steps", []):
                step = WorkflowStep(
                    id=step_data.get("id", str(uuid.uuid4())),
                    name=step_data.get("name", "Unnamed Step"),
                    description=step_data.get("description", ""),
                    agent=step_data.get("agent", "ali_chief_of_staff"),
                    tools=step_data.get("tools", []),
                    inputs=step_data.get("inputs", []),
                    outputs=step_data.get("outputs", {}),
                    approval_required=step_data.get("approval_required", False)
                )
                steps.append(step)
            
            workflow = BusinessWorkflow(
                name=workflow_data.get("name", "Custom Workflow"),
                description=workflow_data.get("description", request.prompt),
                steps=steps,
                entry_point=workflow_data.get("entry_point", steps[0].id if steps else ""),
                exit_points=workflow_data.get("exit_points", [steps[-1].id] if steps else []),
                tags=[request.domain] if request.domain else [],
                estimated_duration_seconds=len(steps) * 300,  # 5 min per step estimate
                estimated_cost=len(steps) * 0.50  # $0.50 per step estimate
            )
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to generate custom workflow: {e}")
            
            # Fallback to simple workflow
            return BusinessWorkflow(
                name="Simple Workflow",
                description=request.prompt,
                steps=[
                    WorkflowStep(
                        id="analysis",
                        name="Analysis",
                        description="Analyze the request",
                        agent="ali_chief_of_staff",
                        tools=["ai_analysis"],
                        outputs={"result": "json"}
                    )
                ],
                entry_point="analysis",
                exit_points=["analysis"],
                estimated_duration_seconds=300,
                estimated_cost=0.50
            )
    
    def validate_workflow(self, workflow: BusinessWorkflow) -> List[str]:
        """Validate workflow for correctness"""
        errors = []
        
        # Check entry point exists
        step_ids = {step.id for step in workflow.steps}
        if workflow.entry_point not in step_ids:
            errors.append(f"Entry point '{workflow.entry_point}' not found in steps")
        
        # Check exit points exist
        for exit_point in workflow.exit_points:
            if exit_point not in step_ids:
                errors.append(f"Exit point '{exit_point}' not found in steps")
        
        # Check step dependencies
        for step in workflow.steps:
            for input_id in step.inputs:
                if input_id not in step_ids:
                    errors.append(f"Step '{step.name}' references unknown input '{input_id}'")
        
        # Check for circular dependencies
        if self._has_circular_dependency(workflow):
            errors.append("Workflow contains circular dependencies")
        
        return errors
    
    def _has_circular_dependency(self, workflow: BusinessWorkflow) -> bool:
        """Check if workflow has circular dependencies"""
        # Build adjacency list
        graph = {step.id: step.inputs for step in workflow.steps}
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def optimize_workflow(self, workflow: BusinessWorkflow) -> BusinessWorkflow:
        """Optimize workflow for parallel execution"""
        # Identify steps that can run in parallel
        parallel_groups = self._identify_parallel_steps(workflow)
        
        # Update workflow metadata with optimization info
        workflow.metadata["parallel_groups"] = parallel_groups
        workflow.metadata["optimized"] = True
        workflow.metadata["optimization_time"] = datetime.utcnow().isoformat()
        
        # Recalculate estimated duration considering parallelism
        max_group_duration = 0
        for group in parallel_groups:
            group_duration = max(
                step.timeout_seconds 
                for step in workflow.steps 
                if step.id in group
            )
            max_group_duration += group_duration
        
        workflow.estimated_duration_seconds = max_group_duration
        
        return workflow
    
    def _identify_parallel_steps(self, workflow: BusinessWorkflow) -> List[List[str]]:
        """Identify steps that can execute in parallel"""
        # Build dependency graph
        dependencies = {step.id: set(step.inputs) for step in workflow.steps}
        
        # Topological sort with level assignment
        levels = []
        remaining = set(dependencies.keys())
        
        while remaining:
            # Find steps with no dependencies in remaining set
            current_level = []
            for step_id in remaining:
                deps = dependencies[step_id]
                if not deps.intersection(remaining):
                    current_level.append(step_id)
            
            if not current_level:
                break  # Circular dependency
            
            levels.append(current_level)
            remaining -= set(current_level)
        
        return levels
    
    def export_to_mermaid(self, workflow: BusinessWorkflow) -> str:
        """Export workflow as Mermaid diagram"""
        lines = ["graph TD"]
        
        # Add nodes
        for step in workflow.steps:
            label = f"{step.name}<br/>{step.agent}"
            shape = "[" if step.approval_required else "("
            close_shape = "]" if step.approval_required else ")"
            lines.append(f"    {step.id}{shape}{label}{close_shape}")
        
        # Add edges
        for step in workflow.steps:
            for input_id in step.inputs:
                lines.append(f"    {input_id} --> {step.id}")
        
        # Mark entry and exit points
        lines.append(f"    {workflow.entry_point}:::entry")
        for exit_point in workflow.exit_points:
            lines.append(f"    {exit_point}:::exit")
        
        # Add styles
        lines.extend([
            "    classDef entry fill:#90EE90",
            "    classDef exit fill:#FFB6C1"
        ])
        
        return "\n".join(lines)