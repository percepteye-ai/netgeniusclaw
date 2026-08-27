# NetGeniusClaw Mobile 1.0.1 — Implementation Brief

**Target**: `mobile/netclaw-mobile/` (Flutter 3.44.8, iOS + Android, watchOS companion)
**Version bump**: `pubspec.yaml` `1.0.0+1` → `1.0.1+2`
**Written**: 2026-08-14, against `main` as of the commit containing spec `108-cloudflare-tunnel-transport`

This is a handoff brief, not a spec-kit spec. If the repo workflow requires one,
split it: items A1–A5 and C1 are small enough for a single spec (suggest
`109-mobile-polish-pass`); items B1–B5 each warrant their own numbered spec.

---

## How to use this document

Every item below carries five things:

- **Evidence** — what is actually in the tree today, with file and line. This was
  verified by reading the repo, not inferred. If an Evidence line turns out to be
  wrong, stop and re-check the surrounding assumptions before proceeding.
- **Change** — what to build.
- **Files** — what to touch or create.
- **Acceptance** — the observable outcome. Write these as test names.
- **Gotchas** — the thing that will waste an afternoon if missed.

### Verification standard

This repo distinguishes "passes the Dart suite" from "verified on real hardware,"
and specs 072/073 are explicit that a clean compile is *not* evidence of on-device
behavior. Keep that discipline. Tag every task 🔌 **DEVICE** if it cannot be proven
by `flutter test` + `flutter analyze` + `xcodebuild build`, and do not mark such a
task done from a green build alone.

Nothing in this document should regress the existing suite. `flutter analyze`
clean and full `flutter test` passing is the floor, not the goal.

---

## Pre-flight: two stale facts in the tree

Resolve both before starting Phase B. Neither is caused by this work, but both
will produce confusing failures inside it.

**P1 — `Runner.entitlements` is live, despite its own comment saying it isn't.**
The file's header block states `CODE_SIGN_ENTITLEMENTS` is "deliberately not set
in project.pbxproj." It *is* set — `project.pbxproj` lines 772, 1054, and 1081 all
carry `CODE_SIGN_ENTITLEMENTS = Runner/Runner.entitlements;`. That means the
`aps-environment` key is being signed today. Either the paid-account migration
happened and the comment was never updated, or free-Personal-Team signing is
already broken. Determine which, then fix the comment or the build setting. Item
B2 adds an App Group to this same file, so its true status must be known first.

**P2 — the App Group is watchOS-only.** `group.ca.automateyournetwork.netclaw.mobile`
appears only in `WatchApp.entitlements` and `WatchComplication.entitlements`.
`HeartbeatStatusStore.swift` and `PendingApprovalCountStore.swift` compile into
the watch targets and are written from `WatchDataStore.swift` (watch side) — see
`WatchDataStore.swift:99` and `:191`. The phone writes nothing to any App Group.
B2 therefore includes new plumbing, not just a new target.

---

## Phase A — cheap, high-visibility

No new Xcode targets, no new capabilities, no Apple Developer portal work. All
five are shippable independently and in parallel.

### A1. Dark mode

**Evidence**: `lib/main.dart:64` — a single `ThemeData(colorScheme:
ColorScheme.fromSeed(seedColor: const Color(0xFFE65733)))`, no `darkTheme`, no
`themeMode`.

**Change**: Add a dark scheme from the same brand seed and follow the system
setting. Extract both schemes into `lib/theme.dart` so screens stop hardcoding
colors.

```dart
theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: brandOrange)),
darkTheme: ThemeData(
  colorScheme: ColorScheme.fromSeed(
    seedColor: brandOrange,
    brightness: Brightness.dark,
  ),
),
themeMode: ThemeMode.system,
```

**Files**: `lib/main.dart`, new `lib/theme.dart`.

