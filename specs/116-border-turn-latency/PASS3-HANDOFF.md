# Pass 2 → Pass 3 Handoff: Border Agent Turn Latency Fix

**From**: Pass 2 (this spec, 116-border-turn-latency, Linux Border-side)
**To**: Pass 3 (Mac-side, NetGeniusClaw Mobile phone app)
**Date**: 2026-08-16

## What changed

`bgp/federation/gateway.py::run_agent_turn()` no longer dispatches agent turns via a per-turn
`openclaw agent --json` CLI subprocess. It now uses a persistent WebSocket JSON-RPC connection
(`bgp/federation/gateway_ws.py`) to the same local gateway, the same way OpenClaw's own internal
`sessions_send` tool does. The root cause and full evidence trail are in
[`research.md`](./research.md); the fix's public contract (unchanged function signature, zero
required changes to any caller) is in [`contracts/run-agent-turn.md`](./contracts/run-agent-turn.md).

**Nothing on the phone or in the mobile app needed to change for this fix to take effect.** Every
existing caller (`chat.py`, `invocation.py`, `service.py`'s phone-facing `_edge_on_ask`) gets the
speedup automatically, with zero code changes on their side.

## The number that matters for your spoken-answer-window decision

| | Before (spec 115's recorded baseline) | After (measured live, this pass) |
|---|---|---|
| A trivial two-character answer, first turn in a brand-new session | 37.9s | **~9s** |
| The SAME conversation, second question onward | Also ~38s (no reuse at all) | **~3.9s** |

Spec 115 (Pass 1) chose an **18-second** spoken-answer window for Siri, tuned against the old
37.9s-and-never-faster baseline. That number was chosen when every turn — first, second, tenth —
cost the same and none of them fit inside 18 seconds anyway. That's no longer true on either count.
**Even the very first question in a brand-new conversation now lands around 9 seconds — comfortably
inside the existing window — and every question after that lands under 4 seconds.**

**What this means for Pass 3's decision**: the 18-second window was sized for a world where nothing
was ever fast enough to use it as a real target, only as an outer bound before falling back to "I'll
let you know when it answers." That world is gone. A window this generous may no longer be
necessary at all — even a substantially shorter one (perhaps 10-12 seconds) should now comfortably
cover the first question in a fresh conversation, with everything after landing in under 4 seconds.
Whether to shrink the window — and by how much — is explicitly a Pass 3 call to make against this
new data, not decided here (per spec 116's own Assumptions: "re-tuning that window is explicitly a
Pass 3 decision, to be made on the Mac against the evidence this pass produces"). Some things worth
weighing when you make that call:

- `session_key` for a phone conversation is `n2n-edge-{member_id}` (feature 067's design) — a fixed
  key per device, not per individual question — so in practice a phone's session stays "warm" across
  most real usage, and even the "cold" ~9s case only recurs after a Border restart or session reset.
- These numbers assume every configured MCP server actually responds promptly at startup. If a
  future server is added with a slow or misbehaving startup path (see "A note on what was actually
  slow" below for exactly this kind of bug), the cold-turn number could regress — `scripts/
  measure-turn-latency.py` is there to catch that early.

## A note on what was actually slow (revised mid-session — read this if you dig into `research.md`)

An earlier version of this document (and `research.md`) attributed the remaining ~26s cold-start
cost to OpenClaw's own vendored plugin-manifest-scanning code, calling it unfixable without patching
a third-party dependency. **That diagnosis was wrong**, caught and corrected the same day after
closer investigation: the entire ~26s cost was `pagerduty-mcp` retrying a failed PagerDuty API
key-validation request three times with growing sleeps (no `PAGERDUTY_USER_API_KEY` has ever been
configured on this host). It had nothing to do with OpenClaw's plugin system at all. Disabling
`pagerduty-mcp` (`mcp.servers.pagerduty-mcp.enabled: false`) eliminated the entire cost — see
`research.md`'s "CORRECTION" section for the full trace. **If a real PagerDuty account/key becomes
available, re-enable the server and re-run the measurement script first** — a valid key should make
that startup check succeed on the first try with no retries, but this hasn't been verified against a
real key yet.

## What else changed (smaller, but worth knowing)

- **Voice-aware answers exist now, but the phone doesn't use them yet.** `run_agent_turn()` accepts
  an optional `origin="voice"` parameter that gets a short, plain-spoken answer instead of the usual
  markdown-formatted one. The phone doesn't send this marker today — that's explicitly this spec's
  own Pass 3 item ("the mobile side begins sending it in Pass 3"). When you wire it up: for simple
  questions it works well (verified live: arithmetic, a fact question). For a question requiring the
  agent to synthesize a lot of structured data (e.g., "what's the Border's health status"), it can
  still come back as a full formatted report rather than 1-2 sentences — documented as a known
  edge case in `research.md`'s "US2 live verification" section, not something Pass 3 needs to fix,
  just something to expect if you test with a complex query.
- **No prioritization code was added.** Investigated and found unnecessary: the gateway already runs
  unrelated conversations fully concurrently (confirmed by direct measurement), and there's no
  actual background/scheduled caller in this codebase for an interactive phone question to compete
  against. If that changes later, it's worth revisiting — not now.

## Verification

`scripts/measure-turn-latency.py` — run it any time to get fresh numbers in the same format as
this document's table: fixed preparation time, a live trivial-turn timing, and (once phone traffic
exists in the recent log window) real phone-question durations. It's meant to be rerun by anyone,
anytime, without needing this conversation's context.

## Files touched

- `mcp-servers/protocol-mcp/bgp/federation/gateway.py` — dispatch mechanism swap, `origin` parameter
- `mcp-servers/protocol-mcp/bgp/federation/gateway_ws.py` — new, the persistent WS RPC client
- `mcp-servers/protocol-mcp/bgp/federation/chat.py` — one stale comment corrected
- `mcp-servers/rag-mcp/storage/chroma_store.py` — made `chromadb` client construction lazy
  (deferred to first real use instead of server startup), saving ~0.6s off every cold turn
- `mcp-servers/protocol-mcp/tests/` — new test suite (14 tests, all passing)
- `mcp-servers/protocol-mcp/pytest.ini` — new, minimal pytest config for the new suite
- `scripts/measure-turn-latency.py` — new, the committed measurement tool (FR-016a)
- `mcp-servers/protocol-mcp/README.md` — new section documenting the dispatch mechanism
- `~/.openclaw/openclaw.json` — `pagerduty-mcp` disabled (`enabled: false`); it was the entire
  remaining cold-start cost, not a plugin-scan issue (see "A note on what was actually slow" above).
  **Not tracked in this repo's git** (it's the live Border's own config), but recorded here since
  it's a real operational change this pass made. Re-enable once a real PagerDuty key exists.
- `specs/116-border-turn-latency/` — this spec's full artifact set (spec, plan, research, tasks,
  contracts, this handoff note)

**This handoff note is the signal that Pass 2 is complete and it's time to move back to the Mac.**
