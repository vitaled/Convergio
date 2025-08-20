# Orchestrator Architecture Documentation
*Last updated: August 20, 2025*

## Overview

The orchestrator architecture has been unified into a single, comprehensive orchestrator system to eliminate duplication and provide consistent behavior across all use cases.

## Architecture Design

### Core Philosophy: Single Source of Truth

Following the user's request: **"se possibile lasciane soltanto uno che faccia tutto quello che serve"** (leave only one that does everything needed), the entire orchestrator system now operates through a single core orchestrator with compatibility adapters.

### Core Component: UnifiedOrchestrator

**Location**: `/backend/src/agents/orchestrators/unified.py`

The `UnifiedOrchestrator` is the single orchestrator that handles ALL use cases:

- ✅ **Intelligent routing** from IntelligentAgentRouter
- ✅ **GroupChat** for multi-agent scenarios  
- ✅ **Direct agent conversation** for efficiency
- ✅ **RAG support** for context-aware responses
- ✅ **Safety gates** for responsible AI
- ✅ **WebSocket streaming support**
- ✅ **Cost and performance tracking**
- ✅ **Circuit breaker patterns** for resilience
- ✅ **Health monitoring**
- ✅ **Swarm orchestration** capabilities
- ✅ **Workflow orchestration** support

### Compatibility Layer: Unified Orchestrator Adapter

**Location**: `/backend/src/agents/services/unified_orchestrator_adapter.py`

Provides compatibility interfaces for existing code:

```python
# All these classes now delegate to UnifiedOrchestrator
- AliSwarmOrchestrator      → orchestrate_swarm()
- StreamingOrchestrator     → streaming capabilities  
- GraphFlowOrchestrator     → workflow capabilities
```

### Entry Point: RealAgentOrchestrator

**Location**: `/backend/src/agents/orchestrator.py`

The main entry point now directly uses `UnifiedOrchestrator` without any wrapper layers.

```python
class RealAgentOrchestrator:
    def __init__(self):
        self.orchestrator: UnifiedOrchestrator = None  # Direct usage
```

## Legacy Files Converted to Compatibility Wrappers

These files now contain minimal compatibility wrappers that delegate to UnifiedOrchestrator:

1. **`ali_swarm_orchestrator.py`** - 4 lines, imports from adapter
2. **`streaming_orchestrator.py`** - 4 lines, imports from adapter  
3. **`graphflow_orchestrator.py`** - 4 lines, imports from adapter
4. **`autogen_groupchat_orchestrator.py`** - Compatibility wrapper for benchmarks

## Removed Files

These files were completely removed as they contained unused/duplicate functionality:

1. **`resilience.py`** - Functionality moved inline to UnifiedOrchestrator
2. **`autogen_orchestrator.py`** - Unused legacy code
3. **`graphflow_orchestrator.py` (original)** - Replaced with simple adapter

## API Compatibility

All existing APIs continue to work exactly as before:

```python
# These all work exactly the same
from agents.services.ali_swarm_orchestrator import AliSwarmOrchestrator
from agents.services.streaming_orchestrator import StreamingOrchestrator
from agents.services.graphflow_orchestrator import get_graphflow_orchestrator
from agents.orchestrator import get_agent_orchestrator
```

## Benefits of the Unified Architecture

### 1. **Eliminates Duplication**
- Single implementation of core logic
- No conflicting behaviors between orchestrators
- Consistent error handling and logging

### 2. **Simplified Maintenance**
- Only one orchestrator to maintain and debug
- Easier to add new features (add once, available everywhere)
- Consistent performance optimizations

### 3. **Better Resource Management**
- Single connection pools, caches, and state management
- Unified cost tracking and circuit breaker patterns
- Consistent health monitoring

### 4. **Improved Testing**
- Test the core once, compatibility is guaranteed
- Easier integration testing
- More predictable behavior

### 5. **Cleaner Codebase**
- Follows DRY principle (Don't Repeat Yourself)
- Clear separation of concerns
- Easier onboarding for new developers

## Usage Examples

### Basic Orchestration
```python
from agents.orchestrator import get_agent_orchestrator

orchestrator = await get_agent_orchestrator()
result = await orchestrator.orchestrate(
    message="Hello",
    user_id="user123"
)
```

### Swarm Orchestration
```python
from agents.services.ali_swarm_orchestrator import AliSwarmOrchestrator

swarm = AliSwarmOrchestrator()
await swarm.initialize()
result = await swarm.orchestrate_conversation(
    message="Complex multi-agent task",
    user_id="user123"
)
```

### Streaming
```python
from agents.services.streaming_orchestrator import get_streaming_orchestrator

streaming = get_streaming_orchestrator()
session_id = await streaming.create_streaming_session(websocket, user_id, agent_name)
async for chunk in streaming.stream_response(session_id, message):
    await websocket.send_json(chunk)
```

### Workflow Orchestration
```python
from agents.services.graphflow_orchestrator import get_graphflow_orchestrator

workflow_orchestrator = get_graphflow_orchestrator()
workflow = await workflow_orchestrator.generate_workflow("Create a user registration flow")
result = await workflow_orchestrator.execute_workflow(workflow["id"])
```

## Internal Architecture Flow

```
User Code
    ↓
Compatibility Wrapper (AliSwarmOrchestrator, StreamingOrchestrator, etc.)
    ↓  
Unified Orchestrator Adapter (unified_orchestrator_adapter.py)
    ↓
UnifiedOrchestrator (unified.py) ← SINGLE SOURCE OF TRUTH
    ↓
Agent Services, Tools, AI Models
```

## Migration Impact

✅ **No breaking changes** - All existing code continues to work
✅ **Performance improvements** - Unified resource management
✅ **Better reliability** - Single, well-tested code path
✅ **Easier debugging** - All orchestration flows through one component

## Future Development

When adding new orchestration capabilities:

1. Add the feature to `UnifiedOrchestrator`
2. Expose it through the appropriate compatibility adapter
3. All existing interfaces automatically benefit from the new feature

This architecture ensures the system stays **clean and maintainable** while providing **maximum functionality** through a **single, unified orchestrator**.