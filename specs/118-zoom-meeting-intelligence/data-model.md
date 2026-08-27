# Data Model: NetGeniusClaw for Zoom — Meeting Intelligence (MVP)

All entities below are in-memory only unless noted. Nothing in this feature introduces a new
database — consistent with `docs/ADDING-AN-MCP.md` precedent (most recent NetGeniusClaw integrations are
`N/A (stateless / in-memory)`), and with spec's own Assumptions section.

## MeetingSession

Held in `zoom-rtms-mcp` process memory, keyed by `meeting_uuid`. One per Zoom meeting currently
being listened to.

| Field | Type | Notes |
|---|---|---|
| `meeting_uuid` | string | Zoom's meeting UUID (RTMS webhook payload) |
| `listening_enabled` | bool | Set false by explicit disable (FR-015); triggers buffer discard |
| `started_at` | timestamp | RTMS stream start |
| `ended_at` | timestamp \| null | Set on meeting-end webhook or explicit disable |
| `connection_state` | enum: `connecting` \| `live` \| `degraded` \| `closed` | `degraded` when the RTMS WS drops but the session hasn't been explicitly ended (edge case: connection drop) |
| `viewers` | set of Zoom participant IDs | Who has opened the shared panel — for SC-004 verification, not access control |
| `avatar_state` | enum: `listening` \| `thinking` \| `investigating` \| `answered` | Mirrored to the panel and any active camera overlays (FR-017/FR-020) |
| `camera_overlay_enrollments` | set of participant IDs | Per FR-018/FR-019 — never implies enrollment for anyone else |

**Lifecycle**: created on RTMS stream start → `listening_enabled=true`, `connection_state=live`.
Destroyed (not merely marked ended) when the meeting ends or listening is explicitly disabled
(FR-014) — this is what "discard the live buffer" means concretely: the Python object and its
`LiveContextBuffer` are dropped, not soft-deleted.

## LiveContextBuffer

One per `MeetingSession`, held in the same process memory. A bounded ring buffer: **the last 15
minutes of activity, capped at 500 entries, whichever limit is reached first** — pinned at
`/speckit.analyze` remediation time (2026-08-17) in place of the earlier "TBD at tasks time" note,
informed by the "recent minutes" framing in the spec's Assumptions. Both bounds are enforced
together so a very high-chat-volume meeting doesn't grow unbounded before 15 minutes elapse.

| Field | Type | Notes |
|---|---|---|
| `entries` | ordered list of `TranscriptEntry` \| `ChatEntry` \| `SpeakerChangeEntry` \| `ContentEntry` | Bounded — oldest entries drop as new ones arrive |

`TranscriptEntry`: `{timestamp, participant_id, participant_name, text}`
`ChatEntry`: `{timestamp, participant_id, participant_name, text}`
`SpeakerChangeEntry`: `{timestamp, participant_id}`
`ContentEntry`: `{timestamp, kind: "screen_share_started"|"screen_share_ended", participant_id}`

## InvestigationRequest

Created by the new Border-side handler (`bgp/federation/zoom_channel.py`) when `zoom-rtms-mcp`'s
extractor (research.md R2) forwards a recognized request. Recorded in NetGeniusClaw's existing GAIT audit
trail (Constitution Principle IV) — not a new database, an append to the existing mechanism.

| Field | Type | Notes |
|---|---|---|
| `request_id` | string (uuid) | |
| `meeting_uuid` | string | Links back to the `MeetingSession` at the time of the request |
| `source` | enum: `speech` \| `chat` | Edge case: identical speech+chat within the same moment collapses to one `InvestigationRequest`, not two |
| `raw_text` | string | The utterance/message that triggered recognition |
| `location` | string \| null | Extracted; null if unresolvable (edge case) |
| `technology` | string \| null | Extracted |
| `time_window` | string \| null | Extracted, approximate (e.g. "~10 minutes") |
| `session_key` | string | `n2n-zoom-{meeting_uuid}` — passed to `run_agent_turn` (research.md R1) |
| `routing_outcome` | enum: `answered` \| `failed_no_tooling` \| `failed_ambiguous` | FR-004/edge cases |
| `answer_summary` | string \| null | Synthesized answer text, once available |
| `evidence_refs` | list of strings | Pointers to what was checked (tool/output references), not raw tool output itself (FR-005) |
| `write_action_detected` | bool | True if the underlying agent turn attempted a configuration-changing action — links to `ApprovalDecision` |

## ApprovalDecision

Only exists when `write_action_detected=true` on an `InvestigationRequest`. This is **not** a new
approval mechanism — it is a reference to whatever existing device-write approval record NetGeniusClaw's
underlying vendor skill/MCP already produces (Constitution Principles I–III), tagged with the
originating `request_id` so the two are correlatable in the audit trail (FR-013, SC-007).

| Field | Type | Notes |
|---|---|---|
| `request_id` | string | FK to `InvestigationRequest` |
| `existing_approval_ref` | string | Whatever identifier NetGeniusClaw's existing approval record already uses (CR number, `approval_id`, etc. — mechanism unchanged, per research.md R7) |
| `decision` | enum: `approved` \| `denied` \| `expired` \| `pending` | Mirrors the existing approval record's own status |

## HistoricalMeetingReference

**Not persisted anywhere by NetGeniusClaw.** Fetched live from the official Zoom Meetings MCP (research.md
R6) each time User Story 2 is exercised — this is external Zoom data (transcripts, assets,
recordings) referenced by ID, the same "stateless proxy to an external API" treatment as most other
NetGeniusClaw MCP integrations (e.g. `azure-network-mcp`: "N/A, reads from Azure ARM APIs").

| Field (as returned by Zoom MCP, shape TBD at implementation) | Notes |
|---|---|
| meeting identifier | Used to correlate with `InvestigationRequest.meeting_uuid` when the current meeting itself is later searchable |
| relevant transcript/asset excerpt | Surfaced in the shared panel, not stored |

## State Transitions

```
MeetingSession.connection_state:
  connecting -> live        (RTMS stream established)
  live -> degraded          (RTMS WS drop, session not explicitly ended)
  degraded -> live          (RTMS WS reconnects)
  live|degraded -> closed   (meeting-end webhook OR explicit disable) -> object destroyed

MeetingSession.avatar_state:
  listening -> thinking       (extractor recognizes a request, before routing)
  thinking -> investigating   (Border-side handler dispatches run_agent_turn)
  investigating -> answered   (result pushed back)
  answered -> listening       (next utterance arrives)

InvestigationRequest.routing_outcome:
  (created) -> answered | failed_no_tooling | failed_ambiguous   (terminal, one transition)
```
