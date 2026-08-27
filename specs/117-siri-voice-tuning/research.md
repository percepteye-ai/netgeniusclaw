# Phase 0 Research: Siri Voice Window Tuning and Origin Marker (Pass 3 of 3)

## R1: What value should replace the flat 18-second `askBorderFastWindow`?

**Decision**: **12 seconds.**

**Rationale**: Spec 116's (Pass 2) own measurements, taken live against the real Border, are the
only evidence available:

| Case | Measured (Pass 2, `PASS3-HANDOFF.md`) |
|---|---|
| Cold — first turn in a brand-new session | ~9s |
| Warm — every turn after the first in the same session | ~3.9s |

12s gives the cold case (~9s) a ~3s margin — enough to absorb ordinary variance without being so
generous it reintroduces the old problem of a window sized for a world where nothing was ever fast
enough to matter. It is also within the exact range Pass 2's own handoff suggested re-tuning
toward ("perhaps 10-12 seconds... comfortably cover the first question in a fresh conversation").
It remains well under Siri's own observed patience ceiling (Pass 1's research: Siri can abandon a
spoken App Intent response and fall back to a web search "well before 30s" if nothing has been
said) — 12s plus normal network/processing overhead stays clear of that ceiling with room to spare.

**Alternatives considered**:
- **9s (exactly the cold measurement)**: rejected — zero margin means any turn even slightly slower
  than the measured average (normal variance, not a regression) falls back unnecessarily.
- **18s (unchanged)**: rejected — this is precisely the value Pass 3 exists to reconsider; keeping
  it wastes the entire benefit of Pass 2's latency fix for the user-perceptible "was it fast enough
  to be spoken" experience.
- **A value under Pass 2's own measured warm case (e.g. 5s)**: rejected — would only ever cover the
  warm case, defeating the point of a *fast* window that still gives a cold first-of-session
  question (the common real-world case: opening the phone, invoking Siri once) a fair chance.

**Confirmation before this is final**: Pass 2 left `scripts/measure-turn-latency.py` on the Border
specifically so a later pass can re-confirm these numbers without re-deriving them. This spec's own
live-phone verification step (User Story 3) is the point where 12s gets checked against reality on
the actual device/Border pairing in use; if live numbers disagree meaningfully, the constant is
adjusted then, not blindly trusted from a document.

## R2: How does the voice-origin marker travel from the phone's Siri intent to `run_agent_turn()`?

**Decision**: Extend the existing `n2n/edge/ask` wire request with one new optional field,
`"origin"`, following exactly the same optional-field pattern the request already uses for
`attachment` (feature 068). `ask_border_headless.dart`'s `runAskBorder()` — the ONLY caller that is
Siri-specific (it is the headless entry point `AskBorderIntent.swift` launches, per its own
doc-comment) — passes `origin: 'voice'` unconditionally on every call it makes. Every other caller
of `EdgeAskClient.ask()` (the app's own Chat screen) passes nothing, so the field is simply absent,
identical to today's wire shape.

On the Border, `service.py`'s `_edge_on_ask()` — the sole handler for `n2n/edge/ask` — reads
`params.get("origin")` and passes it straight through as `run_agent_turn(..., origin=origin)`.
`run_agent_turn()` already normalizes an unrecognized value to `None` (`_normalize_origin()`,
spec 116 FR-012) and treats `None` as today's default behavior (spec 116 FR-008) — so this handler
needs no validation of its own; it is a pure pass-through of an optional string.

**Rationale**: `run_agent_turn(origin=...)` already exists and is verified (spec 116). The only gap
is that nothing between the Siri intent and that function call currently carries the marker. Adding
one optional field to one existing request, read by one existing handler, is the smallest change
that closes the gap — no new wire method, no new Border-side subsystem, matching the "very likely a
matter of passing an existing field one or two layers further" framing from spec 115's own handoff
to spec 116.

**Alternatives considered**:
- **A separate wire method for voice-originated asks (e.g. `n2n/edge/ask_voice`)**: rejected —
  duplicates the entire `n2n/edge/ask` contract (task creation, result push, cancellation, status)
  for a single-field difference; the optional-field pattern already has precedent (`attachment`).
- **Inferring voice origin Border-side from some other signal (e.g. a timeout heuristic)**:
  rejected — fragile and indirect; the phone knows unambiguously when a request came from
  `AskBorderIntent` vs. the Chat screen, so it should simply say so.
- **Threading the marker through `session_key` instead of a new field**: rejected — `session_key`
  is already load-bearing (feature 067: one persistent session per device) and overloading it with
  a second meaning would risk breaking session continuity between voice and chat-screen turns from
  the same phone, which must share the same conversation.

## R3: Does changing the window value or adding the origin field risk breaking any existing caller?

**Decision**: No changes needed to any other caller.

**Evidence**:
- `askBorderFastWindow` and `askBorderPostAckWindow` are both passed as explicit default-valued
  parameters to `runAskBorder()`, and the existing Dart test suite
  (`test/ask_border_headless_test.dart`) already overrides `fastWindow` explicitly per test rather
  than relying on the module constant — changing the constant's value does not change any test's
  behavior.
- `EdgeAskClient.ask()`'s new `origin` parameter is optional with no default value forcing a
  choice — every existing call site (the Chat screen's own send path) compiles and behaves
  unchanged by simply not passing it, exactly as `attachment` already works today.
- `service.py::_edge_on_ask()` reading one additional, possibly-absent `params` key does not change
  behavior for a request that never sends that key (i.e. every non-Siri caller, and every existing
  Python test in `tests/n2n/test_edge_ask.py`, none of which currently send `origin`).

This mirrors spec 116's own SC-006 discipline (verify old callers are byte-identical) applied one
layer further out.
