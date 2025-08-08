Runbook: Real End-to-End Validation

Prerequisites
- Ensure `.env` at repo root contains valid values for:
  - `OPENAI_API_KEY`, `BACKEND_URL`, `DB_*`, `REDIS_*`, `JWT_SECRET`
  - Feature flags: `TRUE_STREAMING=true`, `RAG_IN_LOOP=true`, `SPEAKER_POLICY=true`, `GRAPHFLOW=true`, `HITL=true`, `COST_SAFETY=true`
  - Optional RAG tuning: `RAG_SIMILARITY_THRESHOLD=0.5`, `RAG_MAX_FACTS=5`

Start the App
- From repo root: `uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload`

Validate Streaming (WS3)
- Open a WebSocket to `/api/v1/agents/ws/streaming/{user_id}/{agent_name}`
- Send `{ "message": "Analizza i costi Q4" }`
- Expect events: `agent_status` → `delta` chunks → optional `tool_call`/`tool_result`/`handoff` → `final`
- Health endpoints:
  - `GET /api/v1/agents/streaming/health`
  - `GET /api/v1/agents/streaming/sessions`

Validate RAG (WS2)
- Run a few conversations on topics previously stored in memory; observe better grounding.
- Tune thresholds in `.env` if needed.

Validate Selection Metrics (WS4)
- After streaming a few prompts (budget, security, strategy), check `GET /api/v1/agents/selection-metrics`.

Validate GraphFlow (WS5)
- List: `GET /api/v1/workflows/`
- Execute: `POST /api/v1/workflows/execute` with a valid `workflow_id`
- Status: `GET /api/v1/workflows/execution/{execution_id}` and observe `step_results` and `observability` fields.

Validate HITL (WS6)
- Trigger a conversation with `context.requires_approval=true`
- List approvals: `GET /api/v1/agents/approvals`
- Approve: `POST /api/v1/agents/approvals/{id}/approve`
- Deny: `POST /api/v1/agents/approvals/{id}/deny`

Feature Flags
- `GET /api/v1/agents/feature-flags` to inspect current runtime flags.

