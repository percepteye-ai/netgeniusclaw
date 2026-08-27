# Tasks: NetGeniusClaw Mobile 1.0.1 Polish Pass (Phase A + C1)

**Input**: Design documents from `/specs/110-mobile-polish-pass/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — every prior mobile spec in this project (066–108) ships tests alongside implementation as standard practice, and spec.md's acceptance scenarios are directly testable.

**Organization**: Tasks are grouped by user story (US1–US7, per spec.md's priorities) so each is independently implementable, testable, and deliverable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to US1–US7 from spec.md
- All paths are relative to `mobile/netclaw-mobile/` unless stated otherwise

---

## Phase 1: Setup

**Purpose**: Establish a known-clean baseline and pull in the two new dependencies every later story needs available.

- [x] T001 Run `flutter analyze` and `flutter test` and confirm a clean baseline (0 issues, 289/289 passing) before making any change — this is the starting point every later task's own analyze/test run is measured against
- [x] T002 [P] Add `flutter_markdown_plus: ^1.0.12` and `share_plus: ^13.3.0` to `pubspec.yaml` dependencies (research.md R1/R2), then run `flutter pub get`

**Checkpoint**: Baseline confirmed clean; both new dependencies resolve.

---

## Phase 2: Foundational

**No blocking foundational tasks are required.** All seven user stories are independent by design — each has its own Independent Test criterion in spec.md and touches non-overlapping files, with one exception worth flagging rather than gating on: US1, US4, and US7 all touch `lib/main.dart` (US1 wires `theme`/`darkTheme`/`themeMode` into `MaterialApp`; US4 inserts the lock screen into `EnrollmentGate` and wires Settings' app-lock toggle; US7 factors out `_selectTab` and adds `DashboardScreen` callbacks). None of these edits overlap the same lines, but if working these three stories in parallel, coordinate on `main.dart` rather than serializing behind a false dependency. Proceed directly to the user story phases; they may be done in any order.

---

## Phase 3: User Story 1 - The app looks correct in Dark Mode (Priority: P1) 🎯 MVP

**Goal**: The app defines a proper dark `ColorScheme`, follows the system appearance setting, and no screen hardcodes a color literal that would look wrong or disappear under dark mode.

**Independent Test**: Switch the device to Dark Appearance, launch the app, and visually confirm every screen renders with a dark surface and legible text — no Border, no enrollment, no other story required.

### Tests for User Story 1

- [x] T003 [P] [US1] Write widget tests in `test/theme_test.dart` covering: (a) `lightColorScheme`/`darkColorScheme` are both derived from the same brand seed color, differing only in `Brightness`, (b) a `MaterialApp` built with `theme`/`darkTheme`/`themeMode: ThemeMode.system` from `lib/theme.dart` resolves the dark scheme when the platform brightness is dark and the light scheme when it is light. Confirm these fail against current code before implementing.
- [x] T004 [P] [US1] Write a repo-hygiene test in `test/no_hardcoded_colors_test.dart` that scans every `.dart` file under `lib/screens/` (excluding `enrollment_screen.dart` and `device_scan_screen.dart` per FR-002's camera-scrim exception) for `Colors.grey`, `Colors.black`, or `Colors.white` literals and fails listing any file/line found. Confirm it currently fails (chat_screen.dart's three known literals) before implementing.

### Implementation for User Story 1

- [x] T005 [P] [US1] Create `lib/theme.dart` exporting `lightColorScheme`/`darkColorScheme` (both `ColorScheme.fromSeed` from the existing brand seed color `0xFFE65733`, differing only in `brightness`) plus a small `netclawTheme`/`netclawDarkTheme` `ThemeData` pair built from them
- [x] T006 [US1] Replace `lib/main.dart`'s single `theme: ThemeData(...)` (currently line 64) with `theme`/`darkTheme` from `lib/theme.dart` and add `themeMode: ThemeMode.system` to the `MaterialApp` (depends on T005)
- [x] T007 [P] [US1] Replace the three hardcoded `Colors.grey` literals in `lib/screens/chat_screen.dart` (photo-unavailable placeholder, Cancelled label, failure text — around lines 512/529/538) with `Theme.of(context).colorScheme.onSurfaceVariant`/`.error` as appropriate
- [x] T008 [P] [US1] Wrap the illustration in `lib/screens/empty_state.dart` in a theme-aware backdrop (e.g. a `Container`/`Card` using `colorScheme.surfaceContainer` or similar) so `assets/illustrations/empty_feed.png`/`empty_approvals.png` stay legible if their content is light-background-oriented, without needing new dark-variant image assets
- [x] T009 [US1] Update `pubspec.yaml`'s `flutter_native_splash` config to add `color_dark`/`image_dark` entries, then run `dart run flutter_native_splash:create` to regenerate the platform splash assets (FR-003)

**Checkpoint**: User Story 1 is fully functional and independently testable — dark mode renders correctly everywhere in scope, the color-literal sweep is locked in by a test.

---

## Phase 4: User Story 2 - Chat answers can be selected, copied, shared, and read as formatted text (Priority: P1)

**Goal**: Answer/message text is selectable, copyable (whole answer, question+answer, or an individual code block), shareable, and rendered as Markdown only when it actually looks like Markdown.

**Independent Test**: Seed a turn with a long, multi-line answer; confirm it's selectable, copyable in one action, and — if it contains a fenced block or pipe-table row — renders as formatted Markdown with its own code-block copy button.

### Tests for User Story 2

- [x] T010 [P] [US2] Write unit tests in `test/answer_format_test.dart` for `looksLikeMarkdown(String)` (research.md R3): returns `true` for text containing a closed triple-backtick fenced block, returns `true` for text containing a pipe-table row, returns `false` for raw text containing bare `#`/`*`/`_`/`|` with no fence or table row, returns `false` for plain text. Confirm these fail before implementing.
- [x] T011 [P] [US2] Write widget tests in `test/chat_screen_test.dart` covering: (a) an answer's text is inside a `SelectableText`, (b) tapping the overflow menu's Copy action puts the full answer on a mocked clipboard with a confirmation shown, (c) long-pressing the answer opens the identical menu (not a different action), (d) "Copy question + answer" copies both together question-first, (e) the share action is wired to `SharePlus`, (f) a fenced-block/table answer renders via the Markdown widget while a bare-CLI-output answer renders as plain preformatted text, (g) a non-terminal (pending/working) turn always renders as plain preformatted text regardless of content (Clarifications, 2026-08-14), even if it happens to contain a fence/pipe mid-stream. Confirm these fail before implementing.
- [x] T012 [P] [US2] Write widget tests in `test/feed_screen_test.dart` (create if none exists) asserting the identical selectable/copy/share/Markdown treatment applies to a Feed message body.

