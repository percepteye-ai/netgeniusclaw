# Tasks: iOS App Store Submission Readiness, Phase 1

**Input**: Design documents from `/specs/105-ios-appstore-readiness/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — every prior mobile spec in this project (066–103) ships tests alongside implementation as standard practice, and spec.md's acceptance scenarios are directly testable.

**Organization**: Tasks are grouped by user story (US1/US2/US3, per spec.md's priorities) so each is independently implementable, testable, and deliverable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to US1, US2, or US3 from spec.md
- All paths are relative to `mobile/netclaw-mobile/` unless stated otherwise

---

## Phase 1: Setup

**Purpose**: Establish a known-clean baseline and produce the one shared artifact US3 needs, before any story-specific work begins.

- [x] T001 Run `flutter analyze` and `flutter test` in `mobile/netclaw-mobile/` and confirm a clean baseline (0 issues, all passing) before making any change — this is the starting point every later task's own analyze/test run is measured against
- [x] T002 [P] Generate `mobile/netclaw-mobile/ios/ExportOptions.plist` via a one-time Xcode Organizer export step (Product → Archive → Distribute App → App Store Connect → stop before uploading, export the plist — see quickstart.md), and commit the resulting file. Has no dependency on US1/US2 code, so this can happen at any point but is listed here since it blocks US3's first real task (T009)

**Checkpoint**: Baseline confirmed clean; `ExportOptions.plist` exists and is committed.

---

## Phase 2: Foundational

**No foundational tasks are required.** User Stories 1, 2, and 3 are independent by design — each has its own Independent Test criterion in spec.md and touches non-overlapping code (a new screen, a new Settings control, and a build/upload procedure, respectively). There is no shared blocking infrastructure to build first. Proceed directly to the user story phases; they may be done in any order or in parallel.

---

## Phase 3: User Story 1 - A first-time installer understands what they're looking at (Priority: P1) 🎯 MVP

**Goal**: A brand-new installer sees an explainer screen — stating this is a companion app requiring a self-hosted NetGeniusClaw Border — before the QR scanner, and never sees it again once enrolled.

**Independent Test**: Delete local app data (or install fresh), launch, confirm the explainer appears before the camera/scanner; enroll, relaunch, confirm it does not reappear. No Border interaction, no other story's code, required.

### Tests for User Story 1

- [x] T003 [P] [US1] Write widget tests in `test/onboarding_explainer_screen_test.dart` covering: (a) a fresh install with no persisted `EnrollmentStore` data shows the explainer before `EnrollmentScreen`, (b) an already-enrolled launch skips the explainer entirely and goes straight to the existing enrolled-state UI, (c) tapping through the explainer's continue action leads to the existing QR-scan screen unchanged. Confirm these fail against current code before implementing.

### Implementation for User Story 1

- [x] T004 [P] [US1] Create `OnboardingExplainerScreen` widget in `lib/screens/onboarding_explainer_screen.dart` — static explanatory copy stating the app is a companion client requiring a self-hosted NetGeniusClaw Border server, plus a single continue action (no camera/network/permission calls of its own)
- [x] T005 [US1] Wire `OnboardingExplainerScreen` into `EnrollmentGate`'s unenrolled branch in `lib/main.dart`, shown before `EnrollmentScreen` exactly when `EnrollmentStore.load()` returns `null` (per research.md R1) (depends on T004)

**Checkpoint**: User Story 1 is fully functional and independently testable — a fresh install shows the explainer; an enrolled device does not.

---

## Phase 4: User Story 2 - An operator can remove their own enrollment (Priority: P1)

**Goal**: An enrolled operator can clear their device's enrollment from Settings, gated by the same biometric re-authentication the app already uses for approvals, with zero Border-side dependency.

**Independent Test**: Enroll a test device, open Settings, trigger the new control, complete biometric auth, confirm the app returns to the same state a fresh install shows. Confirm cancelling the biometric prompt leaves the device enrolled and unchanged. No distribution build or App Store Connect access required.

### Tests for User Story 2

- [x] T006 [P] [US2] Write tests in `test/settings_screen_test.dart` (new file) covering: (a) the "Remove this device" control is visible when enrolled, (b) completing biometric re-authentication clears the enrollment (via an injectable `authenticate` callback mirroring `approval_confirmation.dart`'s own test pattern) and returns to the enrollment gate, (c) a cancelled/failed biometric attempt leaves the enrollment untouched, (d) the action cannot fire without going through the confirmation/biometric step, (e) **FR-006**: removal succeeds with no live `EdgeClient`/Border connection at all (construct the widget under test with no reachable Border and confirm the clear-and-return-to-gate path still completes). Confirm these fail against current code before implementing.

### Implementation for User Story 2

- [x] T007 [P] [US2] Add a "Remove this device" control to `lib/screens/settings_screen.dart`, gated by the same `local_auth` pattern `lib/ncfed/approval_confirmation.dart` already uses (per research.md R2) — no new biometric-handling code, call the existing pattern
- [x] T008 [US2] Wire the control's success path to `EnrollmentStore.clear()` followed by returning to the enrollment gate, mirroring the existing `_handleRevoked` path in `lib/main.dart` (depends on T007)

**Checkpoint**: User Stories 1 and 2 both work independently — fresh installs see the explainer, and enrolled operators can self-service remove their enrollment via Settings + biometrics.

---

## Phase 5: User Story 3 - Known testers can install a real, distribution-signed build (Priority: P2)

**Goal**: Produce one distribution-signed archive (including US1/US2's code), upload it to App Store Connect, and get it in front of an External Testing group in TestFlight.

**Independent Test**: Produce the archive, upload it, create the group, invite a tester — verifiable without any App Store public listing existing. Per the Clarifications session (2026-08-11), this story is done once submitted for Apple's Beta App Review, not once that review has passed.

### Implementation for User Story 3

*(No automated tests — this story is a one-time build/upload procedure, not application code. Manual verification steps are in quickstart.md.)*

- [x] T009 [US3] Produce a distribution-signed archive via `flutter build ipa --export-options-plist=ios/ExportOptions.plist` (per research.md R3), run from `mobile/netclaw-mobile/` (depends on T002; should be run after T005/T008 so the archived build actually contains US1/US2)
- [x] T010 [US3] Resolve any distribution-signing/capability errors the archive surfaces — e.g. a `SystemCapabilities` entry missing for a target in `ios/Runner.xcodeproj/project.pbxproj`, following the same diagnostic pattern already used to fix Push Notifications capability registration on this project (depends on T009's result; may be a no-op if the archive succeeds cleanly)
- [x] T011 [US3] Upload the resulting `.ipa` to App Store Connect via `xcrun altool --upload-app` using an App Store Connect API key (per research.md R4 / quickstart.md) (depends on T009/T010)
- [x] T012 [US3] In App Store Connect, once the build finishes processing: create a TestFlight External Testing group, attach the uploaded build, and invite at least one known tester (depends on T011) — **note**: T009–T012 were done outside git; the archive was built and uploaded from a working tree that had US1/US2 code uncommitted, so the shipped TestFlight build already includes it even though this repo had no record of it until this branch was reconciled (2026-08-14)

**Checkpoint**: All three user stories are independently functional. A distribution build exists, has been uploaded, and is submitted for external testing.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T013 [P] Run `flutter analyze` and the full `flutter test` suite across the whole app (not just the new test files) to confirm zero regressions from US1/US2's changes to `lib/main.dart` and `lib/screens/settings_screen.dart` — verified 2026-08-14: `flutter analyze` 0 issues, `flutter test` 289/289 passing
- [ ] T014 Execute quickstart.md's manual verification steps for User Story 1 and User Story 2 end-to-end on a physical device, per its documented commands — explicitly confirm SC-001 (show the explainer to one person with no prior NetGeniusClaw context and confirm they can correctly restate that a self-hosted Border server is required) and SC-002 (time the enrolled-to-enrollment-gate flow via Settings and confirm it completes in under 30 seconds)
- [ ] T015 Per constitution Principle XVII, draft a milestone summary (WordPress blog post via the WordPress MCP server if configured; otherwise note the milestone here and remind the operator to publish manually) once all three stories are complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. T001 and T002 are independent of each other.
- **Foundational (Phase 2)**: None — skipped, see above.
- **User Stories (Phase 3–5)**: US1 and US2 depend only on Setup's T001 (a clean baseline); neither depends on the other. US3 depends on T002 (Setup) directly, and should be sequenced *after* US1/US2 so the archived build is actually complete, though the archive mechanics themselves don't require US1/US2's code to succeed.
- **Polish (Phase 6)**: Depends on whichever of US1/US2/US3 are in scope for a given delivery being complete.

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on US2 or US3.
- **User Story 2 (P1)**: No dependency on US1 or US3.
- **User Story 3 (P2)**: No hard code dependency on US1/US2, but should be sequenced last so the build being submitted for TestFlight actually includes them.

### Within Each User Story

- Tests (T003, T006) MUST be written and failing before their story's implementation tasks.
- US1: T004 (the screen) before T005 (wiring it into the gate).
- US2: T007 (the control) before T008 (wiring it to `EnrollmentStore.clear()`).
- US3: strictly sequential — T009 → T010 (if needed) → T011 → T012, each depending on the previous succeeding.

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel.
- T003 (US1 tests) and T006 (US2 tests) can run in parallel — different files, different stories.
- T004 (US1 screen) and T007 (US2 control) can run in parallel — different files, different stories.
- US1's entire phase (T003–T005) and US2's entire phase (T006–T008) can be worked in parallel by different people, since neither touches the other's files except both eventually touching `lib/main.dart` (US1 at T005, US2 at T008) — coordinate that one shared file if working simultaneously.

---

## Parallel Example: User Story 1 + User Story 2 together

```bash
# Since US1 and US2 are independent, their test-writing can be launched together:
Task: "Write widget tests in test/onboarding_explainer_screen_test.dart (T003)"
Task: "Write tests in test/settings_screen_test.dart (T006)"

