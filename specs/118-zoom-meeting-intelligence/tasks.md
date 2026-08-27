# Tasks: NetGeniusClaw for Zoom — Meeting Intelligence (MVP)

**Input**: Design documents from `/specs/118-zoom-meeting-intelligence/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not explicitly requested in the spec beyond the safety-boundary classification (US4), the
extractor's core recognition logic (US1), buffer-lifecycle correctness, and a pre-existing-capability
regression check (Constitution Principle XV) — those get targeted tests since they are safety-,
correctness-, or constitution-critical; broader test scaffolding is not generated for every task.

**Organization**: Tasks are grouped by user story (US1–US5, per spec.md) to enable independent
implementation and testing of each.

**Revision note (2026-08-17)**: This version incorporates all `/speckit.analyze` remediations —
T013 (buffer-destruction test, was gap M2), T029 (read-path-without-extra-approval check, was gap
M1), and T053 (pre-existing-capability regression check, was CRITICAL gap C1) are new versus the
first draft; all other tasks are renumbered accordingly. `data-model.md`'s buffer bound and
`spec.md`'s SC-009 delay were also pinned to concrete numbers (were H2/H1) — reflected in T006's and
T020's wording below.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)

## Path Conventions

Per plan.md's Structure Decision: new MCP server at `mcp-servers/zoom-rtms-mcp/`, one new module in
the existing federation daemon at `mcp-servers/protocol-mcp/bgp/federation/zoom_channel.py`, one new
browser surface at `ui/netclaw-zoom-app/`, one new skill at `workspace/skills/zoom-meeting-context/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create `mcp-servers/zoom-rtms-mcp/` directory with `pyproject.toml`/`requirements.txt`
      (FastMCP, Zoom's official RTMS Python SDK — research.md R4) and empty `__init__.py`
- [X] T002 [P] Add `.gitignore` negation entry for `mcp-servers/zoom-rtms-mcp/` (per
      `docs/ADDING-AN-MCP.md` step 1 — new server dirs are otherwise silently untracked)
- [X] T003 [P] Add `zoom-rtms-mcp` entry to `config/openclaw.json` (repo-relative `command`/`args`,
      no absolute paths — per `docs/ADDING-AN-MCP.md` step 2)
- [X] T004 [P] Add the official Zoom Meetings MCP to `EXTERNAL_INTEGRATIONS` in
      `scripts/verify-inventory-counts.py` with reason `remote/OAuth` (research.md R6, `docs/ADDING-AN-MCP.md` step 3 — no `config/openclaw.json` entry for this one)
- [X] T005 [P] Add new environment variables to `.env.example` (names + comments only, no values):
      `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET`, `ZOOM_ACCOUNT_ID`, `ZOOM_RTMS_WEBHOOK_SECRET`,
      `ZOOM_MEETING_MCP_CREDENTIAL` (placeholder name pending R6 confirmation)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Implement `MeetingSession`/`LiveContextBuffer`/avatar-state dataclasses in
      `mcp-servers/zoom-rtms-mcp/models.py` per data-model.md — the buffer is bounded to **the last
      15 minutes of activity, capped at 500 entries, whichever limit is reached first** (pinned
      2026-08-17 remediation; both bounds enforced together)
- [X] T007 Implement `mcp-servers/zoom-rtms-mcp/webhook.py`: receive Zoom's
      `meeting.rtms_started`/`meeting.rtms_stopped` webhook, validate the HMAC signature against
      `ZOOM_RTMS_WEBHOOK_SECRET` (the URL-validation handshake — confirmed working via this
      session's stub server), and create/**destroy** (not merely flag) the corresponding
      `MeetingSession` on stop
- [X] T008 Implement `mcp-servers/zoom-rtms-mcp/rtms_listener.py`: per-meeting RTMS SDK session
      (transcript, chat, active-speaker, screen-share-start/stop signals only — no raw audio/video,
      per FR-016/research.md R4), appending entries to the `MeetingSession`'s `LiveContextBuffer`,
      and setting `connection_state` transitions (`connecting`/`live`/`degraded`/`closed`)
- [X] T009 Implement `mcp-servers/zoom-rtms-mcp/server.py`: FastMCP entrypoint with tool stubs for
      all eight tools in `contracts/zoom-rtms-mcp-tools.md` (`zoom_enable_listening`,
      `zoom_disable_listening`, `zoom_list_active_meetings`, `zoom_meeting_status`,
      `zoom_recent_transcript`, `zoom_recent_chat`, `zoom_active_speaker`, `zoom_live_context`) wired
      to the models/webhook/listener above
- [X] T010 [P] Implement `mcp-servers/protocol-mcp/bgp/federation/zoom_channel.py`: the `ZOOM_METHODS`
      allowlist and loopback-only channel per `contracts/zoom-channel-internal.md`, mirroring
      `edge.py`'s restricted-method-dispatch pattern (research.md R1) — handler bodies for
      `n2n/zoom/investigate`/`investigate_result`/`session_closed` stubbed to be filled in by US1
- [X] T011 [P] Implement `mcp-servers/zoom-rtms-mcp/zoom_channel_client.py`: the loopback client side
      that calls into T010's channel
- [X] T012 [P] Add `tests/n2n/test_zoom_channel.py` skeleton in `mcp-servers/protocol-mcp/` (mirrors
      the existing `tests/n2n/test_*` convention) and
      `mcp-servers/zoom-rtms-mcp/tests/__init__.py`
- [X] T013 [P] `mcp-servers/zoom-rtms-mcp/tests/test_webhook.py`: automated test asserting the
      `MeetingSession` object is actually gone (not merely flagged ended) after a stop webhook, and
      that its `LiveContextBuffer` is unreachable afterward — covers SC-006 (was analyze finding M2)

**Checkpoint**: `zoom-rtms-mcp` starts cleanly (`scripts/check-server-startup.py --only zoom-rtms-mcp`
passes — a timeout on stdio is success per that script's own convention), and the Border-side channel
module imports without error. No user-visible behavior yet.

---

## Phase 3: User Story 1 - Ask a live network question during a meeting and get an evidence-backed answer (Priority: P1) 🎯 MVP

**Goal**: A recognized present-tense, first-person investigation request reaches Border's existing
routing path and a synthesized, evidence-backed answer appears in the shared panel.

**Independent Test**: Per spec.md — start a meeting with listening enabled, ask a
location+technology+time-bounded question aloud, confirm an evidence-backed answer appears in the
panel without any bot appearing as a video participant.

- [X] T014 [P] [US1] Implement `mcp-servers/zoom-rtms-mcp/extractor.py`: deterministic recognizer for
      present-tense, first-person investigation requests — extracts location/technology/time-window
      (research.md R2). Happy-path recognition only in this task; safety-boundary classification is
      T025 (US4)
- [X] T015 [US1] `mcp-servers/zoom-rtms-mcp/tests/test_extractor.py`: unit tests for T014's happy-path
      extraction (location/technology/time-window correctly pulled from example utterances)
- [X] T016 [US1] Wire `extractor.py` output into `zoom_channel_client.py` → `n2n/zoom/investigate`
      (contracts/zoom-channel-internal.md request shape)
- [X] T017 [US1] Implement the Border-side `n2n/zoom/investigate` handler in `zoom_channel.py`:
      construct a prompt from the extracted fields, call
      `run_agent_turn(prompt=..., session_key=f"n2n-zoom-{meeting_uuid}")` (research.md R1, mirroring
      `chat.py`'s autonomous-turn pattern), create an `InvestigationRequest` record, emit to GAIT
- [X] T018 [US1] Implement `n2n/zoom/investigate_result` push from `zoom_channel.py` back to
      `zoom-rtms-mcp`, best-effort delivery semantics (mirrors `n2n/edge/task_progress` precedent)
- [X] T019 [US1] On receiving `investigate_result`, update `MeetingSession.avatar_state` and store
      the result for `zoom_live_context`/panel delivery in `zoom-rtms-mcp`
- [X] T020 [US1] Implement `mcp-servers/zoom-rtms-mcp/panel_feed.py`: companion WebSocket server
      (research.md R3) pushing `avatar_state`/`topic_detected`/`investigation_result`/
      `connection_state` messages per `contracts/zoom-app-panel-feed.md`, propagated to connected
      clients within 2 seconds of the underlying state change (SC-009, pinned 2026-08-17)
- [X] T021 [US1] Implement `ui/netclaw-zoom-app/panel.html` + `panel.js`: connects to `panel_feed.py`,
      renders listening → thinking → investigating → answered avatar states and the evidence-backed
      result
- [X] T022 [US1] Handle the ambiguous-location/technology edge case: `routing_outcome=failed_ambiguous`
      surfaced in the panel rather than guessing silently
- [X] T023 [US1] Handle the no-registered-tooling edge case: `routing_outcome=failed_no_tooling`
      surfaced plainly
- [X] T024 [US1] Handle the simultaneous speech+chat duplicate edge case: collapse to one
      `InvestigationRequest`/`request_id`, not two

**Checkpoint**: User Story 1 is fully functional and independently testable/demoable per
`quickstart.md` steps 1–4.

---

## Phase 4: User Story 4 - A casual remark is never treated as authorization (Priority: P1)

**Goal**: Hypothetical/past-tense/third-party speech never reaches the point of constructing an
investigate/agent-turn request; any genuine write/config-change request still requires NetGeniusClaw's
existing device-write approval gate, unchanged; a genuine read/diagnostic request executes without
any extra approval step.

**Independent Test**: Per spec.md — say a hypothetical/past-tense/third-party sentence describing a
change, confirm nothing is attempted or queued; separately issue a direct change request and confirm
it's held for explicit approval; separately confirm a plain read request is not slowed down by any
new approval step.

- [X] T025 [US4] Extend `extractor.py` (T014) with the safety-boundary classifier: recognizes
      hypothetical/past-tense/third-party-attributed phrasing and suppresses the call to
      `zoom_channel_client.py` entirely for those cases — the boundary is enforced by never sending
      the request, not by filtering downstream (research.md R2/R7)
- [X] T026 [US4] `mcp-servers/zoom-rtms-mcp/tests/test_extractor.py`: add classification-boundary unit
      tests (hypothetical/past-tense/third-party vs. genuine present-tense-first-person requests) —
      extends T015's test file
- [X] T027 [US4] Fields added and wired end-to-end (`InvestigationRequest`/`ApprovalDecision`,
      data-model.md). **Honest gap, not hidden**: no real signal exists yet to actually *set*
      `write_action_detected=True` — `zoom_channel.py`'s `_run_investigation` documents this in detail
      inline. The device-write approval gate itself is unaffected/unbypassed; this is only an
      audit-visibility gap for the Zoom-originated record specifically.
- [X] T028 [US4] `mcp-servers/protocol-mcp/tests/test_zoom_channel.py`: integration test confirming a
      direct configuration-change request routed through `n2n/zoom/investigate` still surfaces
      through the existing device-write approval gate rather than executing automatically
- [X] T029 [US4] `mcp-servers/protocol-mcp/tests/test_zoom_channel.py`: companion integration test
      (addresses analyze finding M1 / FR-006, FR-007) confirming a genuine read/diagnostic request
      routed the same way completes *without* any additional approval step being introduced by this
      feature — i.e., the existing read path is provably untouched, not just assumed unaffected

**Checkpoint**: User Stories 1 AND 4 both work — the MVP safety boundary is in place alongside the
core investigation flow.

---

## Phase 5: User Story 2 - Correlate today's discussion with a past meeting (Priority: P2)

**Goal**: Historical meeting content is searchable and compared against current network state.

**Independent Test**: Per spec.md — reference a real past meeting by topic during a live call,
confirm retrieval and a plain match/mismatch statement against current state.

- [ ] T030 [US2] **Not resolvable from this environment** — needs live access to Zoom's own connector
      setup flow, not just documentation. `EXTERNAL_INTEGRATIONS` entry (T004) is added generically
      ("Zoom Meetings MCP") pending this confirmation; `zoom_search_historical_meetings` (T031) is
      implemented as an honest pass-through stub in the meantime, per research.md R6.
- [X] T031 [US2] Implement `zoom_search_historical_meetings` tool in `server.py` (T009) as a thin
      pass-through to the official Zoom MCP, per `contracts/zoom-rtms-mcp-tools.md` — no local
      persistence of results (data-model.md `HistoricalMeetingReference`)
- [X] T032 [P] [US2] Create `workspace/skills/zoom-meeting-context/SKILL.md`: the historical-
      correlation skill — calls `zoom_search_historical_meetings`, then states whether current
      network state (via the same Member-Claw routing US1 uses) matches or differs from what was
      found
- [X] T033 [US2] Handle the "no matching past meeting" case: the skill states this plainly rather
      than presenting an unrelated result as relevant

**Checkpoint**: User Story 2 works independently of US3/US5.

---

## Phase 6: User Story 3 - Every participant can see NetGeniusClaw's status, not just the host (Priority: P2)

**Goal**: Live status/avatar/results are visible identically to every viewer, including an
unauthenticated guest, via Collaborate Mode/Guest Mode.

**Independent Test**: Per spec.md — join as a guest with nothing installed/authenticated, confirm
identical live state to the host.

- [X] T034 [US3] Wire Zoom Apps SDK Collaborate Mode into `ui/netclaw-zoom-app/panel.js`
      (`onCollaborateChange`/`startCollaborate`/`joinCollaborate`/`leaveCollaborate` — research.md R3,
      `contracts/zoom-app-panel-feed.md`) so every viewer for a `meeting_uuid` shares identical state
- [X] T035 [US3] Enable Guest Mode handling in `panel.js`/manifest (already toggled on in the live
      Zoom app config this session) — confirm an unauthenticated viewer's connection to
      `panel_feed.py` behaves identically to an authenticated one
- [X] T036 [P] [US3] Track `MeetingSession.viewers` (data-model.md) in `panel_feed.py` on
      `viewer_joined` messages, for SC-004 verification
- [X] T037 [US3] Confirm `panel_feed.py` broadcasts (not per-viewer-state) so avatar_state/results
      reach all current connections simultaneously

**Checkpoint**: User Stories 1, 2, 3, 4 all independently functional.

---

## Phase 7: User Story 5 - Camera-overlay avatar on a consenting participant's own feed (Priority: P3)

**Goal**: A participant can opt their own outgoing video into an avatar overlay reflecting the same
state as the panel, with no independent audio and no effect on anyone else's feed.

**Independent Test**: Per spec.md — enable the overlay on your own feed, confirm it appears/disappears
correctly and never carries audio.

- [ ] T038 [US5] **Confirmed live 2026-08-21: Layers API is not available for this app at all.**
      Checked the Surface features list on a real Marketplace app with correct scopes/config
      otherwise complete — "Layers"/"Camera mode" doesn't appear anywhere, not even grayed-out or
      marked pending-review. This is an entitlement Zoom doesn't expose through this app-builder flow,
      not a temporary review-queue delay. T039/T040 were built regardless per the spec's own
      graceful-degradation note; **US5 is deferred, not blocked-on-review** — see
      `docs/ZOOM-MEETING-INTELLIGENCE.md`'s "Known gaps" section.
- [X] T039 [US5] Implement `ui/netclaw-zoom-app/overlay.js`: Layers API Camera-mode integration
      rendering the current `avatar_state` as a self-camera overlay
- [X] T040 [US5] Implement `camera_overlay_enable`/`camera_overlay_disable` handling in
      `panel_feed.py`, restricted to the sending participant's own `participant_id`
      (`contracts/zoom-app-panel-feed.md`), tracking `CameraOverlayEnrollment` (data-model.md)
- [ ] T041 [US5] **Deferred alongside T038** — the camera-off edge case can't be exercised without
      Layers API access at all (per T038), so the reasoning below remains unverified against the real
      SDK, not because of a missing live meeting: reasoned to be Zoom's own inherent Layers Camera-
      mode behavior (no camera feed = nothing for the overlay to render onto, resumes automatically
      once a feed exists again). Left unchecked rather than marked done on an assumption.
- [ ] T042 [US5] **Deferred alongside T038** — same reason: no-audio confirmation needs a live
      overlay session, which needs Layers API access this app doesn't have. The design (research.md
      R8, `overlay.js`) never attaches an audio path by construction, but that's unverified live.

**Checkpoint**: User Stories 1–4 are independently functional and live-verified. US5 is explicitly
deferred — confirmed (not just unverified) that Layers API access is unavailable for this app.

---

## Phase 8: Polish & Cross-Cutting Concerns

Per Constitution Principle XI (Full-Stack Artifact Coherence) — all required before this feature is
considered complete, not optional cleanup:

- [X] T043 [P] Update `README.md` (description, architecture note, tool/skill/MCP counts)
- [X] T044 [P] Update `SOUL.md` (skill definition, capability summary, counts)
- [X] T045 [P] Create `mcp-servers/zoom-rtms-mcp/README.md` (tool inventory, env vars, transport,
      install steps)
- [X] T046 [P] Update `TOOLS.md` (infrastructure reference)
- [X] T047 [P] Update `scripts/lib/catalog.sh` (one new `"zoom-rtms-mcp|...|...|..."` entry)
- [X] T048 [P] Update `scripts/lib/install-steps.sh` (`component_install_zoom_rtms_mcp()`)
- [X] T049 Run `scripts/verify-catalog-coverage.py` and `scripts/reconcile-mcp.py`; fix any reported
      gaps before proceeding
- [X] T050 [P] Add a Zoom-integration status node to `ui/netclaw-visual/` (Constitution Principle X)
- [X] T051 Write `docs/ZOOM-MEETING-INTELLIGENCE.md`: a consolidated operator guide — this feature's
      `quickstart.md` prerequisites plus the concrete lessons captured live during this session's own
      Marketplace setup (correct RTMS scope names `rtms:read:rtms_started`/`rtms:read:rtms_stopped`
      plus `meeting:read:meeting_chat`, the auto-start toggle staying grayed out until those scopes
      exist, the DNS/ngrok-stub unblock technique for the "Add app" reachability check, which manifest
      fields are/aren't scriptable, the least-privilege scope exclusions and why) — written for both
      the operator (John) and anyone else standing up this feature fresh
- [X] T052 Record a GAIT session log entry for this feature's implementation (Constitution Principle IV)
- [X] T053 **Real result**: `python3 -m pytest tests/n2n/ -q` → 470 passed, 1 failed
      (`test_gateway_stall_extends_window_and_completes`). Verified via `git stash` A/B test that this
      failure is **pre-existing and unrelated** — identical failure with every change from this
      session stashed out. `scripts/trace-skill.py` run against 2 pre-existing skills
      (`suzieq-observability`, `bgp-registry-intel`) plus the new `zoom-meeting-context` — all three
      resolve cleanly. `scripts/reconcile-mcp.py` PASS on all 7 surfaces including `startup`.
- [X] T054 **Fully live end-to-end, real meeting, real device (2026-08-20)** — a spoken question in
      a real Zoom meeting ("Can you check R1, is the interface status okay?") was recognized,
      routed through the Border to a real the agent Sonnet 5 agent turn, which called pyATS against the
      real DevNet sandbox device, and the real answer rendered back in the live panel — watched
      directly by the operator. US1/US3/US4 (core investigation, panel visibility, safety boundary)
      all confirmed live. RTMS Developer Pack billing confirmed active and metering correctly.
      Roughly a dozen real, previously-undiscovered bugs were found and fixed only by actually doing
      this, across every layer:
      - `rtms_listener.py` called a nonexistent `rtms.connect()` — rewritten against the real
        installed SDK's actual API (`Client()`/`join()`/`on_transcript_data()`/`on_join_confirm()`)
      - SDK transcript callbacks fire from a bare OS thread with no asyncio loop — crashed the whole
        process (`recognition.on_new_entry` now uses `run_coroutine_threadsafe` against the
        server's own background loop, matching `server.py`'s existing pattern)
      - `webhook.py`/`panel_feed.py` were missing `X-Content-Type-Options`/`Referrer-Policy` —
        Zoom's client-side app-launch validator silently aborts without the full OWASP header set
      - `panel.js`'s unconditional Collaborate Mode capability request could kill the whole panel
        before `connect()` ever ran — degrades gracefully to core capabilities now
      - transcript `data` arrives as raw `bytes`, not `str` — undecoded, silently broke
        `extractor.classify()`'s `str`-vs-`bytes` comparison
      - the RTMS SDK needs `ZM_RTMS_CLIENT`/`ZM_RTMS_SECRET` env vars (mirrored from
        `ZOOM_CLIENT_ID`/`SECRET`) and an explicit `TranscriptParams.src_language` — silent no-op
        without either
      - **critical, Marketplace-side**: `zoomSdk.getMeetingContext()`/`getUserContext()` both reject
        with `No Permission for this API [code:80004, reason:app_not_support]` on this app —
        confirmed via live devtools console, independently corroborated by a second AI's review of
        the same evidence. Root cause not resolved (needs Zoom-side investigation — app build type,
        review status, or a separate manifest capability declaration, per the recap in
        `docs/` or the session's own scratch notes) — **worked around**, not fixed: the panel now
        asks this server directly which meeting is active (`identify_by_active_meeting` /
        `identified`, over the same WebSocket) since the server already knows the true meeting_uuid
        authoritatively from the RTMS webhook, independent of the Zoom SDK entirely
      - Zoom's own client-injected CSP blocks inline `<style>` regardless of this server's own CSP
        header — moved to an external `panel.css`
      - added an immediate "Looking into it…" interim push the moment a question is accepted, since
        the real agent turn can take ~1-3 minutes — previously looked like nothing was happening
      - the gateway had 93 registered MCP servers (mostly unrelated leftovers), and the demo device
        collided in name with an old unreachable CML-lab "R1" — both trimmed, cutting total
        turnaround from ~5 minutes to ~1 minute
      Still not live-verified: US2 (historical meeting correlation, needs the official Zoom Meetings
      MCP connector — T030) and US5 (camera-overlay avatar, needs Layers API review — T038/T042).
- [ ] T055 **Drafted (2026-08-20), awaiting John's review before publishing** — not yet published
      anywhere per Constitution Principle XVII's own requirement. Draft lives outside the repo at
      `/private/tmp/agent-503/.../scratchpad/zoom-meeting-intelligence-blog-draft.md` (this
      session's scratchpad, not committed) pending explicit go-ahead to publish.

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. Blocks all user stories.
- **US1 (Phase 3, P1)**: Depends on Foundational. No dependency on other stories — this is the MVP.
- **US4 (Phase 4, P1)**: Depends on Foundational; extends the same `extractor.py`/`zoom_channel.py`
  files US1 creates, so in practice follows immediately after US1 rather than running fully parallel,
  despite both being P1.
- **US2 (Phase 5, P2)**: Depends on Foundational + T004/T009 only — independent of US1's investigate
  path, can proceed in parallel with US1/US4 if staffed separately.
- **US3 (Phase 6, P2)**: Depends on Foundational + T020/T021 (panel must exist) — practically follows
  US1, though its Collaborate/Guest Mode logic is additive, not a rewrite.
- **US5 (Phase 7, P3)**: Depends on Foundational + US3's panel/avatar-state plumbing, and on T038's
  access confirmation.
- **Polish (Phase 8)**: Depends on all desired user stories being complete. T053 (regression check)
  MUST run before T054 (demo validation) — a demo passing over an undetected regression would be a
  false signal.

### Parallel Opportunities

- T002–T005 (Setup) in parallel.
- T010–T013 (Foundational) in parallel with each other, after T006–T009.
- US2 (Phase 5) can run in parallel with US1/US4 (Phases 3–4) — different files, no shared state.
- Polish tasks T043–T048, T050 in parallel.

## Implementation Strategy

### MVP First

1. Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1) → Phase 4 (US4).
2. **STOP and validate**: US1+US4 together are the smallest safe, demoable increment — live
   investigation with the safety boundary already in place. Don't demo US1 without US4.
3. Add US2, then US3, then US5 (if T038 confirms access), each independently validated per its own
   Independent Test before moving on.

### Incremental Delivery

Each phase checkpoint above is a real stopping point — the feature is safe to pause at any checkpoint
without leaving a half-enforced safety boundary in place, because US4 ships together with US1 rather
than after it.
