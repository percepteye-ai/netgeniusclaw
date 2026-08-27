# Research: NetGeniusClaw Mobile Home Screen, Lock Screen, and Control Center Widgets (B1b+B2)

**Feature**: `114-widgets-controlwidget` | **Date**: 2026-08-15

## R1: `WidgetDataStore` mirrors the exact watch-side App-Group pattern, one level up

- **Decision**: A new `WidgetDataStore.swift` (dual membership: `Runner` + `NetClawWidgetExtension`)
  provides `write()`/`read()` pairs for Border health (summary/pushedAt/isAlarm), pending-approval count,
  and unread-feed count, backed by `UserDefaults(suiteName: "group.ca.automateyournetwork.netclaw.mobile
  .ios")` — the new phone-only App Group, never the existing watch-only
  `group.ca.automateyournetwork.netclaw.mobile`.
- **Rationale**: `HeartbeatStatusStore.swift`/`PendingApprovalCountStore.swift`
  (`ios/WatchComplication/`) already solve the identical cross-process problem (a widget extension cannot
  read another process's in-memory state directly) for the watch, with a proven, working shape — same
  `write()`/`read()`-pair-per-value, same nil-safe `read()` returning a distinct "no data" signal. Reusing
  that exact shape means no new pattern to design or review, and the two App Groups staying fully separate
  means the phone-side store change carries zero risk to the watch's own, already-shipped complications.
- **Alternatives considered**: One shared App Group for both watch and phone — rejected; the two are
  already independent by design (Context), and unifying them now would be an unrelated, unrequested
  refactor of already-working watch code for no benefit this spec needs.

## R2: The Control Center control's tap action foregrounds Chat — it does not headlessly invoke `AskBorderIntent`

- **Decision**: The Control Center control's action is a new, small `AppIntent` (not a `LiveActivityIntent`
  — Control Center controls use plain `AppIntent`s for their action, `openAppWhenRun = true`) that opens
  `netgeniusclaw://chat` (a new, argument-less deep-link shape), landing the operator on the Chat tab with the
  compose field ready to type.
- **Rationale**: `AskBorderIntent` (spec 111) has a required `question: String` parameter. Control Center
  provides no text-entry surface for its controls — there is no way for a tap alone to supply that
  parameter's value. The spec's own first draft of this User Story assumed the tap could directly invoke
  `AskBorderIntent`'s headless flow; checked against `AskBorderIntent`'s actual signature before writing
  the plan, that assumption doesn't hold, so the User Story and FR-008 were corrected before this plan was
  written to describe what's actually buildable: a one-tap shortcut to a ready-to-type compose field,
  reusing the exact `openAppWhenRun` + `netgeniusclaw://` pattern spec 113's `ApprovalActionIntent` already
  established, not a new mechanism.
- **Alternatives considered**: A Control Center *toggle* control that invokes `PendingApprovalsIntent` on
  every value refresh to compute its displayed count — rejected in favor of R5 (reading the cached
  `WidgetDataStore` value instead), for the same "never implied live, always a cached point-in-time
  reading" reasoning FR-004 already establishes for the other widget families.

## R3: New `netgeniusclaw://` deep-link shapes reuse the existing listener, not a new mechanism

- **Decision**: Two new shapes recognized by the same `DeviceDeepLinkListener`
  (`lib/ncfed/device_deep_link.dart`) specs 111/113 already extended: `netgeniusclaw://dashboard` (health-widget
  taps — lands on the Dashboard tab, index 0, the same tab that already shows Border connection status) and
  `netgeniusclaw://chat` (the Control Center control's tap target, R2 — no task id, unlike the existing
  `netgeniusclaw://chat/<taskId>` shape, which opens a *specific* turn).
- **Rationale**: Matches the exact reuse pattern already established twice (`netgeniusclaw://approvals` in spec
  113, `netgeniusclaw://chat/<taskId>` also in spec 113) rather than inventing a fourth navigation mechanism for
  a fourth surface. `netgeniusclaw://chat` (no path segment) and `netgeniusclaw://chat/<taskId>` (with one) are
  distinguished the same way `parseChatDeepLink` already checks `uri.pathSegments.isNotEmpty`.
- **Alternatives considered**: A single generic `netgeniusclaw://open?tab=chat` query-parameter shape covering
  every case uniformly — rejected as an unrequested generalization; the existing per-purpose shapes
  (`/approvals`, `/chat`, `/chat/<id>`, `/dashboard`) are simpler to read, test, and reason about
  individually, and nothing in this spec needs a single unified parser.

## R4: Widget timeline refresh policy matches the watch complications' `.never` + explicit reload

