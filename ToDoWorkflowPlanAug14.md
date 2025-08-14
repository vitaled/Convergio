# 📋 AutoGen Workflow Implementation Plan
## Complete Integration Roadmap for Convergio Platform
*Date: August 14, 2025*
*AutoGen Version: 0.7.2*

---

## 🎯 Executive Summary
This document outlines the complete implementation plan to achieve a fully functional AutoGen GraphFlow workflow system in Convergio, from UI to execution, including visual editing, persistence, and multi-agent orchestration.

---

## 📊 Current State Analysis

### ✅ What's Working
1. **GraphFlow Enabled** - Feature flag active in config
2. **Visual Editor UI** - Drag-and-drop interface for workflow design
3. **Workflow Details API** - Returns complete workflow structure with agents
4. **4 Predefined Workflows** - Strategic analysis, product launch, market entry, customer onboarding
5. **Agent Registry** - 30+ agents loaded and available
6. **Basic Execution Endpoint** - `/workflows/execute` endpoint exists

### ⚠️ Critical Issues
1. **Tool Execution Broken** - AutoGen 0.7.x tools not working with agents
2. **Save Workflow API Missing** - No backend endpoint to persist custom workflows
3. **Execution Not Connected** - GraphFlow orchestrator not properly executing workflows
4. **No Workflow Persistence** - Custom workflows lost on refresh
5. **Missing Status Tracking** - No real-time execution monitoring
6. **Agent Communication Broken** - Agents can't pass context between steps

---

## 🛠️ Implementation Plan

### Phase 1: Fix Core Tool Execution (Priority: CRITICAL)
**Timeline: 2-3 days**

#### 1.1 Fix AutoGen 0.7.x Tool Integration
```python
# Location: backend/src/agents/orchestrators/unified.py
# Issue: Tools not being executed by agents
# Solution: Update to new AutoGen 0.7.x tool registration API

- [ ] Research AutoGen 0.7.2 tool registration changes
- [ ] Update DynamicAgentLoader.create_autogen_agents() method
- [ ] Implement proper FunctionTool registration
- [ ] Test with database_tools, web_tools, vector_tools
- [ ] Verify tool execution in agent responses
```

#### 1.2 Fix Agent Message Passing
```python
# Location: backend/src/agents/services/graphflow_orchestrator.py
# Issue: Agents not receiving context from previous steps
# Solution: Implement proper message threading

- [ ] Update create_execution_graph() to pass context
- [ ] Implement WorkflowContext class for state management
- [ ] Add context passing between workflow steps
- [ ] Test multi-step workflows with data flow
```

### Phase 2: Workflow Persistence Layer (Priority: HIGH)
**Timeline: 2 days**

#### 2.1 Database Schema
```sql
-- New tables needed
CREATE TABLE workflows (
    id UUID PRIMARY KEY,
    workflow_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    description TEXT,
    graph_definition JSONB,
    created_by VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY,
    workflow_id VARCHAR(255),
    execution_id VARCHAR(255) UNIQUE,
    status VARCHAR(50),
    context JSONB,
    results JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);
```

#### 2.2 Save/Load Workflow API
```python
# Location: backend/src/api/workflows.py
# New endpoints needed

- [ ] POST /workflows/save - Save custom workflow
- [ ] GET /workflows/custom - List user workflows
- [ ] PUT /workflows/{id} - Update workflow
- [ ] DELETE /workflows/{id} - Delete workflow
- [ ] POST /workflows/import - Import from JSON
- [ ] GET /workflows/export/{id} - Export to JSON
```

### Phase 3: Execution Engine Enhancement (Priority: HIGH)
**Timeline: 3 days**

#### 3.1 GraphFlow Execution Pipeline
```python
# Location: backend/src/agents/services/graphflow_orchestrator.py

- [ ] Implement proper DiGraphBuilder construction
- [ ] Add step-by-step execution tracking
- [ ] Implement parallel step execution
- [ ] Add timeout and retry logic
- [ ] Implement approval gates
- [ ] Add cost tracking per step
```

#### 3.2 Real-time Status Updates
```python
# WebSocket implementation for live updates

- [ ] Add WebSocket endpoint for execution monitoring
- [ ] Implement ExecutionTracker class
- [ ] Send step completion events
- [ ] Stream agent responses in real-time
- [ ] Handle execution cancellation
```

### Phase 4: Enhanced Visual Editor (Priority: MEDIUM)
**Timeline: 2 days**

#### 4.1 Editor Improvements
```javascript
// Location: frontend/src/lib/components/dashboard/WorkflowEditor.svelte

- [ ] Add validation for circular dependencies
- [ ] Implement auto-layout algorithm
- [ ] Add copy/paste functionality
- [ ] Add undo/redo support
- [ ] Add workflow templates
- [ ] Add zoom/pan controls
- [ ] Export workflow as image
```

#### 4.2 Advanced Node Configuration
```javascript
- [ ] Add conditional branching UI
- [ ] Add loop constructs
- [ ] Add parallel execution indicators
- [ ] Add input/output type validation
- [ ] Add tool selection per step
- [ ] Add approval gate configuration
```