### Implementation for User Story 2

- [x] T013 [P] [US2] Create `lib/ncfed/answer_format.dart` with `bool looksLikeMarkdown(String text)` per research.md R3 (checks for a closed fenced code block or a pipe-table row line, nothing more elaborate)
- [x] T014 [US2] In `lib/screens/chat_screen.dart`'s `_TurnTile` (around line 391), replace the bare `Text(turn.answerText ?? '')` (line 549) with: `SelectableText` wrapping either a Markdown widget (`flutter_markdown_plus`, monospaced `code`/`pre` style, per-fenced-block copy button) when `turn.state` is terminal AND `looksLikeMarkdown(turn.answerText)`, or plain monospaced preformatted `SelectableText` otherwise (depends on T013)
- [x] T015 [US2] Add an always-visible overflow menu control to `_TurnTile` offering Copy, "Copy question + answer," and Share, wired to `Clipboard.setData`/`SharePlus.instance.share()` (attaching `turn.photoPath` when present) with a confirmation `SnackBar` on copy; wrap the same tile in a `GestureDetector`/`InkWell` `onLongPress` that opens the identical menu (depends on T014)
- [x] T016 [US2] Apply the identical selectable/copy/share/Markdown-or-preformatted rendering to message bodies in `lib/screens/feed_screen.dart`, reusing `answer_format.dart`'s `looksLikeMarkdown` (depends on T013)

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Approval requests reach the operator even in a Focus mode (Priority: P2)