**Sweep required.** Grep for hardcoded colors and replace each with a scheme role.
Known offenders: `chat_screen.dart:512` (`TextStyle(color: Colors.grey)` on the
photo-unavailable placeholder), `:529` (`Colors.grey` on the Cancelled label),
`:538` (the failure text color). Each becomes `Theme.of(context).colorScheme
.onSurfaceVariant` / `.error` as appropriate. Also check `empty_state.dart` — the
illustrations in `assets/illustrations/` may be light-background PNGs that
disappear on dark; if so, either tint them or supply dark variants.

**Acceptance**: With iOS set to Dark Appearance, every screen renders with a dark
surface, and no text falls below WCAG AA contrast. No `Colors.grey`,
`Colors.black`, or `Colors.white` literal remains in `lib/screens/`.

**Tests**: Widget tests pumping each screen inside a dark `MaterialApp` and
asserting the resolved surface brightness. Cheap, and it locks the sweep in.

**Gotcha**: `flutter_native_splash` in `pubspec.yaml` is configured with
`color: "#FFFFFF"` and no `color_dark`. The splash will flash white before a dark
app. Add `color_dark`/`image_dark` and re-run `dart run flutter_native_splash:create`.

---

### A2. Haptics

**Evidence**: no `HapticFeedback` anywhere under `lib/`. No `WKInterfaceDevice.play()`
anywhere under `ios/WatchApp Watch App/`.

**Change**: Add a thin `lib/ncfed/haptics.dart` wrapper (injectable, so tests
don't hit the platform channel — follow the existing pattern in
`voice_transcription.dart` and `reconnect_supervisor.dart` of an injectable
function with a production default). Fire on:

| Event | Phone | Watch |
|---|---|---|
| Approval arrives | `HapticFeedback.heavyImpact()` | `WKInterfaceDevice.current().play(.notification)` |
| Approval resolved successfully | `HapticFeedback.mediumImpact()` | `.success` |
| Approval resolve failed | `HapticFeedback.vibrate()` | `.failure` |
| Chat answer completes | `HapticFeedback.lightImpact()` | `.click` |
| Enrollment succeeds | `HapticFeedback.mediumImpact()` | — |
| Border connection lost (first transition only) | `HapticFeedback.vibrate()` | `.retry` |

**Files**: new `lib/ncfed/haptics.dart`; call sites in `approval_client.dart`,
`chat_screen.dart` (the `askClient.updates` listener at `:67`),
`enrollment_flow.dart`, `reconnect_supervisor.dart`; watch side in
`ApprovalsView.swift` and `WatchDataStore.swift`.

**Acceptance**: Each event above produces exactly one haptic. Connection-loss
haptic fires on the *transition* to disconnected, not on every retry tick —
`reconnect_supervisor.dart` runs a bounded retry loop and will otherwise buzz
repeatedly.

**Tests**: Inject a recording fake and assert the call sequence per event. The
retry-loop debounce is the one that actually needs a test.

**Gotcha**: Android's `HapticFeedback.vibrate()` needs no permission but is a
no-op when the user has haptics off system-wide — never gate UI state on it.

---

### A3. Copy / share / select / markdown on answers

**Evidence**: `chat_screen.dart:549` renders the answer as a bare
`Text(turn.answerText ?? '')`. No `SelectableText`, no `Clipboard`, no share.
`ConversationTurn.answerText` is a plain `String?` (`conversation_store.dart:6-22`).
The README documents a real 1583-byte answer, so these are long technical
payloads — CLI output, route tables, config fragments.

**Change**: Four parts, in this order.

1. **Selectable**: `Text` → `SelectableText` for answer bodies.
2. **Copy**: long-press or an overflow menu on `_TurnTile` (`chat_screen.dart:391`)
   → `Clipboard.setData` → confirmation `SnackBar`. Add a matching action for
   "copy question + answer" as one block.
3. **Share**: add `share_plus`, wired to `SharePlus.instance.share()`. If the
   turn has a `photoPath` (`conversation_store.dart:15`), share text and image
   together.
