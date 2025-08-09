# Convergio AutoGen Examples

Complete runnable examples demonstrating all major features of the Convergio AutoGen implementation.

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key"
export REDIS_URL="redis://localhost:6379"
export OTEL_EXPORTER_OTLP_ENDPOINT="localhost:4317"  # Optional for observability
```

## Example 1: Basic Conversation with GroupChat

```python
import asyncio
from backend.src.agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
from backend.src.agents.services.redis_state_manager import RedisStateManager
from backend.src.agents.services.cost_tracker import CostTracker

async def basic_conversation():
    """Run a basic multi-agent conversation"""
    
    # Initialize components
    state_manager = RedisStateManager()
    cost_tracker = CostTracker()
    
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    await orchestrator.initialize()
    
    # Run conversation
    result = await orchestrator.orchestrate_conversation(
        message="What's our strategy for entering the European market?",
        user_id="example_user",
        conversation_id="example_conv_1"
    )
    
    print(f"Response: {result.response}")
    print(f"Agents involved: {result.agents_used}")
    print(f"Turns taken: {result.turn_count}")
    print(f"Cost: ${result.cost_breakdown['total_cost_usd']:.4f}")

# Run the example
asyncio.run(basic_conversation())
```

## Example 2: Streaming Session with WebSocket

```python
import asyncio
import json
import websockets

async def streaming_example():
    """Demonstrate real-time streaming with tool events"""
    
    ws_url = "ws://localhost:8000/ws/agents/stream"
    
    async with websockets.connect(ws_url) as websocket:
        # Send initial message
        await websocket.send(json.dumps({
            "type": "start",
            "message": "Analyze our Q1 financial performance and suggest improvements",
            "agent_name": "amy_cfo",
            "user_id": "example_user",
            "context": {"include_tools": True}
        }))
        
        # Receive streaming responses
        async for message in websocket:
            data = json.loads(message)
            
            if data.get("chunk_type") == "delta":
                print(data.get("content", ""), end="", flush=True)
            elif data.get("chunk_type") == "tool_call":
                print(f"\n🔧 Tool: {data['metadata']['tool_name']}")
            elif data.get("chunk_type") == "handoff":
                print(f"\n🤝 Handoff: {data['metadata']['from_agent']} → {data['metadata']['to_agent']}")
            elif data.get("chunk_type") == "final":
                print("\n✅ Conversation complete")
                break

asyncio.run(streaming_example())
```

## Example 3: RAG-Enhanced Conversation (Per-Turn Injection)

```python
import asyncio
from backend.src.agents.services.groupchat.per_turn_rag import initialize_per_turn_rag
from backend.src.agents.services.groupchat.rag import AdvancedRAGProcessor
from backend.src.agents.memory.autogen_memory_system import AutoGenMemorySystem

async def rag_enhanced_conversation():
    """Demonstrate per-turn RAG context injection"""
    
    # Initialize memory system
    memory_system = AutoGenMemorySystem()
    
    # Store some context
    await memory_system.store_conversation(
        user_id="example_user",
        agent_id="system",
        content="Our Q1 revenue was $12M with 15% growth",
        metadata={"type": "fact", "importance": "high"}
    )
    
    await memory_system.store_conversation(
        user_id="example_user",
        agent_id="system",
        content="Customer churn increased from 5% to 8%",
        metadata={"type": "fact", "importance": "high"}
    )
    
    # Initialize orchestrator with RAG enabled
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker,
        memory_system=memory_system
    )
    
    # Enable RAG in settings
    orchestrator.settings.rag_in_loop_enabled = True
    
    await orchestrator.initialize()
    
    # Run conversation - RAG will inject context at each turn
    result = await orchestrator.orchestrate_conversation(
        message="What were our key Q1 metrics and what actions should we take?",
        user_id="example_user"
    )
    
    print(f"Response: {result.response}")
    print(f"Context was injected at {result.turn_count} turns")

asyncio.run(rag_enhanced_conversation())
```

## Example 4: GraphFlow Workflow Execution

```python
import asyncio
from backend.src.agents.services.graphflow_orchestrator import GraphFlowOrchestrator

async def workflow_execution():
    """Execute a predefined business workflow"""
    
    orchestrator = GraphFlowOrchestrator()
    await orchestrator.initialize()
    
    # Execute product launch workflow
    execution_id = await orchestrator.execute_workflow(
        workflow_id="product_launch",
        user_request="Launch our new AI assistant product in Q2",
        user_id="example_user",
        context={
            "budget": 500000,
            "timeline": "3 months",
            "target_markets": ["US", "EU", "UK"]
        }
    )
    
    print(f"Workflow execution started: {execution_id}")
    
    # Check execution status
    status = await orchestrator.get_execution_status(execution_id)
    print(f"Status: {status['status']}")
    print(f"Current step: {status['current_step']}")
    print(f"Progress: {status['progress_percentage']}%")

