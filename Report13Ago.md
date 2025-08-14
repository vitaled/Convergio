## Convergio AutoGen Excellence Program (Action Plan)
Date: 2025-08-13
Owner: Full‑stack/Agents Lead

Links: Microsoft AutoGen (stable) [docs](https://microsoft.github.io/autogen/stable//index.html) · Vision [WhatIsConvergio.md](AgenticManifesto/WhatIsConvergio.md)

### Goal
Make Convergio a top‑tier multi‑agent PM+Intelligence platform: Ali orchestrates teams via AutoGen, data‑source choices are cost/safety‑aware, collaboration is contextual, and UX shows decisions, tools, costs, and outcomes.

### KPIs
- TTFA (P50/P95) ≤ 2.0s / ≤ 6.0s
- Multi‑agent scenario pass ≥ 90%
- Source decision accuracy ≥ 95%
- Cost prediction error ≤ 10%
- UX task completion ≥ 95%

### Status & Key Learnings (updated)
- Wave 1: core implemented
  - DecisionEngine + DecisionPlan integrati nel GroupChat runner (flag `DECISION_ENGINE_ENABLED`).
  - Tool executor onora il piano (web‑first quando richiesto).
  - Test base per DecisionEngine e runner aggiunti; lint pulito.
  - CostTracker esteso con analytics per turno/conversazione.
- Wave 2: avviato
  - Per‑turn RAG: aggiunto scratchpad condiviso e conflict hooks leggeri.
- Key learnings
  - Passare il piano via metadata consente integrazione non‑invasiva con AutoGen.
  - Gating sicurezza rimane uniforme; feature flags evitano regressioni.
  - Telemetria JSON è essenziale per la timeline UI.

### Execution Order (prioritized, tangible shipments)
Wave 1 (2 weeks)
- M1 Decision Engine + Orchestrator v2 (include security gating subset) + M3 Scenario Tests (in parallel)
- Ship: deterministic orchestration with DecisionPlan, cost/budget guardrails, golden tests passing, telemetry `decision_made/tool_invoked` live

Wave 2 (1 week)
- M2 Per‑Turn RAG + Shared Context
- Ship: higher‑quality multi‑agent answers, scratchpad in place, conflict resolution hooks

Wave 3 (2 weeks)
- M4 Frontend Operational UX
- Ship: Agent CRUD, timeline per‑turn (speaker/tools/fonti/costi/razionali), run panel; a11y ≥95

Wave 4 (1 week)
- M5 Governance/Safety/Ops (rate limits + dashboards + runbook)
- Ship: rate limiting, SLO dashboards, on‑call runbook; redaction already active from Wave 1

Wave 5 (2 weeks)
- M6 AutoGen Workflow Generator (GraphFlow)
- Ship: creare/eseguire workflow da template con UI Workflows; eventi `workflow_*` e audit per step

Wave 6 (1 week)
- M7 Agent Lifecycle & Scale
- Ship: schema/lint MD 100%, hot‑reload robusto, guida “create‑agent”

Wave 7 (3 weeks)
- M8 Frontend PM & Intelligence
- Ship: Progetti/Epiche/Task/Risorse/Dipendenze, viste Gantt/Kanban/Calendar/Resource, analytics navigabili, attach agent per task

Wave 8 (2 weeks)
- M10 Ali Proattivo & Insight Engine
- Ship: coach panel con suggerimenti contestuali e explain‑why, notifiche digest

Wave 9 (2 weeks)
- M11 Modello Dati Personalizzabile
- Ship: custom fields/template per domini diversi; UI renderer dinamico

Wave 10 (3 weeks)
- M9 SaaS Multi‑tenancy & Billing per Agente
- Ship: multitenant isolato, metering ±2%, piani+Stripe test mode, fatture per agente

---

## M1: Decision Engine + Orchestrator v2 (2 weeks)
Why: Replace keyword routing with semantic, cost/safety‑aware plans consumati da AutoGen.
Deliverables: DecisionEngine → `DecisionPlan`; Ali usa IntelligentSpeakerSelector; tool path deterministico; budget guardrails.
Tasks: implement scoring (backend/vector/web/LLM), stimatore costi, wiring con GroupChat/Handoff, fallback e redaction.
Acceptance: ≥95% decision accuracy; cost error ≤10%; scenario tests verdi; eventi `decision_made/tool_invoked/budget_event` emessi.

---

## M2: Per‑Turn RAG + Shared Context (1 week)
Why: Collaborazione reale richiede contesto aggiornato e scratchpad condiviso.
Deliverables: per‑turn RAG on by default con cache; scratchpad append‑only; conflict detector.
Acceptance: +latency ≤20%; context hit‑rate ≥70%; conflitti −50%; eventi `rag_injected/conflict_*` emessi.

---

## M3: Scenario Tests (1 week, in parallelo)
Deliverables: 12 scenari (strategy/finance/tech/product/marketing) con golden assertions per decisioni, tool order, cost/latency, failure modes.
Acceptance: ≥90% pass, flaky <2%, artefatti JUnit/HTML, diff golden.

---

## M4: Frontend Operational UX (2 weeks)
Deliverables: Agent CRUD; timeline per‑turn (speaker, strumenti, fonti, costi, razionali); run panel (budget/tokens/errori/partecipanti); a11y ≥95.
Acceptance: 95% eventi telemetria visibili; valori UI ~ backend ±5%.

---

## M5: Governance, Safety, Ops (1 week)
Deliverables: redaction+allow‑list, rate limits, SLO dashboards, runbook.
Acceptance: leakage=0 nei test sintetici; 429 graceful; dashboard live.

---

## M6: AutoGen Workflow Generator (GraphFlow) (2 weeks)

Deliverables
- NL→Workflow Generator: da prompt/PRD a `BusinessWorkflow` (steps, I/O, dipendenze)
- Registry & lifecycle: CRUD, versioni, abilitazione/disabilitazione, tagging
- Safety: gating `AISecurityGuardian` su prompt di step e transizioni
- E2E: API `/api/v1/workflows` complete con esecuzione/monitoraggio/cancel

Tasks: generator NL→workflow + libreria step; registry (CRUD/versioni) + exec (run/status/cancel); safety guardian su step; eventi `workflow_*`; UI pagina Workflows.
Acceptance: 5 template eseguibili senza fix; injection tests verdi; timeline transizioni visibili.

---

## M7: Agent Lifecycle & Scale (1 week)

Deliverables
- Schema metadata agenti (MD front‑matter) con validazione
- Prompt linter per system messages, tag/tier/capabilities registry
- Hot‑reload affidabile + watcher; policy tool dinamiche
- Guida “aggiungi un nuovo agente” + API/UX curate

Tasks: schema+lint MD; watcher+rollback; policy tool per dominio; comandi “create‑agent” + guida.
Acceptance: 100% MD validi; reload <1s; onboarding <15 min.

## M8: Frontend PM & Intelligence (3 weeks)
Deliverables: 
- Domini PM: Progetti, Epiche, Task/Subtask, Risorse, Dipendenze, Stati/SLAs
- Viste: Gantt/Timeline, Kanban, Calendar, Resource board, Analytics (costi/latency/quality)
- AI per task: “Attach agent” per task (routing a specialisti), suggerimenti, auto‑workflow (GraphFlow) e tool logs
- Conversazioni collegate al task (thread + decisioni + costi + fonti)
Acceptance:
- CRUD completo e relazioni; drag&drop board; filtri/saved views; perf P95 < 150ms nav
- Per task: assegnazione agente, esecuzione strumenti con telemetria, decision rationale visibile
- Analytics: dashboard progetto con KPIs (costi, velocity, quality); export CSV/JSON
- A11y ≥95; e2e su flussi PM critici (create→track→close)

## M9: SaaS Multi‑tenancy & Billing per Agente (3 weeks)
Deliverables:
- Tenancy: modello tenant+org+user, RLS Postgres (o schema‑per‑tenant), API keys per tenant, audit trail
- Usage metering: eventi per agent/tool/conversation con token/costo/time; attribuzione per task/progetto
- Billing: piani (Free/Pro/Enterprise), quote/overage, Stripe (portal, invoices, webhooks), fatture con righe per agente
- Admin: dashboard tenant usage/costi, alert soglie, export
Acceptance: isolamento validato (RLS tests); accuracy metering ±2%; Stripe e2e in test mode; overage/quote enforce; audit completo

## M10: Ali Proattivo & Insight Engine (2 weeks)
Deliverables:
- Event bus (domain events: task_changed, risk_detected, budget_event, deadline_near)
- Insight rules + heuristiche LLM per raccomandazioni (priorità, rischi, dipendenze, budget)
- Coach panel in UI: suggerimenti, one‑click actions, explain‑why
- Notifiche: digest giornaliero/settimanale, canali (in‑app/email/webhook)
Acceptance: ≥80% suggerimenti valutati utili; TTS (time‑to‑suggestion) < 2s; opt‑in/privacy; zero spam (rate limit)

## M11: Modello Dati Personalizzabile (2 weeks)
Deliverables:
- Custom fields: JSONB + registry schema per Progetti/Task/Resource; validazioni
- UI renderer: form/board base su schema, viste salvate per template (IT, marketing, legal, ecc.)
- Template library: clona/modifica template; migrazioni
- API typed docs con campi custom; export/import
Acceptance: crea template nuovo, aggiungi campi, viste operative; validazioni lato API/UI; e2e template → delivery

---

## Tracking, Cleanup & Rollout
Status: planned | in‑progress | blocked | review | done. DoD: green tests, telemetria in dashboard, docs aggiornate.
Cleanup: unifica client OpenAI, gating sicurezza ovunque, rimuovi percorsi legacy post‑canary.
Rollout: canary 5%→25%→100%, feature flags (DecisionEngine/PerTurnRAG/RunPanel/Safety/Workflows), revert via toggle.

---

## Appendix A — Acceptance (quick)
- DecisionEngine: ≥95% accuracy; rationale JSON
- Orchestrator v2: IntelligentSpeakerSelector; honors DecisionPlan
- Per‑turn RAG: hit ≥70%; latency in target; conflict tests
- Frontend Ops UX: Agent CRUD; timeline strumenti/fonti/costi/razionali
- Safety/Ops: redaction pass; rate limits; dashboards live
- GraphFlow Generator: 5 template ok; eventi step/edge in UI
- Agent Lifecycle: 100% MD validi; hot‑reload+rollback; guida aggiornata
- PM & Intelligence: CRUD domini, viste, attach agent per task, analytics KPI
- SaaS & Billing: isolamento tenant (RLS), accuracy metering ±2%, Stripe e2e, overage/quote
- Ali Proattivo: ≥80% utilità, TTS <2s, explain‑why
- Dati Custom: template+campi custom funzionanti, validazioni e API typed

## Developer Playbooks (concise, safe for juniors)

M1 Decision Engine + Orchestrator v2
- Files to create/edit: 
  - `backend/src/agents/services/decision_engine.py` (new)
  - `backend/src/agents/services/autogen_groupchat_orchestrator.py`
  - `backend/src/agents/services/groupchat/tool_executor.py`
  - `backend/src/agents/utils/config.py` (feature flags)
- Steps:
  1) Implement `DecisionPlan` dataclass and `DecisionEngine.plan(message, context)` returning sources/tools/model/max_turns/budget/rationale.
  2) In orchestrator, call `DecisionEngine` before GroupChat; pass plan to team (model_client, max_turns) e a `GroupChatToolExecutor`.
  3) Emit telemetry: `decision_made`, `tool_invoked`, `budget_event` (JSON). Keep original behavior behind flag.