4. **Markdown + monospace**: add `flutter_markdown` (or `gpt_markdown` if the
   former's maintenance status is a concern at implementation time — check
   before choosing). Render answers as markdown so tables and fenced code blocks
   display properly. Style `code` and `pre` with a monospace family. Give every
   fenced block its own copy button — the single highest-value micro-feature in
   this entire document for a network engineer.

**Files**: `lib/screens/chat_screen.dart`, `lib/screens/feed_screen.dart` (same
treatment for pushed message bodies), `pubspec.yaml`.

**Acceptance**: A user can select arbitrary text, copy a whole answer in one tap,
copy an individual code block in one tap, and share an answer to Messages/Mail.
A markdown table in an answer renders as a table. A fenced block renders
monospaced and does not wrap mid-token.

**Tests**: Widget tests asserting `SelectableText` presence, that the copy action
puts expected content on a mocked clipboard, and that a fenced block produces a
code widget. Golden tests for markdown rendering are optional but cheap here.

**Gotchas**:

- Border answers are not guaranteed to be valid markdown. Raw CLI output
  containing `*`, `_`, `#`, or a bare `|` will be mangled by a markdown renderer.
  **Decide a policy and encode it as a test.** Safest default: render as markdown
  only when the text contains a fenced block or a pipe-table row; otherwise
  render as monospace preformatted text. Do not silently corrupt `show run` output.
- Long answers inside `ListView.builder` (`chat_screen.dart:326`) with
  `SelectableText` can hurt scroll performance. Profile with a 5000-character
  answer before calling it done.
- `share_plus` on iPad requires `sharePositionOrigin` or it throws. Set it even
  though iPad is not a target yet.

---

### A4. Time Sensitive notifications

**Evidence**: `local_notifications.dart:178-186` — `DarwinNotificationDetails`
sets `categoryIdentifier: approvalCategoryId` and `presentBadge: false`, but no
`interruptionLevel`. Approvals therefore arrive at default priority and are
suppressed by Focus.

**Change**: Set `interruptionLevel: InterruptionLevel.timeSensitive` on approval
notifications only. Leave feed and chat-answer notifications
(`local_notifications.dart:150-161`) at default — passive is correct there.
Android equivalent: the `'approvals'` channel needs `importance: Importance.high`
and `priority: Priority.high` to produce a heads-up notification; the existing
`AndroidNotificationDetails` at `:187` sets neither.

**Files**: `lib/ncfed/local_notifications.dart` only.

**Acceptance**: With a Focus mode active that permits Time Sensitive
notifications, an approval banner appears; a feed message does not. On Android,
an approval produces a heads-up banner.

**Tests**: Assert the constructed `NotificationDetails` carries
`timeSensitive` for approvals and does not for feed/chat. Pure unit test.

**Gotchas**:

- Time Sensitive requires the `com.apple.developer.usernotifications.time-sensitive`
  entitlement. It is *not* in `Runner.entitlements` today — add it. See P1 first,
  since that file's real status is currently ambiguous.
- The user can disable Time Sensitive per-app in Settings. Never assume delivery.
- Do not reach for Critical Alerts here. That is a separate entitlement requiring
  written Apple approval and is out of scope for 1.0.1.

---

### A5. Face ID app lock

**Evidence**: `local_auth: ^3.0.2` is a dependency and is used for approval
confirmation (`lib/ncfed/approval_confirmation.dart`, the shared entry point
introduced by spec 073), but nothing gates app launch.
`NSFaceIDUsageDescription` already exists in `Info.plist`.

**Change**: A Settings toggle, "Require Face ID to open NetGeniusClaw," persisted in
`flutter_secure_storage` (already a dependency). When enabled, `EnrollmentGate`
(`lib/main.dart:75`) presents a lock screen before the `HomeShell` on cold start
and on resume after a configurable grace period (default 60s — immediate re-auth
on every app switch is genuinely hostile).

