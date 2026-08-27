# Contract Amendment: `n2n/edge/ask` gains an optional `origin` field

**Amends**: `specs/067-ncfed-mobile-command-channel/contracts/edge-ask-command-channel.md` §1
**Depends on**: `specs/116-border-turn-latency/contracts/run-agent-turn.md` (`origin` parameter,
already implemented and unchanged by this feature)

## Request (phone → Border) — new optional field

```json
{ "text": "check every core router for BGP problems", "origin": "voice" }
```

- `origin` is **optional**. Absent entirely for any request the app's Chat screen sends — identical
  wire shape to today.
- The only value this feature ever sends is `"voice"`, and only from
  `ask_border_headless.dart`'s `runAskBorder()` — the headless entry point `AskBorderIntent.swift`
  (the Siri/Shortcuts intent) launches. No other caller in the mobile codebase sends this field.
- Follows the exact same optional-field precedent `attachment` already established on this same
  request (feature 068) — a new recognized key, not a new method, not a breaking change to the
  existing shape.

## Result (Border → phone) — unchanged

No change. Still `{ "task_id": "..." }`, immediate, non-blocking, exactly as today.

## Border-side handling

`service.py::_edge_on_ask()` reads `params.get("origin")` (defaulting to `None` when absent, which
is the value it already implicitly has today) and passes it straight through:

```python
output, tokens = await run_agent_turn(
    prompt, session_key=session_key, untrusted=False,
    message_file=message_file,
    timeout_s=timeout_s, on_stall=on_stall,
    origin=origin,   # NEW — read from params, forwarded unchanged
)
```

- No validation performed here. `run_agent_turn()` already normalizes an unrecognized value to
  `None` (spec 116, `_normalize_origin()`) — this handler does not need to duplicate that check.
- A Border build that predates this change simply never reads the key; the field is present in the
  request but silently unused, exactly as any unknown JSON key is today. No version negotiation
  needed.

## Backward compatibility

- A request with no `origin` field behaves byte-identical to today (spec 116's own SC-006
  discipline extended one hop further).
- A Border that does not yet implement this handler-side read still answers `n2n/edge/ask` requests
  normally — sending `origin` costs nothing if the receiving end ignores it.