asyncio.run(workflow_execution())
```

## Example 5: Turn-by-Turn Speaker Selection

```python
import asyncio
from backend.src.agents.services.groupchat.turn_by_turn_selector import TurnByTurnSelectorGroupChat
from backend.src.agents.services.groupchat.selection_policy import IntelligentSpeakerSelector

async def intelligent_selection_demo():
    """Demonstrate intelligent turn-by-turn speaker selection"""
    
    # Initialize with intelligent selection enabled
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    # Enable speaker policy
    orchestrator.settings.speaker_policy_enabled = True
    
    await orchestrator.initialize()
    
    # Complex query requiring multiple specialists
    messages = [
        "We have a security breach affecting financial systems",
        "What's the impact assessment?",
        "How do we coordinate response?",
        "What's the recovery cost?"
    ]
    
    for message in messages:
        result = await orchestrator.orchestrate_conversation(
            message=message,
            user_id="example_user",
            conversation_id="security_incident_001"
        )
        
        print(f"\nQ: {message}")
        print(f"Selected agents: {result.agents_used}")
        print(f"Response: {result.response[:200]}...")
    
    # Get selection metrics
    if hasattr(orchestrator.group_chat, 'get_selection_performance'):
        perf = orchestrator.group_chat.get_selection_performance()
        print(f"\nSelection Performance:")
        print(f"  Speaker diversity: {perf['speaker_diversity']:.2%}")
        print(f"  Avg selection time: {perf['avg_selection_time_ms']}ms")

asyncio.run(intelligent_selection_demo())
```

## Example 6: Per-Turn Token Tracking with Budget

```python
import asyncio
from backend.src.agents.services.turn_token_tracker import (
    initialize_token_tracker,
    budget_monitor_callback
)

async def token_tracking_example():
    """Track token usage per turn with budget monitoring"""
    
    # Initialize token tracker with $1 budget
    token_tracker = initialize_token_tracker(budget_limit_usd=1.0)
    
    # Register budget monitor callback
    token_tracker.register_callback(budget_monitor_callback)
    
    # Initialize orchestrator
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    await orchestrator.initialize()
    
    # Start conversation tracking
    conversation_id = "budget_test_001"
    token_tracker.start_conversation(conversation_id, budget_limit_usd=0.10)
    
    # Run conversation
    messages = [
        "Analyze our complete financial position",
        "Create a detailed strategic plan",
        "Provide implementation roadmap"
    ]
    
    for i, message in enumerate(messages):
        result = await orchestrator.orchestrate_conversation(
            message=message,
            user_id="example_user",
            conversation_id=conversation_id
        )
        
        # Track token usage
        await token_tracker.track_turn(
            conversation_id=conversation_id,
            turn_number=i+1,
            agent_name=result.agents_used[-1] if result.agents_used else "unknown",
            message=None,  # Would pass actual message object
            prompt_tokens=result.cost_breakdown.get("estimated_tokens", 0) // 2,
            completion_tokens=result.cost_breakdown.get("estimated_tokens", 0) // 2
        )
        
        # Check budget status
        timeline = token_tracker.get_timeline(conversation_id)
        print(f"\nTurn {i+1}:")
        print(f"  Message: {message[:50]}...")
        print(f"  Tokens used: {timeline.turns[-1].total_tokens}")
        print(f"  Cost: ${timeline.turns[-1].total_cost_usd:.4f}")
        print(f"  Budget remaining: ${timeline.budget_remaining_usd:.4f}")
        
        if timeline.budget_breach_turn:
            print(f"  ⚠️ Budget breached at turn {timeline.budget_breach_turn}!")
            break
    
    # Get final summary
    summary = token_tracker.get_turn_summary(conversation_id)
    print(f"\nFinal Summary:")
    print(f"  Total turns: {summary['total_turns']}")
    print(f"  Total tokens: {summary['total_tokens']}")
    print(f"  Total cost: ${summary['total_cost_usd']:.4f}")
    print(f"  Avg tokens/turn: {summary['avg_tokens_per_turn']:.0f}")

asyncio.run(token_tracking_example())
```

## Example 7: HITL (Human-in-the-Loop) Approval Flow

```python
import asyncio
from backend.src.agents.services.hitl.approval_store import ApprovalStore