**Files**: `lib/screens/settings_screen.dart`, `lib/main.dart`, new
`lib/ncfed/app_lock.dart`.

**Acceptance**: With the toggle on, a cold start shows the lock screen and no
app content. Backgrounding for less than the grace period and returning does not
re-prompt; longer does. A failed or cancelled auth leaves the lock in place and
never exposes content behind it. With the toggle off, behavior is unchanged.

**Tests**: `app_lock.dart` grace-period logic is pure and fully unit-testable.
Widget test that the locked state renders no `HomeShell` descendant.

**Gotchas**:

- Use `AppLifecycleState.paused` to start the grace timer, and blur or cover the
  content *before* backgrounding, or the iOS app-switcher snapshot leaks the
  screen behind the lock.
- Biometrics can fail permanently (no enrolled face, hardware lockout). Always
  offer device-passcode fallback via `authenticate(options: AuthenticationOptions(
  biometricOnly: false))`, or a user can be locked out of their own enrolled Border.
- This must not interfere with A4's notification actions — the inline
  Approve/Deny path already does its own fresh biometric check via
  `approval_confirmation.dart` and must not end up double-prompting.

---

## Phase B — headline features

Each of these adds an Xcode target, a capability, or both. B1 is the highest
value and should go first; B2 and B3 are cheaper once B1's App Intents scaffolding
exists.

### B1. App Intents (Siri, Action Button, Control Center, Shortcuts)

**Evidence**: no `AppIntent`, `INIntent`, `NSUserActivity`, or `ControlWidget`
anywhere in the tree.

**Change**: A new Swift `AppIntents` implementation in the `Runner` target
exposing at minimum:

- `AskBorderIntent` — parameter: question string. Submits via the existing
  `n2n/edge/ask` path and returns the answer as a spoken/dialog result.
- `PendingApprovalsIntent` — returns the current pending count.
- `BorderHealthIntent` — returns the heartbeat summary.

Add `AppShortcutsProvider` with natural-language phrases so they work from Siri
with zero user setup. This one implementation lights up Siri, the iPhone 15 Pro+
Action Button, the Apple Watch Ultra Action Button, and Shortcuts automations.

Then add a `ControlWidget` (iOS 18+) exposing pending-approval count and a
one-tap "Ask NetGeniusClaw" control in Control Center.

**Files**: new `ios/Runner/AppIntents/` (`AskBorderIntent.swift`,
`PendingApprovalsIntent.swift`, `BorderHealthIntent.swift`,
`NetClawShortcuts.swift`); new `ios/ControlWidget/` target;
`ios/Runner/AppDelegate.swift` for the channel; new `lib/ncfed/app_intent_bridge.dart`.

**The architectural decision that matters.** An App Intent can be invoked when
the Flutter engine is not running. Two options:

1. **`openAppWhenRun = true`** — the intent launches the app, which handles it
   normally. Trivial to build, but Siri becomes "launch the app and type it for
   me," which loses most of the appeal.
2. **Headless `FlutterEngineGroup`** — spin up a background engine, run the ask,
   return a result without foregrounding. This is what makes the feature feel
   magical, and it is substantially more work: engine lifecycle, timeout
   handling, and the fact that `edge_client.dart`'s WebSocket needs to connect
   from cold.

**Recommendation**: ship `AskBorderIntent` with option 2 and the two read-only
intents with option 2 as well (they can read cached state from the App Group in
B2 without any network at all, making them nearly instant). Fall back to option 1
only if the engine lifecycle proves unstable. Decide this explicitly and record
the decision — do not let it be decided implicitly by whatever compiled first.

**Acceptance**: "Hey Siri, ask NetGeniusClaw if BGP is up on the core switch" returns a
spoken answer. The Action Button, configured to NetGeniusClaw, submits a dictated
question. A Shortcuts automation can call all three intents. The Control Center
control shows a live pending count.

**Tests**: The Dart side of the bridge is unit-testable. The intents themselves
are 🔌 **DEVICE** — Siri invocation cannot be simulated meaningfully.