- Tests: `tests/integration/test_decision_engine.py` (accuracy), `tests/integration/test_orchestrator_plan.py`.
- Flags/Rollout: `DECISION_ENGINE_ENABLED=true` canary 5%→25%→100%.
- Safety: call `AISecurityGuardian.validate_prompt` prima di tool/LLM.

M2 Per‑Turn RAG + Shared Context
- Files: `backend/src/agents/services/groupchat/per_turn_rag.py`, `backend/src/agents/services/groupchat/setup.py`.
- Steps: enable injector globally, add scratchpad (dict) to conversation context, add conflict detector utility.
- Tests: `tests/integration/test_per_turn_rag.py` (latency, hit‑rate), `tests/integration/test_conflict_resolution.py`.
- Flag: `RAG_IN_LOOP_ENABLED=true`.

M3 Scenario Tests (golden/failure)
- Files: `tests/integration/test_scenarios/*.py`, `tests/integration/fixtures/scenarios.yaml`.
- Steps: define 12 scenari, golden outputs, assert tool order, source choice, costs/latency; add failure mocks (timeouts, empty results).
- Artifacts: JUnit, HTML, golden diffs.

M4 Frontend Operational UX
- Files: `frontend/src/routes/(app)/agent-management/+page.svelte`, `frontend/src/lib/components/RunPanel.svelte` (new), `frontend/src/lib/components/Timeline.svelte` (new), `frontend/src/lib/stores/telemetry.ts` (new).
- Steps: 
  1) Abilitare Agent CRUD (usa `/api/v1/agent-management`).
  2) Timeline per‑turn (speaker, tools, fonti, costi, rationale) consumando `/api/v1/telemetry` (se non esiste, stub via websocket existing).
  3) Run panel (budget/tokens/error/fallback); a11y.
