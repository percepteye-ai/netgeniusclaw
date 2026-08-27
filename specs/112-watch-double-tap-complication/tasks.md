---

description: "Task list for NetGeniusClaw Mobile Watch Double Tap and Corner Complication (B4+B5)"
---

# Tasks: NetGeniusClaw Mobile Watch Double Tap and Corner Complication (B4+B5)

**Input**: Design documents from `/specs/112-watch-double-tap-complication/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: None added — no `XCTest` target exists for watch SwiftUI views in this repo today
(research.md R5), matching spec 072's own established real-hardware-only verification convention for this
part of the codebase. `flutter analyze`/`flutter test` are re-run only as a regression guard (this spec
touches no Dart code).

**Organization**: Tasks are grouped by user story (US1 = Double Tap on approvals P1, US3 = corner
complications P2, US2 = Double Tap read-aloud P3), per spec.md's priorities. Both items are otherwise fully
independent — no shared plumbing, no execution-order dependency between them.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to US1/US2/US3
- 🔌 **DEVICE**: Cannot be completed or verified without a real, paired Series 9/Ultra 2-or-later Apple
  Watch — per spec.md's Context and every prior mobile spec's verification standard

---

## Phase 1: Setup

**Purpose**: Confirm the branch is in a clean, buildable state before any new code lands.

- [x] T001 [P] Confirm `flutter analyze` and `flutter test` are green on `mobile/netclaw-mobile` at the start of this branch (baseline, no code change — expected to be identical before and after this spec, since no Dart code is touched)
- [x] T002 [P] Confirm `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme WatchApp -sdk watchsimulator -configuration Debug build CODE_SIGNING_ALLOWED=NO` succeeds at the start of this branch (baseline)
- [x] T003 Not a separate check — WatchComplication.appex is embedded and built as part of the WatchApp scheme (T002); a standalone `-scheme WatchComplication -sdk watchsimulator` invocation fails on unmodified code too (confirmed via `git stash`), hitting the pre-existing "cross-SDK build trap" README already documents for spec 072. Superseded by T002.

**Checkpoint**: Foundation confirmed clean — US1, US2, US3 can each proceed independently, in any order.

---

## Phase 2: User Story 1 - Double Tap to confirm the top pending approval (Priority: P1) 🎯 MVP

**Goal**: Double Tap on a supporting watch triggers the same passcode-gated "Approve" action the topmost
pending approval's existing button already calls — never a separate, less-gated path, and never targeting
any approval other than the topmost one.

**Independent Test**: With at least one real pending approval showing on a supporting watch, perform a
Double Tap and confirm the passcode prompt appears for the topmost approval specifically (quickstart.md
User Story 1).

### Implementation for User Story 1

- [x] T004 [US1] In `mobile/netclaw-mobile/ios/WatchApp Watch App/ApprovalsView.swift`, restructure the `List(store.approvals)` to iterate with an index (e.g. `Array(store.approvals.enumerated())`, `id: \.element.id`) and pass an `isTopApproval: Bool` (`index == 0`) into `ApprovalRow` (research.md R2).
- [x] T005 [US1] In the same file's `ApprovalRow`, accept `isTopApproval` and, when true, wrap the "Approve" `Button` in `if #available(watchOS 11.0, *) { ... .handGestureShortcut(.primaryAction) }` (research.md R1/R2/R3) — the "Deny" button and every non-top row's "Approve" button MUST NOT receive the modifier (FR-002).
- [x] T006 [US1] Confirm (by reading the modified `resolve(_:action:)` call site, not by adding a test — research.md R5) that the gesture-triggered `Button.action` closure is byte-for-byte the same closure the manual tap already uses (`Task { await onResolve("approve") }`) — no duplicated or parallel resolution path (FR-001).
- [x] T007 [US1] Run `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme WatchApp -sdk watchsimulator -configuration Debug build CODE_SIGNING_ALLOWED=NO` and fix any compile error before proceeding.
- [ ] T008 [US1] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 1 verification steps in full (single approval, multiple approvals — only the top one responds, successful confirmation, cancelled confirmation, empty/error list state). Record the outcome in `mobile/netclaw-mobile/README.md`'s platform-notes section.

**Checkpoint**: User Story 1 is fully functional and independently shippable (MVP).

---

## Phase 3: User Story 3 - Corner complications on an Infograph watch face (Priority: P2)

**Goal**: Both `HeartbeatComplication` and `PendingApprovalComplication` are selectable and render legibly
in an Infograph face's corner slots, using the same data source and refresh mechanism as their existing
circular/rectangular/inline placements.

**Independent Test**: On a supporting watch, add both complications to corner slots on an Infograph face
and confirm both render legibly and update consistently with their existing placements (quickstart.md User
Story 3).

### Implementation for User Story 3