**Gotchas**:

- A long-running ask (the README documents 2m13s) will blow past the Siri
  response window. `AskBorderIntent` must return promptly with an acknowledgement
  and hand off to the B3 Live Activity for the actual result, not block.
- App Intents require iOS 16; `ControlWidget` requires iOS 18. Check the
  deployment target in `project.pbxproj` before assuming either is available.
- Parameter values that reference a device name should use `EntityQuery` so Siri
  can disambiguate. Consider whether device identity is safe to expose to
  system-wide Siri indexing before doing this.

---

### B2. iOS home screen and Lock Screen widgets

**Evidence**: See pre-flight P2. The existing App Group and its two stores are
watchOS-only; the phone writes nothing to any group.

**Change**: Three pieces, in order.

1. **Phone-side App Group.** Add
   `group.ca.automateyournetwork.netclaw.mobile.ios` (a distinct iOS group — do
   not reuse the watch one, whose lifecycle belongs to the watch targets) to
   `Runner.entitlements` and register it in the Apple Developer portal.
2. **A writer.** A Swift shim plus Dart channel that mirrors border health,
   pending approval count, and unread feed count into the group's
   `UserDefaults` on every meaningful state change, then calls
   `WidgetCenter.shared.reloadAllTimelines()`. Model it on
   `HeartbeatStatusStore.swift` — same shape, phone side.
3. **The widget target.** Small and medium home-screen widgets (border health +
   pending count + last heartbeat time), plus `.accessoryCircular`,
   `.accessoryRectangular`, and `.accessoryInline` Lock Screen widgets. Support
   StandBy by ensuring the medium widget reads well at a distance.

**Files**: `ios/Runner/Runner.entitlements`; new
`ios/Runner/WidgetDataStore.swift` + `ios/Runner/WidgetBridgePlugin.swift`; new
`lib/ncfed/widget_data.dart`; new `ios/NetClawWidget/` target.

**Acceptance**: A home-screen widget shows current border health and pending
count and refreshes within a minute of a state change. Lock Screen accessory
widgets render in all three families. Tapping any widget deep-links to the right
tab via the existing `netgeniusclaw://` scheme (`Info.plist` `CFBundleURLTypes`).

**Tests**: `widget_data.dart` serialization is unit-testable. Rendering is
🔌 **DEVICE**.

**Gotchas**:

- Widget timeline refreshes are budgeted by iOS and cannot be forced on demand.
  A widget will sometimes show stale data — display the timestamp of the reading,
  never imply it is live.
- Do not put approval detail on a Lock Screen widget. The existing Live Activity
  deliberately shows only `targetName` and a coarse status per 099/FR-017; hold
  the widget to the same line.
- Adding an App Group to `Runner.entitlements` changes the provisioning profile.
  Resolve P1 first or this will fail to sign in a confusing way.

---

### B3. Interactive Live Activity + in-flight query Live Activity

**Evidence**: `PendingApprovalLiveActivityView.swift` renders `Text` only — no
`Button`, no intent. `PendingApprovalActivityAttributes` carries `approvalId`,
`targetName`, `status`. `lib/ncfed/live_activity.dart` exposes only `start()` and
`end()` — no update path.

**Change**: Two related pieces.

**B3a — Interactive approval activity.** Add Approve/Deny buttons via
`Button(intent:)` and a `LiveActivityIntent`, iOS 17+.

> **Security constraint, and the design follows from it.** The repo's invariant
> (073, FR-003) is that every resolve is preceded by a *fresh, never-cached*
> biometric confirmation, shared through `approval_confirmation.dart`. A
> `LiveActivityIntent` runs in the app's process but cannot reliably present
> `LAContext` UI from the background. **Do not weaken the invariant to make the
> button work.** Set `openAppWhenRun = true` so the button foregrounds the app
> directly into the approval sheet with the target pre-selected, and the existing
> biometric gate runs untouched. That is still a large improvement — one tap from
> the Lock Screen to a Face ID prompt — and it keeps the security model intact.

