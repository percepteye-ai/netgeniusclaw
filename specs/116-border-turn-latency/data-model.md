# Phase 1 Data Model: Border Agent Turn Latency

**Feature**: [spec.md](./spec.md) | **Research**: [research.md](./research.md)

No new persistent storage is introduced (per the spec's Storage assumption and this plan's
Technical Context: N/A). This document describes the in-memory/runtime entities the fix touches,
their fields, and how they change across a turn's lifecycle — not database rows.

## Entities

### Agent Turn (existing concept, spec Key Entities — behavior changes here)

One complete request/response cycle. Unchanged fields; changed lifecycle:

| Field | Type | Notes |
|---|---|---|
| `session_key` | str | Unchanged. Identifies which MCP runtime cache entry to reuse. |
| `prompt` | str | Unchanged — the question text. |
| `origin` | `str \| None` | **NEW** (FR-007). Optional marker: `"voice"` or absent. Unrecognized values normalize to `None` (FR-012). |
| `reply_text` | str | Unchanged return value. |
| `tokens_used` | int | Unchanged return value. |
| `prep_cost_ms` | — | Not a tracked field on the turn itself; observed externally via the Border's own logs and the new measurement script (FR-016a), not stored per-turn. |

**Lifecycle change**: today, every turn's dispatch (`gateway.py::run_agent_turn`, CLI mode) implies
`cleanupBundleMcpOnRunEnd: true` server-side, so the MCP Tool Set (below) is destroyed at the end of
every turn regardless of `session_key`. After the fix, dispatch goes through the persistent WS RPC
path (no forcing flag), so the MCP Tool Set survives across turns sharing a `session_key`, and is
only rebuilt when genuinely needed (first use in a session, or a config change — FR-006).

### MCP Tool Set (existing concept, spec Key Entities — reuse semantics change here)

The gateway-side, session-scoped cache of connected MCP server sessions and their tool catalog
(`runtimesBySessionId` in OpenClaw's `agent-bundle-mcp-runtime-BkUYqKo5.js` — read-only dependency,
not owned by NetGeniusClaw, but whose *reuse* NetGeniusClaw's dispatch choice now enables instead of defeats).

| Field (conceptual) | Notes |
|---|---|
| `session_id` | Cache key. Tied 1:1 to an `Agent Turn`'s resolved session, not the `session_key` string directly (a session key resolves to a session id; the runtime cache is keyed by the latter). |
| `servers` | Map of configured MCP server name → connected transport/session. Built once per cache miss, reused on hit. |
| `tools` | Flattened tool catalog derived from `servers`, exposed to the model for that turn. |
| `last_used_at` | Drives `mcp.sessionIdleTtlMs`-based eviction — now meaningful again once turns stop force-retiring the cache after every use. |

**No NetClaw-owned representation of this entity is created.** NetGeniusClaw's only lever is *whether it
asks the gateway to destroy it* (the `cleanupBundleMcpOnRunEnd` flag it no longer sets), not how the
cache itself is implemented.

### Request Origin (existing concept, spec Key Entities — this is where it's implemented)

| Field | Type | Notes |
|---|---|---|
| `value` | `Literal["voice"] \| None` | FR-007/FR-012: absent or unrecognized → `None`, treated identically to "not supplied." Only one recognized value exists for this pass (voice); the shape allows more later without a breaking change. |
| carried via | WS RPC `params` (new dispatch) or CLI arg (fallback dispatch, if retained) | FR-009: must survive from receipt to composition. |
| persisted as | existing session/turn record field (FR-013) | Reuses whatever field the session transcript already has available for recording provenance — no new store. |

### Answer Composition (existing concept, spec Key Entities — gains a branch)

Not a data entity so much as a decision point: when `Request Origin == "voice"`, the system prompt
or composition instruction appended for that turn changes (FR-010/FR-011/FR-011a — enforced by
instruction at composition time, not post-hoc truncation). No schema; this is prompt-construction
logic in whichever function assembles the extra system prompt / instructions passed into
`run_agent_turn()`.

## State Transitions

```
Turn arrives (session_key, prompt, origin?)
        │
        ▼
Resolve session_id for session_key (existing OpenClaw session store — unchanged)
        │
        ▼
MCP Tool Set cache lookup by session_id
        │
   ┌────┴─────┐
   │ HIT       │ MISS (first turn in session, or config changed — FR-006)
   ▼           ▼
reuse warm   build cold (pays the one-time cost — FR-004a/FR-004b)
   │           │
   └─────┬─────┘
         ▼
Compose answer (branches on origin — FR-010 vs default)
         ▼
Return (reply_text, tokens_used) — Tool Set is NOT torn down (this is the fix)
```