**Goal**: Approval notifications are Time Sensitive (iOS) / heads-up (Android); feed/chat notifications stay at their current passive level.

**Independent Test**: With a Focus mode allowing only Time Sensitive notifications, trigger an approval push (shown) and a feed push (not shown).

### Tests for User Story 3

- [x] T017 [P] [US3] Write unit tests in `test/local_notifications_test.dart` (create if none exists) asserting: the `DarwinNotificationDetails` constructed for an approval notification carries `interruptionLevel: InterruptionLevel.timeSensitive`; the one constructed for feed/chat-answer notifications does not; the `AndroidNotificationDetails` for the `'approvals'` channel carries `importance: Importance.high`/`priority: Priority.high`; the feed/chat Android channel does not. Confirm these fail before implementing.

### Implementation for User Story 3

- [x] T018 [US3] In `lib/ncfed/local_notifications.dart`, add `interruptionLevel: InterruptionLevel.timeSensitive` to the approval `DarwinNotificationDetails` (currently around lines 178-186), leaving the feed/chat-answer construction (around lines 150-161) unchanged
- [x] T019 [US3] In the same file, set `importance: Importance.high`/`priority: Priority.high` on the `'approvals'` Android notification channel/`AndroidNotificationDetails` (currently around line 187), leaving other channels unchanged

**Checkpoint**: User Story 3 is fully functional and independently testable.

---

## Phase 6: User Story 4 - An operator can require Face ID to open the app (Priority: P2)

**Goal**: An opt-in, operator-adjustable Face ID app-lock gates app content on cold start and after a grace period, without double-prompting against the existing approval biometric flow.

**Independent Test**: Enable the toggle, force-quit/relaunch (lock screen appears), background past the grace period (lock screen reappears), background briefly (no re-prompt).

### Tests for User Story 4

- [x] T020 [P] [US4] Write unit tests in `test/app_lock_test.dart` for the grace-period logic (pure function taking "now," "last foregrounded at," and a grace-period `Duration`, returning whether re-authentication is required) covering: within grace period → false, at/after grace period → true, toggle disabled → always false regardless of elapsed time. Confirm these fail before implementing.
- [x] T021 [P] [US4] Write a widget test asserting that when app-lock is enabled and unauthenticated, no `HomeShell` descendant is present in the widget tree — only the lock screen.
- [x] T022 [P] [US4] Extend `test/settings_screen_test.dart` with tests for the new "Require Face ID to open NetGeniusClaw" toggle and its grace-period duration control: toggling persists via the injected storage, selecting a duration persists it, and both default correctly (disabled / 60s) when nothing has been set yet.

### Implementation for User Story 4

- [x] T023 [P] [US4] Create `lib/ncfed/app_lock.dart`: a pure `bool requiresReauth({required DateTime now, required DateTime? lastForegroundedAt, required Duration gracePeriod})` function (research.md R5), plus an injectable wrapper around `local_auth`'s `authenticate()` (mirroring the pattern in `voice_transcription.dart`/`reconnect_supervisor.dart`, research.md R4) with `biometricOnly: false` so a device-passcode fallback is always available
- [x] T024 [US4] Add the "Require Face ID to open NetGeniusClaw" toggle and a grace-period duration control (a small fixed choice set — e.g. Immediately/30s/60s/5 min, research.md R5) to `lib/screens/settings_screen.dart`, persisting both via `flutter_secure_storage` (`app_lock_enabled`, `app_lock_grace_period_seconds`, per data-model.md)
- [x] T025 [US4] In `lib/main.dart`'s `EnrollmentGate`/`HomeShell` area, insert a lock-screen widget shown before `HomeShell` on cold start when app-lock is enabled, and again on resume (`AppLifecycleState.resumed`) when `app_lock.dart`'s `requiresReauth` returns true against a "last foregrounded at" timestamp stamped on successful auth; blur/cover content before backgrounding (`AppLifecycleState.paused`) so the app-switcher snapshot doesn't leak it (depends on T023, T024)
- [x] T026 [US4] Confirm (via T021's widget test and a code read of `approval_confirmation.dart`'s call sites) that the app-lock flow and the existing per-approval biometric confirmation never both fire for the same user action — no code change expected here if T025 is scoped correctly to app-open/resume only, but this task exists to make FR-010 an explicit, checked deliverable rather than an assumption