- [x] T009 [P] [US3] Add `.accessoryCorner` to `supportedFamilies` in `mobile/netclaw-mobile/ios/WatchComplication/HeartbeatComplication.swift` (research.md R4) — no new view, no new provider.
- [x] T010 [P] [US3] Add `.accessoryCorner` to `supportedFamilies` in `mobile/netclaw-mobile/ios/WatchComplication/PendingApprovalComplication.swift` (research.md R4) — no new view, no new provider.
- [x] T011 [US3] Run the `xcodebuild` command from T002 (`-scheme WatchApp`, which embeds and builds `WatchComplication.appex`) and fix any compile error before proceeding.
- [ ] T012 [US3] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 3 verification steps in full (both complications selectable in a corner slot on an Infograph face, live update on real data changes, the heartbeat complication's distinct "no data" state in a corner slot). Record the outcome in README's platform-notes section.

**Checkpoint**: User Stories 1 and 3 both work independently.

---

## Phase 4: User Story 2 - Double Tap to hear the answer read aloud (Priority: P3)

**Goal**: Double Tap while an answer is showing in the Ask view triggers the same "Read aloud" action the
existing button already calls.

**Independent Test**: With an answer already showing in the Ask view on a supporting watch, perform a
Double Tap and confirm the answer is read aloud (quickstart.md User Story 2).

### Implementation for User Story 2

- [x] T013 [US2] In `mobile/netclaw-mobile/ios/WatchApp Watch App/AskView.swift`, wrap the "Read aloud" `Button` (shown only in the `.answered` state) in `if #available(watchOS 11.0, *) { ... .handGestureShortcut(.primaryAction) }` (research.md R1/R3, FR-005) — this is the only `.primaryAction` claim in `AskView`'s hierarchy, so it does not conflict with `ApprovalsView`'s claim (a different screen, per FR-002/research.md R2's single-control-per-hierarchy constraint).
- [x] T014 [US2] Run the `xcodebuild` command from T007 and fix any compile error before proceeding.
- [ ] T015 [US2] 🔌 **DEVICE** — With the operator: run quickstart.md's User Story 2 verification steps in full (answered state triggers read-aloud, every other state is a no-op). Record the outcome in README's platform-notes section.

**Checkpoint**: All three user stories are independently functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final regression pass and repo-wide coherence once all three stories are done.

- [x] T016 Run the full `flutter analyze` + `flutter test` suite on `mobile/netclaw-mobile` and confirm zero issues, zero regressions versus the T001 baseline (SC-005) — expected to be unchanged, since no Dart code was touched. — `flutter analyze`: zero issues. `flutter test`: 378/378 passing, unchanged from spec 111's baseline.
- [x] T017 Run the `xcodebuild` command from T007/T002 (`-scheme WatchApp`) one final time and confirm it succeeds, embedding both complication changes (SC-005). — `BUILD SUCCEEDED`.
- [x] T018 Verify FR-006 and FR-009: confirm `WATCHOS_DEPLOYMENT_TARGET` in `project.pbxproj` is still unchanged from its pre-spec value across all `WatchApp`/`WatchComplication` build configurations, and `git diff --stat` shows no new Xcode target (no new `PBXNativeTarget`/scheme) and no `.entitlements` file touched by this branch.
- [ ] T019 🔌 **DEVICE** — If a pre-Series-9 watch or a Series 9/Ultra 2 watch running watchOS below 11 is available, run quickstart.md's backwards-compatibility verification (FR-004/FR-006) — manual Approve/Deny/Read-aloud taps behave identically to before this spec. If no such device is available, explicitly record that in README's platform-notes section rather than assuming it.
- [x] T020 Confirm every 🔌 DEVICE scenario across all three stories (plus T019) is either recorded as verified or explicitly listed as unverified in README's platform-notes section (honesty standard, specs 072/073/110/111).
- [x] T021 Draft the milestone WordPress blog post per constitution Principle XVII and present it to the operator for review before publishing (do not publish without explicit approval). — Drafted at `docs/blog/2026-08-15-watch-double-tap-corner-complication.md`, marked "not published," awaiting John's review.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **User Story 1 (Phase 2)**: Depends on Setup only. No dependency on US2/US3.
- **User Story 3 (Phase 3)**: Depends on Setup only. Fully independent of US1/US2 (different files entirely).
- **User Story 2 (Phase 4)**: Depends on Setup only. Independent of US1/US3, but shares the same `if #available(watchOS 11.0, *)` gating pattern as US1 (no shared code, just a repeated idiom).
- **Polish (Phase 5)**: Depends on all three user stories being complete (T020 needs every story's device-verification outcome recorded).

### Parallel Opportunities

- T001/T002/T003 (Setup) in parallel — independent checks.
- T009/T010 (US3) in parallel — different files.
- Once Setup is done: US1, US2, US3 can all proceed in parallel by different people/agents — zero shared
  files between any of the three stories.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (User Story 1 — Double Tap on approvals).
3. **STOP and VALIDATE** with the operator on-device (T008).
4. Ship as the MVP — the one item with a real safety property is proven working first.

### Incremental Delivery

1. Setup → baseline confirmed.
2. US1 → validate on-device → MVP shippable.
3. US3 → validate on-device → corner complications shippable.
4. US2 → validate on-device → all of B4+B5 complete.
5. Polish → final regression, documentation, milestone blog post.