Also add an `update()` method to `live_activity.dart` so the activity reflects
`status: "resolved"` and dismisses, rather than lingering after the approval is
handled elsewhere.

**B3b — In-flight query activity.** New `AskActivityAttributes` with
`questionPreview`, `elapsed`, `respondedMembers`, `expectedMembers`, `state`.
Start it when `edge_ask_client.ask()` returns a task ID; update it as delegation
progress arrives; end it when the turn reaches a terminal state. Dynamic Island
compact shows a spinner and member count; expanded shows the question and elapsed
timer; tap deep-links to the turn in Chat.

Given a documented 2m13s fan-out across risk members, this is the better demo of
the two.

**Files**: `ios/LiveActivityWidget/` (new `AskActivityAttributes.swift`,
`AskLiveActivityView.swift`, `ApprovalActionIntent.swift`; edits to
`PendingApprovalLiveActivityView.swift` and the `WidgetBundle`);
`ios/Runner/LiveActivityBridge.swift`; `lib/ncfed/live_activity.dart`;
`lib/ncfed/edge_ask_client.dart`; `lib/screens/chat_screen.dart`.

**Acceptance**: Submitting a question starts a Live Activity within ~1s showing
the question and a running timer; it updates as members respond; it ends on
completion, failure, or cancel. Tapping it opens that turn. The approval activity
shows Approve/Deny, and tapping either foregrounds to a biometric prompt — never
resolving without one.

**Tests**: The Dart-side start/update/end call sequencing against a fake
`MethodChannel` is fully unit-testable and is where the real regression risk
lives (a stuck activity that never ends is the likely bug). Rendering is
🔌 **DEVICE**.

**Gotchas**:

- Live Activities have a hard system lifetime and a `staleDate`. Set one, and
  design what a stale in-flight query looks like — do not leave a timer counting
  up forever after the app is killed.
- ActivityKit requires the identical `ActivityAttributes` type compiled into both
  the app and the extension target. `PendingApprovalActivityAttributes.swift`
  already documents this dual membership; the new `AskActivityAttributes.swift`
  needs the same treatment in `project.pbxproj`, and forgetting it produces a
  runtime failure with no compile error.
- Update frequency is throttled. Do not push an update per elapsed second — drive
  the timer with SwiftUI's `Text(timerInterval:)` and only push updates on real
  state changes.
- Android has no equivalent. Keep everything behind the existing best-effort
  try/catch in `live_activity.dart`.

---

### B4. Apple Watch Double Tap

**Evidence**: `ApprovalsView.swift` renders an `ApprovalRow` with approve/deny
actions gated by a fresh `.deviceOwnerAuthentication` check. No
`handGestureShortcut` anywhere.

**Change**: Mark the primary action with
`.handGestureShortcut(.primaryAction)` so Double Tap on Series 9 / Ultra 2 and
later triggers it.

**The question to answer first**: should Double Tap trigger *approve*, or should
it trigger *"show me the confirmation prompt"*? Approving a network change with
an accidental finger pinch is a bad outcome. Recommendation: Double Tap surfaces
the passcode confirmation for the top approval; the confirmation itself remains a
deliberate act. Also apply `.primaryAction` to the "Read aloud" button in
`AskView.swift`, where the stakes are zero and the gesture is pure delight.

**Files**: `ios/WatchApp Watch App/ApprovalsView.swift`, `AskView.swift`.

**Acceptance**: On a supporting watch, Double Tap on the Approvals view raises the
confirmation for the top pending approval. Double Tap never resolves an approval
by itself. On older watches, nothing changes and nothing breaks.

**Tests**: 🔌 **DEVICE** entirely. Requires Series 9 / Ultra 2 or later.

**Gotchas**: `handGestureShortcut` is watchOS 11+. Check the watch target's
deployment target. Exactly one view in a hierarchy may claim `.primaryAction` —
two silently disables both.

