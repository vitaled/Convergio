Streaming WebSocket Protocol (WS3)

Overview: Real-time streaming of agent responses over WebSocket with granular events, backpressure, and heartbeat.

Endpoint: `GET /api/agents/ws/streaming/{user_id}/{agent_name}`

Client → Server message:
- JSON with keys:
  - `message`: user text prompt
  - `context`: optional object with extra context

Server → Client events: All frames are JSON with keys `type`, `event`, `data`.
- `status`:`session_created` — session established; includes optional `context`.
- `agent_status` — thinking/typing indicator with a short message.
- `delta` — incremental text chunk of the agent reply.
- `tool_call` — tool invocation details `{tool, arguments}` as stringified JSON.
- `tool_result` — tool result payload as string.
- `handoff` — signal of agent handoff target `handoff_to:{agent}`.
- `final` — completion marker indicating the turn is complete.
- `status`:`heartbeat` — periodic keep-alive with session status metadata.
- `error` — error payload with `message`.

Backpressure: The server buffers a small number of chunks (window size 5) and flushes early for non-text events to keep latency low.

Feature flag: The endpoint respects `TRUE_STREAMING`. When disabled, the connection is closed with a `disabled` status event.

Example server frame:
{
  "type": "streaming_response",
  "event": "delta",
  "data": {
    "chunk_id": "...",
    "session_id": "...",
    "agent_name": "ali_chief_of_staff",
    "chunk_type": "text",
    "content": "Strategically, we should…",
    "timestamp": "2025-08-08T20:00:00Z"
  }
}

Error handling: On internal errors, the server emits an `error` event and attempts graceful session closure.