async def hitl_approval_example():
    """Demonstrate human-in-the-loop approval workflow"""
    
    approval_store = ApprovalStore()
    
    # Initialize orchestrator with HITL enabled
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    orchestrator.settings.hitl_enabled = True
    orchestrator.approval_store = approval_store
    
    await orchestrator.initialize()
    
    # Start conversation that will require approval
    conversation_id = "hitl_demo_001"
    
    # This will trigger approval requirement
    async def run_with_approval():
        result = await orchestrator.orchestrate_conversation(
            message="Execute emergency shutdown of production systems",
            user_id="example_user",
            conversation_id=conversation_id,
            context={"requires_approval": True, "risk_level": "high"}
        )
        return result
    
    # Start the task (will wait for approval)
    task = asyncio.create_task(run_with_approval())
    
    # Simulate human approval after 2 seconds
    await asyncio.sleep(2)
    
    # Get pending approval
    pending = await approval_store.get_pending_approvals()
    if pending:
        approval_id = pending[0]["id"]
        print(f"Pending approval: {pending[0]['action_type']}")
        
        # Approve the action
        await approval_store.approve(
            approval_id=approval_id,
            approver_id="supervisor_001",
            comments="Approved for emergency response"
        )
        print("✅ Action approved")
    
    # Wait for conversation to complete
    result = await task
    print(f"Result: {result.response}")

asyncio.run(hitl_approval_example())
```

## Example 8: Observability with OpenTelemetry

```python
import asyncio
from backend.src.agents.observability.otel_integration import (
    initialize_otel,
    otel_span,
    record_conversation_metrics
)

async def observability_example():
    """Demonstrate observability with OTEL spans and metrics"""
    
    # Initialize OTEL
    otel_provider = initialize_otel(
        service_name="convergio-example",
        otlp_endpoint="localhost:4317",
        enable_prometheus=True
    )
    
    # Run conversation with tracing
    with otel_span("example.conversation", {
        "user_id": "example_user",
        "scenario": "observability_demo"
    }) as span:
        
        orchestrator = ModernGroupChatOrchestrator(
            state_manager=state_manager,
            cost_tracker=cost_tracker
        )
        
        await orchestrator.initialize()
        
        # Add event to span
        if span:
            span.add_event("orchestrator_initialized")
        
        # Run conversation
        result = await orchestrator.orchestrate_conversation(
            message="What are our key performance metrics?",
            user_id="example_user"
        )
        
        # Record metrics
        record_conversation_metrics(
            conversation_id="obs_demo_001",
            user_id="example_user",
            agent_count=len(result.agents_used),
            duration_ms=int(result.duration_seconds * 1000),
            tokens_used=result.cost_breakdown.get("estimated_tokens", 0),
            cost_usd=result.cost_breakdown.get("total_cost_usd", 0),
            success=True
        )
        
        print(f"Response: {result.response[:200]}...")
        print(f"Metrics recorded to OTEL")
        print(f"View metrics at http://localhost:9090/metrics (Prometheus)")
        print(f"View traces in your OTEL backend")

asyncio.run(observability_example())
```

## Example 9: Running Benchmarks

```python
import asyncio
from backend.src.agents.benchmarks.autogen_bench_scenarios import AutoGenBenchRunner

async def run_benchmarks():
    """Run AutoGen benchmark scenarios"""
    
    # Initialize orchestrator
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    await orchestrator.initialize()
    
    # Create benchmark runner
    runner = AutoGenBenchRunner(orchestrator)
    
    # Run specific category
    report = await runner.run_all_scenarios(
        categories=["strategic", "analytics"],
        verbose=True
    )
    
    # Save report
    report_path = await runner.save_report(report)
    
    print(f"\nBenchmark Results:")
    print(f"  Total scenarios: {report.total_scenarios}")
    print(f"  Passed: {report.passed_scenarios}")
    print(f"  Failed: {report.failed_scenarios}")
    print(f"  Pass rate: {report.passed_scenarios/report.total_scenarios*100:.1f}%")
    print(f"  Avg duration: {report.avg_duration_ms:.0f}ms")
    print(f"  Total cost: ${report.total_cost_usd:.4f}")
    print(f"\nReport saved to: {report_path}")

asyncio.run(run_benchmarks())
```

## Example 10: Grounding Quality Measurement

```python
import asyncio
from backend.src.agents.benchmarks.grounding_quality import GroundingQualityBenchmark

async def measure_grounding_quality():
    """Measure the quality improvement from RAG"""
    
    # Initialize orchestrator
    orchestrator = ModernGroupChatOrchestrator(
        state_manager=state_manager,
        cost_tracker=cost_tracker
    )
    
    await orchestrator.initialize()
    
    # Create benchmark
    benchmark = GroundingQualityBenchmark(
        orchestrator=orchestrator,
        threshold=0.15  # Require 15% improvement
    )
    
    # Run benchmark
    report = await benchmark.run_benchmark()
    
    # Save report
    await benchmark.save_report(report)
    
    print(f"\nGrounding Quality Results:")
    print(f"  With RAG: {report.avg_grounding_with_rag:.2%}")
    print(f"  Without RAG: {report.avg_grounding_without_rag:.2%}")
    print(f"  Lift: {report.grounding_lift_percentage:+.1f}%")
    print(f"  Benchmark: {'PASSED ✅' if report.passed else 'FAILED ❌'}")
    
    # Category breakdown
    for category, perf in report.category_performance.items():
        print(f"  {category}: {perf['grounding_lift_percentage']:+.1f}% lift")

