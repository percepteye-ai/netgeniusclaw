# Feature Specification: NetGeniusClaw Mobile Interactive and In-Flight Live Activity (B3)

**Feature Branch**: `113-live-activity-interactive-inflight`
**Created**: 2026-08-15
**Status**: Draft
**Input**: User description: "NetGeniusClaw Mobile App Intents integration follow-on — Phase B3 of mobile/netclaw-mobile/NETCLAW-MOBILE-1.0.1-BRIEF.md. B3a: add Approve/Deny buttons to the existing pending-approval Lock Screen Live Activity via a `LiveActivityIntent` (iOS 17+), foregrounding the app to the Approvals tab rather than resolving headlessly, since a `LiveActivityIntent` cannot reliably present a biometric confirmation prompt from the background — the existing fresh passcode/biometric gate must stay completely intact. Also add an `update()` method so the activity reflects a resolved status and dismisses when handled from any surface. B3b: a new in-flight query Live Activity, started when a submitted question returns a task ID, showing an elapsed timer and the question preview, updated as progress notifications arrive, ended on a terminal state — narrowed from the brief's original `respondedMembers`/`expectedMembers` design after research found that concept isn't real in this system (a submitted ask is one sequential agent turn discovering delegated members one at a time, never a fanned-out request with a known member count upfront)."

## Context

This spec implements item B3 of `mobile/netclaw-mobile/NETCLAW-MOBILE-1.0.1-BRIEF.md`'s Phase B — the
brief's own "best demo per unit of work" item, per that phase's suggested ordering. Two related pieces,
both building on the existing Lock Screen Live Activity infrastructure spec 099 already shipped.

Before writing this spec, the codebase and the Border's actual delegation model were researched directly:

- **The existing approval Live Activity already has everything B3a needs to build on.**
  `PendingApprovalActivityAttributes.swift` carries `approvalId`/`targetName`/`status` ("pending"|
  "resolved"); `PendingApprovalLiveActivityView.swift` renders `Text` only, no button, no intent;
  `LiveActivityBridge.swift`'s `start()`/`end()` are called from `main.dart`'s single
  `approvalClient.pending.listen(...)` hook, which already reacts identically no matter which surface
  changed the underlying pending list — in-app buttons, notification actions, or the watch (spec 072).
  `live_activity.dart`'s Dart-side `LiveActivity` class currently exposes only `start()`/`end()` — no
  `update()`.
- **A `LiveActivityIntent` cannot present a biometric prompt.** This repo's own invariant (spec 073, FR-003)
  is that every approval resolution is preceded by a fresh, never-cached biometric/passcode confirmation.
  `ActivityKit`'s `Button(intent:)` runs a `LiveActivityIntent`'s `perform()` in the app's process, but
  Apple provides no supported way to reliably present `LAContext` UI from that context while the phone is
  locked or the app is backgrounded. This spec does **not** weaken that invariant to make a button work —
  the button instead sets `openAppWhenRun = true`, foregrounding the app directly to the existing Approvals
  tab (`_selectTab(3)` in `main.dart`, the same tab `DashboardScreen`'s `onOpenApprovals` callback already
  uses, spec 110 US7), where the existing, unmodified biometric-gated resolve flow runs exactly as it does
  today.
