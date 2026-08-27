---

description: "Task list for NetGeniusClaw Mobile Home Screen, Lock Screen, and Control Center Widgets (B1b+B2)"
---

# Tasks: NetGeniusClaw Mobile Home Screen, Lock Screen, and Control Center Widgets (B1b+B2)

**Input**: Design documents from `/specs/114-widgets-controlwidget/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included for the Dart-side mirror-call wiring and deep-link parsers (research.md R7). No
automated test for the native WidgetKit/ControlWidget rendering itself, matching specs 112/113's
established convention.

**Organization**: Tasks are grouped by user story (US1 = home-screen widget P1/MVP, US2 = Lock Screen
widget P1, US3 = Control Center control P2), per spec.md's priorities. US1/US2 share the same underlying
`TimelineProvider`/view (data-model.md), so their implementation tasks touch the same file; US3 is fully
independent (different Swift files entirely).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to US1/US2/US3
- 🔌 **DEVICE**: Cannot be completed or verified without the operator and a real, enrolled iPhone running
  iOS 18+ — per spec.md's Context and every prior mobile spec's verification standard

---

## Phase 1: Setup

**Purpose**: Confirm the branch is in a clean, buildable state before any new code lands (the widget
target's own setup defects were already found and fixed in this branch's prior commit).

- [x] T001 [P] Confirm `flutter analyze` and `flutter test` are green on `mobile/netclaw-mobile` at the start of this spec's work (baseline, no code change beyond the already-committed target fix)
- [x] T002 [P] Confirm `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` succeeds at the start of this spec's work (baseline — already confirmed working after the prior commit's target fix; re-confirm before adding new code)

**Checkpoint**: Foundation confirmed clean.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `WidgetDataStore`/`WidgetBridgePlugin`/the Dart-side mirror wiring — every user story reads
from this store, so it must exist and be populated before any widget/control can show real data.

**⚠️ CRITICAL**: No user story phase begins until this phase is complete.

- [x] T003 [P] Create `mobile/netclaw-mobile/ios/Runner/WidgetDataStore.swift`: `write()`/`read()` pairs for Border health (summary/pushedAt/isAlarm), pending-approval count, and unread-feed count, backed by `UserDefaults(suiteName: "group.ca.automateyournetwork.netclaw.mobile.ios")` — mirroring `HeartbeatStatusStore.swift`/`PendingApprovalCountStore.swift`'s exact shape (research.md R1), including the same nil-safe "no data" `read()` behavior for health (FR-007).
- [x] T004 Add `WidgetDataStore.swift` to BOTH the `Runner` and `NetClawWidgetExtension` targets using the `xcodeproj` gem, passing the bare filename relative to the `Runner` group (research.md R6 — the lesson learned the hard way in spec 113's research.md R5, applied here from the start) — confirm via `project.pbxproj` diff that TWO `PBXBuildFile` entries reference the one new `PBXFileReference`.
- [x] T005 [P] Create `mobile/netclaw-mobile/ios/Runner/WidgetBridgePlugin.swift`: a `FlutterPlugin` on channel `ca.automateyournetwork.netclaw/widget_data` with `writeHealth`/`writePendingCount`/`writeUnreadCount` methods, each calling the matching `WidgetDataStore.write(...)` then `WidgetCenter.shared.reloadAllTimelines()` (data-model.md) — `Runner`-only (T004's dual membership does not apply here).
- [x] T006 Register `WidgetBridgePlugin` in `AppDelegate.swift`'s plugin registration (matching how `LiveActivityBridge`/`EdgeIdentityPlugin` are already registered).
- [x] T007 [P] Write `test/widget_data_test.dart`: given a fake `MethodChannel`, `mirrorHealth(status)` invokes `writeHealth` with the given summary/pushedAt/isAlarm; `mirrorPendingCount(n)` invokes `writePendingCount`; `mirrorUnreadCount(n)` invokes `writeUnreadCount`; a channel exception on any is swallowed (matching `live_activity.dart`'s established pattern). Confirm it fails (source doesn't exist yet).
- [x] T008 Create `mobile/netclaw-mobile/lib/ncfed/widget_data.dart` with `mirrorHealth`/`mirrorPendingCount`/`mirrorUnreadCount` (data-model.md). Confirm T007 passes.
- [x] T009 Wire the three mirror calls into `mobile/netclaw-mobile/lib/main.dart`'s three existing, already-identified call sites (data-model.md): the `looksLikeDeviceHeartbeat(message)` branch inside `wireMessageFeed`'s `onMessage` (health), the existing `approvalClient.pending.listen(...)` block (pending count), and `_recomputeBadge()` (unread count) — no new hook invented on any store.
- [x] T010 Run `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` and fix any compile error before proceeding.

**Checkpoint**: `WidgetDataStore` exists, is populated from real app events, and both targets build — US1, US2, US3 can each proceed independently.

---

## Phase 3: User Story 1 - Border status at a glance from the home screen (Priority: P1) 🎯 MVP

**Goal**: Small and medium home-screen widgets show Border health, pending count, and a timestamped
last-heartbeat reading, reading from `WidgetDataStore`.

**Independent Test**: Add both widget sizes to a real home screen and confirm both render current data
with a visible reading age (quickstart.md User Story 1).

### Implementation for User Story 1

- [x] T011 [US1] Rewrite `mobile/netclaw-mobile/ios/NetClawWidget/NetClawWidget.swift`: replace the placeholder `Provider`/`SimpleEntry`/`ConfigurationAppIntent`-based scaffolding with a real `TimelineProvider` reading `WidgetDataStore.read()`, timeline policy `.never` (research.md R4, relying entirely on `WidgetBridgePlugin`'s explicit `reloadAllTimelines()`), and a real entry view for `.systemSmall`/`.systemMedium` showing Border health, pending count, and the heartbeat's age (formatted the same way `border_health_headless.dart`'s `_formatAge` does, FR-004) — a distinct "no data yet" state when `WidgetDataStore.read()`'s health value is nil (FR-007).
- [x] T012 [US1] Not a separate task — `AppIntent.swift`'s placeholder `ConfigurationAppIntent`/`favoriteEmoji` content (superseded by T011's provider, which takes no user configuration) is replaced in one pass by T021's full rewrite in Phase 5, not deleted here and rewritten twice.
- [x] T013 [US1] Run the `xcodebuild` command from T010 and fix any compile error before proceeding.
- [ ] T014 [US1] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 1 verification steps in full (both sizes render correctly, real state changes reflected on next refresh, "no data yet" state on a fresh enrollment). Record the outcome in `mobile/netclaw-mobile/README.md`'s platform-notes section.

**Checkpoint**: User Story 1 is functional and independently shippable (MVP).

---

## Phase 4: User Story 2 - Border status on the Lock Screen (Priority: P1)

**Goal**: `.accessoryCircular`/`.accessoryRectangular`/`.accessoryInline` Lock Screen widgets show Border
health and/or pending count, with zero per-approval detail, and deep-link correctly on tap.

**Independent Test**: Add all three accessory families to a real Lock Screen and confirm each renders
legibly with no approval-specific detail (quickstart.md User Story 2).

### Tests for User Story 2

- [x] T015 [P] [US2] Add coverage to `test/device_deep_link_test.dart` for `parseDashboardDeepLink`/an updated `parseChatDeepLink` distinguishing `netgeniusclaw://chat` (no task id) from `netgeniusclaw://chat/<taskId>` (research.md R3, data-model.md). Confirm it fails.