- **Decision**: `NetClawWidget`'s `TimelineProvider` returns a single-entry `Timeline` with policy `.never`
  for every family, relying entirely on `WidgetBridgePlugin`'s `WidgetCenter.shared.reloadAllTimelines()`
  call (triggered by real Dart-side state changes) to refresh it — never a periodic guess.
- **Rationale**: `HeartbeatComplication.swift`/`PendingApprovalComplication.swift`
  (`ios/WatchComplication/`) already use exactly this policy with the identical justification in their own
  doc comments: "`reloadAllTimelines()`... is the only thing that should refresh this, not a periodic
  policy guessing when a new heartbeat might have landed." The phone-side widgets read the same kind of
  data from the same kind of store, so the same policy applies for the same reason.
- **Alternatives considered**: A short periodic refresh policy (e.g. every 15 minutes) as a backstop —
  rejected; iOS's own refresh budget for periodic policies is already tightly rationed and unpredictable
  (this spec's own FR-004 exists precisely because refreshes cannot be forced or scheduled reliably), so a
  periodic policy would add complexity without a real guarantee, on top of the explicit-reload path that
  already covers every real state change this spec cares about.

## R5: The Control Center control's displayed value is read from `WidgetDataStore`, not queried live

- **Decision**: `NetClawWidgetControl`'s `AppIntentControlValueProvider.currentValue(configuration:)` reads
  `WidgetDataStore`'s mirrored pending-approval count — the same value the home-screen and Lock Screen
  widgets read — rather than opening a fresh headless connection to the Border on every Control Center
  refresh.
- **Rationale**: Consistent with FR-004's "never implied live" philosophy already established for the other
  two widget families, and avoids giving Control Center's own refresh scheduler (which iOS also budgets,
  similar to widget timelines) a live-network dependency that could make the control appear to hang or show
  stale/error states under normal iOS throttling.
- **Alternatives considered**: A live `n2n/edge/approvals_list` call (spec 111's own RPC) on every
  `currentValue()` invocation — rejected for the reasons above; that RPC remains reserved for
  `PendingApprovalsIntent`'s own on-demand, Siri-triggered use case, where a real network round trip is
  the whole point.

## R6: No new Xcode target-membership complexity beyond what the operator already created

- **Decision**: `WidgetDataStore.swift` needs dual membership (`Runner` + `NetClawWidgetExtension`), added
  via the `xcodeproj` gem using bare filenames relative to each file's own group (the exact lesson learned
  and documented in spec 113's research.md R5, applied here from the start rather than re-learned).
  `WidgetBridgePlugin.swift` is `Runner`-only (it's a `FlutterPlugin`, meaningless inside the extension).
  `NetClawWidget.swift`/`NetClawWidgetControl.swift`/`AppIntent.swift` (the new Chat-deep-link intent) are
  all rewritten in place inside the already-`fileSystemSynchronizedGroups`-tracked `NetClawWidget/`
  directory — Xcode's newer synchronized-group mechanism (confirmed present on this target,
  `PBXFileSystemSynchronizedRootGroup`) means editing or adding files in that folder needs no manual
  `PBXFileReference`/`PBXBuildFile` bookkeeping at all, unlike `LiveActivityWidget`'s older-style explicit
  file list.
- **Rationale**: Spec 113's research.md already paid the cost of learning the `xcodeproj` gem's
  bare-filename-relative-to-group requirement the hard way (three separate path/membership mistakes, each
  only caught by a real `xcodebuild` run); applying that lesson from the very first file addition here
  avoids repeating it. The discovery that `NetClawWidget/` uses a synchronized group is a genuine
  simplification specific to this newer target — confirmed directly in `project.pbxproj`, not assumed.
- **Alternatives considered**: None — this is a direct application of an already-learned, already-verified
  lesson, not a new design decision with real alternatives to weigh.

## R7: No automated test for the native WidgetKit rendering itself; the Dart-side bridge is fully unit-testable

- **Decision**: `widget_data.dart`'s wiring — which existing events (`DeviceHeartbeatStore` writes,
  `ApprovalClient.pending`, `MessageFeedStore.unreadCount` changes) trigger which `WidgetBridgePlugin` calls
  — is unit-tested against a fake `MethodChannel`, matching `live_activity_test.dart`'s established shape
  (spec 113 R8). The native `TimelineProvider`/`ControlWidget` rendering itself is verified via `xcodebuild`
  compiling `NetClawWidgetExtension` successfully, plus 🔌 DEVICE for actual placement/rendering.
- **Rationale**: Matches this repo's established split (specs 112/113) between what's genuinely testable in
  Dart (call sequencing/wiring logic) and what requires real hardware (actual SwiftUI/WidgetKit rendering,
  refresh timing, Control Center interaction).
- **Alternatives considered**: None new — same reasoning as every prior spec in this series.
