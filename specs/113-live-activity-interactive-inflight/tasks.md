---

description: "Task list for NetGeniusClaw Mobile Interactive and In-Flight Live Activity (B3)"
---

# Tasks: NetGeniusClaw Mobile Interactive and In-Flight Live Activity (B3)

**Input**: Design documents from `/specs/113-live-activity-interactive-inflight/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included for the Dart-side sequencing logic (research.md R8 — the spec's own flagged highest-
risk area: "a stuck activity that never ends is the likely bug"). No automated test for the native
SwiftUI/ActivityKit rendering itself, matching spec 112's established convention for this repo.

**Organization**: Tasks are grouped by user story (US1 = Approve/Deny from the Lock Screen P1/MVP, US2 =
activity reflects resolution from any surface P2, US3 = in-flight query activity P2), per spec.md's
priorities. US1/US2 are both part of B3a and share files; US3 (B3b) is fully independent — no shared Swift
or Dart files with US1/US2 beyond `live_activity.dart`/`LiveActivityBridge.swift` themselves (extended with
distinct, non-overlapping methods for each).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to US1/US2/US3
- 🔌 **DEVICE**: Cannot be completed or verified without the operator and a real, enrolled iPhone (iOS 17+
  for US1/US2's interactive buttons) — per spec.md's Context and every prior mobile spec's verification
  standard

---

## Phase 1: Setup

**Purpose**: Confirm the branch is in a clean, buildable state before any new code lands.

- [x] T001 [P] Confirm `flutter analyze` and `flutter test` are green on `mobile/netclaw-mobile` at the start of this branch (baseline, no code change)
- [x] T002 [P] Confirm `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` succeeds at the start of this branch (baseline, no code change)
- [x] T003 Confirm the `xcodeproj` Ruby gem is available (`gem list xcodeproj -i`) — needed later to add new Swift files to the `Runner`/`LiveActivityWidget` targets with correct membership (research.md R5).

**Checkpoint**: Foundation confirmed clean — US1/US2 (B3a) and US3 (B3b) can each proceed independently.

---

## Phase 2: User Story 1 - Approve or deny straight from the Lock Screen (Priority: P1) 🎯 MVP

**Goal**: On iOS 17+, the pending-approval Live Activity shows Approve/Deny buttons that foreground the
app to Approvals — never resolving without the existing fresh biometric/passcode confirmation.

**Independent Test**: With a real pending approval showing its Live Activity, tap "Approve" and confirm
the app foregrounds directly to the Approvals tab with the biometric prompt available, never already
resolved (quickstart.md User Story 1).

### Implementation for User Story 1

- [x] T004 [US1] Add a new sibling function to `parseDeviceDeepLink` in `mobile/netclaw-mobile/lib/ncfed/device_deep_link.dart` — e.g. `bool isApprovalsDeepLink(String raw)` recognizing `netgeniusclaw://approvals` — and write `test/device_deep_link_test.dart` coverage for it (recognized shape, unrelated shapes return false) (research.md R2/R3, data-model.md).
- [x] T005 [US1] Wire the recognized `netgeniusclaw://approvals` link to the existing `_selectTab(3)` navigation in `mobile/netclaw-mobile/lib/main.dart` — reuse the same `app_links` listener already wired for `netgeniusclaw://device/<id>`, adding one more recognized-shape branch (research.md R2).
- [x] T006 [US1] Create `mobile/netclaw-mobile/ios/Runner/ApprovalActionIntent.swift`: a `LiveActivityIntent` (under `if #available(iOS 17.0, *)`, research.md R6) with `static var openAppWhenRun = true`, whose `perform()` calls `UIApplication.shared.open(URL(string: "netgeniusclaw://approvals")!)` and returns `.result()` — no approval-resolution logic of its own (FR-001).
- [x] T007 [US1] Add `ApprovalActionIntent.swift` to BOTH the `Runner` and `LiveActivityWidget` targets using the `xcodeproj` gem (T003, research.md R5 — corrected during implementation: `PendingApprovalLiveActivityView.swift`'s `Button(intent: ApprovalActionIntent())` compiles into `LiveActivityWidget`, so that target needs the concrete type too) — confirm via `project.pbxproj` diff that TWO `PBXBuildFile` entries reference the one new `PBXFileReference`. Also add an `IS_EXTENSION_TARGET` `SWIFT_ACTIVE_COMPILATION_CONDITIONS` flag to `LiveActivityWidget`'s build settings and wrap `perform()`'s `UIApplication.shared.open(...)` call in `#if !IS_EXTENSION_TARGET` (research.md R5) — that API is unavailable in extensions, and `openAppWhenRun`'s copy in `LiveActivityWidget` never actually executes anyway.
- [x] T008 [US1] In `mobile/netclaw-mobile/ios/LiveActivityWidget/PendingApprovalLiveActivityView.swift`, add Approve/Deny `Button(intent: ApprovalActionIntent())` controls to both the Lock Screen view and the Dynamic Island expanded region, wrapped in `if #available(iOS 17.0, *) { ... }` so devices below 17 render exactly as before (FR-001/FR-002).
- [x] T009 [US1] Run `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` and fix any compile error before proceeding.
- [ ] T010 [US1] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 1 verification steps in full (Approve foregrounds to Approvals without resolving, Deny does the same, an iOS 16.2 device if available shows no buttons and is otherwise unaffected). Record the outcome in `mobile/netclaw-mobile/README.md`'s platform-notes section.

**Checkpoint**: User Story 1 is functional and independently shippable (MVP) — the activity foregrounds correctly, even before User Story 2's dismiss-on-resolve behavior is built.

---

## Phase 3: User Story 2 - The approval activity reflects resolution from any surface (Priority: P2)

**Goal**: A pending-approval Live Activity resolved through any surface (in-app, notification, watch)
updates to a resolved state and dismisses, instead of lingering with stale content.

**Independent Test**: Start a pending-approval Live Activity, resolve it through a different surface, and
confirm the activity updates and dismisses without the operator touching the activity itself (quickstart.md
User Story 2).

### Tests for User Story 2

- [x] T011 [P] [US2] Write `test/live_activity_test.dart` (new file — research.md R8): given a fake `MethodChannel`, `LiveActivity().update(approvalId:, status:)` invokes the channel's `update` method with the given arguments exactly once; a channel exception is swallowed (matches the existing `start`/`end`'s try/catch, FR-009). Confirm it fails (the method doesn't exist yet).

### Implementation for User Story 2

- [x] T012 [US2] Add `update({required int approvalId, required String status})` to `mobile/netclaw-mobile/lib/ncfed/live_activity.dart`'s `LiveActivity` class, wrapped in the same try/catch pattern as `start`/`end` (FR-003/FR-009). Confirm T011 passes.
- [x] T013 [US2] In `mobile/netclaw-mobile/lib/main.dart`'s existing `approvalClient.pending.listen(...)` block, call `liveActivity.update(...)` when a previously-pending approval disappears from the list because it was resolved (rather than only ever calling `end()` unconditionally) — reuse the existing `pending` stream, no new subscription.
- [x] T014 [US2] Add an `"update"` case to `LiveActivityBridge.swift`'s `handle(_:result:)`, calling `activity.update(.init(state: ..., staleDate: nil))` with `status: "resolved"` on the existing `currentActivity`, then relying on the existing `dismissalPolicy` behavior already established in `end()` for how quickly it disappears (FR-003).
- [x] T015 [US2] Run the `xcodebuild` command from T009 and fix any compile error before proceeding.
- [ ] T016 [US2] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 2 verification steps in full (resolve from in-app, from a notification action, and from the watch if available — confirm the activity updates and dismisses each time). Record the outcome in README's platform-notes section.

**Checkpoint**: User Stories 1 and 2 together complete B3a end to end.

---

## Phase 4: User Story 3 - See a submitted question's progress on the Lock Screen (Priority: P2)

**Goal**: A new, per-question Live Activity starts when a question is submitted, shows an elapsed timer
and the Border's own free-text progress detail (never a fabricated member count), and ends on a terminal
state.

**Independent Test**: Submit a real question expected to take at least a minute, confirm a Live Activity
appears showing the question and a ticking timer, updates on a real progress notification, and ends on a
terminal state (quickstart.md User Story 3).

### Tests for User Story 3

- [x] T017 [P] [US3] Extend `test/live_activity_test.dart`: `LiveActivity().startAsk(taskId:, questionPreview:)` / `.updateAsk(taskId:, progressDetail:)` / `.endAsk(taskId:, state:)` each invoke the corresponding channel method with the given `taskId` and arguments; calling `updateAsk`/`endAsk` for a `taskId` that was never started is a no-op that does not throw; a channel exception on any of the three is swallowed, matching T011's same assertion for `update()` (FR-004/FR-006/FR-007/FR-009, data-model.md). Confirm it fails.
- [x] T018 [P] [US3] Write `test/ask_live_activity_test.dart` (new file): given a `ConversationStore` and a fake `LiveActivity`-shaped recorder, `wireAskLiveActivity(...)`'s `onAdded` handler calls `startAsk` exactly once per new pending turn with that turn's `taskId`/`requestText`; its `onTerminal` handler calls `endAsk` exactly once per turn reaching any of completed/failed/cancelled, passing that state through verbatim; a `task_progress` event on `EdgeAskClient.updates` for a still-tracked `taskId` calls `updateAsk` with its `progressDetail` — an event for an already-ended `taskId` is a no-op (FR-004/FR-005/FR-006/FR-007). Confirm it fails.
- [x] T019 [P] [US3] Add coverage to `test/device_deep_link_test.dart` for a new `netgeniusclaw://chat/<taskId>` parser (e.g. `parseChatDeepLink`): extracts `taskId` correctly, returns `null` for unrelated shapes (FR-008, data-model.md). Confirm it fails.

### Implementation for User Story 3

- [x] T020 [US3] Add `startAsk`/`updateAsk`/`endAsk` to `mobile/netclaw-mobile/lib/ncfed/live_activity.dart` (data-model.md), each wrapped in the same try/catch pattern as the existing methods (FR-009). Confirm T017 passes.
- [x] T021 [US3] Add `onAdded`/`onTerminal` callback fields to `mobile/netclaw-mobile/lib/ncfed/conversation_store.dart`'s `ConversationStore`, invoked from `addPending()` and `updateState()` respectively (research.md R4) — `onCompleted`'s existing completed-only trigger and behavior MUST remain byte-for-byte unchanged.
- [x] T022 [US3] Create `mobile/netclaw-mobile/lib/ncfed/ask_live_activity.dart`: a `wireAskLiveActivity(ConversationStore store, EdgeAskClient askClient, LiveActivity liveActivity)`-shaped function (exact signature decided against T018's test) that wires `store.onAdded` → `liveActivity.startAsk(...)`, `store.onTerminal` → `liveActivity.endAsk(...)`, and `askClient.updates` (filtering for `TaskState.working` entries carrying `progressDetail`, per `TaskUpdate.fromProgress`) → `liveActivity.updateAsk(...)`. Confirm T018 passes.
- [x] T023 [US3] Call `wireAskLiveActivity(...)` once, alongside the existing `approvalClient.pending.listen(...)` wiring in `mobile/netclaw-mobile/lib/main.dart` — not from `chat_screen.dart` directly, so it covers all of `addPending()`'s existing call sites uniformly (research.md R4/plan.md Project Structure).
- [x] T024 [US3] Add the `netgeniusclaw://chat/<taskId>` parser from T019 to `mobile/netclaw-mobile/lib/ncfed/device_deep_link.dart` and wire it to `NotificationDeepLink`'s existing `openChatTurn` callback via `findTurnForIdentifier` (FR-008, research.md R3). Confirm T019 passes.
- [x] T025 [US3] Create `mobile/netclaw-mobile/ios/LiveActivityWidget/AskActivityAttributes.swift`: `ActivityAttributes` with `taskId`/`questionPreview` fixed fields and a `ContentState` carrying `startedAt`/`progressDetail`/`state` (data-model.md) — no `respondedMembers`/`expectedMembers` field anywhere (FR-006).
- [x] T026 [US3] Add `AskActivityAttributes.swift` to BOTH the `Runner` and `LiveActivityWidget` targets using the `xcodeproj` gem (T003, research.md R5) — confirm via `project.pbxproj` diff that TWO `PBXBuildFile` entries reference the one new `PBXFileReference`, mirroring `PendingApprovalActivityAttributes.swift`'s existing dual-membership shape exactly.
- [x] T027 [US3] Create `mobile/netclaw-mobile/ios/LiveActivityWidget/AskLiveActivityView.swift`: an `ActivityConfiguration` for `AskActivityAttributes` showing `context.attributes.questionPreview` and `Text(timerInterval:)` driven by `context.state.startedAt` (FR-005), `context.state.progressDetail` when non-nil (FR-006), and setting `.widgetURL(URL(string: "netgeniusclaw://chat/\(context.attributes.taskId)"))` on the Lock Screen view (FR-008, research.md R3) — add it to `LiveActivityWidgetBundle` alongside the existing `PendingApprovalLiveActivityView()`.
- [x] T028 [US3] Add `AskLiveActivityView.swift` to the `LiveActivityWidget` target only (single membership, like `PendingApprovalLiveActivityView.swift` itself) using the `xcodeproj` gem.
- [x] T029 [US3] Extend `LiveActivityBridge.swift`: replace the single `currentActivity` pattern's approval-only scope is unaffected, but add `askActivities: [String: Activity<AskActivityAttributes>]` (data-model.md) and `"startAsk"`/`"updateAsk"`/`"endAsk"` method-channel cases — `startAsk` computes and sets a `staleDate` matching the Border's own ask-timeout ceiling (research.md R7/FR-011), not an arbitrary value.
- [x] T030 [US3] Run the `xcodebuild` command from T009 and fix any compile error before proceeding — this is also where dual-membership mistakes (T026) surface as a *runtime*, not compile-time, failure per research.md R5's own warning, so re-confirm the `project.pbxproj` diff from T026 explicitly rather than relying on a clean build alone.
- [ ] T031 [US3] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 3 verification steps in full (activity appears promptly with a ticking timer, updates on a real progress notification with no member count ever shown, ends on a terminal state, two concurrent asks get two independent activities, tapping opens Chat to that turn). Record the outcome in README's platform-notes section.

**Checkpoint**: All three user stories are independently functional — B3 (both B3a and B3b) is complete.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final regression pass and repo-wide coherence once all three stories are done.

- [x] T032 Run the full `flutter analyze` + `flutter test` suite on `mobile/netclaw-mobile` and confirm zero issues, zero regressions (SC-006).
- [x] T033 Run the full `xcodebuild` command from T009 one final time against all changes together and confirm it succeeds (SC-006).
- [x] T034 Verify FR-010: confirm `IPHONEOS_DEPLOYMENT_TARGET` in `project.pbxproj` is still unchanged from its pre-spec value (16.2) across all `Runner` build configurations.
- [x] T035 Verify FR-006/SC-005 by direct code review: grep the diff for `respondedMembers`/`expectedMembers`/any member-count-shaped field or computation and confirm zero matches anywhere in the new/changed code.
- [x] T035b Verify FR-011 by code review (not a real-time device wait — the Border's own ask-timeout ceiling can run 780s+, impractical to sit through in one verification pass): confirm `startAsk`'s `staleDate` calculation in `LiveActivityBridge.swift` reads the same timeout concept `service.py`'s `_edge_ask_timeout()` uses (research.md R7), not a hardcoded/arbitrary value.
- [x] T036 Confirm every 🔌 DEVICE scenario across all three stories is either recorded as verified or explicitly listed as unverified in README's platform-notes section (honesty standard, specs 072/073/110/111/112).
- [x] T037 Draft the milestone WordPress blog post per constitution Principle XVII and present it to the operator for review before publishing (do not publish without explicit approval). — Drafted at `docs/blog/2026-08-15-live-activity-interactive-inflight.md`, marked "not published," awaiting John's review.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **User Story 1 (Phase 2)**: Depends on Setup only.
- **User Story 2 (Phase 3)**: Depends on Setup only — NOT a hard dependency on User Story 1 despite both being part of B3a; US2's Independent Test (an activity dismissing when resolved elsewhere) holds regardless of whether Approve/Deny buttons exist yet, and is exercisable even on iOS below 17 via the existing tap-to-open-only activity. US1 and US2 do touch overlapping files (`main.dart`, `LiveActivityBridge.swift`) in different, non-overlapping spots — sequence commits to avoid a merge conflict, not because of a functional dependency.
- **User Story 3 (Phase 4)**: Depends on Setup only — fully independent of US1/US2 (different Swift files, different Dart files, only touching `live_activity.dart`/`LiveActivityBridge.swift` via distinct, non-overlapping new methods).
- **Polish (Phase 5)**: Depends on all three user stories being complete.

### Parallel Opportunities

- T001/T002/T003 (Setup) in parallel.
- Once Setup is done: User Story 3 (Phase 4) can proceed fully in parallel with User Stories 1+2 (Phases 2–3) — no shared files beyond additive, non-conflicting method additions to `live_activity.dart`/`LiveActivityBridge.swift`.
- Within User Story 3: T017/T018/T019 (tests, different files) in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (User Story 1 — Approve/Deny foregrounds to Approvals).
3. **STOP and VALIDATE** with the operator on-device (T010).
4. Ship as the MVP — the Lock Screen shortcut already works, even before the dismiss-on-resolve polish.

### Incremental Delivery

1. Setup → foundation confirmed.
2. US1 → validate on-device → MVP shippable.
3. US2 → validate on-device → B3a fully complete (activity always reflects true state).
4. US3 → validate on-device → B3b complete, all of B3 done.
5. Polish → final regression, documentation, milestone blog post.
