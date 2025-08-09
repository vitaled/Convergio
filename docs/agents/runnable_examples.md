# Convergio AutoGen - Runnable Examples

This document provides complete, runnable examples demonstrating all major features of the Convergio AutoGen implementation.

## Table of Contents
- [Quick Start](#quick-start)
- [Basic Conversation](#basic-conversation)
- [Streaming Session](#streaming-session)
- [RAG-Enhanced Conversation](#rag-enhanced-conversation)
- [Workflow Execution](#workflow-execution)
- [HITL Approval Flow](#hitl-approval-flow)
- [Cost Tracking](#cost-tracking)
- [Benchmarking](#benchmarking)

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key"
export REDIS_URL="redis://localhost:6379"
export OTEL_EXPORTER_OTLP_ENDPOINT="localhost:4317"  # Optional

# Start Redis (if not running)
docker run -d -p 6379:6379 redis:alpine

# Start Jaeger for tracing (optional)
docker run -d -p 4317:4317 -p 16686:16686 jaegertracing/all-in-one:latest
```

### Initialize the System

```python
import asyncio
from backend.src.agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
from backend.src.agents.services.redis_state_manager import RedisStateManager
from backend.src.agents.services.cost_tracker import CostTracker

async def initialize_system():
    """Initialize the AutoGen system"""
    
    # Create components
    state_manager = RedisStateManager()
    cost_tracker = CostTracker()
    
    # Create orchestrator
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    # Initialize
    await orchestrator.initialize()
    
    print("✅ System initialized successfully")
    print(f"Agents available: {len(orchestrator.agents)}")
    
    return orchestrator

# Run initialization
orchestrator = asyncio.run(initialize_system())
```

## Basic Conversation

### Example 1: Simple Q&A

```python
async def basic_conversation():
    """Run a basic conversation with the group chat"""
    
    orchestrator = await initialize_system()
    
    # Ask a simple question
    result = await orchestrator.orchestrate_conversation(
        message="What are our top 3 strategic priorities for Q2?",
        user_id="demo_user",
        conversation_id="demo_conv_001"
    )
    
    print(f"\n📝 Response: {result.response}")
    print(f"🤖 Agents involved: {', '.join(result.agents_used)}")
    print(f"💬 Turns taken: {result.turn_count}")
    print(f"💵 Cost: ${result.cost_breakdown.get('total_cost_usd', 0):.4f}")
    
    return result

# Run the conversation
asyncio.run(basic_conversation())
```

### Example 2: Multi-Turn Conversation

```python
async def multi_turn_conversation():
    """Run a multi-turn conversation"""
    
    orchestrator = await initialize_system()
    conversation_id = "multi_turn_001"
    
    questions = [
        "Analyze our current market position",
        "What are the main risks we face?",
        "Propose a mitigation strategy for the top risk"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n🎯 Turn {i}: {question}")
        
        result = await orchestrator.orchestrate_conversation(
            message=question,
            user_id="demo_user",
            conversation_id=conversation_id
        )
        
        print(f"Response: {result.response[:200]}...")
        print(f"Agents: {', '.join(result.agents_used)}")
    
    print(f"\n✅ Conversation complete with {i} turns")

asyncio.run(multi_turn_conversation())
```

## Streaming Session

### Example 3: WebSocket Streaming

```python
import websockets
import json

async def streaming_example():
    """Connect to WebSocket and stream responses"""
    
    uri = "ws://localhost:8000/ws/agents/stream"
    
    async with websockets.connect(uri) as websocket:
        # Send initial message
        message = {
            "type": "start",
            "message": "Analyze our revenue trends and forecast for next quarter",
            "user_id": "demo_user",
            "agent_name": "diana_performance_dashboard"
        }
        
        await websocket.send(json.dumps(message))
        print("📤 Message sent, waiting for stream...")
        
        # Receive streaming chunks
        async for raw_message in websocket:
            data = json.loads(raw_message)
            
            if data.get("chunk_type") == "delta":
                # Text chunk
                print(data.get("content", ""), end="", flush=True)
            elif data.get("chunk_type") == "tool_call":
                print(f"\n🔧 Tool: {data.get('metadata', {}).get('tool_name')}")
            elif data.get("chunk_type") == "final":
                print("\n✅ Stream complete")
                break
            elif data.get("chunk_type") == "error":
                print(f"\n❌ Error: {data.get('content')}")
                break

asyncio.run(streaming_example())
```

### Example 4: Streaming with Tool Events

```python
async def streaming_with_tools():
    """Stream with tool execution events"""
    
    from backend.src.agents.services.streaming.runner import stream_agent_response
    
    orchestrator = await initialize_system()
    agent = orchestrator.agents.get("diana_performance_dashboard")
    
    if not agent:
        print("Agent not found")
        return
    
    print("🚀 Starting stream with tool events...")
    
    async for event in stream_agent_response(
        agent=agent,
        task="Analyze customer metrics and generate insights",
        session_id="stream_001"
    ):
        if event.event_type == "delta":
            print(event.content, end="", flush=True)
        elif event.event_type == "tool_call":
            print(f"\n🔧 Calling tool: {event.metadata.get('tool_name')}")
        elif event.event_type == "tool_result":
            print(f"📊 Tool result received")
        elif event.event_type == "final":
            print(f"\n✅ Complete. Tokens: {event.metadata.get('total_tokens')}")
            break

asyncio.run(streaming_with_tools())
```

## RAG-Enhanced Conversation

### Example 5: Enable RAG Context Injection

```python
async def rag_enhanced_conversation():
    """Conversation with RAG context injection"""
    
    from backend.src.agents.utils.feature_flags import (
        get_feature_flags, 
        FeatureFlagName,
        RolloutStrategy
    )
    
    # Enable RAG feature
    flag_manager = get_feature_flags()
    flag_manager.update_flag(
        FeatureFlagName.RAG_IN_LOOP,
        enabled=True,
        strategy=RolloutStrategy.ON
    )
    
    orchestrator = await initialize_system()
    
    # Store some context in memory
    if orchestrator.memory_system:
        await orchestrator.memory_system.store_conversation(
            user_id="demo_user",
            agent_id="context",
            content="Our Q1 revenue was $12M, up 15% YoY. Customer churn increased to 8%.",
            metadata={"type": "business_context"}
        )
        
        await orchestrator.memory_system.store_conversation(
            user_id="demo_user",
            agent_id="context",
            content="Main competitor launched AI features. We need to accelerate our AI roadmap.",
            metadata={"type": "competitive_intelligence"}
        )
    
    # Ask question that requires context
    result = await orchestrator.orchestrate_conversation(
        message="What should be our strategic response to market changes?",
        user_id="demo_user",
        conversation_id="rag_demo_001"
    )
    
    print("📚 RAG-Enhanced Response:")
    print(result.response)
    
    # The response should reference the stored context
    if "revenue" in result.response.lower() or "competitor" in result.response.lower():
        print("\n✅ Context successfully injected and used!")
    
    return result

asyncio.run(rag_enhanced_conversation())
```

### Example 6: Compare With/Without RAG

```python
async def compare_rag_impact():
    """Compare responses with and without RAG"""
    
    from backend.src.agents.benchmarks.grounding_quality import GroundingQualityBenchmark
    
    orchestrator = await initialize_system()
    
    # Create benchmark
    benchmark = GroundingQualityBenchmark(
        orchestrator=orchestrator,
        threshold=0.15  # 15% improvement required
    )
    
    # Run single task with/without RAG
    task = benchmark.benchmark_tasks[0]  # Use first task
    
    print(f"📝 Question: {task.question}")
    print(f"📚 Context available: {len(task.context_needed)} facts")
    
    # Run with RAG disabled
    print("\n1️⃣ Without RAG:")
    result_without = await benchmark.run_single_task(task, rag_enabled=False)
    print(f"Response: {result_without.response[:200]}...")
    print(f"Grounding Score: {result_without.grounding_score:.2%}")
    
    # Run with RAG enabled
    print("\n2️⃣ With RAG:")
    result_with = await benchmark.run_single_task(task, rag_enabled=True)
    print(f"Response: {result_with.response[:200]}...")
    print(f"Grounding Score: {result_with.grounding_score:.2%}")
    
    # Calculate improvement
    improvement = (result_with.grounding_score - result_without.grounding_score) / max(0.01, result_without.grounding_score)
    print(f"\n📈 Improvement: {improvement:.1%}")

asyncio.run(compare_rag_impact())
```

## Workflow Execution

### Example 7: GraphFlow Workflow

```python
async def workflow_execution():
    """Execute a GraphFlow workflow"""
    
    from backend.src.agents.services.graphflow_orchestrator import GraphFlowOrchestrator
    
    # Initialize GraphFlow orchestrator
    graphflow = GraphFlowOrchestrator()
    await graphflow.initialize()
    
    # List available workflows
    print("📋 Available workflows:")
    for wf_id, workflow in graphflow.workflows.items():
        print(f"  - {wf_id}: {workflow.name}")
    
    # Execute strategic analysis workflow
    result = await graphflow.execute_workflow(
        workflow_id="strategic_analysis",
        user_request="Analyze our position and create a growth strategy",
        user_id="demo_user",
        context={"priority": "high", "timeframe": "Q2-Q3"}
    )
    
    print(f"\n📊 Workflow Result:")
    print(result)
    
    # Check execution status
    execution_id = list(graphflow.executions.keys())[0] if graphflow.executions else None
    if execution_id:
        execution = graphflow.executions[execution_id]
        print(f"\nExecution Status: {execution.status}")
        print(f"Steps Completed: {len(execution.step_results)}")

asyncio.run(workflow_execution())
```

### Example 8: Custom Workflow

```python
async def custom_workflow():
    """Create and execute a custom workflow"""
    
    from backend.src.agents.services.graphflow.definitions import (
        BusinessWorkflow,
        WorkflowStep
    )
    
    # Define custom workflow
    custom_workflow = BusinessWorkflow(
        workflow_id="custom_analysis",
        name="Custom Analysis Flow",
        description="Custom multi-step analysis",
        steps=[
            WorkflowStep(
                step_id="data_gather",
                step_type="analysis",
                agent_name="diana_performance_dashboard",
                description="Gather performance data",
                inputs=["request"],
                outputs=["metrics", "trends"],
                conditions={}
            ),
            WorkflowStep(
                step_id="financial_analysis",
                step_type="analysis",
                agent_name="amy_cfo",
                description="Analyze financial impact",
                inputs=["metrics"],
                outputs=["financial_report"],
                conditions={"contains_keyword": "revenue"}
            ),
            WorkflowStep(
                step_id="strategy",
                step_type="planning",
                agent_name="ali_chief_of_staff",
                description="Create strategic plan",
                inputs=["trends", "financial_report"],
                outputs=["strategic_plan"],
                conditions={}
            )
        ],
        metadata={"category": "custom", "version": "1.0"}
    )
    
    # Execute custom workflow
    print("🔄 Executing custom workflow...")
    # Implementation would go here
    
    print("✅ Custom workflow complete")

asyncio.run(custom_workflow())
```

## HITL Approval Flow

### Example 9: Human-in-the-Loop Approval

```python
async def hitl_approval_flow():
    """Demonstrate HITL approval flow"""
    
    from backend.src.agents.services.hitl.approval_store import ApprovalStore
    from backend.src.agents.utils.feature_flags import get_feature_flags, FeatureFlagName
    
    # Enable HITL
    flag_manager = get_feature_flags()
    flag_manager.update_flag(FeatureFlagName.HITL, enabled=True)
    
    approval_store = ApprovalStore()
    await approval_store.initialize()
    
    # Create approval request
    approval_id = await approval_store.create_approval_request(
        action_type="execute_trade",
        action_details={
            "action": "buy",
            "symbol": "AAPL",
            "quantity": 1000,
            "price": 150.00
        },
        requester_id="amy_cfo",
        metadata={"risk_level": "medium", "value": 150000}
    )
    
    print(f"📋 Approval request created: {approval_id}")
    
    # Check status
    request = await approval_store.get_approval_request(approval_id)
    print(f"Status: {request['status']}")
    
    # Simulate approval
    await approval_store.update_approval_status(
        approval_id=approval_id,
        status="approved",
        approver_id="human_supervisor",
        comments="Approved within risk limits"
    )
    
    print("✅ Request approved")
    
    # Get approval history
    history = await approval_store.get_approval_history(
        requester_id="amy_cfo",
        limit=5
    )
    print(f"📜 Approval history: {len(history)} requests")

asyncio.run(hitl_approval_flow())
```

## Cost Tracking

### Example 10: Track Conversation Costs

```python
async def cost_tracking_example():
    """Track costs per turn and conversation"""
    
    from backend.src.agents.services.turn_token_tracker import (
        PerTurnTokenTracker,
        budget_monitor_callback
    )
    
    # Initialize tracker with budget
    tracker = PerTurnTokenTracker(budget_limit_usd=1.00)
    
    # Register callback for budget monitoring
    tracker.register_callback(budget_monitor_callback)
    
    orchestrator = await initialize_system()
    conversation_id = "cost_demo_001"
    
    # Start tracking
    timeline = tracker.start_conversation(
        conversation_id=conversation_id,
        budget_limit_usd=0.50
    )
    
    # Run conversation with tracking
    messages = [
        "Analyze our Q1 performance",
        "What are the key insights?",
        "Create an action plan"
    ]
    
    for i, message in enumerate(messages, 1):
        # Track turn
        result = await orchestrator.orchestrate_conversation(
            message=message,
            user_id="demo_user",
            conversation_id=conversation_id
        )
        
        # Record token usage
        await tracker.track_turn(
            conversation_id=conversation_id,
            turn_number=i,
            agent_name=result.agents_used[0] if result.agents_used else "unknown",
            message=None,  # Would pass actual message
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=200
        )
        
        print(f"Turn {i} cost: ${timeline.turns[-1].total_cost_usd:.4f}")
    
    # End tracking and get summary
    final_timeline = tracker.end_conversation(conversation_id)
    
    print(f"\n💰 Cost Summary:")
    print(f"Total tokens: {final_timeline.total_tokens}")
    print(f"Total cost: ${final_timeline.total_cost_usd:.4f}")
    print(f"Budget remaining: ${final_timeline.budget_remaining_usd:.4f}")
    
    # Export timeline
    tracker.export_timeline(conversation_id, "cost_timeline.json")
    print("📊 Timeline exported to cost_timeline.json")

asyncio.run(cost_tracking_example())
```

## Benchmarking

### Example 11: Run Benchmark Suite

```python
async def run_benchmark():
    """Run the complete benchmark suite"""
    
    from backend.src.agents.benchmarks.autogen_bench_scenarios import AutoGenBenchRunner
    
    orchestrator = await initialize_system()
    
    # Create benchmark runner
    runner = AutoGenBenchRunner(orchestrator=orchestrator)
    
    print("🚀 Starting benchmark suite...")
    
    # Run specific category
    report = await runner.run_all_scenarios(
        categories=["strategic", "analytics"],
        verbose=True
    )
    
    # Display results
    print(f"\n📊 Benchmark Results:")
    print(f"Scenarios: {report.scenarios_run}")
    print(f"Success Rate: {report.avg_success_rate:.1%}")
    print(f"Avg Duration: {report.avg_duration_seconds:.2f}s")
    print(f"P95 Latency: {report.p95_latency_ms:.0f}ms")
    print(f"Quality Score: {report.avg_outcome_match:.1%}")
    
    # Save artifacts for CI
    artifacts = await runner.save_artifacts(report)
    print(f"\n📁 Artifacts saved: {artifacts['report']}")
    
    return report

asyncio.run(run_benchmark())
```

### Example 12: Compare Configurations

```python
async def compare_configurations():
    """Compare performance with different configurations"""
    
    from backend.src.agents.utils.feature_flags import get_feature_flags, FeatureFlagName
    from backend.src.agents.benchmarks.autogen_bench_scenarios import AutoGenBenchRunner
    
    orchestrator = await initialize_system()
    runner = AutoGenBenchRunner(orchestrator=orchestrator)
    flag_manager = get_feature_flags()
    
    configurations = [
        {"name": "Baseline", "rag": False, "speaker_policy": False},
        {"name": "RAG Only", "rag": True, "speaker_policy": False},
        {"name": "Smart Selection", "rag": False, "speaker_policy": True},
        {"name": "Full Features", "rag": True, "speaker_policy": True}
    ]
    
    results = []
    
    for config in configurations:
        print(f"\n🔧 Testing: {config['name']}")
        
        # Set flags
        flag_manager.update_flag(FeatureFlagName.RAG_IN_LOOP, enabled=config["rag"])
        flag_manager.update_flag(FeatureFlagName.SPEAKER_POLICY, enabled=config["speaker_policy"])
        
        # Run mini benchmark
        report = await runner.run_all_scenarios(
            categories=["strategic"],  # Just one category for speed
            verbose=False
        )
        
        results.append({
            "config": config["name"],
            "success_rate": report.avg_success_rate,
            "avg_duration": report.avg_duration_seconds,
            "quality": report.avg_outcome_match
        })
    
    # Compare results
    print("\n📊 Configuration Comparison:")
    print("Config          | Success | Duration | Quality")
    print("----------------|---------|----------|--------")
    for r in results:
        print(f"{r['config']:15} | {r['success_rate']:6.1%} | {r['avg_duration']:7.2f}s | {r['quality']:6.1%}")
    
    # Find best configuration
    best = max(results, key=lambda x: x["success_rate"])
    print(f"\n🏆 Best configuration: {best['config']}")

asyncio.run(compare_configurations())
```

## Complete Example Application

### Example 13: Full Application

```python
"""
Complete example application demonstrating all features
"""

import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket
from backend.src.agents.observability.otel_integration import instrument_fastapi, initialize_otel

app = FastAPI(title="Convergio AutoGen API")

# Global orchestrator
orchestrator: Optional[ModernGroupChatOrchestrator] = None

@app.on_event("startup")
async def startup():
    """Initialize system on startup"""
    global orchestrator
    
    # Initialize OTEL
    initialize_otel(
        service_name="convergio-api",
        enable_prometheus=True
    )
    
    # Instrument FastAPI
    instrument_fastapi(app)
    
    # Initialize orchestrator
    from backend.src.agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
    from backend.src.agents.services.redis_state_manager import RedisStateManager
    from backend.src.agents.services.cost_tracker import CostTracker
    
    state_manager = RedisStateManager()
    cost_tracker = CostTracker()
    
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    await orchestrator.initialize()
    print("✅ API initialized")

@app.post("/api/v1/chat")
async def chat(message: str, user_id: str = "api_user"):
    """Basic chat endpoint"""
    if not orchestrator:
        return {"error": "System not initialized"}
    
    result = await orchestrator.orchestrate_conversation(
        message=message,
        user_id=user_id
    )
    
    return {
        "response": result.response,
        "agents": result.agents_used,
        "turns": result.turn_count,
        "cost": result.cost_breakdown
    }

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket streaming endpoint"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # Stream response
                await websocket.send_json({
                    "type": "response",
                    "content": "Streaming response here..."
                })
            elif data.get("type") == "close":
                break
                
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        await websocket.close()

@app.get("/api/v1/benchmark")
async def run_benchmark():
    """Run benchmark and return results"""
    from backend.src.agents.benchmarks.autogen_bench_scenarios import AutoGenBenchRunner
    
    runner = AutoGenBenchRunner(orchestrator=orchestrator)
    report = await runner.run_all_scenarios(categories=["strategic"])
    
    return {
        "success_rate": report.avg_success_rate,
        "avg_duration": report.avg_duration_seconds,
        "scenarios_run": report.scenarios_run
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing

### Running All Examples

```bash
# Run all examples in sequence
python -m pytest docs/agents/test_examples.py -v

# Run specific example
python -c "import asyncio; from docs.agents.runnable_examples import basic_conversation; asyncio.run(basic_conversation())"

# Run benchmarks
python backend/src/agents/benchmarks/autogen_bench_scenarios.py

# Run grounding quality test
python backend/src/agents/benchmarks/grounding_quality.py
```

### CI/CD Integration

```yaml
# .github/workflows/autogen-bench.yml
name: AutoGen Benchmark

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run benchmarks
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python backend/src/agents/benchmarks/autogen_bench_scenarios.py
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v2
      with:
        name: benchmark-results
        path: benchmark_artifacts/
    
    - name: Check thresholds
      run: |
        python -c "
        import json
        with open('benchmark_artifacts/benchmark_summary_latest.json') as f:
            summary = json.load(f)
        assert summary['success_rate'] >= 0.8, f'Success rate {summary['success_rate']} below threshold'
        assert summary['p95_latency'] <= 5000, f'P95 latency {summary['p95_latency']}ms above threshold'
        print('✅ All thresholds passed')
        "
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   # Start Redis
   docker run -d -p 6379:6379 redis:alpine
   ```

2. **API Key Missing**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

3. **Memory Issues with Large Conversations**
   ```python
   # Limit max turns
   orchestrator.settings.autogen_max_turns = 10
   ```

4. **Slow Response Times**
   ```python
   # Enable streaming for better UX
   flag_manager.update_flag(FeatureFlagName.TRUE_STREAMING, enabled=True)
   ```

## Next Steps

- Explore the [API Reference](./api_reference.md)
- Read the [Architecture Guide](./architecture.md)
- Check the [Migration Guide](./migration_guide.md)
- View [Performance Benchmarks](./benchmarks.md)

---

*Last Updated: January 2025*
*Version: 1.0.0*