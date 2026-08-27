# Tasks: NetGeniusClaw Mobile Siri Reliability Fix + Two-Way Voice + Theme Toggle (Pass 1 of 3)

**Input**: Design documents from `/specs/115-siri-reliability-fix/`
**Prerequisites**: plan.md, research.md, data-model.md, quickstart.md

**Tests**: This codebase's convention (specs 066-114) unit-tests every headless-entrypoint's
testable core and every small preference class; 🔌 DEVICE tasks cover what only reproduces on
real hardware. Both are included below.

**Organization**: Tasks are grouped by user story from `spec.md` so each story is independently
completable and testable. User Story 1's three root-cause fixes were already implemented and
verified live during the session that produced this plan (see research.md R1-R3) — its tasks
below are marked accordingly and consist of formal verification + regression-proofing, not new
implementation.

## Phase 1: Setup

- [ ] T001 Confirm working tree is on branch `115-siri-reliability-fix` with tonight's prior
      commit (`fix(111): headless App Intents never ran + true two-way Siri voice`) as its base;
      no setup action needed beyond this confirmation (existing project, no new dependencies).

## Phase 2: Foundational

*No foundational/blocking work — all three user stories build directly on already-fixed,
already-existing code paths with no shared new infrastructure between them.*

## Phase 3: User Story 1 - Siri/Shortcuts actually reach NetGeniusClaw (Priority: P1) 🎯 MVP

**Goal**: Every fresh install reliably reaches NetGeniusClaw's own code from Border Health, Pending
Approvals, and Ask NetGeniusClaw, with no manual workaround and no crash.

**Independent Test**: Fresh install, no foreground launch, say "Hey Siri, check NetGeniusClaw Border
health" (and the other two actions) — see quickstart.md steps 1-3, 6.

**Status**: The three root-cause fixes are already implemented and committed
(`mobile/netclaw-mobile/lib/main.dart`, `mobile/netclaw-mobile/ios/Runner/HeadlessEngineRunner.swift`,
`AskBorderIntent.swift`, `BorderHealthIntent.swift`, `PendingApprovalsIntent.swift`) and were each
verified individually on a real device during the session that produced this plan. The tasks
below formalize a full, fresh, from-scratch regression pass covering all three actions together
under realistic conditions, since each fix was previously verified one at a time while iterating.

- [X] T002 [US1] Root cause 1 fixed: import the three headless entrypoint files from
      `mobile/netclaw-mobile/lib/main.dart` (already done; confirmed via `strings` on the
      compiled `App.framework` binary showing all three entrypoint symbols present).
- [X] T003 [US1] Root cause 2 fixed: `mobile/netclaw-mobile/ios/Runner/HeadlessEngineRunner.swift`
      uses `FlutterEngineGroup` and a minimal explicit plugin allow-list instead of
      `GeneratedPluginRegistrant.register(with:)` (already done; confirmed via a pulled `.ips`
      crash report showing the failure mode before the fix, and its absence after).
- [X] T004 [US1] Root cause 3 fixed: every `HeadlessEngineRunner(...)` call site in
      `AskBorderIntent.swift`, `BorderHealthIntent.swift`, `PendingApprovalsIntent.swift` passes
      the correct `libraryURI` (already done; confirmed via an on-disk diagnostic log showing full
      Dart-side execution after the fix, versus none before it).
- [ ] T005 [US1] 🔌 DEVICE: Fresh-install regression pass — uninstall the app completely, install
      the current `115-siri-reliability-fix` build, and without ever opening the app's UI, run
      quickstart.md steps 1-3 for all three actions back-to-back. Record pass/fail per action.
- [ ] T006 [US1] 🔌 DEVICE: Crash-safety regression pass — repeat T005's three actions with the
      main app foregrounded, then backgrounded, then fully force-quit beforehand (quickstart.md
      step 6); confirm via `idevicecrashreport` that no new `Runner-*.ips` crash report appears
      after any of the nine (3 actions × 3 app states) invocations.

**Checkpoint**: User Story 1 is fully verified once T005/T006 both pass — this alone is a
shippable, valuable fix independent of User Stories 2 and 3.

---

## Phase 4: User Story 2 - A fast answer is spoken directly, not just acknowledged (Priority: P2)

