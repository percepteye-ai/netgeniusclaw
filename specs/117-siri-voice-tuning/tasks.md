# Tasks: Siri Voice Window Tuning and Origin Marker (Pass 3 of 3)

**Input**: Design documents from `/specs/117-siri-voice-tuning/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/edge-ask-origin-field.md, quickstart.md

**Tests**: Included — this repo's convention (spec 116, 067, 068) is to extend the existing
automated suites alongside the code they cover, and both changed files already have such suites
(`tests/n2n/test_edge_ask.py`, `mobile/netclaw-mobile/test/ask_border_headless_test.dart`).

**Organization**: Tasks are grouped by user story (US1: window retune, US2: origin marker, US3:
live phone verification) per spec.md's priorities.

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

Two-sided repo layout, matching every 066+ mobile spec: `mobile/netclaw-mobile/` (Dart/Flutter) and
`mcp-servers/protocol-mcp/bgp/federation/` (Python, Border-side) with tests in
`mobile/netclaw-mobile/test/` and `tests/n2n/` respectively.

---

## Phase 1: Setup

**Purpose**: Confirm the baseline is green before touching anything.

- [X] T001 Run `python3 -m pytest tests/n2n/test_edge_ask.py -v` from repo root and confirm all
      existing tests pass before any change (baseline for US2).
- [X] T002 [P] Run `flutter test test/ask_border_headless_test.dart` from
      `mobile/netclaw-mobile/` and confirm all existing tests pass before any change (baseline for
      US1/US2).

**Checkpoint**: Both baselines green — safe to proceed.

---

## Phase 2: Foundational

**Purpose**: N/A for this feature. US1 (window value) and US2 (origin marker) touch disjoint code
paths with no shared new infrastructure — each can proceed directly from Setup. This phase is
intentionally empty; do not add speculative shared scaffolding.

---

## Phase 3: User Story 1 - Cold first Siri question still gets a spoken answer (Priority: P1) 🎯 MVP

**Goal**: Shrink `askBorderFastWindow` from 18s to 12s so it is sized against Pass 2's real
measurements (~9s cold, ~3.9s warm) instead of the old ~38s-always baseline.

**Independent Test**: Unit-verify the constant's new value and doc comment; live confirmation
happens in User Story 3 (needs the phone).

### Implementation for User Story 1

- [X] T003 [US1] In `mobile/netclaw-mobile/lib/ncfed/ask_border_headless.dart`, change
      `askBorderFastWindow` from `Duration(seconds: 18)` to `Duration(seconds: 12)`, and rewrite
      its doc comment to cite Pass 2's measured ~9s cold / ~3.9s warm numbers
      (`specs/116-border-turn-latency/PASS3-HANDOFF.md`) and this feature's research.md R1,
      replacing the now-stale "chosen comfortably under Siri's own observed real-world patience...
      well before 30s" framing (still true, but no longer the binding constraint — Pass 2's
      latency fix is).

### Tests for User Story 1

- [X] T004 [US1] In `mobile/netclaw-mobile/test/ask_border_headless_test.dart`, add a test in a
      new `group('askBorderFastWindow')` asserting `askBorderFastWindow == Duration(seconds: 12)`
      — a direct regression guard on the retuned value, distinct from the existing tests that
      already override `fastWindow` explicitly per-test and are unaffected by this change.

**Checkpoint**: User Story 1's code change is in place and unit-guarded. Full behavioral
confirmation (does 12s actually work against a real Border) is User Story 3.

---

## Phase 4: A spoken answer sounds like it was meant to be heard (Priority: P2)

**Goal**: Every Siri-originated `n2n/edge/ask` request carries an `origin: "voice"` marker; the
Border's `_edge_on_ask()` handler reads and forwards it to `run_agent_turn(origin=...)`, which
already knows how to compose a short, plain answer for it (spec 116). Non-Siri requests are
byte-identical to today.

**Independent Test**: Submit a fake `n2n/edge/ask` with `origin: "voice"` and confirm
`run_agent_turn` receives it; submit one without `origin` and confirm it receives `None`, matching
today's behavior exactly.

### Tests for User Story 2 ⚠️

> Write these first; confirm they fail against the current code before implementing.

- [X] T005 [P] [US2] In `tests/n2n/test_edge_ask.py`, add
      `test_edge_ask_origin_reaches_run_agent_turn` (+ its `async def _edge_ask_origin_reaches_run_agent_turn`
      helper, following the file's existing `asyncio.run(...)` pattern): mock `run_agent_turn` to
      record `kwargs.get("origin")`, call `phone.call("n2n/edge/ask", {"text": "...", "origin": "voice"})`,
      and assert the recorded value is exactly `"voice"`.
- [X] T006 [P] [US2] In the same file, add `test_edge_ask_no_origin_is_unchanged`: same shape, but
      call `n2n/edge/ask` with no `origin` key at all (as every existing test in this file already
      does) and assert `run_agent_turn` still receives `origin=None` (or the key absent) —
      confirms FR-004's byte-identical-for-non-Siri-callers requirement.
- [X] T007 [P] [US2] In `mobile/netclaw-mobile/test/ask_border_headless_test.dart`, extend
      `_FakeRpc` to record the `params` passed to each `call()` (not just the method name — add a
      `paramsCalled` list alongside the existing `methodsCalled`), then add a test asserting that
      `runAskBorder()`'s call to `n2n/edge/ask` includes `'origin': 'voice'` in its params.

### Implementation for User Story 2

- [X] T008 [US2] In `mobile/netclaw-mobile/lib/ncfed/edge_ask_client.dart`, add an optional
      `String? origin` parameter to `EdgeAskClient.ask()` and include it in the request map as
      `'origin': ?origin` (same null-aware-omit pattern already used for `'attachment': ?attachment`
      on the line above it). Update the method's doc comment to mention the new field, referencing
      `contracts/edge-ask-origin-field.md`.
- [X] T009 [US2] In `mobile/netclaw-mobile/lib/ncfed/ask_border_headless.dart`, update
      `runAskBorder()`'s call to `askClient.ask(question)` to `askClient.ask(question, origin: 'voice')`
      — this is the sole Siri-specific caller in the codebase (per its own doc comment, mirroring
      `AskBorderIntent.swift`), so it always sends the marker unconditionally.
- [X] T010 [US2] In `mcp-servers/protocol-mcp/bgp/federation/service.py`'s `_edge_on_ask()`, read
      `origin = params.get("origin")` alongside the existing `text`/`attachment` reads, and pass it
      through on the `run_agent_turn(...)` call inside `worker()`: add `origin=origin` to that
      call's keyword arguments (next to the existing `timeout_s=timeout_s, on_stall=on_stall`).
      Do not add any validation — `run_agent_turn`'s own `_normalize_origin()` (spec 116) already
      handles an unrecognized value safely.

**Checkpoint**: User Stories 1 AND 2 are both implemented and unit-verified. All new/extended
automated tests pass.

---

## Phase 5: The full Siri loop is verified end-to-end on a real phone (Priority: P1)

**Goal**: Confirm, by listening on a real device, that the combined effect of US1 and US2 matches
what they promise.

**⚠️ Requires a real, enrolled, unlocked iPhone reachable to the Border running this feature's
code — this phase cannot be completed by an automated agent alone.**

### Live verification for User Story 3

- [ ] T011 [US3] Deploy this feature's Border-side change (`service.py`) to the running Border host
      and restart the Border process so `_edge_on_ask()` picks up the `origin` read.
- [ ] T012 [US3] Rebuild and reinstall the NetGeniusClaw Mobile app on the test iPhone so it picks up the
      12s window and the `origin: 'voice'` send.
- [ ] T013 [US3] Follow `quickstart.md`'s "Live verification" section step 1 (cold case): restart
      the Border (or wait for phone session idle), ask a trivial question by Siri, confirm a real
      spoken answer (SC-001).
- [ ] T014 [US3] Follow `quickstart.md` step 2 (warm case): ask a second trivial Siri question in
      the same session, confirm it lands inside the window (SC-002).
- [ ] T015 [US3] Follow `quickstart.md` step 3 (voice-shaped answer): ask a naturally longer
      question by Siri and the identical question via the Chat screen; confirm the Siri answer is
      shorter/plainer and the Chat-screen answer is unchanged (SC-003, SC-004).
- [ ] T016 [US3] Follow `quickstart.md` step 4: on the Border host, run
      `python3 scripts/measure-turn-latency.py` and compare fresh numbers against Pass 2's
      recorded ~9s/~3.9s baseline this feature's 12s window was chosen against (SC-005). If they
      disagree meaningfully, revisit the constant from T003 before considering this feature done.
- [ ] T017 [US3] If live verification surfaces a genuine Border-side gap that cannot be fixed from
      this session (e.g. something requiring hands-on work on the Linux Border host itself), write
      a Pass 3 → Pass 4 handoff doc at `specs/117-siri-voice-tuning/pass4-handoff.md`, mirroring
      the style and structure of `specs/115-siri-reliability-fix/pass2-handoff.md` and
      `specs/116-border-turn-latency/PASS3-HANDOFF.md`, so a fresh session on the Border host can
      pick it up as spec 118.

**Checkpoint**: All three user stories confirmed. Feature complete only when this phase's
acceptance scenarios are actually observed on the device, not merely coded.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T018 [P] Re-run `python3 -m pytest tests/n2n/test_edge_ask.py -v` and
      `flutter test test/ask_border_headless_test.dart` together after all of Phase 3/4's changes
      to confirm nothing regressed.
- [ ] T019 Update `specs/117-siri-voice-tuning/quickstart.md` if live verification (Phase 5)
      surfaces any deviation from the documented steps.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Empty — nothing blocks US1/US2.
- **User Story 1 (Phase 3)**: Depends on Setup only. Fully independent of US2.
- **User Story 2 (Phase 4)**: Depends on Setup only. Fully independent of US1.
- **User Story 3 (Phase 5)**: Depends on BOTH US1 and US2 being implemented (it verifies their
  combined effect) — the one phase in this feature that is not independent, by design (spec.md's
  own "equal priority... blocks the other two from being considered complete").
- **Polish (Phase 6)**: T018 depends on Phases 3-4; T019 depends on Phase 5.

### Parallel Opportunities

- T001/T002 (Setup) in parallel.
- T005/T006/T007 (US2 tests) in parallel — three different assertions, two different files.
- Phase 3 (US1) and Phase 4 (US2) can be implemented in parallel by different people/sessions —
  disjoint files, no shared state.

---

## Implementation Strategy

### MVP First

1. Phase 1 (Setup).
2. Phase 3 (US1) — smallest possible change, immediately gives a shorter window even before US2
   lands, and is independently testable.
3. **STOP and hand off to the phone** for Phase 5's T013/T014 if US2 isn't ready yet — a shorter
   window alone is already an improvement worth verifying.

### Full Delivery (this session, without the phone)

1. Phase 1 → Phase 3 (US1) → Phase 4 (US2) → Phase 6's T018.
2. Everything through here is completed and verified by automated tests alone.
3. **Phase 5 (US3) is handed to the user** — it requires the real, unlocked, connected iPhone
   mentioned at the start of this work, plus deploying the Border-side change to the live Border
   host. T017 exists specifically to capture a follow-up spec (118) if that live pass finds
   something this session couldn't reach.