# Likewise their initial implementation:
Task: "Create OnboardingExplainerScreen widget in lib/screens/onboarding_explainer_screen.dart (T004)"
Task: "Add Remove this device control in lib/screens/settings_screen.dart (T007)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001; T002 can wait, it only serves US3)
2. Skip Phase 2: no foundational work needed
3. Complete Phase 3: User Story 1 (T003–T005)
4. **STOP and VALIDATE**: run quickstart.md's US1 verification on a physical device
5. This alone is a real, shippable improvement (closes the "confusing first launch" gap) independent of US2/US3

### Incremental Delivery

1. Setup → User Story 1 → validate → (optional stop point)
2. Add User Story 2 → validate → (optional stop point) — both P1 stories now close the two Guideline-risk gaps
3. Add User Story 3 → produces and submits the actual distribution build carrying US1+US2
4. Polish phase confirms nothing regressed and closes out the milestone

### Notes

- [P] tasks touch different files and have no incomplete dependency — safe to parallelize.
- Commit after each task or logical group, consistent with this project's existing commit granularity (see spec 103's commit history for the established pattern: one commit per coherent chunk of work, not one per file).
- Verify each story's tests fail before implementing, then pass after.
- Stop at either checkpoint (after US1, after US1+US2) to validate independently before continuing — no requirement to do all three stories in one sitting.