### Implementation for User Story 2

- [x] T016 [US2] Extend `NetClawWidget.swift`'s `supportedFamilies` to add `.accessoryCircular`/`.accessoryRectangular`/`.accessoryInline`, with a layout branch per family showing only health and/or pending count — never target name, requesting agent, or any other approval-specific field (FR-005), matching `PendingApprovalLiveActivityView`'s existing restriction.
- [x] T017 [US2] Add `parseDashboardDeepLink`/extend `parseChatDeepLink` in `mobile/netclaw-mobile/lib/ncfed/device_deep_link.dart` (research.md R3). Confirm T015 passes.
- [x] T018 [US2] Wire `netgeniusclaw://dashboard` to `_selectTab(0)` in `mobile/netclaw-mobile/lib/main.dart`'s existing `DeviceDeepLinkListener` construction (same pattern as spec 113's `onOpenApprovals`), and set each Lock Screen widget's `.widgetURL(...)` to the appropriate shape (`netgeniusclaw://dashboard` for health, `netgeniusclaw://approvals` — already existing, spec 113 — for pending count).
- [x] T019 [US2] Run the `xcodebuild` command from T010 and fix any compile error before proceeding.
- [ ] T020 [US2] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 2 verification steps in full (all three families legible, zero per-approval detail, correct tap-through for both health and pending-count widgets). Record the outcome in README's platform-notes section.

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Check pending approvals and jump straight to asking, from Control Center (Priority: P2)

**Goal**: The Control Center control shows the cached pending count and, on tap, foregrounds Chat ready to
type — not a headless, textless `AskBorderIntent` invocation (research.md R2).

**Independent Test**: Add the control to Control Center and confirm it shows the count and its tap opens
Chat with the compose field ready (quickstart.md User Story 3).

### Implementation for User Story 3

