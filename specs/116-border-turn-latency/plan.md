# Implementation Plan: Border Agent Turn Latency + Voice-Aware Answers (Pass 2 of 3)

**Branch**: `116-border-turn-latency` | **Date**: 2026-08-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/116-border-turn-latency/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Every NetGeniusClaw turn — regardless of channel or answer length — pays a fixed ~27s tax before any
real work starts. Phase 0 research (below) traced it to a single root cause: `run_agent_turn()` in
`bgp/federation/gateway.py` invokes the agent via the `openclaw agent` CLI, whose gateway dispatch
path (`agent-via-gateway-BB-FX7EM.js`) unconditionally passes `cleanupBundleMcpOnRunEnd: true` on
every call. That flag tears down the session's entire MCP tool runtime — including a full
disk scan across 69 registered plugin manifests and a fresh spawn+handshake of every configured
MCP server — at the end of every turn, so the next turn always rebuilds from cold, even in the same
session, even in the long-lived gateway process. OpenClaw's own internal `sessions_send`/
`runAgentStep` path (`openclaw-tools-DnJ9m035.js`) proves the runtime CAN be kept warm across turns
— it simply omits this flag. The fix is entirely on NetGeniusClaw's side of the boundary: switch
`run_agent_turn()`'s gateway dispatch from CLI-per-turn to a persistent WebSocket RPC connection
that calls the gateway's own `agent` method the same way `sessions_send` does, without forcing
teardown. Voice-aware answer composition (US2) and interactive-over-background prioritisation (US3)
are additive on top of that fix and do not depend on it structurally.

## Technical Context

**Language/Version**: Python 3.10+ (matches `bgp/federation/*`, specs 052–115); no new language.
**Primary Dependencies**: `websockets` (new — Border-side persistent WS client to the OpenClaw
  gateway's JSON-RPC-over-WebSocket protocol, replacing the per-turn `openclaw agent` CLI subprocess
  in `gateway.py::run_agent_turn()`); existing `bgp/federation/*` modules (gateway.py, chat.py,
  invocation.py, service.py — all current CLI callers); no new Node.js/TypeScript code — the
  OpenClaw gateway itself (`~/.nvm/.../openclaw/dist/*.js`) is a vendored dependency, read-only,
  not modified by this feature (evidence gathered by reading its bundled source, not by patching it).
**Storage**: N/A (stateless; no new persistent state — this is a runtime dispatch/performance fix)
**Testing**: pytest (existing convention for `mcp-servers/protocol-mcp`); a new committed
  measurement script (FR-016a) invokable standalone, not just as a pytest case.
**Target Platform**: Linux server (the Border host; matches every dependent spec since 052)
**Project Type**: Single project — extends the existing `bgp/federation/*` daemon package.
**Performance Goals**: SC-001 (<12s trivial-turn end-to-end, from a measured 37.9s baseline),
  SC-002 (<3s fixed preparation, from a measured 26.8s baseline), SC-004 (≥3× median improvement
  on real phone-question durations, from a measured 36s–452s range).
**Constraints**: FR-004/FR-004a — zero permanent capability loss; any first-use warm-up cost must be
  one-time per session, not recurring. FR-006 — must not serve an indefinitely stale tool set when
  NetGeniusClaw's own MCP config changes at runtime. FR-008/SC-006 — the optional origin marker (US2) must
  be fully backward compatible; zero observable change for callers that don't send it.
**Scale/Scope**: 8 configured MCP servers today (fortinet, gait, memory, n2n, pagerduty, rag,
  twilio-voice, twitter) plus 3 enabled plugins (defenseclaw, memory-core, slack) out of 69
  registered — the fixed cost scales with total registered plugins scanned per turn, not with how
  many are enabled, which is itself part of what Phase 0 found and this plan must account for.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle V (MCP-Native Integration)** — PASS. This feature changes how NetGeniusClaw's own code
  *invokes* the agent runtime (CLI subprocess → persistent WS RPC to the same gateway). It does not
  introduce a bespoke integration pattern outside MCP: the MCP servers themselves, their transports,
  and their tool contracts are untouched. The WS RPC call is OpenClaw's own documented gateway
  protocol, already used internally by `sessions_send`/`runAgentStep` — this plan adopts an
  existing, in-product pattern rather than inventing one.
