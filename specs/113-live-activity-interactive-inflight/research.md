# Research: NetGeniusClaw Mobile Interactive and In-Flight Live Activity (B3)

**Feature**: `113-live-activity-interactive-inflight` | **Date**: 2026-08-15

## R1: The member-count concept in the brief's original B3b design is not real — narrowing FR-006

- **Decision**: The in-flight query activity shows only what genuinely exists: the question text, a
  client-computed elapsed timer, and the Border's own free-text `task_progress` detail when one arrives.
  No `respondedMembers`/`expectedMembers` or any derived member count is computed, estimated, or displayed.
- **Rationale**: Dedicated research against `gateway.py`'s `run_agent_turn`, `service.py`'s `_edge_on_ask`,
  and `router.py`'s `RiskRouter` confirmed a phone-submitted question is one single, sequential agent turn.
  `_edge_on_ask`'s own docstring states plainly that the agent's existing tool-using behavior
  (`n2n_route`/`n2n_delegate`/`n2n_invoke`) decides whether and where to delegate — no branching logic
  exists in the Border for fan-out, because there is no fan-out; delegation is discovered one tool call at
  a time as the model reasons. `RiskRouter.select_member` selects exactly one member per capability, never
  a candidate set. A real captured trace (`mobile/netclaw-mobile/MAC-IOS-HANDOFF.md`) shows this directly:
  `cml` completes at 13:04:46, and only then does the router select `pyats` at 13:04:59 — sequential
  discovery, not a parallel request with a known N. There is also no parent/child correlation column on
  `delegated_task` rows to count completions against even if a count were meaningful. Displaying a
  fabricated or approximated count would violate spec.md's own SC-005.
- **Alternatives considered**: Build the Border-side instrumentation needed for real counts (a
  parent/child task correlation id plus counting logic) — rejected as substantial, disproportionate new
  scope for what this spec is otherwise a small, additive UI change; genuinely counting delegations would
  also require deciding what "expected" even means in a system where the total is only known in hindsight,
  once the turn finishes. Show a static, non-numeric "delegating..." indicator instead of a member count —
  considered, but rejected as adding no real information beyond what the elapsed timer and existing
  progress text already communicate.

## R2: The Approve/Deny buttons foreground the app via the same URL-based deep-link mechanism already in use

- **Decision**: A new `ApprovalActionIntent` (`LiveActivityIntent`, iOS 17+) sets `openAppWhenRun = true`
  and, inside `perform()`, calls `UIApplication.shared.open(URL(string: "netgeniusclaw://approvals")!)`. The
  existing `app_links`-based listener (`lib/ncfed/device_deep_link.dart`'s sibling pattern, already wired
  for cold-start AND foreground-tap per its own doc comment) gains a new recognized shape,
  `netgeniusclaw://approvals`, that calls the existing `_selectTab(3)` navigation `main.dart` already exposes via
  `DashboardScreen`'s `onOpenApprovals` callback (spec 110, US7) — no new navigation mechanism.
- **Rationale**: `openAppWhenRun = true` only tells the OS to launch/foreground the app — it does not by
  itself communicate *where* to navigate once launched. Reusing the existing URL-scheme/`app_links`
  plumbing (already proven for `netgeniusclaw://device/<id>`) means zero new native-to-Dart plumbing is needed
  beyond registering one more URL shape; the intent itself needs no method channel, no static state, and no
  new Swift-side navigation logic.
- **Alternatives considered**: A dedicated new `FlutterMethodChannel` the intent calls directly — rejected
  as a second, parallel foreground-navigation mechanism duplicating what the URL scheme already does more
  simply, and inconsistent with how every other "foreground to X" case in this app already works.

## R3: The in-flight activity's tap target reuses the same mechanism, extended with a task id

