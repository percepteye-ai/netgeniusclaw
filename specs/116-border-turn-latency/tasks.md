# Tasks: Border Agent Turn Latency + Voice-Aware Answers (Pass 2 of 3)

**Input**: Design documents from `/home/johncapobianco/netclaw/specs/116-border-turn-latency/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included — plan.md commits to a new `tests/` suite for this package (none existed before),
and correctness of the WS RPC dispatch swap (the entire fix) is not safely verifiable without them.

**Organization**: Tasks are grouped by user story per spec.md priorities (US1 = P1, US2 = P2,
US3 = P3), preceded by Setup and Foundational phases per research.md's confirmed root cause.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- All file paths are absolute from `/home/johncapobianco/netclaw/`

## Path Conventions

Single project, extending `mcp-servers/protocol-mcp/bgp/federation/` in place (per plan.md's
Structure Decision — no new top-level directory).

---

## Phase 1: Setup

**Purpose**: Confirm the environment is ready for the WS RPC dispatch swap; no code changes yet.

- [X] T001 Confirm `websockets>=12.0` (already declared in `mcp-servers/protocol-mcp/requirements.txt`
      per feature 066) is installed in the Border's actual runtime environment: run
      `python3 -c "import websockets; print(websockets.__version__)"` from
      `mcp-servers/protocol-mcp/` and record the version. No new dependency to add — this only
      verifies the existing declaration is honored in the live venv used by the gateway's Python
      MCP subprocesses.
- [X] T002 Create `mcp-servers/protocol-mcp/tests/` directory with an empty `__init__.py` — no test
      directory exists for this package today (confirmed by search); this is the first one.
- [X] T003 [P] Read `~/.openclaw/openclaw.json`'s `gateway` block on the live Border host and record
      the exact `port`, `bind`, `mode`, and `auth.mode`/`auth.token` fields being used today, so the
      new WS client in T010 targets the real running configuration (`ws://127.0.0.1:18789` with
      token auth, per research.md — confirm this is still current before coding against it, since
      config can drift between sessions).

**Checkpoint**: Environment confirmed; no functional change yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the persistent WS RPC client that Phase 3 (US1) depends on. This is the actual
fix's core infrastructure — every user story's implementation task in Phase 3+ requires it to exist
first.

**⚠️ CRITICAL**: No user story work can begin until T010 is complete and T011 passes.

- [X] T004 [P] Create `mcp-servers/protocol-mcp/bgp/federation/gateway_ws.py` — new module holding
      the persistent WebSocket client. Define `class GatewayWsClient` with `__init__(self, url: str,
      token: str)`, an internal `_ws` handle (initially `None`), and a `_lock` (`asyncio.Lock`) to
      serialize connect attempts.
- [X] T005 In `gateway_ws.py`, implement `async def _ensure_connected(self)`: if `self._ws` is None
      or closed, open a new `websockets.connect(self.url)`, then perform the `connect` handshake per
      `specs/116-border-turn-latency/contracts/gateway-ws-rpc.md` (`type: "req"`, `method:
      "connect"`, `role: "operator"`, `client.mode: "backend"`, `auth.token`), and raise a clear
      exception if the handshake response's `ok` is not `true`. Reuse this method internally before
      every RPC call — do not require callers to manage connection state.