- **The app already has a working URL-based deep-link mechanism to reuse for the foreground jump.** The
  `netgeniusclaw://` scheme is registered (`Info.plist`'s `CFBundleURLTypes`) and `app_links` already handles both
  cold-start and foreground-tap URLs for the existing `netgeniusclaw://device/<id>` shape
  (`lib/ncfed/device_deep_link.dart`). This spec adds one new recognized shape, `netgeniusclaw://approvals`, to
  that same existing listener rather than building a second, parallel foreground-navigation mechanism.
- **The brief's `AskActivityAttributes` design assumed a data source that does not exist.** Direct research
  into `gateway.py`'s `run_agent_turn`, `service.py`'s `_edge_on_ask`, and `router.py`'s `RiskRouter`
  confirmed: a phone-submitted question is **one single, sequential agent turn**. The underlying model
  decides, one tool call at a time, whether and which risk member to delegate to next — there is no
  upfront "this will fan out to N members" decision, no parallel N-member request, and no structured
  per-member response tracking anywhere in the Border. A real captured trace in this repo
  (`MAC-IOS-HANDOFF.md`) shows this directly: the `cml` delegation completes at 13:04:46, and only *then*
  does the router select `pyats` at 13:04:59 — sequential discovery, not parallel fan-out. Building genuine
  `respondedMembers`/`expectedMembers` counts would require new Border-side task-correlation
  instrumentation (a parent/child task id linking a top-level ask to whatever it delegates to, plus
  counting logic) — real, disproportionate new scope for what this spec is otherwise a small, additive
  Dart/Swift change. This spec instead shows what the system genuinely knows today: an elapsed timer
  (computed client-side from when the ask was submitted) and the Border's own existing best-effort
  free-text progress detail (`n2n/edge/task_progress`'s `detail` field, e.g. "Still working on this — 47s
  so far.") — never a fabricated member count.
- **The in-flight activity is per-question, not aggregated.** Unlike the approval Live Activity (one
  aggregate activity showing "the first pending approval," since approvals are reviewed one at a time),
  Chat already supports multiple concurrent in-progress asks (`ConversationStore.hasInProgressTurns` checks
  for *any* non-terminal turn, and a real multi-minute fan-out is a documented normal case). This spec
  starts one Live Activity per submitted question, keyed by its `task_id`, ending independently when that
  specific turn reaches a terminal state.
- **`ConversationStore` needs one new hook, `onAdded`, alongside its existing `onCompleted`.** `addPending`
  is called from three separate sites in `chat_screen.dart` plus one in `main.dart` (a normal submit, a
  retry, and a photo-attached submit) — mirroring `onCompleted`'s own reason for existing (spec 073's doc
  comment: a single hook fires regardless of which call site triggered the transition, rather than
  duplicating the same wiring at every call site) avoids re-deriving that same lesson for a fourth time.
  `onCompleted` alone is insufficient for ending the in-flight activity, since it fires only for the
  `'completed'` state specifically (by design, for the chat-answer-notification use case) — this spec adds
  a second hook, `onTerminal`, that fires for any of `completed`/`failed`/`cancelled`, since a Live Activity
  must end on every one of those outcomes, not only a successful answer.

This repo's verification standard (specs 072/073/099/110/111/112) applies unchanged: real Live Activity
rendering (Lock Screen, Dynamic Island compact/expanded/minimal), a real interactive button foregrounding
the app, and a real elapsed timer ticking are 🔌 **DEVICE**-only — not claimed done from a green
`flutter test`/Xcode build alone.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Approve or deny straight from the Lock Screen (Priority: P1)

An operator sees a pending-approval Live Activity on their Lock Screen. They tap "Approve" (or "Deny")
directly on the activity, without unlocking the phone first. The phone unlocks/foregrounds directly into
the Approvals tab, where the exact same fresh biometric/passcode confirmation the in-app button already
requires appears — never approving anything without it.

**Why this priority**: The whole point of B3a — one tap from the Lock Screen to a Face ID prompt is a real
improvement over today's tap-to-open-then-navigate-then-tap-Approve flow, without weakening the security
invariant this app has held since spec 073.

**Independent Test**: With a real pending approval showing its Live Activity, tap "Approve" on the
activity and confirm the app foregrounds directly to the Approvals tab with the biometric prompt already
in progress or immediately available for that approval.

**Acceptance Scenarios**:

1. **Given** a pending-approval Live Activity is showing, **When** the operator taps its "Approve" button,
   **Then** the app foregrounds directly to the Approvals tab — it does NOT resolve the approval without
   the operator completing a fresh biometric/passcode confirmation there.
2. **Given** the same setup, **When** the operator taps "Deny" instead, **Then** the same foreground-to-
   Approvals behavior occurs — Deny is not resolved from the Lock Screen either.
3. **Given** the operator completes the confirmation in the Approvals tab after being foregrounded this
   way, **Then** the approval resolves exactly as it would via a normal in-app tap, and the Live Activity
   updates to reflect the resolved status and dismisses (User Story 2).
4. **Given** the device is running an iOS version below 17, **When** the pending-approval Live Activity is
   shown, **Then** it renders exactly as it does today (tap-to-open only, no interactive buttons) — no
   crash, no missing activity.

---

### User Story 2 - The approval activity reflects resolution from any surface (Priority: P2)

An operator resolves a pending approval from the in-app Approvals screen, a notification action, or the
paired Apple Watch — not from the Live Activity itself. The Live Activity updates to show it was resolved
and disappears, instead of continuing to show a now-stale "pending" state.

**Why this priority**: Without this, a Live Activity started for an approval that gets resolved elsewhere
would linger indefinitely on the Lock Screen showing outdated information — a real regression the brief
explicitly calls out avoiding.

**Independent Test**: Start a pending-approval Live Activity, then resolve that approval through a
different surface (in-app button, notification action, or watch) and confirm the Live Activity updates and
dismisses without the operator having touched it directly.

**Acceptance Scenarios**:

1. **Given** a pending-approval Live Activity is showing, **When** the underlying approval is resolved
   through any surface other than the activity itself, **Then** the activity's content updates to show a
   resolved status and dismisses, rather than continuing to show "pending."

---

### User Story 3 - See a submitted question's progress on the Lock Screen (Priority: P2)

An operator submits a question through Chat that they expect to take a while to answer. A Live Activity
appears within about a second, showing the question and a running elapsed-time counter. As the Border
reports it is still working, the activity's status text updates. When the answer arrives (or the turn
fails or is cancelled), the activity reflects that outcome and then ends.

