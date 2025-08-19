"""
GraphFlow Orchestrator for Convergio Business Processes
Advanced workflow patterns using AutoGen 0.7.1 GraphFlow capabilities
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import asdict
import structlog
from uuid import uuid4

from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from core.config import get_settings
from agents.services.agent_loader import agent_loader
from agents.services.graphflow.definitions import WorkflowStep, BusinessWorkflow, WorkflowExecution
from agents.services.graphflow.registry import load_predefined_workflows
from agents.services.graphflow.runner import create_execution_graph, save_execution_state
from agents.memory.autogen_memory_system import AutoGenMemorySystem
from agents.security.ai_security_guardian import AISecurityGuardian
from core.redis import get_redis_client

logger = structlog.get_logger()

 

class GraphFlowOrchestrator:
    """Advanced workflow orchestrator using AutoGen GraphFlow"""
    
    def __init__(self):
        self.workflows: Dict[str, BusinessWorkflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.memory_system = AutoGenMemorySystem()
        self.security_guardian = AISecurityGuardian()
        self.redis_client = None
        
    async def initialize(self):
        """Initialize the GraphFlow orchestrator"""
        logger.info("🚀 Initializing GraphFlow Orchestrator")
        
        # Initialize Redis connection
        self.redis_client = get_redis_client()
        
        # Load pre-defined business workflows
        self.workflows = await load_predefined_workflows()
        
        logger.info(f"✅ GraphFlow Orchestrator initialized with {len(self.workflows)} workflows")

    async def _load_predefined_workflows(self):
        self.workflows = await load_predefined_workflows()

    async def create_execution_graph(self, workflow: BusinessWorkflow) -> DiGraphBuilder:
        """Create AutoGen GraphFlow execution graph from workflow definition"""
        
        builder = DiGraphBuilder()
        s = get_settings()
        
        # Create agents for each step
        step_agents = {}
        for step in workflow.steps:
            agent_config = await agent_loader.get_agent_config(step.agent_name)
            if not agent_config:
                logger.warning(f"⚠️ Agent {step.agent_name} not found, using default")
                agent_config = {
                    "name": step.agent_name,
                    "description": f"Agent for {step.step_type}",
                    "model": s.OPENAI_MODEL
                }
            
            # Create AutoGen agent
            client = OpenAIChatCompletionClient(
                model=agent_config.get("model", s.OPENAI_MODEL),
                api_key=s.OPENAI_API_KEY
            )
            
            agent = AssistantAgent(
                name=f"{step.step_id}_agent",
                model_client=client,
                system_message=f"""You are {step.agent_name} working on: {step.description}
                
Your role: {step.step_type}
Expected inputs: {', '.join(step.inputs)}
Expected outputs: {', '.join(step.outputs)}

