---

description: "Task list for NetGeniusClaw Mobile Siri / App Intents Integration (B1a)"
---

# Tasks: NetGeniusClaw Mobile Siri / App Intents Integration (B1a)

**Input**: Design documents from `/specs/111-siri-app-intents/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included, matching this repo's established TDD discipline for the mobile app (specs 099–110) —
write each Dart/Python test first, confirm it fails for the right reason, then implement.

**Organization**: Tasks are grouped by user story (US1 = AskBorderIntent P1/MVP, US2 = PendingApprovalsIntent
P2, US3 = BorderHealthIntent P2), per spec.md's priorities.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to US1/US2/US3
- 🔌 **DEVICE**: Cannot be completed or verified without the operator and a real, enrolled iPhone — per
  spec.md's Context and every prior mobile spec's verification standard

---

## Phase 1: Setup

**Purpose**: Confirm the branch is in a clean, buildable state before any new code lands.

- [x] T001 Confirm `flutter analyze` and `flutter test` are green on `mobile/netclaw-mobile` at the start of this branch (baseline, no code change)
- [x] T002 Confirm `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` succeeds at the start of this branch (baseline, no code change) — first attempt failed on a stale `ios/Flutter/ephemeral/` cache (`FlutterGeneratedPluginSwiftPackage` regenerated with a hardcoded iOS 13 floor instead of reading `AppFrameworkInfo.plist`'s `MinimumOSVersion` 16.2, spec 099's own documented fix). `flutter build ios --config-only --debug` regenerated it correctly; **`BUILD SUCCEEDED`** on retry. Not a real blocker — see README platform-notes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared plumbing all three intents need — the cold-connect helper (Dart) and the
deterministic-teardown engine runner (Swift). Building this once, here, avoids tripling the same 10s-timeout/
error-classification and engine-lifecycle logic across three otherwise-independent intents.

**⚠️ CRITICAL**: No user story phase begins until this phase is complete.

- [x] T003 [P] Write `test/headless_connect_test.dart`: given no `EnrollmentStore` file, `connectHeadless()` throws a `NotEnrolledError`; given a connect attempt that never completes, it throws a `ConnectTimeoutError` after 10s (fake the delay, don't sleep in the test); given a successful connect, it returns a live `EdgeClient`. Confirm it fails (the source file doesn't exist yet).
- [x] T004 Implement `lib/ncfed/headless_connect.dart`: `connectHeadless({Duration timeout = const Duration(seconds: 10)})` — loads `StoredEnrollment` via `EnrollmentStore` (matching `background_refresh.dart`'s existing precedent), throws `NotEnrolledError` if none exists, otherwise opens `EdgeClient.reconnect()` wrapped in `.timeout(timeout)` and throws `ConnectTimeoutError` on expiry, returning the connected `EdgeClient` on success (research.md R6). Confirm T003 now passes.
- [x] T005 [P] Implement `ios/Runner/HeadlessEngineRunner.swift`: a small Swift helper that constructs a plain `FlutterEngine` (never `FlutterEngineGroup`, research.md R1), registers only `EdgeIdentityPlugin`, runs the given Dart entrypoint name, wires a `FlutterMethodChannel` for the completion callback, and guarantees teardown (`defer`-style, covering success, a Dart-reported error, and a Swift-side timeout firing first) per FR-009/research.md R7.

**Checkpoint**: Foundation ready — US1, US2, US3 can each proceed independently.

---

## Phase 3: User Story 1 - Ask NetGeniusClaw a question by voice (Priority: P1) 🎯 MVP

**Goal**: "Hey Siri, ask NetGeniusClaw [question]" submits the question headlessly, speaks a brief acknowledgment
without opening the app, and later delivers the real answer via a local notification.

**Independent Test**: Force-quit the app, invoke the Siri phrase with a real question, confirm a spoken
acknowledgment within a few seconds with the app never opening, then confirm a local notification with the
real answer arrives once the Border responds (per quickstart.md's User Story 1 section).

### Tests for User Story 1

- [x] T006 [P] [US1] Write `test/ask_border_headless_test.dart`: given a fake `EdgeAskClient` whose `ask()` resolves with a `task_id`, `askBorderMain`'s core logic reports the acknowledgment before the fake's `updates` stream ever emits (proves FR-003's non-blocking requirement); given the fake's `updates` stream later emits a matching `ask_result`, confirm exactly one `ConversationStore` write with `origin: 'siri'` and exactly one call into a fake `LocalNotifications.postChatNotification(...)`. Confirm it fails (source doesn't exist yet).
- [x] T007 [P] [US1] Extend `test/conversation_store_test.dart`: a turn written with `origin: 'siri'` round-trips through `toJson()`/`fromJson()` unchanged, exactly as `'watch'` already does. Confirm it fails first if the assertion doesn't already hold (it likely already does, since `origin` is an unconstrained `String` — confirm rather than assume, per research.md R5).

### Implementation for User Story 1

- [x] T008 [US1] Update the `origin` doc comment in `lib/ncfed/conversation_store.dart` to document `'siri'` as a third valid value alongside `'phone'`/`'watch'` (no code change — `origin` is already an unconstrained `String`, research.md R5). Confirm T007 passes.
- [x] T009 [US1] Implement `lib/ncfed/ask_border_headless.dart`'s `@pragma('vm:entry-point') askBorderMain()`: use `connectHeadless()` (T004); on `NotEnrolledError`/`ConnectTimeoutError`/any connect failure, report a distinct failure string over the method channel and return (FR-008/FR-010) without ever reaching the ask step; otherwise call `EdgeAskClient.ask(question)`, immediately persist a `ConversationStore.addPending(...)` turn with `origin: 'siri'` (FR-005), report the acknowledgment over the method channel as soon as the `task_id` comes back (FR-003), then keep the engine alive listening on `updates` for a bounded ~25s window (research.md R8) for the matching `ask_result` — if it arrives in time, finalize the turn via `updateState(...)` and call `LocalNotifications.postChatNotification(...)` directly (FR-004, research.md R2) before tearing down; if the window elapses first, tear down anyway (FR-009) and leave the turn `'pending'` for `reconcileStaleTurns` to finish later (research.md R8). Confirm T006 passes.
- [x] T010 [US1] Implement `ios/Runner/AskBorderIntent.swift`: an `AppIntent` with a `question: String` `@Parameter`, using `HeadlessEngineRunner` (T005) to run `askBorderMain`, returning `some IntentResult & ProvidesDialog` with the spoken acknowledgment (or the distinct failure/not-set-up dialog per FR-008/FR-010).
- [x] T011 [US1] Create `ios/Runner/NetClawShortcuts.swift`: an `AppShortcutsProvider` declaring `AskBorderIntent`'s natural-language phrase(s) (FR-001).
- [x] T012 [US1] Run `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` and fix any compile error before proceeding. — `BUILD SUCCEEDED` (after the stale-cache fix in T002).
- [ ] T013 [US1] 🔌 **DEVICE** — With the operator: force-quit the app on the enrolled test iPhone, run quickstart.md's User Story 1 verification steps in full (happy path, Border-unreachable failure, not-enrolled failure, Action Button, Shortcuts automation). Record the outcome in `mobile/netclaw-mobile/README.md`'s platform-notes section.

**Checkpoint**: User Story 1 is fully functional and independently shippable (MVP).

---

## Phase 4: User Story 2 - Ask how many approvals are pending, by voice (Priority: P2)

**Goal**: "Hey Siri, ask NetGeniusClaw how many approvals are pending" speaks the live, current count directly.

**Independent Test**: With the app backgrounded/terminated and at least one real pending approval on the
Border, invoke the phrase and confirm the spoken count matches the Approvals tab (quickstart.md User Story 2).

### Tests for User Story 2

- [x] T014 [P] [US2] Write `tests/n2n/test_edge_approvals_list.py` (repo root — matching the existing per-RPC test convention of `tests/n2n/test_edge_approval.py`/`test_edge_ask.py`/`test_edge_heartbeat.py`, run via `python3 -m pytest tests/n2n/test_edge_approvals_list.py` from repo root, per `tests/n2n/conftest.py`'s `sys.path` shim): asserting a new `n2n/edge/approvals_list` handler returns `{"count": N}` matching `Authorizer.pending_approvals()`'s current row count, and that the count changes when an approval is resolved. Confirm it fails (handler doesn't exist yet).
- [x] T015 [P] [US2] Write `test/pending_approvals_headless_test.dart`: given a fake `EdgeClient` whose `n2n/edge/approvals_list` call resolves with `{"count": 3}`, `pendingApprovalsMain`'s core logic reports "3" (or the exact phrasing FR-006 requires) over the method channel; given `{"count": 0}`, confirm the explicit zero-case wording (not a bare "0"). Confirm it fails.

### Implementation for User Story 2

- [x] T016 [US2] Add `"n2n/edge/approvals_list"` to the method allowlist in `mcp-servers/protocol-mcp/bgp/federation/edge.py`, matching the existing entries' style (data-model.md).
- [x] T017 [US2] Implement the handler in `mcp-servers/protocol-mcp/bgp/federation/service.py`: on `n2n/edge/approvals_list`, call `self.authz.pending_approvals()` unchanged and return `{"count": len(rows)}` — no new authorization check (the channel is already authenticated at connect time), mirroring `edge_self_status`'s shape. Confirm T014 passes.
- [x] T018 [US2] Implement `lib/ncfed/pending_approvals_headless.dart`'s `@pragma('vm:entry-point') pendingApprovalsMain()`: use `connectHeadless()` (T004) with the same not-enrolled/unreachable failure handling as T009, then call the new `n2n/edge/approvals_list` method with a 10s timeout (research.md R6), and report the spoken count (with the explicit zero-case wording, FR-006) over the method channel before tearing down. Confirm T015 passes.
- [x] T019 [US2] Implement `ios/Runner/PendingApprovalsIntent.swift`: a parameterless `AppIntent` using `HeadlessEngineRunner` (T005) to run `pendingApprovalsMain`, returning the spoken count or the distinct failure/not-set-up dialog.
- [x] T020 [US2] Extend `ios/Runner/NetClawShortcuts.swift`'s `AppShortcutsProvider` with `PendingApprovalsIntent`'s phrase(s) (FR-001).
- [x] T021 [US2] Run the `xcodebuild` command from T012 and fix any compile error before proceeding. — `BUILD SUCCEEDED`.
- [ ] T022 [US2] 🔌 **DEVICE** — With the operator: with at least one real pending approval on the Border and the app backgrounded/terminated, run quickstart.md's User Story 2 verification steps in full (live count, count changes after resolution, explicit zero case, Border-unreachable and not-enrolled failures). Record the outcome in README's platform-notes section.

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Ask for Border health status, by voice (Priority: P2)

**Goal**: "Hey Siri, ask NetGeniusClaw for Border health" speaks the current cached heartbeat/health summary.

**Independent Test**: With the app backgrounded/terminated, invoke the phrase and confirm the spoken summary
matches the Dashboard's own connection-status display (quickstart.md User Story 3).

### Tests for User Story 3

- [x] T023 [P] [US3] Write `test/border_health_headless_test.dart`: given a `DeviceHeartbeatStore` seeded with a saved `DeviceHeartbeatStatus`, `borderHealthMain`'s core logic reports the summary folded together with a human-readable age (e.g. "As of 4 minutes ago: All systems normal") over the method channel; given an empty store (never received a heartbeat), confirm the distinct "no health data yet" message rather than a false "Border unreachable." Confirm it fails.

### Implementation for User Story 3

- [x] T024 [US3] Implement `lib/ncfed/border_health_headless.dart`'s `@pragma('vm:entry-point') borderHealthMain()`: use `connectHeadless()` (T004) — a failure here is the genuine "Border unreachable"/not-set-up path (FR-008/FR-010, research.md R4); on success, read `DeviceHeartbeatStore.load()` (no network call — research.md R4) and report the spoken summary-with-age, or the distinct "no health data yet" message if `load()` returns null, over the method channel before tearing down. Confirm T023 passes.
- [x] T025 [US3] Implement `ios/Runner/BorderHealthIntent.swift`: a parameterless `AppIntent` using `HeadlessEngineRunner` (T005) to run `borderHealthMain`, returning the spoken summary or the distinct failure/not-set-up/no-data dialog.
- [x] T026 [US3] Extend `ios/Runner/NetClawShortcuts.swift`'s `AppShortcutsProvider` with `BorderHealthIntent`'s phrase(s), completing all three (FR-001).
- [x] T027 [US3] Run the `xcodebuild` command from T012 and fix any compile error before proceeding. — `BUILD SUCCEEDED`.
- [ ] T028 [US3] 🔌 **DEVICE** — With the operator: with the app backgrounded/terminated, run quickstart.md's User Story 3 verification steps in full (live summary matches Dashboard, summary updates after a real heartbeat push, "no health data yet" on a never-heartbeated device, Border-unreachable and not-enrolled failures). Record the outcome in README's platform-notes section.

**Checkpoint**: All three intents are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final regression pass and repo-wide coherence once all three stories are done.

- [x] T029 Run the full `flutter analyze` + `flutter test` suite on `mobile/netclaw-mobile` and confirm zero issues, zero regressions (SC-005).
- [x] T030 Run the full `xcodebuild` command from T012 one final time against all three intents + the completed `AppShortcutsProvider` together (SC-005). — `BUILD SUCCEEDED`, zero warnings in any of the 5 new Swift files, all three intents and the shortcuts provider compiled and linked into `Runner.app`.
- [x] T031 Confirm every 🔌 DEVICE scenario across all three stories is either recorded as verified or explicitly listed as unverified in README's platform-notes section (honesty standard, specs 072/073/110).
- [x] T032 Verify FR-012: diff `mobile/netclaw-mobile/ios/Runner/Runner.entitlements` against its state before this branch and confirm it is byte-for-byte unchanged; confirm `IPHONEOS_DEPLOYMENT_TARGET` in `project.pbxproj` is still `16.2` across all Runner build configurations.
- [x] T033 Draft the milestone WordPress blog post per constitution Principle XVII and present it to the operator for review before publishing (do not publish without explicit approval). — Drafted at `docs/blog/2026-08-15-siri-app-intents.md`, marked "not published," awaiting John's review.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all three user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational only. No dependency on US2/US3.
- **User Story 2 (Phase 4)**: Depends on Foundational only. Independent of US1/US3 (its own Border RPC, own Dart entrypoint, own Swift file).
- **User Story 3 (Phase 5)**: Depends on Foundational only. Independent of US1/US2.
- **Polish (Phase 6)**: Depends on all three user stories being complete (T031 in particular needs every story's device-verification outcome recorded).

Note: US2 and US3 both edit `ios/Runner/NetClawShortcuts.swift` (T020, T026) — sequence those two edits
relative to each other even though the stories are otherwise independent, to avoid a merge conflict on the
same file.

### Parallel Opportunities

- T001/T002 (Setup) in parallel.
- T003/T005 (Foundational) in parallel — different files (T004 depends on T003 existing as a failing test first).
- Once Foundational is done: US1, US2, US3 implementation work can proceed in parallel by different people/agents, EXCEPT for the shared `NetClawShortcuts.swift` edits noted above.
- Within each story, its own `[P]`-marked test tasks (T006/T007, T014/T015) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) + Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1 — AskBorderIntent).
3. **STOP and VALIDATE** with the operator on-device (T013).
4. Ship as the MVP — Siri can already ask NetGeniusClaw a real question hands-free.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → validate on-device → MVP shippable.
3. US2 → validate on-device → pending-approval voice query shippable.
4. US3 → validate on-device → Border health voice query shippable, all of B1a complete.
5. Polish → final regression, documentation, milestone blog post.