**Goal**: When the Border answers quickly enough, Siri speaks the real, markdown-free answer;
otherwise, today's acknowledge-then-notify behavior is preserved exactly, and every Siri-answered
turn lands correctly in conversation history exactly once regardless of which path served it.

**Independent Test**: Ask a question with a known-fast answer path via Siri and confirm the real
answer is spoken, markup-free (quickstart.md steps 4-5).

**Status**: The two-way-voice fast/fallback split in `runAskBorder`
(`mobile/netclaw-mobile/lib/ncfed/ask_border_headless.dart`) is already implemented, unit-tested
(7/7 passing including a dedicated fast-path test), and verified live end-to-end on a real
device. Markdown stripping (FR-005) is the one remaining piece of new work for this story.

- [X] T007 [US2] Two-way-voice fast/fallback split implemented in
      `mobile/netclaw-mobile/lib/ncfed/ask_border_headless.dart`'s `runAskBorder` (already done;
      `askBorderFastWindow` currently 18s per research.md R4; unit test
      `'a real answer arriving within fastWindow is returned directly for Siri to speak (two-way
      voice)'` in `mobile/netclaw-mobile/test/ask_border_headless_test.dart` passing).
- [ ] T008 [P] [US2] Add a small markdown-stripping function (strip `**bold**`/`*italic*`,
      `# `/`## ` headers, and `- `/`* ` list-item markers, collapsing resulting blank lines) in
      `mobile/netclaw-mobile/lib/ncfed/ask_border_headless.dart`. Apply it ONLY to the string
      returned from the fast-voice path (what Siri speaks) — the value passed to
      `store.updateState(taskId, ..., answerText: ...)` MUST remain the original, unstripped text,
      since that's what the app's Chat screen displays (research.md R5). Never applied on the
      fallback acknowledgment or the notify/reconciliation paths.
- [ ] T009 [P] [US2] Unit tests in `mobile/netclaw-mobile/test/ask_border_headless_test.dart` for
      the markdown-stripping function: bold, headers, bullet lists, a mix of all three, and plain
      text with no markup (must pass through unchanged). Add NEW test case(s) with genuinely
      markdown-laden fake-answer input (the existing fast-path test's input, "Yes, BGP is up.",
      has no markdown, so it cannot exercise stripping — do not rely on extending it alone).
      Assert both that the *returned* value is stripped and that `store.turns.single.answerText`
      still holds the original, unstripped text.
- [ ] T010 [US2] 🔌 DEVICE: Ask a question via Siri whose answer is known to arrive within the
      fast window (quickstart.md step 4); confirm the spoken answer is intelligible and free of
      literal `**`, `#`, or leading `- `/`* ` characters.
- [ ] T011 [US2] 🔌 DEVICE: Ask a question via Siri whose answer is known to be slow
      (quickstart.md step 5); confirm the fallback acknowledgment is unchanged, and that the real
      answer later appears exactly once in the conversation history with no duplicate or missing
      entry (FR-007).

**Checkpoint**: User Story 2 is fully verified once T010/T011 both pass, independent of whether
User Story 3 has landed.

---

## Phase 5: User Story 3 - Choose light or dark appearance manually (Priority: P3)

**Goal**: The operator can override the phone's system Light/Dark setting from within NetGeniusClaw's
own Settings, with the choice taking effect immediately and persisting across restarts.

**Independent Test**: Change the appearance in Settings while the system setting differs; confirm
the whole app reflects it immediately and after a full restart (quickstart.md step 7).

- [ ] T012 [P] [US3] Create `mobile/netclaw-mobile/lib/ncfed/theme_preference.dart`: a
      `ThemePreference` class mirroring `AppLockPreference`'s existing shape
      (`mobile/netclaw-mobile/lib/ncfed/app_lock.dart`) — constructor-injectable
      `FlutterSecureStorage`, async `load()` returning `ThemeMode` (default `ThemeMode.system` if
      no value stored), async `save(ThemeMode)`.
- [ ] T013 [P] [US3] Unit tests in `mobile/netclaw-mobile/test/theme_preference_test.dart`: round
      trips all three values (`system`/`light`/`dark`), and defaults to `ThemeMode.system` when
      nothing has ever been saved.