Provide structured, actionable responses that clearly address the required outputs.
"""
            )
            
            step_agents[step.step_id] = agent
            builder.add_node(agent)
        
        # Add edges based on workflow dependencies
        for step in workflow.steps:
            current_agent = step_agents[step.step_id]
            
            # Find dependent steps (steps that use this step's outputs)
            for dependent_step in workflow.steps:
                if any(output in dependent_step.inputs for output in step.outputs):
                    dependent_agent = step_agents[dependent_step.step_id]
                    
                    # Add edge with optional condition
                    if step.conditions:
                        # Create condition function
                        condition_func = self._create_condition_function(step.conditions)
                        builder.add_edge(current_agent, dependent_agent, condition=condition_func)
                    else:
                        builder.add_edge(current_agent, dependent_agent)
        
        return builder
    
    def _create_condition_function(self, conditions: Dict[str, Any]) -> Callable:
        """Create a condition function for GraphFlow edges"""
        
        def condition_check(messages) -> bool:
            if not messages:
                return False
                
            last_message = messages[-1]
            if not hasattr(last_message, 'content'):
                return False
                
            content = last_message.content.lower()
            
            # Check various condition types
            for condition_type, condition_value in conditions.items():
                if condition_type == "contains_keyword":
                    if condition_value.lower() in content:
                        return True
                elif condition_type == "min_length":
                    if len(content) >= condition_value:
                        return True
                elif condition_type == "status_complete":
                    if any(keyword in content for keyword in ["complete", "done", "finished", "ready"]):
                        return True
                        
            return False
        
        return condition_check

    async def execute_workflow(
        self,
        workflow_id: str,
        user_request: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute a business workflow asynchronously"""
        
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        workflow = self.workflows[workflow_id]
        execution_id = str(uuid4())
        
        # Create workflow execution tracking
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="pending",
            current_step=None,
            step_results={},
            start_time=datetime.utcnow(),
            end_time=None,
            error_message=None,
            user_id=user_id
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Update status to running
            execution.status = "running"
            await self._save_execution_state(execution)
            
            logger.info(f"🚀 Starting workflow execution", 
                       workflow_id=workflow_id, execution_id=execution_id)
            
            # Create execution graph
            graph_builder = await create_execution_graph(workflow)
            graph = graph_builder.build()
            
            # Create GraphFlow team
            graphflow_team = GraphFlow(graph=graph)
            
            # Prepare initial message with context
            initial_context = {
                "user_request": user_request,
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "context": context or {}
            }
            
            initial_message = f"""
WORKFLOW EXECUTION REQUEST

User Request: {user_request}

Context: {json.dumps(initial_context, indent=2)}

Please process this request according to your role in the {workflow.name} workflow.
Provide structured outputs as specified in your step definition.
            """
            
            # Execute workflow with basic observability
            exec_start = datetime.utcnow()
            result = await graphflow_team.run(
                task=TextMessage(content=initial_message, source="user")
            )
            exec_end = datetime.utcnow()
            
            # Process results
            execution.step_results = await self._extract_workflow_results(result)
            # Attach basic observability
            try:
                execution.step_results.setdefault("observability", {})
                execution.step_results["observability"]["duration_seconds"] = (exec_end - exec_start).total_seconds()
                if hasattr(result, 'messages'):
                    execution.step_results["observability"]["message_count"] = len(result.messages)
            except Exception:
                pass
            execution.status = "completed"
            execution.end_time = datetime.utcnow()
            
            logger.info(f"✅ Workflow execution completed", 
                       workflow_id=workflow_id, execution_id=execution_id)
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed", 
                        workflow_id=workflow_id, execution_id=execution_id, 
                        error=str(e))
            execution.status = "failed"
            execution.error_message = str(e)
            execution.end_time = datetime.utcnow()
            
        finally:
            await save_execution_state(self.redis_client, execution)
            
        return execution_id

    async def _extract_workflow_results(self, flow_result) -> Dict[str, Any]:
        """Extract structured results from GraphFlow execution"""
        
        results: Dict[str, Any] = {}
        step_details: Dict[str, Any] = {}
        
        try:
            if hasattr(flow_result, 'messages'):
                for message in flow_result.messages:
                    if hasattr(message, 'source') and hasattr(message, 'content'):
                        agent_name = message.source
                        content = message.content
                        ts = getattr(message, 'created_at', None)
                        # Infer step_id from agent name pattern "{step_id}_agent"
                        step_id = None
                        if isinstance(agent_name, str) and agent_name.endswith('_agent'):
                            step_id = agent_name[:-6]
                        
                        if step_id:
                            step_rec = step_details.setdefault(step_id, {
                                'agent_name': agent_name,
                                'messages': [],
                                'first_seen': None,
                                'last_seen': None,
                            })
                            step_rec['messages'].append(content)
                            if ts:
                                try:
                                    # try ISO format to datetime
                                    from datetime import datetime as _dt
                                    tsv = ts if isinstance(ts, str) else str(ts)
                                    dt = _dt.fromisoformat(tsv) if isinstance(tsv, str) else None
                                except Exception:
                                    dt = None
                                if dt:
                                    if step_rec['first_seen'] is None or dt < step_rec['first_seen']:
                                        step_rec['first_seen'] = dt
                                    if step_rec['last_seen'] is None or dt > step_rec['last_seen']:
                                        step_rec['last_seen'] = dt
                        
                        # Try to extract structured data
                        try:
                            # Look for JSON-like structures in the content
                            import re
                            json_matches = re.findall(r'\{[^{}]*\}', content)
                            for json_str in json_matches:
                                try:
                                    structured_data = json.loads(json_str)
                                    results[f"{agent_name}_structured"] = structured_data
                                except json.JSONDecodeError:
                                    pass
                        except:
                            pass
                        
                        # Store raw content as well
                        results[agent_name] = content
                        
        except Exception as e:
            logger.warning(f"⚠️ Could not extract structured results: {e}")
            results["raw_result"] = str(flow_result)
            
        # Attach step details and approximate durations if available
        try:
            for sid, rec in step_details.items():
                if rec.get('first_seen') and rec.get('last_seen'):
                    rec['duration_seconds'] = (rec['last_seen'] - rec['first_seen']).total_seconds()
                # Store last message as output summary
                if rec.get('messages'):
                    rec['output_summary'] = rec['messages'][-1][:500]
                # Convert datetimes to iso
                for k in ('first_seen', 'last_seen'):
                    if isinstance(rec.get(k), (list, tuple)):
                        continue
                    v = rec.get(k)
                    if v is not None:
                        rec[k] = v.isoformat() if hasattr(v, 'isoformat') else str(v)
            results['steps'] = step_details
        except Exception:
            pass
        return results
        
    async def _save_execution_state(self, execution: WorkflowExecution):
        """Save execution state to Redis for persistence"""
        
        try:
            if self.redis_client:
                key = f"workflow_execution:{execution.execution_id}"
                data = asdict(execution)
                # Convert datetime objects to ISO strings
                if data.get('start_time'):
                    data['start_time'] = data['start_time'].isoformat()
                if data.get('end_time'):
                    data['end_time'] = data['end_time'].isoformat()
                    
                await self.redis_client.setex(
                    key,
                    86400,  # 24 hours TTL
                    json.dumps(data, default=str)
                )
        except Exception as e:
            logger.warning(f"⚠️ Could not save execution state: {e}")

    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get current status of workflow execution"""
        
        if execution_id in self.executions:
            return self.executions[execution_id]
            
        # Try to load from Redis
        try:
            if self.redis_client:
                key = f"workflow_execution:{execution_id}"
                data = await self.redis_client.get(key)
                if data:
                    execution_data = json.loads(data)
                    # Convert ISO strings back to datetime
                    if execution_data.get('start_time'):
                        execution_data['start_time'] = datetime.fromisoformat(execution_data['start_time'])
                    if execution_data.get('end_time'):
                        execution_data['end_time'] = datetime.fromisoformat(execution_data['end_time'])
                        
                    execution = WorkflowExecution(**execution_data)
                    self.executions[execution_id] = execution
                    return execution
        except Exception as e:
            logger.warning(f"⚠️ Could not load execution from Redis: {e}")
            
        return None

    async def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows with metadata"""
        
        return [
            {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "category": workflow.metadata.get("category", "general"),
                "complexity": workflow.metadata.get("complexity", "medium"),
                "estimated_duration": workflow.metadata.get("estimated_duration", 1800),
                "steps_count": len(workflow.steps)
            }
            for workflow in self.workflows.values()
        ]

    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        
        execution = await self.get_workflow_status(execution_id)
        if execution and execution.status == "running":
            execution.status = "cancelled"
            execution.end_time = datetime.utcnow()
            await save_execution_state(self.redis_client, execution)
            logger.info(f"🛑 Workflow execution cancelled", execution_id=execution_id)
            return True
        return False

# Global GraphFlow orchestrator instance - lazy loaded
graphflow_orchestrator = None

def get_graphflow_orchestrator() -> GraphFlowOrchestrator:
    """Get or create the global GraphFlow orchestrator instance"""
    global graphflow_orchestrator
    if graphflow_orchestrator is None:
        graphflow_orchestrator = GraphFlowOrchestrator()
    return graphflow_orchestrator