- [X] T006 In `gateway_ws.py`, implement `async def call(self, method: str, params: dict, timeout_s:
      float) -> dict`: assigns a UUID request id, sends `{"type": "req", "id": ..., "method":
      method, "params": params}` over the ensured connection, and awaits the matching `{"type":
      "res", "id": ...}` response (ignoring/dispatching `{"type": "event", ...}` frames that arrive
      interleaved — per `contracts/gateway-ws-rpc.md`'s Framing section). Raise a
      `TimeoutError` if no matching response arrives within `timeout_s`. Raise a clear error
      (including the gateway's `error` payload) if `ok` is `false`.
- [X] T007 In `gateway_ws.py`, implement reconnect-with-backoff: on a `ConnectionClosed` (or
      equivalent) exception during `call()`, clear `self._ws`, retry `_ensure_connected()` once with
      a short backoff, then retry the single failed call once before giving up and raising to the
      caller — per `contracts/gateway-ws-rpc.md`'s Failure modes table ("Reconnect with backoff...
      must not corrupt in-flight turn bookkeeping").
- [X] T008 [P] In `gateway_ws.py`, implement `def resolve_gateway_ws_config() -> tuple[str, str]`
      reading the gateway URL and auth token the same way the existing `openclaw` CLI resolves them
      today: from `~/.openclaw/openclaw.json`'s `gateway.port`/`gateway.bind`/`gateway.auth.token`
      (loopback → `ws://127.0.0.1:<port>`), with an `OPENCLAW_GATEWAY_WS_URL`/
      `OPENCLAW_GATEWAY_TOKEN` environment override for parity with `gateway.py`'s existing
      `OPENCLAW_BIN`-style override convention (`_openclaw_bin()` at
      `mcp-servers/protocol-mcp/bgp/federation/gateway.py:27`).
- [X] T009 In `gateway_ws.py`, provide a module-level singleton accessor
      `def get_gateway_ws_client() -> GatewayWsClient` (lazy-constructed, one persistent connection
      shared by every `run_agent_turn()` call in the process — this is what makes the connection
      "one per Border process, not one per turn" per `contracts/gateway-ws-rpc.md`'s Connection
      section).
- [X] T010 Add `mcp-servers/protocol-mcp/tests/test_gateway_ws_client.py`: unit tests for
      `GatewayWsClient` against a minimal fake WebSocket server (use `websockets.serve` in the test
      itself, no live gateway needed) covering: successful connect handshake, a request/response
      round trip, reconnect-after-drop, and timeout-when-no-response. This is the Foundational
      phase's own correctness gate — must pass before Phase 3 begins.

**Checkpoint**: `GatewayWsClient` exists, is unit-tested in isolation, and is ready for
`run_agent_turn()` to use. User Story 1 implementation can now begin.

---

## Phase 3: User Story 1 - NetGeniusClaw answers without a fixed startup delay (Priority: P1) 🎯 MVP

**Goal**: Eliminate the ~27s fixed preparation cost from every turn by dispatching through the
persistent WS RPC connection (Phase 2) instead of a per-turn `openclaw agent` CLI subprocess, so
`cleanupBundleMcpOnRunEnd: true` is never sent and the gateway's own session-scoped MCP runtime
cache is allowed to survive across turns (research.md, Findings 2 and 3).

**Independent Test**: Per spec.md — ask a trivially-answerable question and measure wall-clock time
against the 37.9s baseline; ask a second question in the same conversation and confirm it is not
slower than the first (no repeated full-preparation cost).

### Tests for User Story 1 ⚠️

> Write these first; they must FAIL against today's CLI-dispatch `run_agent_turn()` before the
> implementation tasks below make them pass.

- [X] T011 [P] [US1] Add
      `mcp-servers/protocol-mcp/tests/test_run_agent_turn_dispatch.py::test_no_cleanup_flag_sent`:
      mock `GatewayWsClient.call` and assert the `params` dict passed for method `"agent"` never
      contains a `cleanupBundleMcpOnRunEnd` key — this is the single assertion that directly encodes
      research.md's root-cause fix (Finding 2/Finding 3).
- [X] T012 [P] [US1] Add
      `mcp-servers/protocol-mcp/tests/test_run_agent_turn_dispatch.py::test_reply_extraction_from_ws_response`:
      feed a fake WS `res` payload shaped like `contracts/gateway-ws-rpc.md`'s example
      (`result.payloads[*].text`) through `_extract_reply`-equivalent logic and assert it returns the
      same `(reply_text, tokens_used)` shape the existing CLI-stdout path returns today for an
      equivalent JSON envelope — proving the reuse claimed in
      `contracts/run-agent-turn.md`'s "Reused unchanged" section actually holds.
- [X] T013 [P] [US1] Add
      `mcp-servers/protocol-mcp/tests/test_run_agent_turn_dispatch.py::test_stall_and_timeout_semantics_preserved`:
      assert `run_agent_turn`'s `on_stall`/`stall_after_s`/`timeout_s` parameters still behave as
      documented in `contracts/run-agent-turn.md` ("Timeout semantics unchanged") when dispatch goes
      through the WS client instead of a subprocess — i.e., a call that doesn't respond within
      `stall_after_s` still invokes `on_stall`, and a call that never responds still raises
      `TimeoutError` at `timeout_s`.

### Implementation for User Story 1

- [X] T014 [US1] In `mcp-servers/protocol-mcp/bgp/federation/gateway.py`, add
      `_build_agent_rpc_params(prompt, session_key, timeout_s, ...) -> dict` producing the exact
      params shape from `contracts/gateway-ws-rpc.md`'s "Agent turn request" section (`message`,
      `agentId`, `sessionKey`, `deliver: false`, `timeout`, `idempotencyKey`) — **without** a
      `cleanupBundleMcpOnRunEnd` key. This is a pure function, independently testable (feeds T011).
- [X] T015 [US1] In `gateway.py`, add `_extract_reply_from_ws_payload(payload: dict) -> tuple[str,
      int]` that mirrors the existing `_extract_reply(stdout: str)` (line 104) parsing logic —
      reusing its `_find`/`_extract_one` helper strategy — but reads from the WS response's
      `payload` dict directly instead of scanning `stdout` for JSON objects (no banner-noise problem
      exists on this path, since the WS response is already structured JSON, not subprocess stdout —
      this may let the new function be simpler than the 80-line stdout scanner it parallels).
- [X] T016 [US1] In `gateway.py`, modify `run_agent_turn()` (line 187): when `local=False` (the
      default, non-embedded gateway-dispatch path), replace the `asyncio.create_subprocess_exec(...
      "openclaw", "agent", ...)` block (lines 254–299) with: `client =
      get_gateway_ws_client()` (from `gateway_ws.py`, T009); `params =
      _build_agent_rpc_params(...)` (T014); `response = await client.call("agent", params,
      timeout_s)` (using the existing `on_stall`/`stall_after_s` extension logic adapted to await
      the WS call instead of the subprocess `comm` future — T013 governs this); `return
      _extract_reply_from_ws_payload(response["payload"])` (T015). The `local=True` embedded path
      (lines 255–263, `EnforcementRefused` gating) is untouched per
      `contracts/run-agent-turn.md`'s explicit scope note.
- [X] T017 [US1] In `gateway.py`, keep `_openclaw_bin()`, `_agent_env()`, and the original
      `_extract_reply(stdout)` function in place — they remain used by the `local=True` embedded
      path (T016 does not remove them, only stops calling them from the `local=False` branch).
- [X] T018 [US1] Create `scripts/measure-turn-latency.py` per quickstart.md and FR-016a: a
      standalone, repeatable script (runnable via `python3 scripts/measure-turn-latency.py`, no
      pytest harness required) that in one invocation (a) fires one trivial-answer turn against the
      live gateway and reads its `[trace:embedded-run]` log line (via `journalctl --user -u
      openclaw-gateway` or the gateway's configured log file) to extract the `bundle-tools:NNms`
      component, (b) times the same trivial turn end-to-end wall-clock, and (c) reads the last 20
      Siri/phone-originated turn durations from the session store and reports min/median/max — the
      exact three figures SC-009 requires be reproducible by "a later session with no knowledge of
      this work."
- [X] T019 [US1] Run `scripts/measure-turn-latency.py` (T018) against the fixed `gateway.py` (T016)
      on the live Border and record the before/after comparison against the spec's recorded baseline
      (37.9s / 26.8s / 36s–452s), including firing at least two turns in the same session to confirm
      the second is not slower than the first (SC-003) — this is the evidence artifact
      FR-017/SC-003/SC-008 requires exist before handoff to Pass 3.
- [X] T020 [US1] Manually verify FR-006 (no indefinitely stale tool set): with the fix in place,
      change NetGeniusClaw's own MCP config (e.g., toggle a `mcp.servers.*.enabled` flag in
      `~/.openclaw/openclaw.json`) while the gateway is running, then confirm a subsequent turn in
      an existing session picks up the change without requiring a Border restart — this exercises
      the existing `configFingerprint` invalidation logic in the gateway's own session-runtime cache
      (research.md Finding 2's cache-hit path already checks this; verify it still fires correctly
      when reached via WS RPC rather than CLI).
- [X] T021 [US1] Manually verify the Edge Case "two operators ask at the same moment" (spec.md):
      fire two concurrent `run_agent_turn()` calls with different `session_key`s through the fixed
      dispatch and confirm neither blocks on the other for the duration of a full toolkit rebuild —
      `GatewayWsClient`'s single connection (T004–T009) multiplexes concurrent RPC calls by request
      id (T006), so this should hold structurally; this task is the verification, not new code.

**Checkpoint**: User Story 1 is fully functional — every channel using `run_agent_turn()`
(chat.py, invocation.py, service.py — all unmodified callers) now benefits from the fix
automatically, since the signature and behavior contract are unchanged (contracts/run-agent-turn.md).

---

## Phase 4: User Story 2 - A spoken question gets an answer shaped for speech (Priority: P2)

**Goal**: Thread an optional `origin` marker from request to answer composition so voice-originated
questions get a short, plain-spoken answer, with zero behavior change for unmarked requests.

**Independent Test**: Per spec.md — submit a request marked `origin="voice"` and a functionally
identical unmarked request; confirm the first returns 1–2 plain sentences with no markup, and the
second returns exactly what today's unmodified path returns.

### Tests for User Story 2 ⚠️

- [X] T022 [P] [US2] Add
      `mcp-servers/protocol-mcp/tests/test_run_agent_turn_origin.py::test_no_origin_is_backward_compatible`:
      call `run_agent_turn(prompt, session_key)` with no `origin` argument and assert the RPC params
      built (T014's function) are byte-identical to what today's (pre-feature) call would have
      produced, minus the removed `cleanupBundleMcpOnRunEnd` key — this is SC-006's explicit test.
- [X] T023 [P] [US2] Add
      `test_run_agent_turn_origin.py::test_voice_origin_threads_into_rpc_params`: call
      `run_agent_turn(prompt, session_key, origin="voice")` and assert the built params include the
      voice-composition instruction/provenance marker per `contracts/gateway-ws-rpc.md`'s
      `extraSystemPrompt`/`inputProvenance` fields.
- [X] T024 [P] [US2] Add `test_run_agent_turn_origin.py::test_unrecognized_origin_normalizes_to_none`:
      call `run_agent_turn(prompt, session_key, origin="carrier-pigeon")` and assert it behaves
      identically to `origin=None` (FR-012) — the request must not fail, and no origin-specific
      instruction is added.

### Implementation for User Story 2

- [X] T025 [US2] In `gateway.py`, extend `run_agent_turn()`'s signature with `origin: str | None =
      None` per `contracts/run-agent-turn.md`. Normalize any value other than the literal string
      `"voice"` (or `None`) to `None` before use (FR-012).
- [X] T026 [US2] In `gateway.py`, extend `_build_agent_rpc_params` (T014) to accept `origin` and,
      when it is `"voice"`, add the voice-composition instruction to the RPC params'
      `extraSystemPrompt` — the instruction text: "Answer in one or two short, plain spoken
      sentences. No headers, bullet lists, or emphasis markup. If the full answer cannot fit,
      summarise honestly rather than truncate" (FR-010/FR-011/FR-011a — composed short from the
      start, never post-hoc truncated, per the spec's own clarification answer). When `origin` is
      `None`, `extraSystemPrompt` is omitted exactly as it is today (FR-008).
- [X] T027 [US2] In `gateway.py`, thread `origin` through to wherever the turn's record/log already
      captures metadata (FR-013) — reusing the existing field/mechanism per data-model.md's Request
      Origin entity ("reuses whatever field the session transcript already has available for
      recording provenance").
- [X] T028 [US2] Manually verify the Edge Case "a voice-marked question that returns an error or a
      refusal" (spec.md): trigger an error path with `origin="voice"` and confirm the error itself
      is spoken as a plain sentence, not a formatted diagnostic block — this depends on the
      voice-composition instruction (T026) applying uniformly regardless of whether the model's
      response is a normal answer or an error/refusal.
- [X] T029 [US2] Manually verify the Edge Case "a request arrives marked as voice-originated but is
      very long or carries an attachment" (spec.md): confirm `origin` only changes phrasing, never
      what NetGeniusClaw is willing to accept (no new validation/rejection path is introduced by T025/T026).

**Checkpoint**: User Stories 1 AND 2 both work independently. Existing callers (chat.py,
invocation.py, service.py) still call `run_agent_turn()` with no `origin` argument and see identical
behavior; the mobile side begins sending `origin="voice"` in Pass 3 (out of scope here, per spec.md
Assumptions).

---

## Phase 5: User Story 3 - A person waiting on an answer is served before background work (Priority: P3)

**Goal**: Ensure an interactive request is not queued behind unattended background work, without
adding overhead in the common idle case.

**Independent Test**: Per spec.md — occupy the Border with background work, then ask an interactive
question and confirm it is picked up ahead of the queued background work; with no competing work,
confirm no added overhead.

### Tests for User Story 3 ⚠️

- [X] T030 [P] [US3] Add
      `mcp-servers/protocol-mcp/tests/test_agent_prioritisation.py::test_no_overhead_when_idle`:
      with no background work queued, time an interactive `run_agent_turn()` call dispatched through
      `GatewayWsClient` and assert no measurable added latency versus the non-prioritised path
      (FR-015's "no added overhead in the common idle case") — a regression guard, since T016's fix
      alone already makes the idle case fast (confirmed live: T019's warm-turn measurement, 6.08s).
- [X] T031 [P] [US3] Add
      `test_agent_prioritisation.py::test_concurrent_sessions_do_not_serialize`: fire two concurrent
      `run_agent_turn()` calls on different session keys through the SAME `GatewayWsClient` instance
      and assert both complete in roughly the time of ONE call, not the sum of both — proving the
      client's request-id multiplexing (gateway_ws.py's `_pending` dict) doesn't itself introduce
      serialization, regardless of what either call's session happens to be doing.

### Implementation for User Story 3

- [X] T032 [US3] Investigated whether the gateway's own WS RPC protocol exposes an "interactive"
      priority lane. **Finding (research.md, "T032 finding")**: the `lane` values
      (`nested`/`cron-nested`/`subagent`/`cron`, `lanes-CI0_P-yC.js`) classify WHERE a
      nested/subagent/cron run's session state lives for isolation, not queue priority. The
      `queued_behind_active_work` classification in gateway logs is a per-session-key in-order
      queue, not a cross-session scheduler. `agents.defaults.maxConcurrent` is unset, so unrelated
      sessions already run fully concurrently (confirmed directly by T021: two session keys
      completed in ~33s total, not ~66s). No gateway-native priority mechanism exists to use.
- [X] T033 [US3] **Revised scope per T032's finding, documented in research.md**: auditing every
      real `run_agent_turn()` call site (`chat.py`, `invocation.py`, `service.py`'s `_edge_on_ask`
      — the phone's own interactive path — and `service.py`'s delegated-skill worker, which uses
      `local=True` embedded mode and never touches the WS RPC path) found **no NetClaw-authored
      scheduled/background call site that competes with an interactive request today** — the
      `netclaw-heartbeat` cron job runs entirely inside the OpenClaw gateway's own cron subsystem,
      never through this codebase's `run_agent_turn()`. Building new NetClaw-side priority-queue
      machinery for a background caller that does not exist would be speculative complexity for a
      hypothetical scenario (CLAUDE.md: "Don't design for hypothetical future requirements").
      FR-014/FR-015 are satisfied as-is by User Story 1's fix (T016) plus the existing,
      already-concurrent session model (T021/T031) — no code change needed beyond what US1 delivered.
- [X] T034 [US3] **No longer applicable per T033's revised scope** — there is no cron/heartbeat call
      site in `service.py` invoking `run_agent_turn()` to update (confirmed by audit in T033); the
      `netclaw-heartbeat` job is entirely gateway-internal. If NetGeniusClaw later adds its own scheduled
      background caller of `run_agent_turn()`, revisit T032's decision against that caller's real
      characteristics rather than the hypothetical one originally assumed here.

**Checkpoint**: All three user stories independently functional. Prioritisation (US3) is protective
per spec.md Assumptions — it does not change the measured idle-case latency numbers from US1, and
is already satisfied by US1's fix plus the gateway's existing (unbounded) cross-session concurrency.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification against the spec's full Success Criteria and Edge Cases, and evidence
capture for Pass 3 handoff.

- [X] T035 [P] Manually verify Edge Case "the very first request after the Border restarts" (spec.md):
      restart the gateway service, fire one turn, confirm it succeeds (may be slower — a one-time
      cold `getCatalog()` build is expected and acceptable per FR-004b) and does not present as a
      hang; fire a second turn immediately after and confirm it is fast (proving the fix's warm-reuse
      benefit kicks in from the second turn even after a cold restart).
- [X] T036 [P] Manually verify Edge Case "a tool NetGeniusClaw needs is slow or broken at the moment it is
      needed" (spec.md, FR-005): temporarily misconfigure one MCP server (e.g., point `fortinet-mcp`
      at an invalid script path) and confirm a turn that needs it surfaces the failure clearly in
      the answer rather than hanging or silently proceeding as if the tool didn't exist.
- [X] T036a Run `quickstart.md`'s "Verify capability retention" check (FR-004, FR-004a, SC-005):
      exercise each of the 8 configured MCP servers' tools once each through a real turn (not just
      `openclaw mcp doctor`) post-fix, confirming every one still answers correctly. If any
      capability is made ready on first use (FR-004a), exercise it twice in the same session and
      confirm the readiness cost is paid only on the first of the two (SC-005). Record the result —
      this is currently the only place in the task list that actually runs this check, so it must
      not be skipped before declaring the feature done.
- [X] T036b [P] Verify FR-003 across distinct real channels, not just distinct session keys: fire one
      post-fix turn through the Slack group session and one through a scheduled/cron-triggered call
      (`service.py`'s heartbeat path), and confirm both show the same latency improvement as the
      direct-CLI turns measured in T019. T021 already proves concurrent session keys don't block each
      other; this task proves the fix isn't accidentally channel-specific, closing the gap between
      "every caller of `run_agent_turn()` benefits automatically" (an architectural claim) and an
      observed result across more than one channel.
- [X] T037 Run the full SC-001–SC-009 verification pass from `quickstart.md` end-to-end on the live
      Border and record results (this is the single artifact that answers "is the feature done" per
      spec.md's binding-targets clarification, FR-018). T036a and T036b's results feed into this
      pass rather than duplicating it.
- [X] T038 [P] Update `mcp-servers/protocol-mcp/README.md` (or wherever `gateway.py`'s dispatch
      mechanism is documented, if anywhere) to describe the WS RPC dispatch path and its
      `cleanupBundleMcpOnRunEnd`-omission rationale, so a future session does not accidentally
      reintroduce the CLI-per-turn pattern this feature removes.
- [X] T039 Prepare the Pass 3 handoff note (per this spec's own Input line: "Pass 3 decision... to be
      made on the Mac against the evidence this pass produces") summarizing: the before/after
      measurement (T019/T037), whether the 18-second spoken-answer window is now appropriate given
      the new trivial-turn timing, and confirmation that the mobile app itself required zero changes
      for US1's latency fix to take effect. **This is the signal to move back to the Mac for
      phone-side testing.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS all user stories** — `GatewayWsClient`
  (T004–T010) is the shared infrastructure every story's dispatch change relies on.
- **User Story 1 (Phase 3)**: Depends on Foundational. This is the MVP — it alone satisfies the
  spec's stated priority ("nothing else in this spec produces a noticeable improvement while a ~27s
  toll remains on every turn").
- **User Story 2 (Phase 4)**: Depends on Foundational + US1's `_build_agent_rpc_params` (T014)
  existing (US2 extends it, T026) — cannot be usefully tested before US1 makes turns fast enough to
  be worth composing briefly for (per spec.md's own priority rationale).
- **User Story 3 (Phase 5)**: Depends on Foundational. Structurally independent of US1/US2's
  content, but its own spec.md rationale notes it's "second-order" and protective — sequence it
  last among the three stories as spec.md's priority order (P1 → P2 → P3) directs.
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Within Each Phase

- Tests (T011–T013, T022–T024, T030–T031) MUST be written and FAIL against the pre-fix code before
  their corresponding implementation tasks proceed.
- T014 → T015 → T016 is a strict sequence (each depends on the previous existing) — do not
  parallelize.
- T004 → T005 → T006 → T007 is a strict sequence within `gateway_ws.py` (each method depends on the
  class/prior method existing).

### Parallel Opportunities

- T001, T002, T003 (Setup) can run in parallel.
- T004 and T008 (different concerns within `gateway_ws.py` — class skeleton vs. config resolution)
  can be drafted in parallel, then merged before T005 proceeds.
- T011, T012, T013 (US1 tests) can run in parallel — different test functions, no shared state.
- T022, T023, T024 (US2 tests) can run in parallel.
- T030, T031 (US3 tests) can run in parallel.
- T035, T036, T038 (Polish) can run in parallel — independent verification/documentation tasks.

---

## Parallel Example: Phase 2 (Foundational)

```bash
# T004 and T008 touch the same new file but different concerns (class skeleton vs. config
# resolution helper) — draft as separate patches, merge before T005:
Task: "Create GatewayWsClient skeleton in mcp-servers/protocol-mcp/bgp/federation/gateway_ws.py"
Task: "Implement resolve_gateway_ws_config() in mcp-servers/protocol-mcp/bgp/federation/gateway_ws.py"
```

## Parallel Example: User Story 1 tests

```bash
Task: "test_no_cleanup_flag_sent in mcp-servers/protocol-mcp/tests/test_run_agent_turn_dispatch.py"
Task: "test_reply_extraction_from_ws_response in mcp-servers/protocol-mcp/tests/test_run_agent_turn_dispatch.py"
Task: "test_stall_and_timeout_semantics_preserved in mcp-servers/protocol-mcp/tests/test_run_agent_turn_dispatch.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) — confirm environment, create test scaffolding.
2. Complete Phase 2 (Foundational) — build and unit-test `GatewayWsClient` in isolation. This is the
   highest-risk new code in the whole feature (a hand-rolled persistent WS RPC client); get it right
   and tested before touching `gateway.py` at all.
3. Complete Phase 3 (US1) — swap `run_agent_turn()`'s dispatch, measure before/after (T019).
4. **STOP and VALIDATE**: T019's measurement against SC-001/SC-002/SC-003. This alone is the
   feature's entire value proposition per spec.md's own priority rationale — everything past this
   point is additive polish, not the fix.

### Incremental Delivery

1. Setup + Foundational → `GatewayWsClient` ready, unit-tested against a fake server (no live
   gateway dependency yet).
2. US1 → the actual latency fix, measured against the live Border → this is what unblocks moving
   to the Mac to re-test the mobile spoken-answer window (T039), which is this pass's stated purpose.
3. US2 → voice-aware composition, verifiable directly (no phone yet — Assumptions) even before
   Pass 3 adds the phone-side origin marker.
4. US3 → protective prioritisation, lowest urgency per spec.md's own P3 rationale.
5. Polish → full SC sweep + Pass 3 handoff note (T039) — **the explicit trigger to resume Mac-side
   testing**.

---

## Notes

- [P] tasks = different files or independent concerns, no blocking dependency.
- Every task's file path is absolute from `/home/johncapobianco/netclaw/` per plan.md's Project
  Structure section.
- T016 is the single task that actually fixes the measured 27s cost (research.md Findings 2/3) —
  every other task either builds its prerequisite (T004–T015), extends it additively (T025–T029,
  T032–T034), or verifies it (T019–T021, T028–T029, T035–T037).
- Commit after each task or logical group, consistent with repo convention.
- Do not skip T011–T013: they are what proves the root cause (Finding 2) is actually fixed, not just
  plausibly fixed — the single most important regression to prevent reintroducing.