**Why this priority**: The brief's own assessment — "given a documented 2m13s fan-out... this is the
better demo of the two" — and genuinely useful for exactly that scenario: knowing a long-running ask is
still alive without having to open the app and check.

**Independent Test**: Submit a real question expected to take at least a minute, confirm a Live Activity
appears promptly showing the question and a ticking timer, confirm it updates if a progress notification
arrives, and confirm it ends once the turn reaches a terminal state.

**Acceptance Scenarios**:

1. **Given** the operator submits a question through Chat, **When** the Border acknowledges it with a
   task ID, **Then** a Live Activity appears within about a second showing the question text and a
   running elapsed timer starting from zero.
2. **Given** the Live Activity is showing, **When** the Border sends a progress update for that specific
   task, **Then** the activity's status text updates to reflect it (the Border's own free-text detail,
   e.g. "Still working on this — 47s so far") — the elapsed timer continues ticking independently of
   whether a progress update has arrived.
3. **Given** the Live Activity is showing, **When** the turn reaches a terminal state (completed, failed,
   or cancelled), **Then** the activity reflects that outcome and ends — it never continues ticking after
   the turn is over.
4. **Given** the operator submits a second question while the first is still in flight, **When** both are
   showing, **Then** each has its own independent Live Activity, tracking its own elapsed time and
   progress — resolving one does not affect the other.
5. **Given** an in-flight query Live Activity is showing, **When** the operator taps it, **Then** the app
   opens to Chat, where that specific turn is visible (matching how the existing chat-answer notification
   already deep-links to a specific turn, spec 073).
6. **Given** the device is running an iOS version where Live Activities are unavailable or disabled,
   **When** a question is submitted, **Then** the ask itself proceeds normally — the absence of a Live
   Activity never blocks or degrades the actual ask/answer flow, matching how the existing approval
   Live Activity already fails silently and harmlessly on such devices.

### Edge Cases

