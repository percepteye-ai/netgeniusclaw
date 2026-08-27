# Contract: Border → OpenClaw Gateway WS RPC (agent turn dispatch)

**Feature**: [spec.md](../spec.md) | **Research**: [research.md](../research.md)

This is NetGeniusClaw's contract with the OpenClaw gateway's existing, documented WebSocket protocol
(`docs/gateway/protocol.md` in the vendored `openclaw` package, `~/.nvm/.../openclaw/docs/`) — not
a new protocol NetGeniusClaw defines. It replaces the current `openclaw agent ...` CLI subprocess call
inside `gateway.py::run_agent_turn()`.

## Connection

- URL: `ws://127.0.0.1:<gateway.port>` (loopback; matches the Border's existing local-mode gateway
  config — `gateway.bind: "loopback"`, `gateway.mode: "local"`, `gateway.port: 18789` observed on
  the live host). No TLS, no remote mode — same trust boundary the CLI already operates in today.
- Auth: shared gateway token (`gateway.auth.mode: "token"`, `gateway.auth.token` — already present
  in `~/.openclaw/openclaw.json` config, already what the CLI path resolves via
  `resolveGatewayCredentials`). The persistent client reads it the same way, from the same config
  file — no new secret, no new credential storage.
- Lifetime: **persistent**, one connection per Border process (not one per turn). This is the
  structural change from today's one-CLI-subprocess-per-turn model. Reconnect on drop with backoff;
  a dropped connection must not corrupt in-flight turn bookkeeping (fail that turn cleanly, let the
  caller's existing error-surfacing handle it — FR-005's "surface failure clearly" applies at this
  layer too, not just to MCP tool failures).

## Handshake

Standard `connect` request/response per `docs/gateway/protocol.md`. Role: `operator` (same class of
client the CLI presents as today — `client.mode: "backend"` per
`agent-via-gateway-BB-FX7EM.js`'s `GATEWAY_CLIENT_MODES.BACKEND` for non-model-override calls).
Trusted same-process backend clients on loopback may omit `device` and authenticate with the shared
token directly (protocol.md, "Trusted same-process backend clients" — this is the exact
classification the Border's own dispatch already qualifies for).

```json
// Border → Gateway
{
  "type": "req", "id": "<uuid>", "method": "connect",
  "params": {
    "minProtocol": 3, "maxProtocol": 4,
    "client": { "id": "gateway-client", "version": "116", "platform": "linux", "mode": "backend" },
    "role": "operator", "scopes": ["operator.read", "operator.write"],
    "auth": { "token": "<gateway.auth.token>" }
  }
}
```

## Agent turn request

Framed as a standard `req`, `method: "agent"`. Params mirror exactly what
`agent-via-gateway-BB-FX7EM.js` sends today (confirmed by reading its `dispatchGatewayAgentCall`),
**minus** `cleanupBundleMcpOnRunEnd` (the root cause — omitting it is the entire point, per
research.md Finding 3's precedent in `runAgentStep`/`sessions_send`):

```json
{
  "type": "req", "id": "<uuid>", "method": "agent",
  "params": {
    "message": "<prompt>",
    "agentId": "main",
    "sessionKey": "<session_key>",
    "deliver": false,
    "timeout": 300,
    "idempotencyKey": "<uuid>",
    "extraSystemPrompt": "<voice-composition instruction, only when origin==voice — FR-010>"
  }
}
```

- `deliver: false` — matches `runAgentStep`'s pattern; the Border reads the reply from the RPC
  response, it does not need the gateway to also push it through a channel delivery path.
- **No `cleanupBundleMcpOnRunEnd` field.** This is the fix. Its absence lets the gateway's own
  session-scoped MCP runtime cache persist across turns sharing `sessionKey`, exactly as
  `sessions_send` already relies on for its own internal use (research.md Finding 3).
- **No `inputProvenance` field.** Confirmed during implementation (by reading the gateway's own
  `normalizeInputProvenance`, `input-provenance-CQSqbDss.js`): `inputProvenance.kind` is validated
  against a fixed enum (`external_user`/`inter_session`/`internal_system`) and anything else is
  silently dropped — an ad-hoc `{"origin": "voice"}` shape is not a recognized extension point and
  would be inert. `extraSystemPrompt` alone is the real, gateway-accepted mechanism driving FR-010;
  it is confirmed present and forwarded in `agent-CtFDOo4w.js`'s handler (`request.extraSystemPrompt`).
  FR-013 (retaining origin for after-the-fact inspection) is satisfied entirely on NetGeniusClaw's own
  side — the caller records `origin` itself — not by round-tripping it through the gateway.

## Agent turn response

```json
{ "type": "res", "id": "<uuid>", "ok": true, "payload": { "result": { "payloads": [{ "text": "..." }] } } }
```

Reply extraction reuses the exact same parsing logic `gateway.py::_extract_reply()` already
implements for the CLI's JSON envelope — the underlying result shape is the same `result.payloads`
structure whether it arrives via CLI stdout or WS response payload (confirmed: `agent-CtFDOo4w.js`
builds the same `payloads` array the CLI JSON output surfaces). `_extract_reply()` is reused
as-is; only how its input arrives changes.

## Backward compatibility (FR-008, SC-006, Constitution Principle XV)

- `run_agent_turn(prompt, session_key, ...)`'s **Python signature and return type are unchanged**:
  `(reply_text: str, tokens_used: int)`. `chat.py`, `invocation.py`, `service.py` require zero code
  changes — they already only depend on this signature.
- The new `origin` parameter is added to `run_agent_turn()` with a default of `None`; every existing
  call site that does not pass it behaves identically to today (FR-008).
- The `local=True` embedded-mode path (used for iN2N members per `EnforcementRefused` gating in
  `gateway.py`) is **out of scope for this dispatch change** — it does not go through the gateway at
  all today (`openclaw agent --local`), so it has no `cleanupBundleMcpOnRunEnd` cost to fix, and
  this contract does not touch it.

## Failure modes (Edge Cases, FR-005)

| Condition | Behavior |
|---|---|
| WS connection not yet established / drops mid-turn | Reconnect with backoff; the in-flight turn fails with a clear error surfaced to the caller (same shape as today's CLI non-zero-exit handling), not a silent hang. |
| Gateway restarts | Persistent client detects the close, reconnects once the gateway is back up; first turn after reconnect may pay a fresh MCP Tool Set build (this is the same "first request after a Border restart" case the spec's Edge Cases and Assumptions already accept as a one-time cost). |
| Auth token rotated | Reconnect fails auth; surfaced as a clear configuration error (matches today's behavior when the CLI's resolved credentials are stale). |
