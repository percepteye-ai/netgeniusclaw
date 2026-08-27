# Feature Specification: NetGeniusClaw Mobile Home Screen, Lock Screen, and Control Center Widgets (B1b+B2)

**Feature Branch**: `114-widgets-controlwidget`
**Created**: 2026-08-15
**Status**: Draft
**Input**: User description: "NetGeniusClaw Mobile App Intents integration follow-on — Phase B1b+B2 of mobile/netclaw-mobile/NETCLAW-MOBILE-1.0.1-BRIEF.md, bundled since Xcode already scaffolded both into the same new NetClawWidgetExtension target the operator created (File > New > Target > Widget Extension), which ships a home-screen/Lock-Screen Widget and a Control Center ControlWidget in the same template. B2: a phone-side writer mirrors Border health, pending approval count, and unread feed count into a new App Group's UserDefaults on every meaningful state change and calls WidgetCenter.reloadAllTimelines(), modeled on the existing watch-side HeartbeatStatusStore/PendingApprovalCountStore pattern. Small/medium home-screen widgets plus accessoryCircular/accessoryRectangular/accessoryInline Lock Screen widgets show Border health, pending count, and last heartbeat time — always with the reading's timestamp, never implying it's live. No approval detail on the Lock Screen widget, matching the existing Live Activity's target-name-and-coarse-status-only restriction. Tapping any widget deep-links via the existing netgeniusclaw:// scheme. B1b: the already-scaffolded ControlWidget is built out to show a live pending-approval count and a one-tap 'Ask NetGeniusClaw' control, completing the App Intents item spec 111 split off as B1a."

## Context

This spec implements items B1b and B2 of `mobile/netclaw-mobile/NETCLAW-MOBILE-1.0.1-BRIEF.md`'s Phase B,
bundled because Xcode's own current Widget Extension template ships a home-screen/Lock-Screen `Widget` and
a Control Center `ControlWidget` in the same target by default — the operator created that target once,
and it already contains scaffolding for both.

Before writing this spec, the new target and the existing phone/watch code it needs to mirror were
verified directly:

- **The new `NetClawWidgetExtension` target needed real fixes before it would even build**, caught by a
  full `xcodebuild` run rather than assumed correct: it was embedded under `WatchApp` instead of `Runner`
  (wrong bundle identifier, wrong — old, watch-only — App Group in its own entitlements), and its default
  `ControlWidget` template code required iOS 18 (`buildExpression`) while inheriting the project's 16.2
  floor. All three are already fixed in this branch's setup commit: the target now depends on and embeds
  into `Runner`, carries the correct `ca.automateyournetwork.netclaw.mobile.netclawwidget` bundle
  identifier, references the new `group.ca.automateyournetwork.netclaw.mobile.ios` App Group, and has its
  own deployment target set to iOS 18 — authorized directly by the operator ("drop old version support,
  this is for modern device OSs").
- **Xcode's default template content is 100% placeholder** (`NetClawWidget.swift`'s "favorite emoji"
  example, `NetClawWidgetControl.swift`'s "start a timer" example, `AppIntent.swift`'s
  `ConfigurationAppIntent`) — every file in the new target needs its real content written from scratch;
  none of the scaffolded business logic is reused.
- **The watch side already solved the exact "cross-process data" problem B2 needs solved on the phone.**
  `HeartbeatStatusStore.swift`/`PendingApprovalCountStore.swift` (`ios/WatchComplication/`) already bridge
  `WatchDataStore`'s in-memory state to the `WatchComplication` extension via a shared App Group's
  `UserDefaults` — a `write()`/`read()` pair per value, called from `WatchDataStore.swift` immediately
  followed by `WidgetCenter.shared.reloadAllTimelines()`. B2's phone-side writer is the same pattern, one
  level up, using the *new* phone-only App Group (not the existing watch-only one, which stays exactly as
  it is — no cross-wiring between the two).