### Phase 5: Workflow Library & Templates (Priority: MEDIUM)
**Timeline: 1 day**

#### 5.1 Template System
```python
# Predefined workflow templates

- [ ] Sales Pipeline Automation
- [ ] Customer Support Escalation
- [ ] Financial Analysis & Reporting
- [ ] Product Development Cycle
- [ ] Marketing Campaign Orchestration
- [ ] HR Onboarding Process
- [ ] Data Analysis Pipeline
```

### Phase 6: Testing & Validation (Priority: HIGH)
**Timeline: 2 days**

#### 6.1 Unit Tests
```python
- [ ] Test workflow creation
- [ ] Test workflow execution
- [ ] Test agent communication
- [ ] Test tool execution
- [ ] Test error handling
- [ ] Test persistence layer
```

#### 6.2 Integration Tests
```python
- [ ] End-to-end workflow execution
- [ ] Multi-agent collaboration
- [ ] Tool integration
- [ ] WebSocket communication
- [ ] UI workflow creation and execution
```

---

## 📝 Technical Requirements

### Backend Dependencies
```python
# Required packages
autogen-agentchat==0.7.2
asyncpg  # For PostgreSQL async
redis  # For state management
websockets  # For real-time updates
pydantic>=2.0  # For data validation
```

### Frontend Dependencies
```javascript
// Required packages
"@sveltejs/kit": "latest",
"d3": "^7.0.0",  // For graph visualization
"svelte-dnd-action": "^0.9.0",  // For drag-and-drop
```

### Infrastructure Requirements
- PostgreSQL 14+ with JSONB support
- Redis 6+ for state management
- WebSocket support in deployment environment

---

## 🚀 Quick Start Implementation

### Step 1: Fix Tool Execution (DAY 1)
```bash
# Priority fix for tools
1. Update unified.py to use new AutoGen tool API
2. Test with simple database query tool
3. Verify agents can execute tools
```

### Step 2: Add Save Workflow API (DAY 2)
```bash
# Minimum viable persistence
1. Add save endpoint to workflows.py
2. Store in PostgreSQL as JSONB
3. Test save/load cycle
```

### Step 3: Connect Execution (DAY 3)
```bash
# Make workflows actually run
1. Fix GraphFlow orchestrator execute method
2. Add proper context passing
3. Test end-to-end execution
```

---

## 🎯 Success Metrics

### Functional Requirements
- [ ] Users can create custom workflows visually
- [ ] Workflows persist across sessions
- [ ] Workflows execute with real agent collaboration
- [ ] Tools work correctly in agent steps
- [ ] Real-time execution status visible
- [ ] Results properly captured and displayed

### Performance Requirements
- [ ] Workflow creation < 2 seconds
- [ ] Workflow execution start < 5 seconds
- [ ] Status updates < 500ms latency
- [ ] Support 10+ concurrent executions

### Quality Requirements
- [ ] 90% test coverage on critical paths
- [ ] Error handling for all failure modes
- [ ] Graceful degradation on tool failures
- [ ] Audit trail for all executions

---

## 🔧 Immediate Next Steps

### TODAY (Priority Actions)
1. **Fix Tool Execution** - Update to AutoGen 0.7.2 tool API
2. **Add Save Endpoint** - Implement POST /workflows/save
3. **Test Basic Flow** - Create → Save → Load → Execute

### TOMORROW
1. **Add Persistence Layer** - PostgreSQL schema and models
2. **Fix Execution Pipeline** - Connect GraphFlow properly
3. **Add Status Tracking** - WebSocket or polling

### THIS WEEK
1. **Complete Editor Features** - Validation, templates
2. **Add Test Coverage** - Unit and integration tests
3. **Documentation** - API docs and user guide

---

## 📚 References

### AutoGen Documentation
- [AutoGen 0.7.2 Migration Guide](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/migration.html)
- [GraphFlow Documentation](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html)
- [Tool Registration](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/tools.html)

### Code Locations
- **Orchestrator**: `backend/src/agents/orchestrators/unified.py`
- **GraphFlow**: `backend/src/agents/services/graphflow_orchestrator.py`
- **Workflows API**: `backend/src/api/workflows.py`
- **Editor UI**: `frontend/src/lib/components/dashboard/WorkflowEditor.svelte`
- **Config**: `backend/src/agents/utils/config.py`

---

## ⚠️ Known Blockers

1. **AutoGen 0.7.x Breaking Changes** - Tool API completely changed
2. **Message Passing** - New message format required
3. **Async Execution** - Need proper async/await throughout
4. **State Management** - Redis integration incomplete

---

## 💡 Recommendations

1. **Start with Tool Fix** - Nothing works without tools
2. **Use Existing Agents** - Don't create new agents yet
3. **Simple Workflows First** - 2-3 step workflows for testing
4. **Add Logging** - Extensive logging for debugging
5. **Incremental Testing** - Test each component separately

---

*This plan provides a clear roadmap to achieve fully functional AutoGen workflow orchestration in Convergio. Focus on Phase 1 (Tool Execution) as the critical blocker, then proceed with persistence and execution enhancements.*