---

### B5. `.accessoryCorner` complication

**Evidence**: `HeartbeatComplication.swift:66` and
`PendingApprovalComplication.swift:56` both declare
`.supportedFamilies([.accessoryCircular, .accessoryRectangular, .accessoryInline])`.
`.accessoryCorner` — prime real estate on Infograph faces — is absent.

**Change**: Add `.accessoryCorner` to both, with a corner-appropriate layout
(gauge or text + curved label).

**Files**: the two complication files.

**Acceptance**: Both complications are selectable in the corner slots of a
Infograph watch face and render legibly.

**Tests**: 🔌 **DEVICE**.

**Gotcha**: `.accessoryCorner` is watchOS-only; guard it so shared code still
builds for iOS Lock Screen accessory families.

---

## Phase C — quality

### C1. Search across Feed and History

**Evidence**: `grep -rl TextField lib/screens` returns only
`manual_enrollment_screen.dart` and `chat_screen.dart` (the compose field at
`:354`). There is no search anywhere. `ConversationStore` holds all turns in a
`List<ConversationTurn>` in memory (`conversation_store.dart:73`), and
`MessageFeedStore` is the same shape, so search is a filter, not a query engine.

**Change**: A search field on both Chat and Feed. Case-insensitive substring
match across `requestText` and `answerText` for turns, and message body for feed
items. Highlight matches. Add filter chips for state (`pending`/`working`/
`completed`/`failed`/`cancelled`) and origin (`phone`/`watch` — `origin` already
exists at `conversation_store.dart:22` and is currently surfaced nowhere).

Scope note: full-text indexing is not warranted. If in-memory filtering becomes
slow, that is a signal the stores need pagination, which is a separate piece of
work — do not preempt it here.

**Files**: `lib/screens/chat_screen.dart`, `lib/screens/feed_screen.dart`, new
`lib/ncfed/conversation_search.dart`.

**Acceptance**: Typing filters the list live. Clearing restores it. Filter chips
compose with the text query. Search state does not persist across app launches.

**Tests**: `conversation_search.dart` is a pure function over a list — test it
directly, including the empty query, no-match, and combined-filter cases.

**Gotcha**: Do not filter the underlying store. Filter the view. Spec 073 added
`acknowledged` state and `acknowledge()`/`delete()`; a filtered view must still
apply those to the correct underlying item, not to a filtered index.

---

## Suggested ordering

```
Week 1   A1 A2 A4 A5        — no new targets, no portal work, ships alone
Week 1   A3                 — largest Phase A item; the markdown policy is the risk
Week 2   P1 P2              — resolve before any target/entitlement work
Week 2   B5 B4              — smallest headline items, watch-side only
Week 2-3 B3b                — in-flight Live Activity; best demo per unit of work
Week 3   B2                 — widgets; depends on the P2 App Group plumbing
Week 3-4 B1                 — App Intents; largest, and the engine decision gates it
Week 4   B3a C1             — interactive approval activity, search
```

If only three ship: **A1**, **A3**, **B3b**. The first two fix things users will
complain about within a day of installing; the third is the screenshot.

## Definition of done for the release

- [ ] `flutter analyze` clean
- [ ] `flutter test` fully passing, no skipped tests, no regressions
- [ ] `xcodebuild` clean for `Runner`, `WatchApp`, `WatchComplication`,
      `LiveActivityWidget`, and any new targets
- [ ] Every 🔌 **DEVICE** item exercised on real hardware, or explicitly listed as
      unverified in the README's platform-notes section — matching the honesty
      standard specs 072/073 already set there
- [ ] `pubspec.yaml` at `1.0.1+2`
- [ ] README platform-notes section updated with what was and was not verified
- [ ] `APP-STORE-ROADMAP.md` updated if any new capability requires a portal or
      App Store Connect change (B1, B2, and A4 all do)