- [x] T021 [US3] Rewrite `mobile/netclaw-mobile/ios/NetClawWidget/AppIntent.swift`: a new `OpenChatIntent` (`AppIntent`, `openAppWhenRun = true`) whose `perform()` opens `netgeniusclaw://chat` (research.md R2) — no parameters, no approval-resolution or ask logic of its own, mirroring `ApprovalActionIntent`'s shape from spec 113.
- [x] T022 [US3] Rewrite `mobile/netclaw-mobile/ios/NetClawWidget/NetClawWidgetControl.swift`: replace the placeholder "timer" `ControlWidget`/`Value`/`Provider`/`TimerConfiguration`/`StartTimerIntent` with a real `ControlWidgetButton` (or `ControlWidgetToggle`-free equivalent, whichever the SwiftUI ControlWidget API makes cleaner) whose displayed label reads `WidgetDataStore.read()`'s pending count (research.md R5 — never a fresh network call) and whose action is `OpenChatIntent` (T021, FR-008). Rename the widget `kind` string away from the stale `"ca.automateyournetwork.netclaw.mobile.watchapp.NetClawWidget"` placeholder to something under the corrected `ca.automateyournetwork.netclaw.mobile.netclawwidget` namespace.
- [x] T023 [US3] Wire `netgeniusclaw://chat` (no task id) to open Chat with no turn highlighted, in `mobile/netclaw-mobile/lib/main.dart`'s existing `DeviceDeepLinkListener` construction, alongside T018's `netgeniusclaw://dashboard` wiring.
- [x] T024 [US3] Run the `xcodebuild` command from T010 and fix any compile error before proceeding.
- [ ] T025 [US3] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 3 verification steps in full (control shows the count, tap foregrounds Chat ready to type). Record the outcome in README's platform-notes section.

**Checkpoint**: All three user stories are independently functional — B1b+B2 is complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final regression pass and repo-wide coherence once all three stories are done.

- [x] T026 Run the full `flutter analyze` + `flutter test` suite on `mobile/netclaw-mobile` and confirm zero issues, zero regressions (SC-005).
- [x] T027 Run the full `xcodebuild` command from T010 one final time against all changes together and confirm it succeeds (SC-005) — including a check that no Xcode placeholder template code ("favorite emoji," "start a timer," `ConfigurationAppIntent`) remains anywhere in `NetClawWidget/`.
- [x] T028 Verify FR-009/FR-010: confirm `git diff --stat` shows no new Xcode target beyond the already-existing `NetClawWidgetExtension`, and confirm `Runner`'s/`WatchApp`'s own `IPHONEOS_DEPLOYMENT_TARGET` values are unchanged from their pre-spec values (only `NetClawWidgetExtension`'s floor is 18.0, set in the prior setup commit).
- [x] T029 Confirm every 🔌 DEVICE scenario across all three stories is either recorded as verified or explicitly listed as unverified in README's platform-notes section (honesty standard, specs 072/073/110/111/112/113).
- [x] T030 Draft the milestone WordPress blog post per constitution Principle XVII and present it to the operator for review before publishing (do not publish without explicit approval). — Drafted at `docs/blog/2026-08-15-widgets-controlwidget.md`, marked "not published," awaiting John's review.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all three user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational only.
- **User Story 2 (Phase 4)**: Depends on Foundational AND on User Story 1's `NetClawWidget.swift` rewrite (T011) — it extends the SAME file's `supportedFamilies`/view, not a separate one.
- **User Story 3 (Phase 5)**: Depends on Foundational only — fully independent of US1/US2 (different Swift files: `AppIntent.swift`, `NetClawWidgetControl.swift`).
- **Polish (Phase 6)**: Depends on all three user stories being complete.

Note: T018 (US2) and T023 (US3) both edit `main.dart`'s `DeviceDeepLinkListener` construction — sequence
those two relative to each other even though the stories are otherwise independent, to avoid a merge
conflict on the same block (matching spec 112's own `NetClawShortcuts.swift` precedent for this class of
note).

### Parallel Opportunities

- T001/T002 (Setup) in parallel.
- T003/T005/T007 (Foundational) in parallel — different files.
- Once Foundational is done: User Story 3 (Phase 5) can proceed fully in parallel with User Stories 1+2
  (Phases 3–4) — zero shared files.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) + Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1 — home-screen widget).
3. **STOP and VALIDATE** with the operator on-device (T014).
4. Ship as the MVP — Border status is already visible from the home screen.

### Incremental Delivery

1. Setup + Foundational → `WidgetDataStore` populated and both targets building.
2. US1 → validate on-device → MVP shippable.
3. US2 → validate on-device → Lock Screen coverage shippable.
4. US3 → validate on-device → Control Center control shippable, all of B1b+B2 complete.
5. Polish → final regression, documentation, milestone blog post.
