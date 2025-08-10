Title: Selective backport from CursorCloudAug8: safer fallbacks without regressions

Summary
- Keep master as source of truth; do NOT merge branch wholesale.
- Evaluate and (if acceptable) port a minimal set of robustness improvements from `origin/CursorCloudAug8` without removing any existing features, docs, or tests.

Recommended changes to consider
- Agent selection fallback: In `backend/src/agents/services/groupchat/selection_policy.py`, add keyword-based fallback and deterministic selection only when intelligent selection returns no agent. Preserve existing reasons/picked schema.
- RAG minimal fallback for tests: In `backend/src/agents/services/groupchat/rag.py`, keep advanced path intact but add a guarded fallback when using fake memory in tests. Avoid changing behavior from returning `None` when truly no context is found (prevent unintended downstream effects). Consider a feature flag/env (e.g., `RAG_TEST_FALLBACK=true`) for the fallback behavior.
- Pure-Python cosine similarity: In `backend/src/agents/tools/vector_search_client.py`, add a safe pure-Python `calculate_similarity` implementation and use it as a fallback if NumPy is unavailable. Prefer existing fast path when NumPy is present.
- Lazy router imports (startup robustness): In `backend/src/main.py`, wrap router imports in try/except to avoid startup failures in minimal test environments while keeping routes unchanged when modules are present. Log warnings on failures.
- Config defaults (dev-only): In `backend/src/agents/utils/config.py`, consider optional dev-friendly defaults for `BACKEND_URL`, `DB_HOST/PORT`, telemetry endpoints. Keep `JWT_SECRET` non-default in prod; guard with an environment profile or only apply in tests.

Explicitly out of scope (do not port)
- Any deletion of docs, tests, HITL/approvals, monitoring, cost circuit breaker, streaming protocol, or graphflow functionality present on master.
- Removal of advanced RAG features (cache, quality metrics) unless replaced equivalently.

Acceptance criteria
- No file or endpoint removals relative to master.
- All existing tests on master pass unchanged.
- New fallbacks are off by default for production (guarded by env/flags) and documented.
- CHANGELOG entry summarizing the fallbacks and guardrails.

Implementation plan
- Create branch `port-cursor-aug8` from `master`.
- Cherry-pick the minimal commits for fallbacks: `c243c03`, `1ef0be0`, extracting only the relevant hunks; prefer manual edits if cherry-pick conflicts.
- Optionally extract `main.py` lazy-import pattern and guarded config defaults from `1c45b1e` with care to avoid side effects.
- Add unit tests for selection fallback paths and pure-Python similarity.
- Open PR with clear rationale and risk assessment.

Labels
- enhancement, stability, tech-debt

Notes
- Branch `origin/CursorCloudAug8` appears behind master and includes sweeping deletions; wholesale merge is intentionally avoided.
