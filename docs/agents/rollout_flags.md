Feature Flags and Rollout

Flags (env vars):
- `RAG_IN_LOOP`: enable RAG memory injection in GroupChat.
- `TRUE_STREAMING`: enable WebSocket streaming endpoints; when disabled, the endpoint returns a disabled status and closes.
- `SPEAKER_POLICY`: enable curated participant set for GroupChat.
- `GRAPHFLOW`: enable GraphFlow workflows API; health endpoint reports disabled when off.
- `HITL`: enable human-in-the-loop approval gates in GroupChat.
- `COST_SAFETY`: enable budget checks and security validation on prompts.

Rollout strategy:
- Dev: enable all flags and validate happy paths with mock data.
- Staging: enable `TRUE_STREAMING` and `GRAPHFLOW` for internal users; keep `HITL` opt-in.
- Prod: progressive enablement per feature with monitoring and rollback via flags.

Rollback:
- Toggle flag to false and redeploy. Components are coded to short-circuit gracefully when disabled.