- **Principle XV (Backwards Compatibility)** — PASS, with an explicit design constraint (FR-008,
  SC-006): the optional origin marker must be additive-only, and every existing caller of
  `run_agent_turn()` (chat.py, invocation.py, service.py) must see identical behavior when it sends
  no marker. The dispatch-mechanism swap (CLI → WS) must be internal to `gateway.py` — its public
  function signature and return shape (`reply_text, tokens_used`) stay the same, so no caller needs
  to change.
- **Principle IV (Immutable Audit Trail)** — PASS. No change to GAIT logging; this is a latency/
  performance fix to an existing invocation path, not a new operational capability requiring new
  audit coverage.
- **Principle XI (Full-Stack Artifact Coherence)** — N/A for the latency work itself (no new MCP
  server, skill, or integration is being added — this modifies existing internal plumbing in
  `bgp/federation/gateway.py`). The new committed measurement script (FR-016a) is a `scripts/`-style
  tooling addition and will be documented inline, not as a new capability requiring the full
  checklist.
- **Principle IX (Security by Default)** — PASS. The WS RPC path reuses whatever gateway
  authentication the CLI path already resolves today (local loopback gateway, existing
  token/password credential resolution) — no new trust boundary is introduced, no new elevated
  permission is requested.

No violations requiring justification. Proceeding to Phase 0 (research.md — below, since research
was completed as part of this planning session) and Phase 1 (data-model.md, contracts/, quickstart.md).

## Project Structure

### Documentation (this feature)

```text
specs/116-border-turn-latency/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — confirmed root cause, evidence, alternatives
├── data-model.md        # Phase 1 output — entities touched by the fix
├── quickstart.md        # Phase 1 output — how to run the measurement script and verify SC-001–SC-009
├── contracts/           # Phase 1 output — gateway WS RPC contract, origin-marker contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mcp-servers/protocol-mcp/bgp/federation/
├── gateway.py            # MODIFIED — run_agent_turn() gains a persistent WS RPC dispatch path,
│                         # replacing the per-turn `openclaw agent` CLI subprocess as the default;
│                         # public signature (prompt, session_key, ... ) → (reply_text, tokens_used)
│                         # is unchanged so every caller below needs zero changes.
├── chat.py               # UNCHANGED CALLER — imports run_agent_turn from .gateway
├── invocation.py         # UNCHANGED CALLER — imports run_agent_turn from .gateway (2 call sites)
├── service.py            # UNCHANGED CALLER — imports run_agent_turn from .gateway (2 call sites)
└── controls.py           # UNCHANGED — production containment gate, orthogonal to dispatch mechanism

scripts/
└── measure-turn-latency.py   # NEW — FR-016a's committed, repeatable measurement script: reports
                               # fixed preparation time, trivial-turn end-to-end time, and recent
                               # real phone-question durations in one invocation (SC-009).

mcp-servers/protocol-mcp/tests/   # NEW directory — no test suite existed for this package before
├── __init__.py
├── test_gateway_ws_client.py       # NEW — GatewayWsClient in isolation: handshake, request/
│                                   # response round trip, reconnect-after-drop, timeout
├── test_run_agent_turn_dispatch.py # NEW — no cleanupBundleMcpOnRunEnd sent, reply extraction from
│                                   # WS response, stall/timeout semantics preserved
├── test_run_agent_turn_origin.py   # NEW — origin marker passthrough, backward-compat with no
│                                   # marker, unrecognized-origin normalization
└── test_agent_prioritisation.py    # NEW — interactive-ahead-of-background, no idle-case overhead
```

**Structure Decision**: Single project, extending the existing `bgp/federation/*` package in place
— no new top-level directory. This is a targeted fix to one function's internal dispatch mechanism
(`gateway.py::run_agent_turn()`), not a new component, so it follows the existing package structure
established by specs 052–115 rather than introducing an Option 2/3 layout.

## Complexity Tracking

*No constitution violations — this section is not applicable.*
