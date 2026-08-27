# Contract: `zoom-rtms-mcp` MCP Tool Surface

Standard FastMCP tool contract, following the same `tools/list` / `tools/call` JSON-RPC lifecycle as
every other NetGeniusClaw MCP server (Constitution Principle V). This is the on-demand query surface for
the agent and operator; it is separate from the autonomous recognition path (research.md R1/R2),
which runs inside the server regardless of whether any tool here is ever called.

## `zoom_enable_listening`

Enable RTMS listening for a meeting.

- **Input**: `{ "meeting_id": string }`
- **Output**: `{ "meeting_uuid": string, "listening_enabled": true }`
- **Errors**: `not_authorized` (FR-001 access boundary — reuses whatever operator-access model
  already gates other NetGeniusClaw operations, per spec Assumptions), `rtms_unavailable` (Zoom account/app
  doesn't have RTMS entitlement).

## `zoom_disable_listening`

- **Input**: `{ "meeting_uuid": string }`
- **Output**: `{ "listening_enabled": false }`
- **Effect**: Destroys the `MeetingSession` and its `LiveContextBuffer` immediately (FR-014).

## `zoom_list_active_meetings`

- **Input**: `{}`
- **Output**: `{ "meetings": [ { "meeting_uuid", "started_at", "connection_state" } ] }`
- **Purpose**: FR-015 — see which meetings currently have listening enabled.

## `zoom_meeting_status`

- **Input**: `{ "meeting_uuid": string }`
- **Output**: `{ "connection_state", "avatar_state", "participant_count" }`

## `zoom_recent_transcript`

- **Input**: `{ "meeting_uuid": string, "minutes": number (default: buffer max) }`
- **Output**: `{ "entries": [ TranscriptEntry, ... ] }` (see data-model.md)

## `zoom_recent_chat`

- **Input**: `{ "meeting_uuid": string, "minutes": number }`
- **Output**: `{ "entries": [ ChatEntry, ... ] }`

## `zoom_active_speaker`

- **Input**: `{ "meeting_uuid": string }`
- **Output**: `{ "participant_id": string \| null }`

## `zoom_live_context`

Convenience aggregate of the above four, for a single call when the agent wants "what's going on in
this meeting right now."

- **Input**: `{ "meeting_uuid": string }`
- **Output**: `{ "connection_state", "avatar_state", "recent_transcript": [...], "recent_chat": [...],
  "active_speaker": string \| null, "current_investigation": InvestigationRequest \| null }`

## `zoom_search_historical_meetings`

Thin pass-through to the official Zoom Meetings MCP (research.md R6) — included here only so the
zoom-meeting-context skill has one place to call regardless of which MCP actually answers; exact
Zoom MCP tool name(s) TBD at implementation time.

- **Input**: `{ "query": string, "time_hint": string \| null }`
- **Output**: `{ "matches": [ HistoricalMeetingReference, ... ] }` — see data-model.md; never persisted
  locally.