asyncio.run(measure_grounding_quality())
```

## Running All Examples

Create a script `run_examples.py`:

```python
#!/usr/bin/env python3
import asyncio
import sys
from typing import List

# Import all example functions
from examples import (
    basic_conversation,
    streaming_example,
    rag_enhanced_conversation,
    workflow_execution,
    intelligent_selection_demo,
    token_tracking_example,
    hitl_approval_example,
    observability_example,
    run_benchmarks,
    measure_grounding_quality
)

async def run_all_examples():
    """Run all examples sequentially"""
    
    examples = [
        ("Basic Conversation", basic_conversation),
        ("Streaming Session", streaming_example),
        ("RAG-Enhanced", rag_enhanced_conversation),
        ("GraphFlow Workflow", workflow_execution),
        ("Speaker Selection", intelligent_selection_demo),
        ("Token Tracking", token_tracking_example),
        ("HITL Approval", hitl_approval_example),
        ("Observability", observability_example),
        ("Benchmarks", run_benchmarks),
        ("Grounding Quality", measure_grounding_quality)
    ]
    
    print("="*60)
    print("CONVERGIO AUTOGEN EXAMPLES")
    print("="*60)
    
    for name, func in examples:
        print(f"\n🚀 Running: {name}")
        print("-"*40)
        
        try:
            await func()
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
        
        # Small delay between examples
        await asyncio.sleep(2)
    
    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETED")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_all_examples())
```

## Docker Compose Setup

For a complete environment setup:

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: convergio
      POSTGRES_USER: convergio
      POSTGRES_PASSWORD: convergio123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
      - "9090:9090"  # Prometheus metrics

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./grafana_dashboard.json:/var/lib/grafana/dashboards/dashboard.json
      - grafana_data:/var/lib/grafana

  convergio-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://convergio:convergio123@postgres:5432/convergio
      - OTEL_EXPORTER_OTLP_ENDPOINT=otel-collector:4317
    depends_on:
      - redis
      - postgres
      - otel-collector

volumes:
  redis_data:
  postgres_data:
  grafana_data:
```

## Testing the Examples

```bash
# Run unit tests
pytest tests/unit/test_per_turn_rag.py -v
pytest tests/unit/test_turn_by_turn_selection.py -v
pytest tests/unit/test_turn_token_tracker.py -v

# Run integration tests
pytest tests/integration/test_feature_flags.py -v
pytest tests/integration/test_selection_metrics.py -v

# Run E2E tests
pytest tests/e2e/test_streaming_e2e.py -v

# Run benchmarks
python backend/src/agents/benchmarks/autogen_bench_scenarios.py
python backend/src/agents/benchmarks/grounding_quality.py

# Run all examples
python docs/agents/run_examples.py
```

## Monitoring and Debugging

### View Prometheus Metrics
```
http://localhost:9090/metrics
```

### View Grafana Dashboard
```
http://localhost:3000
Username: admin
Password: admin
```

### Check Redis State
```bash
redis-cli
> KEYS convergio:*
> GET convergio:conversation:example_conv_1
```

### View Logs
```bash
# With structured logging
PYTHONPATH=. python examples.py 2>&1 | jq '.'

# Filter by level
PYTHONPATH=. python examples.py 2>&1 | jq 'select(.level=="ERROR")'
```

## Performance Tips

1. **Enable caching**: RAG context is cached for 60 seconds by default
2. **Use connection pooling**: Redis and database connections are pooled
3. **Batch operations**: Multiple messages can be processed in one conversation
4. **Feature flags**: Disable unused features to reduce overhead
5. **Budget limits**: Set appropriate budget limits to control costs

## Troubleshooting

### Common Issues

1. **Redis connection error**
   ```bash
   # Check Redis is running
   redis-cli ping
   ```

2. **OpenAI API key missing**
   ```bash
   export OPENAI_API_KEY="your-key"
   ```

3. **OTEL export failing**
   ```bash
   # Disable OTEL if not needed
   export OTEL_SDK_DISABLED=true
   ```

4. **Memory issues with large contexts**
   ```python
   # Limit RAG facts
   orchestrator.settings.rag_max_facts = 3
   ```

5. **Slow streaming**
   ```python
   # Reduce heartbeat interval
   orchestrator.heartbeat_interval_sec = 5.0
   ```

## Next Steps

- Explore the [API Documentation](./api.md)
- Review the [Architecture Guide](./architecture.md)
- Read the [Migration Guide](./migration_guide.md)
- Check the [Security Guidelines](./security.md)

---

*Last Updated: January 2025*
*Version: 1.0.0*