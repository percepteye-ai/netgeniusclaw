# Contract: `run_agent_turn()` (NetClaw-internal, `bgp/federation/gateway.py`)

**Feature**: [spec.md](../spec.md)

This is the contract NetGeniusClaw's own callers depend on. It does not change shape — only its internal
dispatch mechanism changes (see [gateway-ws-rpc.md](./gateway-ws-rpc.md)).

## Signature

```python
async def run_agent_turn(
    prompt: str,
    session_key: str = "n2n",
    timeout_s: int = 300,
    local: bool = False,
    model: str = None,
    untrusted: bool = False,
    on_stall=None,
    stall_after_s: int = 120,
    message_file: str = None,
    origin: str | None = None,          # NEW — FR-007. Default None: zero behavior change (FR-008).
) -> tuple[str, int]:                    # (reply_text, tokens_used) — UNCHANGED
    ...
```

## Behavior contract

- **Unchanged for every existing caller.** `chat.py`, `invocation.py` (2 sites), `service.py`
  (2 sites) call this today without `origin`; after the fix they get byte-identical behavior
  (SC-006) unless/until they are updated to pass `origin="voice"` — which is explicitly out of
  scope for this pass for the mobile-originated path (Assumptions: "the phone does not yet send an
  origin marker... Pass 3 decision").
- **`local=True` (embedded mode) is untouched.** This contract's dispatch change applies only to
  the default gateway-RPC path. The embedded path's own `EnforcementRefused` fail-closed gating
  (untrusted eN2N input, production sandbox/model-guard checks) is unmodified.
- **Timeout semantics unchanged.** `timeout_s`, `on_stall`, `stall_after_s` keep their existing
  meaning (surfacing a stall during a gateway scope-upgrade approval gate) — the WS RPC path must
  implement the same stall-detection/extension behavior the CLI path's `asyncio.wait` +
  `on_stall` callback provides today, not silently drop it.
- **Error surface unchanged in kind.** On failure, callers still get either a raised
  `TimeoutError`/`EnforcementRefused` or a `(error_text, 0)` tuple — whichever the CLI path
  returns today for the equivalent failure — so no caller's exception handling needs to change.

## New behavior (additive only)

- `origin` is threaded into the WS RPC request's `inputProvenance`/`extraSystemPrompt` fields
  (per [gateway-ws-rpc.md](./gateway-ws-rpc.md)) so the gateway can compose a voice-appropriate
  answer (FR-010) when `origin == "voice"`.
- An unrecognized `origin` value (anything other than `"voice"` or `None`) is normalized to `None`
  before being sent (FR-012) — the gateway is never asked to honor a value NetGeniusClaw itself doesn't
  recognize, and the request never fails because of it.
- The turn's record (wherever `chat.py`/`invocation.py`/`service.py` log or persist turn metadata
  today) gains the ability to retain `origin` for after-the-fact inspection (FR-013) — reusing
  whatever field already exists for this purpose, not a new store (data-model.md).

## Reused unchanged

- `_extract_reply()` — same JSON-envelope parsing, now fed WS response payloads instead of CLI
  stdout, but the shape it parses (`result.payloads[*].text`, `finalAssistantVisibleText`, etc.) is
  identical either way (contracts/gateway-ws-rpc.md).
- `_openclaw_bin()` / `_agent_env()` — still used by the `local=True` embedded path, which this
  contract does not touch.
- `EnforcementRefused` gating for untrusted embedded turns — unchanged.
