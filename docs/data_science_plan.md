# Data Science Plan & Evaluation — Convergio

Models & Providers
- Azure OpenAI / OpenAI compatible models via AutoGen. Deterministic configs for tests where possible.

Evaluation Approach
- Scenario-based functional tests for strategic Q&A, routing, and workflows.
- Hallucination checks via retrieval grounding toggles (RAG_IN_LOOP on/off).

Metrics
- Turns, latency (p50/p95), cost (USD/tokens), selection accuracy proxy, RAG hits.

Safety
- Pre/post filters via AISecurityGuardian; test blocked cases and budget limits.

Artifacts
- Store evaluation logs and coverage.xml as CI artifacts for traceability.