- **Decision**: The in-flight query Live Activity's Lock Screen and Dynamic Island views set
  `.widgetURL(URL(string: "netgeniusclaw://chat/\(taskId)"))` (or wrap content in `Link(destination:)`,
  whichever ActivityKit's API surface makes cleaner at implementation time) so tapping it opens
  `netgeniusclaw://chat/<taskId>`, parsed by a new sibling function to `parseDeviceDeepLink` and routed to the
  existing `openChatTurn` callback `NotificationDeepLink` already exposes (spec 073) — the same call site
  the chat-answer notification's tap already uses.
- **Rationale**: Matches R2's reuse of the existing URL-scheme mechanism exactly, and matches FR-008's
  explicit requirement to behave like the existing chat notification's deep-link. `taskId` is already the
  identifier `ConversationTurn`/`findTurnForIdentifier` use, so no new identifier scheme is introduced.
- **Alternatives considered**: A separate, activity-specific navigation path — rejected for the same
  reason as R2's alternative: unnecessary duplication of an already-proven mechanism.

## R4: `ConversationStore` gains `onAdded` and `onTerminal`, distinct from the existing `onCompleted`

- **Decision**: Add `void Function(ConversationTurn turn)? onAdded`, invoked at the end of `addPending()`,
  and `void Function(ConversationTurn turn)? onTerminal`, invoked in `updateState()` whenever the new state
  is any of `completed`/`failed`/`cancelled` (i.e. `_isTerminal(state)` becomes newly true) — both alongside
  the existing `onCompleted` (which continues to fire only for `'completed'` specifically, unchanged, for
  its existing chat-notification purpose).
- **Rationale**: `addPending()` is already called from three sites in `chat_screen.dart` (normal submit,
  retry, photo-attached submit) plus one in `main.dart` — the exact same "many call sites, one true event"
  shape `onCompleted` was originally introduced to solve (spec 073's own doc comment on `onCompleted`:
  fires "regardless of which tab the operator is looking at," a single hook rather than duplicated wiring
  per call site). `onCompleted` alone cannot end the in-flight Live Activity correctly, since a `failed` or
  `cancelled` turn must also end its activity (FR-007), and `onCompleted`'s existing completed-only trigger
  is intentional for its own use case (only a real answer produces a chat notification) and must not be
  broadened, or every failed ask would start incorrectly posting a chat-answer notification too.
- **Alternatives considered**: Broaden `onCompleted` itself to fire on any terminal state — rejected because
  it is already relied upon (`main.dart`) specifically for the completed-answer notification path; changing
  its trigger condition would be a behavior change to existing, shipped functionality, not something this
  spec should risk for a new feature's convenience.

## R5: `AskActivityAttributes.swift` AND `ApprovalActionIntent.swift` both need dual Xcode-target membership — corrected during implementation

- **Decision**: `AskActivityAttributes.swift`, `AskLiveActivityView.swift`, and `ApprovalActionIntent.swift`
  are added to `project.pbxproj` using the `xcodeproj` Ruby gem (confirmed available in this environment),
  mirroring exactly how spec 071's own README entry describes adding `EdgeIdentityPlugin.swift`/
  `X509SelfSigned.swift` to the `Runner` target after discovering they had never been added at all.
  `AskActivityAttributes.swift` needs membership in BOTH `Runner` (starts/updates/ends the activity) and
  `LiveActivityWidget` (renders it) — the same dual membership `PendingApprovalActivityAttributes.swift`
  already has. `ApprovalActionIntent.swift` **also** needs dual membership — this was gotten wrong on the
  first implementation pass (originally scoped Runner-only, reasoning "it only foregrounds the Runner app")
  and corrected only once a real `xcodebuild` run failed with `cannot find 'ApprovalActionIntent' in
  scope` inside `LiveActivityWidget`'s own compile: `PendingApprovalLiveActivityView.swift`'s
  `Button(intent: ApprovalActionIntent())` calls are compiled *into* the `LiveActivityWidget` target, so
  that target needs the concrete type too, for the exact same reason `AskActivityAttributes.swift` does.
  `AskLiveActivityView.swift` remains `LiveActivityWidget`-only (single membership, like
  `PendingApprovalLiveActivityView.swift` itself), since nothing in `Runner` ever references it directly.
- **A second, deeper problem surfaced by the same dual-membership fix**: `ApprovalActionIntent.perform()`
  calls `UIApplication.shared.open(...)` to trigger the `netgeniusclaw://approvals` navigation (R2) —
  `UIApplication.shared` is unavailable in application extensions, so the *same source file*, once compiled
  into `LiveActivityWidget` too, failed with `'shared' is unavailable in application extensions for iOS`.
  This is not actually a functional problem — `openAppWhenRun = true` means the OS always executes
  `perform()` in the app's own process, never inside the extension's, so the extension's copy of this method
  is compiled but never actually runs — but Swift still enforces `APPLICATION_EXTENSION_API_ONLY`
  restrictions on code that merely *exists* in an extension target, whether or not it is ever called.
  **Fix**: added a custom `IS_EXTENSION_TARGET` flag to `LiveActivityWidget`'s
  `SWIFT_ACTIVE_COMPILATION_CONDITIONS` (via the `xcodeproj` gem, all three build configurations), and
  wrapped the `UIApplication.shared.open(...)` call in `#if !IS_EXTENSION_TARGET ... #endif` — dead code in
  the extension's build either way, just code that target's compiler must never be asked to accept.
- **A third, purely mechanical mistake, twice**: the `xcodeproj` gem's `group.new_reference(path)` expects
  a path *relative to that group's own directory*, not relative to the project root — passing
  `"LiveActivityWidget/AskActivityAttributes.swift"` while already inside the `LiveActivityWidget` group
  (and similarly `"Runner/ApprovalActionIntent.swift"` while inside the `Runner` group) doubled the path
  segment, producing file references `xcodebuild` could not resolve (`Build input files cannot be found`).
  Fixed by passing bare filenames to `new_reference` when already working within the target file's own
  group — confirmed against the existing, working `PendingApprovalActivityAttributes.swift` entry's own
  `path = PendingApprovalActivityAttributes.swift` (no directory prefix) as the reference pattern to match.
- **Rationale**: This is the brief's own explicitly flagged gotcha — forgetting dual membership produces a
  failure with no compile error being the FEARED case; in practice here it *did* surface as a compile error
  (a stricter and more fortunate outcome than the brief's own warning implied), but only once a real
  `xcodebuild` run was attempted — none of the earlier single-file `swiftc -parse`/SourceKit checks caught
  either the missing membership or the extension-availability violation, underscoring why this spec's own
  quickstart.md treats a full `xcodebuild` run (not just a syntax check) as mandatory before claiming any
  Swift-side task done.
- **Alternatives considered**: Hand-edit `project.pbxproj`'s XML/plist-like text directly — rejected as
  fragile and error-prone for a file format with UUID cross-references between `PBXBuildFile`/
  `PBXFileReference`/`PBXSourcesBuildPhase` entries; the `xcodeproj` gem is the same tool this repo's own
  prior spec already used successfully for the identical class of problem, and its own path-relativity
  mistake was self-correcting once verified against a real build rather than assumed correct.

## R6: iOS 17+ interactive buttons are gated by availability, not a deployment-target bump

- **Decision**: `ApprovalActionIntent`'s conformance and the `Button(intent:)` controls in
  `PendingApprovalLiveActivityView.swift` are wrapped in `if #available(iOS 17.0, *)`, leaving
  `IPHONEOS_DEPLOYMENT_TARGET` at its current `16.2`.
- **Rationale**: Matches FR-010 and the identical pattern spec 112 already established for watchOS Double
  Tap (research.md R3 there) — adopt a version-gated API via a runtime check rather than moving the floor
  and dropping support for devices on the current minimum.
- **Alternatives considered**: Bump `IPHONEOS_DEPLOYMENT_TARGET` to 17.0 — rejected; nothing in this spec's
  scope requires abandoning iOS 16.2 support, and FR-002's own acceptance bar ("On iOS below 17... exactly
  as it does today") forbids it.

## R7: `staleDate` values (FR-011)

- **Decision**: The approval activity's `staleDate` remains `nil` (unchanged from today — an approval has
  no natural expiry this spec introduces one for). The in-flight query activity sets a `staleDate`
  matching the Border's own existing ask-timeout ceiling (`N2N_EDGE_ASK_TIMEOUT_S`, effectively the
  member-turn budget plus stall extension, `service.py`'s `_edge_ask_timeout()`) rather than an arbitrary
  client-side guess, so a genuinely abandoned/never-terminal activity goes stale at the same point the
  Border itself would have given up.
- **Rationale**: FR-011 explicitly requires the in-flight activity not imply liveness indefinitely.
  Reusing the Border's own existing timeout concept (already the source of truth for "how long is a
  legitimately still-running ask allowed to take") avoids inventing a second, disconnected timeout value
  that could drift out of sync with the real one.
- **Alternatives considered**: A fixed short client-side staleness window (e.g. 5 minutes) — rejected as
  arbitrary and liable to mark a genuinely still-running, Border-acknowledged-as-alive turn (the README's
  own 2m13s+ real examples) as stale well before it actually finishes.

## R8: No automated test for the native ActivityKit/SwiftUI rendering itself; Dart-side sequencing is fully unit-testable

- **Decision**: `live_activity.dart`'s `start()`/`update()`/`end()` call sequencing (per task id) against a
  fake `MethodChannel` is unit-tested directly — this is exactly where spec.md's own Context flags the real
  regression risk ("a stuck activity that never ends is the likely bug"). The native Swift rendering itself
  is verified via `xcodebuild` compiling the `Runner`/`LiveActivityWidget` targets, plus 🔌 DEVICE for actual
  appearance/interaction — matching spec 099's own original verification split for this exact feature area.
- **Rationale**: `MethodChannel.setMockMethodCallHandler` is already this codebase's standard way to test a
  bridge class's call sequencing without a real platform implementation (used throughout the existing test
  suite for other bridges); this is the highest-value place to catch a logic bug (calling `end()` twice,
  never calling it at all, starting a second activity for the same task id) before it ever reaches a device.
- **Alternatives considered**: Skip Dart-side testing entirely, treating the whole feature as 🔌 DEVICE-only
  like spec 112's SwiftUI-only changes — rejected because, unlike spec 112, this spec's core sequencing
  logic (start-once-per-task, update-on-progress, end-exactly-once-on-terminal) lives entirely in
  testable Dart code, not SwiftUI view wiring; not testing it would forgo the highest-leverage verification
  available for this spec's single most likely bug class.