**Checkpoint**: User Stories 1-4 all work independently.

---

## Phase 7: User Story 7 - Tapping the Dashboard's unread or pending count opens it (Priority: P2)

**Goal**: The Dashboard's "Unread" and "Pending approvals" rows navigate to the right tab instead of doing nothing.

**Independent Test**: With unread Feed messages, tap "Unread" on Dashboard and confirm it switches to Feed and clears the badge; with unread Chat only, confirm it goes to Chat instead; tap "Pending approvals" and confirm it always goes to Approvals.

### Tests for User Story 7

- [x] T027 [P] [US7] Write widget tests in `test/dashboard_screen_test.dart` (create if none exists) covering: (a) tapping "Unread" when `unreadFeed > 0` invokes the `onOpenFeed` callback, (b) tapping it when `unreadFeed == 0 && unreadChat > 0` invokes `onOpenChat`, (c) tapping it when both are zero invokes neither callback, (d) tapping "Pending approvals" always invokes `onOpenApprovals` regardless of count. Confirm these fail before implementing.

### Implementation for User Story 7

- [x] T028 [US7] In `lib/main.dart`'s `_HomeShellState`, factor the tab-switch-plus-mark-read logic already inside `NavigationBar.onDestinationSelected` (currently lines 710-720) into a reusable `_selectTab(int index)` method, and pass `onOpenFeed: () => _selectTab(2)`, `onOpenChat: () => _selectTab(1)`, `onOpenApprovals: () => _selectTab(3)` into the `DashboardScreen` constructor (currently line 655) (research.md R7)
- [x] T029 [US7] Add `onOpenFeed`, `onOpenChat`, `onOpenApprovals` `VoidCallback` parameters to `lib/screens/dashboard_screen.dart`'s `DashboardScreen`, and wire the "Unread" `ListTile`'s `onTap` (currently no `onTap` at all, lines 61-65) to invoke `onOpenFeed` when `snapshot.unreadPending.unreadFeed > 0`, else `onOpenChat` when `unreadChat > 0`, else nothing; wire "Pending approvals" (lines 66-70) `onTap` unconditionally to `onOpenApprovals` (depends on T028)

**Checkpoint**: User Stories 1-4 and 7 all work independently.

---

## Phase 8: User Story 5 - Key events produce haptic feedback (Priority: P3)

**Goal**: Six distinct events produce exactly one haptic each, on phone and watch, with no repeated buzzing during a bounded reconnect retry loop.

**Independent Test**: Trigger each event and confirm exactly one haptic fires per event; force a disconnect and confirm the reconnect retry loop doesn't repeat the haptic.

### Tests for User Story 5

- [x] T030 [P] [US5] Write unit tests in `test/haptics_test.dart` against an injected recording fake covering: each of the six events (approval arrives, approval resolved successfully, approval resolve failed, chat answer completes, enrollment succeeds, Border connection lost) invokes exactly the haptic call mapped to it, and that a bounded sequence of reconnect retry failures after the initial disconnect produces no additional haptic calls (the retry-loop debounce). Confirm these fail before implementing.

### Implementation for User Story 5

