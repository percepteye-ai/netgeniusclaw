# Contract: Border-side Zoom Channel (`bgp/federation/zoom_channel.py`)

A loopback-only, restricted-method channel between `zoom-rtms-mcp` and the Border federation daemon,
modeled on `edge.py`'s `EdgeChannel`/`EDGE_METHODS` pattern (feature 066) but scoped to a local process
on the same host rather than a remote, independently-enrolled device (research.md R1). JSON-RPC 2.0
messages, matching every other NCFED channel's framing convention.

## Method allowlist: `ZOOM_METHODS`

Mirroring `EDGE_METHODS`'s explicit-allowlist shape — a method not in this list is never dispatched,
regardless of what's registered:

```
"n2n/zoom/investigate"        # zoom-rtms-mcp -> Border, request 1
"n2n/zoom/investigate_result" # Border -> zoom-rtms-mcp, push (best-effort)
"n2n/zoom/session_closed"     # zoom-rtms-mcp -> Border, notify (fire-and-forget)
```

## `n2n/zoom/investigate` (zoom-rtms-mcp → Border, request)

Sent only after the in-server extractor (research.md R2) has already classified the utterance as a
present-tense, first-person investigation request — this method is never called for a
hypothetical/past-tense/third-party remark (FR-009 is enforced by never sending the request, not by
the Border side filtering it out).

- **Params**:
  ```json
  {
    "request_id": "uuid",
    "meeting_uuid": "string",
    "source": "speech | chat",
    "raw_text": "string",
    "location": "string | null",
    "technology": "string | null",
    "time_window": "string | null"
  }
  ```
- **Border behavior**: constructs a prompt from the extracted fields, calls
  `run_agent_turn(prompt=..., session_key=f"n2n-zoom-{meeting_uuid}")` (research.md R1, mirroring
  `chat.py`'s autonomous-turn pattern), records an `InvestigationRequest` (data-model.md) and emits it
  to GAIT (FR-013). Returns immediately with `{ "accepted": true, "request_id": "uuid" }` — the actual
  answer arrives asynchronously via `n2n/zoom/investigate_result`, mirroring how `n2n/edge/ask` +
  `n2n/edge/ask_result` are split into request/push halves for mobile (feature 067).
- **Errors**: `no_tooling_available` (FR-004 edge case — no registered Member Claw can answer this),
  `ambiguous_reference` (location/technology unresolvable, edge case).

## `n2n/zoom/investigate_result` (Border → zoom-rtms-mcp, push, best-effort)

- **Params**:
  ```json
  {
    "request_id": "uuid",
    "routing_outcome": "answered | failed_no_tooling | failed_ambiguous",
    "answer_summary": "string | null",
    "evidence_refs": ["string", ...],
    "write_action_detected": false,
    "approval_ref": "string | null"
  }
  ```
- **zoom-rtms-mcp behavior**: updates the `MeetingSession.avatar_state` to `answered`, stores the
  result for `zoom_live_context`/panel delivery, pushes it down the browser-facing WebSocket
  (research.md R3) for every current viewer at once (FR-011, SC-004).
- **Delivery semantics**: best-effort, matching `n2n/edge/task_progress`'s precedent — a
  `zoom-rtms-mcp` that has restarted mid-flight simply never gets the push; the panel shows the
  investigation as still in progress rather than erroring, and the audit record (Border-side,
  independent of this push) remains authoritative regardless (SC-007).

## `n2n/zoom/session_closed` (zoom-rtms-mcp → Border, notify, fire-and-forget)

- **Params**: `{ "meeting_uuid": "string" }`
- **Border behavior**: no state to clean up Border-side beyond closing out any still-`pending`
  `InvestigationRequest` for that meeting as `failed_no_tooling`-equivalent ("meeting ended before
  answer") in the audit trail — the live buffer itself was already destroyed on the `zoom-rtms-mcp`
  side per FR-014 before this notify is even sent.