- [ ] T014 [US3] In `mobile/netclaw-mobile/lib/main.dart`: create a single app-wide
      `ValueNotifier<ThemeMode>`, load its initial value from `ThemePreference` before `runApp`,
      and wrap `NetClawMobileApp`'s existing `MaterialApp` (`theme`/`darkTheme` unchanged) in a
      `ValueListenableBuilder<ThemeMode>` so `themeMode:` reflects the notifier's current value
      instead of the hardcoded `ThemeMode.system` (depends on T012).
- [ ] T015 [US3] In `mobile/netclaw-mobile/lib/screens/settings_screen.dart`: add a
      Light/Dark/System control (e.g. a segmented control or radio group, matching this screen's
      existing control style) that calls `ThemePreference.save(...)` and updates the T014
      notifier's value on selection (depends on T012, T014).
- [ ] T016 [US3] 🔌 DEVICE: Full theme-toggle walkthrough (quickstart.md step 7) — switch to Light
      against a system-Dark phone, confirm immediate effect; force-quit and reopen, confirm it
      persisted; switch back to System, confirm it now follows the system setting again.

**Checkpoint**: User Story 3 is fully verified once T016 passes, independent of User Stories 1
and 2.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T017 [P] Remove the temporary diagnostic logging added while chasing root causes 1-3
      (research.md R7): delete `_diag()` and its call sites in
      `mobile/netclaw-mobile/lib/ncfed/border_health_headless.dart`, and delete `diagLog()` and
      its call sites in `mobile/netclaw-mobile/ios/Runner/HeadlessEngineRunner.swift`.
- [ ] T018 🔌 DEVICE: Confirm cleanup (quickstart.md step 8) — after a fresh install and repeating
      the User Story 1/2 walkthroughs, pull the app's Documents directory via `devicectl device
      copy from` and confirm neither `bh_diag.log` nor `bh_diag_native.log` is present.
- [ ] T019 Run the full existing mobile test suite (`flutter test`) to confirm no regression
      outside the files this plan touches.
- [ ] T020 Draft the WordPress milestone blog post per constitution Principle XVII, covering what
      was built (three real root causes found via live on-device debugging, true two-way Siri
      voice, theme toggle), why it matters, and the key technical lessons (AOT entrypoint
      reachability, `FlutterEngineGroup` vs. raw second engine, `libraryURI` resolution) — present
      to John for review before publishing, per that principle's requirement.

## Dependencies & Execution Order

- **User Stories 1, 2, 3 are mutually independent** — none blocks another; they may be executed
  and verified in any order, or in parallel across sessions, per the spec's own priority ordering
  (P1 → P2 → P3) if done sequentially.
- Within User Story 2: T008 (implementation) before T009/T010/T011 (tests/verification that
  depend on it existing).
- Within User Story 3: T012 before T013 (tests need the class to exist), T012 before T014
  (main.dart needs the class), T012+T014 before T015 (Settings needs both the class and the
  notifier it updates), all of T012-T015 before T016 (device verification needs the full chain).
- Phase 6 (Polish) follows all three user stories, since T018's verification needs the full
  regression surface from T005/T006/T010/T011/T016 to already be green.

## Parallel Example

```text
# T008 and T012/T013 touch entirely different files (ask_border_headless.dart vs. a new
# theme_preference.dart) and belong to independent user stories — safe to run together:
Task: "Add markdown-stripping function in ask_border_headless.dart" (T008)
Task: "Create ThemePreference class in theme_preference.dart" (T012)
Task: "Unit test ThemePreference round-trip/default in theme_preference_test.dart" (T013)
```

## Implementation Strategy

### MVP First (User Story 1 only)

User Story 1 (T002-T006) is already implemented and mostly already verified — the remaining work
is T005/T006's full fresh-install regression pass. This alone restores spec 111's entire promise
and is independently shippable.

### Incremental Delivery

1. Complete User Story 1's regression pass (T005-T006) → confidently shippable on its own.
2. Add User Story 2 (T008-T011) → real spoken answers, still shippable independent of Story 3.
3. Add User Story 3 (T012-T016) → theme toggle, cosmetic and fully independent.
4. Phase 6 polish (T017-T020) closes out Pass 1 once all three stories are verified.