- [x] T031 [P] [US5] Create `lib/ncfed/haptics.dart`: an injectable wrapper (production default calling `HapticFeedback.heavyImpact()`/`.mediumImpact()`/`.vibrate()`/`.lightImpact()` per spec.md's event table) exposing one function per event, following the injectable-function pattern in `voice_transcription.dart`/`reconnect_supervisor.dart` (research.md R4)
- [x] T032 [US5] Wire haptic calls into `lib/ncfed/approval_client.dart` (approval arrives / resolved successfully / resolve failed), `lib/screens/chat_screen.dart`'s `askClient.updates` listener (chat answer completes), `lib/ncfed/enrollment_flow.dart` (enrollment succeeds) (depends on T031)
- [x] T033 [US5] Wire the connection-lost haptic into `lib/ncfed/reconnect_supervisor.dart`, firing only on the transition into the disconnected state (not on each subsequent retry attempt within the same disconnected period) (depends on T031)
- [x] T034 [P] [US5] 🔌 DEVICE — Add the watch-native equivalent haptic calls (`WKInterfaceDevice.current().play(.notification/.success/.failure/.click/.retry)`) directly in `ios/WatchApp Watch App/ApprovalsView.swift` and `WatchDataStore.swift` for the same six events (research.md R6 — no Dart bridge, Swift-only change)

**Checkpoint**: User Stories 1-5 and 7 all work independently.

---

## Phase 9: User Story 6 - Chat history and Feed can be searched and filtered (Priority: P3)

**Goal**: Live, case-insensitive search plus state/origin filter chips on Chat and Feed, filtering the view only.

**Independent Test**: Type a query, confirm live narrowing with highlights; clear it, confirm full list returns; combine a filter chip with a query and confirm both apply together.

### Tests for User Story 6

- [x] T035 [P] [US6] Write unit tests in `test/conversation_search_test.dart` for the pure filter function(s) over `List<ConversationTurn>`/`List<EdgeMessage>` covering: empty query returns everything, a query matching nothing returns an empty list, a query matching a subset returns only that subset (case-insensitive), a state filter and an origin filter combine with an active query via AND (not OR), and — critically — that the function returns filtered *items* (or indices mappable back to the original list), never a structure that could cause an "acknowledge the 2nd visible item" action to hit the wrong underlying item (FR-014). Confirm these fail before implementing.
- [x] T036 [P] [US6] Extend `test/chat_screen_test.dart` with tests for the search field/filter chips UI: live narrowing as text is typed, highlighted matches, filter chips composing with the query, acknowledging/deleting a turn while filtered affects the correct underlying turn, and search/filter state resetting on a fresh widget mount (not persisted). Confirm these fail before implementing.
- [x] T037 [P] [US6] Extend `test/feed_screen_test.dart` with the equivalent search-field tests for message bodies.

### Implementation for User Story 6

- [x] T038 [P] [US6] Create `lib/ncfed/conversation_search.dart`: pure functions filtering a list of turns/messages by case-insensitive substring match plus optional state/origin filter sets, returning the filtered list without mutating or copying-and-losing-identity of the underlying items (FR-014)
- [x] T039 [US6] Add a search field and match-highlighting to `lib/screens/chat_screen.dart`'s turn list, plus filter chips for turn state and origin, wired through `conversation_search.dart`; ensure acknowledge/delete actions on a filtered item still resolve to the correct underlying turn (depends on T038)
- [x] T040 [US6] Add the equivalent search field and match-highlighting to `lib/screens/feed_screen.dart`'s message list (depends on T038)

**Checkpoint**: All seven user stories are independently functional.

---

## Phase 10: Polish & Cross-Cutting Concerns

- [x] T041 Bump `pubspec.yaml`'s `version` from `1.0.0+1` to `1.0.1+2` (FR-016)
- [x] T042 [P] Run `flutter analyze` and the full `flutter test` suite across the whole app (not just new test files) to confirm zero regressions and zero skipped tests (SC-007)
- [ ] T043 Execute quickstart.md's manual/🔌 DEVICE verification steps for every story that has one (US2's long-answer scroll check, US3's Focus-mode check, US4's biometric prompts, US5's phone-and-watch haptics)
- [x] T044 Update `mobile/netclaw-mobile/README.md`'s platform-notes section recording what was verified on real hardware versus left as an automated-tests-only claim, per specs 072/073's honesty convention (explicitly: US2's scroll-performance scenario, US5's watch-side haptics, any other 🔌 DEVICE item not exercised)
- [x] T045 Update `mobile/netclaw-mobile/APP-STORE-ROADMAP.md` if any of this spec's items turn out to need a portal/App Store Connect note (expected: none, since Phase A/C1 explicitly avoids new capabilities — confirm rather than assume)
- [x] T046 Per constitution Principle XVII, draft a milestone summary (WordPress blog post via the WordPress MCP server if configured; otherwise note the milestone here and remind the operator to publish manually) once all seven stories are complete — Drafted at `docs/blog/2026-08-14-mobile-polish-pass.md`, marked "not published," awaiting John's review.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: None — skipped, see above (shared-file coordination note only, not a gate).
- **User Stories (Phase 3–9)**: All seven depend only on Setup's T001/T002 (a clean baseline with the two new dependencies resolved); none depend on each other's completion.
- **Polish (Phase 10)**: Depends on all in-scope user stories being complete.

### User Story Dependencies

- **US1, US2, US3, US4, US5, US6, US7**: No dependency on each other. US2 depends on Setup's T002 (new packages) specifically; the rest need only T001.

### Within Each User Story

- Tests (T003/T004, T010-T012, T017, T020-T022, T027, T030, T035-T037) MUST be written and failing before their story's implementation tasks.
- US1: T005 (theme.dart) before T006 (wiring); T007-T009 independent of T005/T006 and of each other.
- US2: T013 (classifier) before T014 (rendering); T014 before T015 (menu/actions); T016 (Feed) depends only on T013.
- US4: T023 (app_lock.dart) before T024 (Settings UI) and T025 (main.dart wiring); T026 is a verification task, last.
- US7: T028 (main.dart factor-out) before T029 (DashboardScreen wiring).
- US5: T031 (haptics.dart) before T032/T033; T034 (watch-side) is independent Swift work, no Dart dependency.
- US6: T038 (pure filter functions) before T039/T040.

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel.
- All seven user story phases (3-9) can be worked in parallel by different people once Setup completes, modulo the `lib/main.dart` coordination note in Phase 2 (US1/US4/US7).
- Within each story, every task marked `[P]` touches a different file than its siblings and can run concurrently.

---

## Parallel Example: Highest-priority stories together

```bash
# US1 and US2 are both P1 and fully independent — their tests can be launched together:
Task: "Write widget tests in test/theme_test.dart (T003)"
Task: "Write repo-hygiene test in test/no_hardcoded_colors_test.dart (T004)"
Task: "Write unit tests in test/answer_format_test.dart (T010)"
Task: "Write widget tests in test/chat_screen_test.dart for US2 (T011)"

# Likewise their initial implementation:
Task: "Create lib/theme.dart (T005)"
Task: "Create lib/ncfed/answer_format.dart (T013)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001; T002 only serves US2, can wait)
2. Skip Phase 2: no foundational work needed
3. Complete Phase 3: User Story 1 (T003-T009)
4. **STOP and VALIDATE**: run quickstart.md's US1 verification on a physical device
5. This alone is the single most visible fix a new Dark-Appearance user will notice, independent of every other story

### Incremental Delivery

1. Setup → User Story 1 → validate → (optional stop point)
2. Add User Story 2 → validate → (optional stop point) — both P1 stories now ship together as the brief's own "if only three ship" MVP half
3. Add User Stories 3, 4, 7 (all P2) → validate each independently
4. Add User Stories 5, 6 (both P3) → validate each independently
5. Polish phase confirms nothing regressed and closes out the milestone

### Notes

- [P] tasks touch different files and have no incomplete dependency — safe to parallelize.
- Commit after each task or logical group, consistent with this project's existing commit granularity.
- Verify each story's tests fail before implementing, then pass after.
- Stop at any checkpoint to validate independently before continuing — no requirement to do all seven stories in one sitting.
