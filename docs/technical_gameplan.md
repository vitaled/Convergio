# Technical Gameplan — Convergio

Architecture
- Backend: FastAPI (Python 3.11), AutoGen 0.7.2, Postgres (pgvector), Redis, JWT RS256.
- Frontend: SvelteKit + TypeScript, Tailwind.
- Streaming: WebSocket with granular events and heartbeats.
- Security: AI Security Guardian, multi-layer validation, digital signatures.

Testing Strategy
- Unit tests (pytest + pytest-cov) for agents/orchestrators/utilities.
- Integration tests for APIs, workflows, and streaming.
- E2E (frontend) for key user journeys and accessibility.
- Coverage report exported as coverage.xml on each CI run (artifact).

Acceptance Criteria
- All health endpoints green in CI.
- Coverage ≥ 60% for backend modules in scope.
- Streaming protocol validated (delta, status, final).
- WS11 docs stubs present and referenced from README.

Deployment Path
- Local: `./start.sh` for dev.
- Cloud: Prefer containerized deploy (Azure Container Apps or App Service) following `deployment/README.md` guidance.