- What happens if the app is force-quit while an in-flight query Live Activity is showing? Live Activities
  are managed by the OS independently of the app process — per Apple's own lifetime rules, an activity a
  developer never explicitly ended will eventually go stale (this spec's own staleness handling, FR-011)
  rather than being immediately torn down; this spec does not need to detect app termination specifically.
- What happens if two Live Activities' worth of concurrent asks exceeds whatever limit iOS imposes on
  simultaneous activities for one app? The Border/Dart side is unaffected either way; a request that iOS
  itself refuses to start an activity for is a silent, best-effort failure exactly like every other Live
  Activity failure mode already handled (`live_activity.dart`'s existing try/catch) — the ask itself is
  never blocked by it.
- What happens if the operator taps "Approve" on the Lock Screen activity while genuinely offline (no
  network)? Foregrounding to the Approvals tab still happens (that part is purely local); the actual
  resolve attempt then fails the same way any other offline resolve attempt already fails today — no new
  failure mode introduced by this spec.
- What happens to an in-flight query's progress text if the Border never sends a `task_progress`
  notification at all (an older Border build, or a fast answer that finishes before any stall checkpoint)?
  The activity shows just the question and the ticking timer with no status line — never a stale or
  fabricated status.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: On iOS 17+, the pending-approval Live Activity MUST show Approve and Deny buttons that, when
  tapped, foreground the app directly to the Approvals tab — MUST NOT resolve the approval without the
  operator subsequently completing the existing fresh biometric/passcode confirmation there.
- **FR-002**: On iOS below 17, the pending-approval Live Activity MUST render exactly as it does today
  (informational only, tap-to-open) — no crash, no missing activity, no partial button support.
- **FR-003**: The Dart-side `LiveActivity` bridge MUST gain an `update()` method so the pending-approval
  activity can be told an approval was resolved (from any surface) and reflect that state, dismissing
  rather than continuing to show "pending."
- **FR-004**: A new Live Activity MUST start for each submitted question independently, at the moment
  `EdgeAskClient.ask()` returns a task ID — keyed by that task ID, so multiple concurrently in-flight
  questions each get their own activity.
- **FR-005**: The in-flight query activity MUST show the question text and an elapsed-time counter that
  ticks continuously from the moment the activity starts, independent of whether any progress update has
  arrived.
- **FR-006**: The in-flight query activity MUST update its shown status text whenever a `task_progress`
  notification arrives for its specific task ID, using the Border's own free-text detail verbatim — this
  spec MUST NOT compute, estimate, or display any member count (`respondedMembers`/`expectedMembers` or
  equivalent), since no such structured data exists in this system (Context).
- **FR-007**: The in-flight query activity MUST end when its task reaches any terminal state (completed,
  failed, or cancelled) — reflecting that outcome before ending, not disappearing silently.
- **FR-008**: Tapping the in-flight query activity MUST open the app to Chat, showing that specific turn —
  matching the existing chat-answer-notification deep-link behavior (spec 073).
- **FR-009**: Neither Live Activity's absence, failure to start, or failure to update (e.g. Live Activities
  disabled, an unsupported OS version, an iOS-imposed concurrent-activity limit) MUST ever block, delay, or
  otherwise degrade the underlying approval-resolution or ask/answer flow — matching the existing
  best-effort try/catch pattern `live_activity.dart` already uses.
- **FR-010**: This spec MUST NOT change `IPHONEOS_DEPLOYMENT_TARGET` — the iOS 17+ interactive-button
  capability MUST be gated by a runtime availability check, not a deployment-target floor change, so
  devices on iOS 16.2 (the current floor) continue to receive the existing, unmodified informational Live
  Activity.
- **FR-011**: Both Live Activity types MUST set a `staleDate` appropriate to their own expected lifetime,
  per Apple's own Live Activity lifetime guidance — an in-flight query activity in particular MUST NOT be
  left implying it is live and counting up indefinitely well past any realistic answer time.

### Key Entities

- **`PendingApprovalActivityAttributes` / `PendingApprovalLiveActivityView` (existing, modified)**: gains
  Approve/Deny `Button(intent:)` controls (iOS 17+ only) and reacts to a new `update()` call from Dart; no
  new field on `ContentState` beyond what already exists (`targetName`, `status`).
- **`AskActivityAttributes` (new)**: a new `ActivityAttributes` type carrying the question preview and task
  ID; its `ContentState` carries the elapsed-time start reference, the latest free-text progress detail (if
  any), and terminal state — deliberately no member-count fields (FR-006).
- **`ApprovalActionIntent` (new)**: a `LiveActivityIntent` (iOS 17+) that sets `openAppWhenRun = true` and
  triggers the existing Approvals-tab navigation — carries no approval-resolution logic of its own.
- **`LiveActivity` (existing Dart class, extended)**: gains `update()` alongside its existing `start()`/
  `end()`, and gains a second start/end pair (or equivalent per-task addressing) for the new in-flight query
  activity type, keyed by task ID.
- **`ConversationStore` (existing, extended)**: gains an `onAdded` callback (fires wherever `addPending` is
  called, mirroring `onCompleted`'s existing single-hook pattern) and an `onTerminal` callback (fires for
  any of completed/failed/cancelled, distinct from `onCompleted`'s completed-only trigger) — no new
  persisted field.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator on iOS 17+ can go from a pending approval showing on the Lock Screen to a
  biometric confirmation prompt for that specific approval without unlocking the phone first or navigating
  through the app manually.
- **SC-002**: No approval is ever resolved from a Live Activity tap without the operator completing the
  existing fresh biometric/passcode confirmation — verified across every path (Lock Screen button, in-app,
  notification, watch).
- **SC-003**: A Live Activity resolved through any surface other than itself updates and dismisses within
  the same timeframe the existing notification-badge/list updates already do, without operator action on
  the activity itself.
- **SC-004**: An operator submitting a question that takes over a minute to answer can see, on the Lock
  Screen alone, that it is still in progress (via a ticking timer and/or a real status update) without
  opening the app, and sees the moment it finishes.
- **SC-005**: Nothing shown by the in-flight query activity is ever fabricated — every value displayed
  traces to a real, existing data source (the submitted question text, a client-computed elapsed duration,
  or the Border's own verbatim progress detail string).
- **SC-006**: `flutter analyze` reports zero issues and the full `flutter test` suite passes with zero
  regressions once this spec's Dart-side code (the `LiveActivity` bridge extension, `ConversationStore`'s
  new hooks) is implemented; the native Swift/ActivityKit portion is verified via `xcodebuild` compiling
  the `Runner`/`LiveActivityWidget` targets successfully and, separately and explicitly, via real on-device
  Live Activity rendering and interaction (🔌 DEVICE) — not claimed done from either alone.

## Assumptions

- Scope is exactly B3 of `NETCLAW-MOBILE-1.0.1-BRIEF.md`'s Phase B, narrowed per Context's research finding:
  the in-flight query activity shows an elapsed timer and the Border's existing free-text progress detail,
  never a member count, since that concept does not exist in this system today and building it would
  require substantial new Border-side instrumentation out of proportion to this spec.
- The security invariant established in spec 073 (every approval resolution preceded by a fresh,
  never-cached biometric/passcode confirmation) is treated as non-negotiable — this spec's interactive
  button explicitly routes around, not through, any temptation to resolve directly from a
  `LiveActivityIntent`'s background context, per the brief's own explicit instruction.
- No deployment-target change is made — the iOS 17+ interactive button is gated by a runtime availability
  check (FR-010), consistent with the same "no regression on an older OS" approach spec 112 already used
  for watchOS.
- The in-flight query activity is per-question (keyed by task ID), not an aggregate — a deliberate
  departure from the existing approval activity's "show the first pending one" aggregation, justified by
  Chat's existing support for multiple genuinely concurrent in-progress asks.
- "Verified" for the native Swift/ActivityKit portion of this spec means compiling successfully via
  `xcodebuild` for the `Runner` and `LiveActivityWidget` targets; actual Live Activity rendering,
  interactive button behavior, and a real ticking timer are 🔌 **DEVICE**-only and will be exercised
  directly with the operator, not simulated.