- Tests: `frontend/tests/e2e/ops-ui.spec.ts` (timeline/panel), `frontend/tests/accessibility.spec.ts`.
- Flag: `OPS_UI_ENABLED=true`.

M5 Governance/Safety/Ops
- Files: `backend/src/agents/security/ai_security_guardian.py` (ensure gating), `backend/src/core/rate_limit.py` (new), `backend/src/main.py` (middleware), dashboards (Grafana json).
- Steps: rate limiting per IP/user/tool; redaction in tool executor; export metrics.
- Tests: `tests/security/test_injection_and_redaction.py`, `tests/performance/test_rate_limits.py`.

M6 AutoGen Workflow Generator (GraphFlow)
- Files: `backend/src/agents/services/graphflow/generator.py` (new), `backend/src/api/workflows.py` (extend), UI `frontend/src/routes/(app)/workflows/+page.svelte` (new).
- Steps: generator NL→`BusinessWorkflow`; registry CRUD/version; run/status/cancel; eventi `workflow_*`.
- Tests: `tests/integration/test_workflow_generator.py`, `frontend/tests/e2e/workflows.spec.ts`.

M7 Agent Lifecycle & Scale
- Files: `backend/src/agents/definitions/agent.schema.json` (new), `backend/scripts/agent_lint.py` (new), `backend/src/agents/services/agent_loader.py` (watcher/rollback), docs `docs/AGENTS.md` (new).
- Steps: validazione front‑matter MD, linter prompt, watcher con rollback se invalid; comando “create‑agent”.
- Tests: `tests/backend/unit/test_agent_schema.py`.

