# Contract: Zoom App Panel Feed (`zoom-rtms-mcp` companion WebSocket ↔ `ui/netclaw-zoom-app`)

A presentation-layer-only WebSocket between the browser-embedded Zoom App and `zoom-rtms-mcp`'s
companion endpoint (research.md R3). Explicitly does not touch NCFED, GAIT, or peer trust — this is
NetGeniusClaw's own equivalent of any other web app's "live status" socket.

## Connection

The Zoom App, on load (`zoomSdk.config()` / `getRunningContext()`), opens one connection per
`meeting_uuid` it's running inside. Supports Collaborate Mode (research: Collaborate UUID from
`onCollaborateChange`) and Guest Mode (unauthenticated viewers) per FR-011/FR-012 — the feed itself
does not distinguish host from guest; every open connection for a given `meeting_uuid` receives
identical pushes (SC-004: no separate state per viewer).

## Server → client pushes

```json
{ "type": "avatar_state", "meeting_uuid": "...", "state": "listening|thinking|investigating|answered" }
{ "type": "topic_detected", "meeting_uuid": "...", "location": "...", "technology": "...", "time_window": "..." }
{ "type": "investigation_result", "meeting_uuid": "...", "request_id": "...", "answer_summary": "...", "evidence_refs": [...] }
{ "type": "connection_state", "meeting_uuid": "...", "state": "connecting|live|degraded|closed" }
```

`connection_state: degraded` is how the edge case "RTMS connection drops mid-meeting" becomes visible
in the panel rather than silently looking like normal listening continues.

## Client → server messages

```json
{ "type": "viewer_joined", "meeting_uuid": "...", "participant_id": "..." }
{ "type": "camera_overlay_enable", "meeting_uuid": "...", "participant_id": "..." }
{ "type": "camera_overlay_disable", "meeting_uuid": "...", "participant_id": "..." }
```

`camera_overlay_enable`/`disable` only ever apply to the sending participant's own feed (FR-018/
FR-019) — the server never accepts a participant_id other than the one the connection authenticated
as via the Zoom Apps SDK context, closing off the edge case of one participant toggling another's
overlay.

## Camera overlay (User Story 5)

On `camera_overlay_enable`, the Zoom App frontend invokes the Zoom Apps SDK's Layers API Camera mode
(exact call signature confirmed against the Zoom Apps SDK reference at implementation time — research
md R8 flags that Camera mode requires the Controller-mode component and app review) to render the
current `avatar_state` as a small overlay on that participant's own outgoing video. The overlay
content is driven by the same `avatar_state` push already being sent to the panel — one state,
two renderings, never out of sync (SC-009).
