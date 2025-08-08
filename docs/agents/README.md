Convergio Agents Architecture (Docs Stub)

- Streaming protocol: events `delta`, `agent_status`, `final`, `error`, `status`, `tool_call`, `tool_result`, `handoff`.
- RAG policy: memory context built via `build_memory_context` when `RAG_IN_LOOP` enabled.
- Speaker selection: `selection_policy.py` with flag `SPEAKER_POLICY`.
- Workflows: GraphFlow orchestrator, workflows exposed via API.
- HITL: approval store for gating sensitive actions.
- Safety & Cost: `AISecurityGuardian` pre‑check; `CostTracker` budget guard and tracking.

This folder will contain detailed guides for extending agents, tools, and workflows.