M8 Frontend PM & Intelligence
- Files: backend models/API (`backend/src/models/{project,epic,task,resource}.py`, `backend/src/api/projects.py`), migrations; UI pages (`frontend/src/routes/(app)/projects/...`), components (Gantt/Kanban/Calendar), `frontend/src/lib/components/AttachAgentToTask.svelte`.
- Steps: CRUD domini, viste, attach agent→esecuzione tool/telemetria; analytics KPI.
- Tests: e2e su create→track→close; unit serpentine perf.

M9 SaaS Multi‑tenancy & Billing per Agente
- Files: migrations add `tenant_id`, RLS policies; `backend/src/core/tenancy.py` (new), `backend/src/api/billing.py` (new), Stripe server hooks; admin UI `frontend/src/routes/(app)/admin/billing/+page.svelte`.
- Steps: isolare dati per tenant; metering eventi; integrazione Stripe (test mode), piani/quote/overage.
- Tests: tenancy isolation tests; metering accuracy; Stripe webhook tests.

M10 Ali Proattivo & Insight Engine
- Files: `backend/src/core/events.py` (new), `backend/src/agents/services/insights.py` (new), UI `frontend/src/lib/components/AliCoachPanel.svelte`.
- Steps: domain events, regole/LLM insights, suggerimenti contestuali con explain‑why e azioni one‑click.
- Tests: utility score ≥0.8, rate limit anti‑spam.

M11 Modello Dati Personalizzabile
- Files: JSONB fields + registry `backend/src/core/custom_fields.py` (new), API `backend/src/api/customization.py` (new), UI renderer `frontend/src/lib/components/CustomFormRenderer.svelte`.
- Steps: aggiungi campi custom per progetto/task/resource; viste su schema; template library.
- Tests: validazioni API/UI; e2e template→delivery.

Note operative
- Sempre dietro feature flag; PR piccole; canary + revert; aggiungere test e telemetria in ogni PR.
- Non rimuovere codice legacy finché la Wave non è al 100% su canary.