- **All three values B2 needs already exist on the phone, just not mirrored anywhere a widget can read
  them.** `DeviceHeartbeatStore` (`lib/ncfed/device_heartbeat.dart`) already tracks the same
  summary/pushedAt/isAlarm shape `HeartbeatStatusStore` mirrors on the watch side (and is the same store
  spec 111's `BorderHealthIntent` already reads). `ApprovalClient`'s `pending` stream already tracks the
  live pending-approval count. `MessageFeedStore.unreadCount` already tracks the unread feed count. None of
  the three needs a new source of truth — only a new mirror.
- **The existing Live Activity already established the "no sensitive detail on an unlockable-screen
  surface" restriction B2 must match.** `PendingApprovalActivityAttributes`/`PendingApprovalLiveActivityView`
  (spec 099/113) deliberately show only `targetName` and a coarse status, never the full approval payload
  or requesting-agent detail — the Lock Screen widget's pending-count display follows the identical
  restriction (a bare count, never per-approval detail).
- **The `netgeniusclaw://` deep-link mechanism already handles exactly this "tap opens the right tab" need.**
  Specs 111 and 113 both added shapes to the same `app_links`-based listener
  (`lib/ncfed/device_deep_link.dart`'s `DeviceDeepLinkListener`) — `netgeniusclaw://approvals` and
  `netgeniusclaw://chat/<taskId>` already exist; this spec adds `netgeniusclaw://health` (or reuses `netgeniusclaw://
  approvals` where a tap should land on Approvals) to the same listener rather than building a fourth,
  separate mechanism.

This repo's verification standard (specs 072/073/099/110/111/112/113) applies unchanged: real widget
placement, rendering, and refresh timing on an actual home screen/Lock Screen/Control Center are 🔌
**DEVICE**-only — not claimed done from a green `flutter test`/Xcode build alone.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Border status at a glance from the home screen (Priority: P1)

An operator adds a NetGeniusClaw widget to their home screen. Without opening the app, they can see the Border's
health, how many approvals are pending, and when the last heartbeat was received — with that last point
explicitly timestamped, not implied to be live.

**Why this priority**: The core value of B2 — the same information the Dashboard already shows, visible
without unlocking the phone or opening the app at all.

**Independent Test**: Add both the small and medium widget sizes to a real home screen and confirm both
render current Border health, pending count, and a timestamped last-heartbeat reading; trigger a real state
change (a new heartbeat, a new approval) and confirm the widget updates within iOS's own refresh budget.

**Acceptance Scenarios**:

1. **Given** a NetGeniusClaw widget is on the home screen, **When** the operator looks at it, **Then** it shows
   the current Border health summary, the current pending-approval count, and the last heartbeat's
   timestamp — explicitly labeled as a point-in-time reading, never phrased as "live."
2. **Given** the widget is showing, **When** a real state change occurs (new heartbeat arrives, an approval
   is created or resolved, a feed message arrives), **Then** the phone mirrors the new value into the
   shared App Group and requests a timeline reload — the widget reflects it the next time iOS actually
   grants that widget a refresh (never claimed to be instantaneous, since iOS budgets this).
3. **Given** no heartbeat has ever been received, **When** the widget renders, **Then** it shows a distinct
   "no data yet" state, matching the same distinction the watch complications and `BorderHealthIntent`
   already make — never a false "all clear."

---

### User Story 2 - Border status on the Lock Screen (Priority: P1)

An operator adds a NetGeniusClaw Lock Screen accessory widget (circular, rectangular, or inline). They can see
Border health/pending-count at a glance without unlocking the phone — with no approval detail exposed on
a screen anyone nearby could see.

**Why this priority**: Same value as User Story 1, on the surface visible even more often than the home
screen — paired with the tightest privacy bar, since a Lock Screen is visible to anyone glancing at the
phone.

**Independent Test**: Add all three accessory families to a real Lock Screen and confirm each renders
legibly and shows no target name, requesting-agent, or other approval-specific detail beyond a bare count.

**Acceptance Scenarios**:

1. **Given** a NetGeniusClaw Lock Screen widget is showing (any of the three accessory families), **When** the
   operator looks at it, **Then** it shows Border health and/or pending count — never the target name,
   requesting agent, or any other detail of a specific pending approval.
2. **Given** the same widget, **When** the operator taps it, **Then** the app opens to the relevant tab
   (Approvals for a pending-count tap, Dashboard/Feed for a health tap) via the existing `netgeniusclaw://`
   deep-link mechanism — matching how the existing Live Activity and notifications already deep-link.

---

### User Story 3 - Check pending approvals and jump straight to asking, from Control Center (Priority: P2)

An operator adds NetGeniusClaw's control to Control Center. They can see the current pending-approval count at a
glance, and tapping the control takes them straight into Chat, ready to type a question — one tap instead
of unlocking, finding the app, and opening the Chat tab.

**Why this priority**: Completes the App Intents story spec 111 (B1a) started — same underlying app, one
more surface, per the brief's own "one implementation, several surfaces" framing for B1's full scope.

**Independent Test**: Add the NetGeniusClaw control to Control Center on a real device, confirm it shows the
current pending-approval count, and confirm tapping it foregrounds the app directly to Chat with the
compose field ready.

**Acceptance Scenarios**:

1. **Given** the NetGeniusClaw control is added to Control Center, **When** the operator opens Control Center,
   **Then** it shows the current pending-approval count (read from the same mirrored value the home-screen
   widget reads — Context notes why this is not a live network call performed on every Control Center
   open).
2. **Given** the same control, **When** the operator taps it, **Then** the app foregrounds directly to
   Chat, ready for the operator to type and submit a question — reusing the exact same
   `openAppWhenRun`-plus-deep-link pattern spec 113's Approve/Deny buttons already established (research.md
   R2), not a headless, textless invocation of `AskBorderIntent` (Control Center provides no text-entry
   surface, so there is no question text to submit without first opening the app).

### Edge Cases

- What happens if the widget extension process runs before the App Group has ever been written to (a
  fresh install, widget added before the app has ever launched)? Each store's `read()` must return a
  distinct "no data yet" value rather than crashing or showing a misleading zero/empty state — matching
  the existing `HeartbeatStatusStore`/`PendingApprovalCountStore`'s own nil-safe `read()` pattern.
- What happens if iOS declines to grant a timeline refresh for an extended period? The widget continues
  showing its last-written value with its own timestamp still visible — never silently going stale without
  indicating how old the reading is, per FR-004.
- What happens if the operator has both the phone widget and the existing watch complication showing the
  same kind of data? Each reads from its own App Group (phone-only vs. watch-only) — this spec does not
  unify them or require them to refresh in lockstep, since they are already independent stores by design
  (Context).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A phone-side writer MUST mirror Border health (summary, timestamp, alarm flag), the current
  pending-approval count, and the current unread-feed count into the new `group.ca.automateyournetwork
  .netclaw.mobile.ios` App Group's `UserDefaults` on every meaningful state change, then call `WidgetCenter
  .shared.reloadAllTimelines()` — mirroring `HeartbeatStatusStore`/`PendingApprovalCountStore`'s existing
  watch-side pattern exactly, using the new phone-only App Group, never the existing watch-only one.
- **FR-002**: Small and medium home-screen widgets MUST show Border health, pending-approval count, and the
  last heartbeat's timestamp.
- **FR-003**: `.accessoryCircular`, `.accessoryRectangular`, and `.accessoryInline` Lock Screen widgets MUST
  show Border health and/or pending count, legible in each family's real size constraints.
- **FR-004**: Every widget showing a heartbeat-derived value MUST display that reading's timestamp
  explicitly (e.g. "as of 4 minutes ago") — MUST NOT imply the value is live, since widget timeline
  refreshes are budgeted by iOS and cannot be forced on demand.
- **FR-005**: No widget MUST show any per-approval detail (target name, requesting agent, or any other
  field beyond a bare count) — matching the existing Live Activity's identical restriction.
- **FR-006**: Tapping any widget MUST deep-link to the relevant tab via the existing `netgeniusclaw://` scheme —
  MUST NOT introduce a second, parallel foreground-navigation mechanism alongside the one specs 111/113
  already established.
- **FR-007**: A never-written store (fresh install, widget added before first app launch) MUST render a
  distinct "no data yet" state in every widget family that reads it — MUST NOT show a false "all clear" or
  an empty/zero value indistinguishable from a real reading.
- **FR-008**: The Control Center control MUST show the current pending-approval count (read from the same
  mirrored `WidgetDataStore` value the home-screen widget reads, not a fresh network call on every Control
  Center open) and, when tapped, MUST foreground the app directly to Chat, ready for the operator to type a
  question — reusing the existing `openAppWhenRun`-plus-`netgeniusclaw://` deep-link pattern (research.md R2)
  rather than a headless, textless invocation of `AskBorderIntent`, which requires a question string
  Control Center has no surface to collect.
- **FR-009**: This spec MUST NOT introduce a new Xcode target beyond the `NetClawWidgetExtension` target
  the operator already created — all widget/control work lives inside it.
- **FR-010**: This spec MUST NOT change `Runner`'s or `WatchApp`'s own deployment targets — only the
  already-bumped `NetClawWidgetExtension` target requires iOS 18 (Context), authorized directly by the
  operator for this specific target.

### Key Entities

- **`WidgetDataStore` (new, Swift, dual membership: `Runner` + `NetClawWidgetExtension`)**: the phone-side
  counterpart to `HeartbeatStatusStore`/`PendingApprovalCountStore` — `write()`/`read()` pairs for Border
  health, pending count, and unread feed count, backed by the new App Group's `UserDefaults`.
- **`WidgetBridgePlugin` (new, Swift, `Runner`-only)**: a `FlutterPlugin` exposing `WidgetDataStore.write(...)`
  + `WidgetCenter.shared.reloadAllTimelines()` to Dart, mirroring `LiveActivityBridge`'s existing shape.
- **`widget_data.dart` (new, Dart)**: the Dart-side bridge to `WidgetBridgePlugin`, wired to the same
  existing state-change events (`DeviceHeartbeatStore` writes, `ApprovalClient.pending`,
  `MessageFeedStore.unreadCount`) that already drive the watch relay and Live Activity.
- **`NetClawWidget` / `NetClawWidgetControl` (existing scaffolding, rewritten)**: Xcode's placeholder
  "favorite emoji"/"timer" template content replaced with real `TimelineProvider`s reading
  `WidgetDataStore`, and a real `ControlWidget` reading the pending count and invoking spec 111's existing
  intents.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can add a NetGeniusClaw widget to their home screen and see Border health, pending
  count, and a timestamped last-heartbeat reading without opening the app.
- **SC-002**: An operator can add a NetGeniusClaw Lock Screen widget in any of the three accessory families and
  see the same information, with zero per-approval detail ever shown.
- **SC-003**: An operator can add NetGeniusClaw's control to Control Center, see the current pending count, and
  go from a single tap to a ready-to-type Chat compose field — no separate "open the app, find Chat" steps.
- **SC-004**: No widget ever displays a heartbeat-derived value without also showing how old that reading
  is.
- **SC-005**: `flutter analyze` reports zero issues and the full `flutter test` suite passes with zero
  regressions once this spec's Dart-side code (`widget_data.dart`) is implemented; the native Swift portion
  is verified via `xcodebuild` compiling `Runner`/`NetClawWidgetExtension` successfully and, separately and
  explicitly, via real on-device widget placement and rendering (🔌 DEVICE) — not claimed done from either
  alone.

## Assumptions

- Scope is exactly B1b and B2 of `NETCLAW-MOBILE-1.0.1-BRIEF.md`'s Phase B, bundled because Xcode's own
  current Widget Extension template already scaffolds both a `Widget` and a `ControlWidget` into one
  target — building them as two separate specs would mean touching the same target/files twice.
- The `NetClawWidgetExtension` target's real-world setup issues (wrong embedding, wrong bundle id, wrong
  App Group, missing iOS 18 floor) are fixed in this branch's own setup commit, prior to this spec's own
  Phase 0 research — Context records what was found and fixed, not something this spec's own tasks need to
  redo.
- The operator has explicitly authorized dropping pre-iOS-18 support for the widget extension target
  specifically ("drop old version support, this is for modern device OSs") — `Runner`'s and `WatchApp`'s
  own deployment targets are unaffected (FR-010).
- "Verified" for the native Swift/WidgetKit portion of this spec means compiling successfully via
  `xcodebuild` for the `Runner` scheme (which embeds `NetClawWidgetExtension`); actual widget placement,
  rendering, refresh timing, and Control Center interaction are 🔌 **DEVICE**-only and will be exercised
  directly with the operator, not simulated.
