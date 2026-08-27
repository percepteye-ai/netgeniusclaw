# Research: NetGeniusClaw Mobile Watch Double Tap and Corner Complication (B4+B5)

**Feature**: `112-watch-double-tap-complication` | **Date**: 2026-08-15

Both items are small enough that most of the research needed was already done and recorded directly in
spec.md's Context section before writing the requirements. This file formalizes those findings into the
decision/rationale/alternatives format the rest of this repo's specs use, plus the remaining
implementation-level details plan.md's Phase 1 needs.

## R1: Double Tap routes through the existing passcode gate, not a new one

- **Decision**: `.handGestureShortcut(.primaryAction)` is applied directly to the existing "Approve"
  `Button` for the topmost approval row — the same `Button` whose action already calls
  `resolve(approval, action: "approve")`. No new function, no new gate, no parallel resolution path.
- **Rationale**: `resolve(_:action:)` (`ApprovalsView.swift`) already requires a fresh
  `LAContext.evaluatePolicy(.deviceOwnerAuthentication, ...)` success before calling `watch/approvals/
  resolve` — this is true for every caller of `resolve()`, not something specific to a manual tap. Wiring
  Double Tap to the identical `Button.action` closure means it inherits this guarantee automatically and by
  construction, rather than needing to be re-verified as a separate safety property.
- **Alternatives considered**: A dedicated "confirm via gesture" intermediate state (e.g., Double Tap shows
  a distinct on-screen "tap again to confirm" affordance before the passcode prompt) — rejected as
  redundant. The passcode prompt itself already is the deliberate-act requirement the brief asks for; adding
  a second confirmation layer in front of it would be friction with no corresponding safety gain, since the
  passcode prompt cannot itself be triggered accidentally in a way that resolves anything.

## R2: Only the topmost approval's Approve button claims the gesture

- **Decision**: `ApprovalsView`'s `List` is restructured to iterate with an index (e.g.
  `Array(store.approvals.enumerated())`), and `ApprovalRow` gains an `isTopApproval: Bool` parameter. Only
  when `isTopApproval` is true does its "Approve" `Button` get `.handGestureShortcut(.primaryAction)`
  applied (under the availability gate, R3). No other row, and never the "Deny" button, ever claims it.
- **Rationale**: Apple's platform behavior (confirmed in spec.md's Context, also the brief's own Gotchas)
  is that claiming `.handGestureShortcut(.primaryAction)` on more than one visible control silently
  disables Double Tap entirely, with no runtime warning. A `List` of pending approvals can show more than
  one row at once, so the modifier cannot be applied unconditionally to every row's button — it must be
  scoped to exactly one, and the brief's own User Story text ("the top pending approval") specifies which
  one.
- **Alternatives considered**: Apply the modifier only when `store.approvals.count == 1` (single-approval
  case only) — rejected as unnecessarily restrictive; nothing in the brief or the safety analysis (R1)
  requires disabling the gesture just because more than one approval happens to be pending, and the
  topmost-only behavior degrades exactly the same way whether there is one approval or several.

## R3: No deployment-target change — gate with `if #available(watchOS 11.0, *)`

- **Decision**: Wrap the `.handGestureShortcut(.primaryAction)` modifier applications (both in
  `ApprovalsView` and `AskView`) in `if #available(watchOS 11.0, *) { ... }`, leaving
  `WATCHOS_DEPLOYMENT_TARGET` at its current `10.0` across every `WatchApp`/`WatchComplication` build
  configuration.
- **Rationale**: `.handGestureShortcut(.primaryAction)` requires watchOS 11 (confirmed, and flagged in the
  brief's own Gotchas). Raising the deployment target to 11.0 would drop build/run support for every watch
  below Series 9/Ultra 2 (all of which shipped watchOS 10 as their newest OS at some point in their
  lifecycle) — a real regression the brief's own B4 acceptance criterion explicitly forbids: "On older
  watches, nothing changes and nothing breaks." An availability check is the standard, zero-regression way
  to adopt a version-gated API without moving the floor.
- **Alternatives considered**: Bump `WATCHOS_DEPLOYMENT_TARGET` to 11.0 — rejected outright per FR-006 and
  the brief's own acceptance bar; this would be a real, unrequested scope expansion (dropping supported
  hardware) to gain a convenience feature.

## R4: `.accessoryCorner` needs no new view — same `StaticConfiguration`, one line each

- **Decision**: Add `.accessoryCorner` to the `supportedFamilies` array in both
  `HeartbeatComplication.swift` and `PendingApprovalComplication.swift` — no new `TimelineProvider`, no new
  `View`, no new `Widget` type.
- **Rationale**: Both complications already use a single `StaticConfiguration` view closure
  (`HeartbeatComplicationView`/`PendingApprovalComplicationView`) shared across every family in
  `supportedFamilies` — WidgetKit itself adapts that one view's presentation per family. Both existing
  views already pair a small glyph or short text with `.widgetLabel { Text(...) }`, which is exactly the
  icon/gauge-plus-curved-label composition `.accessoryCorner` renders on an Infograph face's corner slot.
  `.accessoryCorner` has been available since watchOS 9, comfortably under the existing 10.0 floor, so no
  availability gate or deployment-target change is needed for this item (unlike R3's Double Tap gate).
- **Alternatives considered**: Write a dedicated corner-specific view (e.g. a `Gauge`-based layout) —
  considered per the brief's own "gauge or text + curved label" phrasing, but rejected as unnecessary scope
  once the existing views were confirmed to already fit the shape `.accessoryCorner` needs; the two
  Acceptance Scenarios in User Story 3 (legibility, live update, no-data distinction) are testable against
  the existing view as-is, and a corner-specific view can be revisited later if real-device rendering (🔌
  DEVICE) shows it reads poorly — a risk to verify, not a certainty to design around preemptively.

## R5: No automated test coverage exists (or is being added) for watch SwiftUI views

- **Decision**: This spec adds no new automated test — neither Dart (no Dart code is touched at all) nor
  Swift (no `XCTest` target exists for `WatchApp`/`WatchComplication` views today; the only Swift test
  target in this repo, `RunnerTests`, covers phone-side plugin code like `WatchRelayPluginTests.swift`, not
  the watch app's own SwiftUI views). Verification is `xcodebuild` compiling the `WatchApp`/
  `WatchComplication` targets successfully, plus 🔌 DEVICE for actual gesture/complication behavior.
- **Rationale**: Matches this repo's existing, established convention for the watch app (spec 072's own
  README entry: "Verified end to end on real hardware," not via automated Swift tests) — this spec does not
  introduce a new testing pattern for a two-file, additive change when none exists for the surrounding code
  it modifies.
- **Alternatives considered**: Add a new `WatchAppTests` XCTest target specifically for this spec —
  rejected as disproportionate new infrastructure for a two-file change, and inconsistent with how every
  prior watch-app spec (066–073) has been verified in this repo.
