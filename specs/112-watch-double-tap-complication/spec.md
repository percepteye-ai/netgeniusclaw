# Feature Specification: NetGeniusClaw Mobile Watch Double Tap and Corner Complication (B4+B5)

**Feature Branch**: `112-watch-double-tap-complication`
**Created**: 2026-08-15
**Status**: Draft
**Input**: User description: "NetGeniusClaw Mobile App Intents integration follow-on — Phase B4+B5 of mobile/netclaw-mobile/NETCLAW-MOBILE-1.0.1-BRIEF.md, bundled together as both are small, watch-only changes with no new Xcode target and no new entitlement. B4: mark the primary action in the watch app's ApprovalsView with `.handGestureShortcut(.primaryAction)` so Double Tap on Series 9/Ultra 2+ triggers it — the brief's own design constraint is that Double Tap must surface the SAME passcode-gated confirmation flow the manual Approve button already uses for the top pending approval, never bypass it; also apply `.primaryAction` to the low-stakes 'Read aloud' button in AskView.swift. B5: add `.accessoryCorner` to `supportedFamilies` in both HeartbeatComplication.swift and PendingApprovalComplication.swift (currently `.accessoryCircular`/`.accessoryRectangular`/`.accessoryInline` only)."

## Context

This spec implements items B4 and B5 of `mobile/netclaw-mobile/NETCLAW-MOBILE-1.0.1-BRIEF.md`'s Phase B, bundled into one spec per that phase's own "Suggested ordering" section, which groups them together as "the smallest headline items, watch-side only." Both are additive changes to existing watch-app files — no new Xcode target, no new entitlement, no App Group.

Before writing this spec, the codebase was checked directly to ground both items in what already exists:

- **`ApprovalsView.swift`'s `resolve(_:action:)` already IS the confirmation gate.** Tapping either the existing "Approve" or "Deny" button calls `resolve(approval, action:)`, which immediately triggers a fresh `LAContext.evaluatePolicy(.deviceOwnerAuthentication, ...)` passcode prompt (FR-003 of spec 072) — an approve/deny only actually reaches the Border if that prompt succeeds; a cancelled/failed prompt sends nothing. This means the brief's core safety concern — "an accidental gesture must not be able to approve a network change" — is already structurally satisfied by the existing code: there is no path from "Double Tap fires" to "an approval is resolved" that skips the passcode prompt, because no such path exists in `resolve()` for ANY caller, manual tap or gesture alike. The design question this spec actually needs to answer is narrower: *which single control, across a screen that can show multiple pending approvals, gets to claim the gesture* — not whether the gesture is safe once claimed.
- **Exactly one control may claim `.handGestureShortcut(.primaryAction)` at a time**, confirmed against Apple's own documented behavior (also called out directly in the brief's Gotchas) — claiming it on more than one visible control produces no error and silently disables Double Tap entirely. `ApprovalsView` renders every pending approval in a `List`, so the modifier can only ever be applied to one row's Approve button — the top (first) approval — never to every row's button, and never to both a row's Approve AND Deny button at once.
- **`WATCHOS_DEPLOYMENT_TARGET` is `10.0`** across every `WatchApp`/`WatchComplication` build configuration in `project.pbxproj` — confirmed by direct search, not assumed. `.handGestureShortcut(.primaryAction)` requires watchOS 11 (the brief's own stated gotcha). The brief's own acceptance criteria for B4 ("On older watches, nothing changes and nothing breaks") is the deciding signal here: this spec does **not** raise the deployment target (which would drop support for every watch below Series 9/Ultra 2 running watchOS 10), and instead gates the new modifier behind an `if #available(watchOS 11.0, *)` check, matching Apple's standard pattern for adopting a newer API while keeping a lower floor.
- **`.accessoryCorner` needs no deployment-target change.** It has been available since watchOS 9, comfortably under the existing 10.0 floor.
- **Both complication views already render in the exact shape `.accessoryCorner` expects.** `HeartbeatComplicationView` and `PendingApprovalComplicationView` both already pair a small glyph or short text with a `.widgetLabel { Text(...) }` curved-label modifier — precisely the icon/gauge-plus-curved-label composition `.accessoryCorner` uses on an Infograph watch face's corner slot. Both complications use `StaticConfiguration` with a single view closure shared across every family in `supportedFamilies`, so WidgetKit itself adapts the existing view's presentation per family; this spec does not need to write a second, corner-specific view.

This repo's verification standard (specs 072/073/110/111) applies unchanged: a real Double Tap gesture and real complication placement on an Infograph watch face are 🔌 **DEVICE**-only, requiring a physical Series 9/Ultra 2-or-later watch (Double Tap is a hardware-gated system gesture, unavailable in the Simulator) — not claimed done from a green `flutter test`/Xcode build alone.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Double Tap to confirm the top pending approval (Priority: P1)

An operator wearing a supporting Apple Watch (Series 9, Ultra 2, or later) has one or more pending
approvals showing in the watch app's Approvals tab. Without touching the screen, they perform a Double
Tap gesture (pinching thumb and index finger together twice). This raises the exact same passcode
confirmation prompt that manually tapping "Approve" on the topmost approval would — never resolving the
approval outright, and never affecting any approval other than the topmost one.

**Why this priority**: This is the entire point of building B4 — a hands-free way to act on the most
urgent, freshest pending approval while the other hand is occupied (a real scenario for someone actively
working in a rack or on a ladder). It is the only part of this spec with a real safety property to get
right.

**Independent Test**: With at least one real pending approval showing on a supporting watch, perform a
Double Tap and confirm the passcode prompt appears for the topmost approval specifically; complete the
prompt and confirm it resolves exactly as a manual "Approve" tap would; cancel the prompt and confirm
nothing was resolved.

**Acceptance Scenarios**:

1. **Given** exactly one pending approval is showing on a supporting watch, **When** the operator
   performs a Double Tap, **Then** the same passcode confirmation prompt a manual "Approve" tap would
   trigger appears, referencing that approval's target name.
2. **Given** the passcode prompt from Double Tap is showing, **When** the operator successfully confirms
   it, **Then** that approval is approved and disappears from the list — identical in outcome to a manual
   "Approve" tap succeeding.
3. **Given** the passcode prompt from Double Tap is showing, **When** the operator cancels or fails it,
   **Then** no approval is resolved, and the list is unchanged — identical to a manual tap being
   cancelled.
4. **Given** two or more pending approvals are showing, **When** the operator performs a Double Tap,
   **Then** only the topmost approval's confirmation prompt appears — no other approval in the list is
   affected.
5. **Given** the Approvals list is empty or shows a connection-error state (no approval to target),
   **When** the operator performs a Double Tap, **Then** nothing happens — there is no control for the
   gesture to trigger.
6. **Given** the watch is a model or OS version that does not support Double Tap (older than Series
   9/Ultra 2, or running watchOS below 11), **When** the operator uses the Approvals view normally,
   **Then** everything behaves exactly as it does today — manual Approve/Deny taps work unchanged, and no
   crash or degraded behavior occurs.

---

### User Story 2 - Double Tap to hear the answer read aloud (Priority: P3)

An operator has just received an answer in the watch app's Ask view and is looking at the on-screen "Read
aloud" button. They perform a Double Tap instead of touching the screen, and the answer is spoken exactly
as if they had tapped the button.

**Why this priority**: A genuine convenience, but the brief itself is explicit that "the stakes are zero"
here — nothing is approved, resolved, or sent. Lowest priority of the two Double Tap surfaces in this
spec.

**Independent Test**: With an answer already showing in the Ask view on a supporting watch, perform a
Double Tap and confirm the answer is read aloud, identical to tapping "Read aloud" manually.

**Acceptance Scenarios**:

1. **Given** an answer is showing with the "Read aloud" button visible, **When** the operator performs a
   Double Tap, **Then** the answer is spoken aloud, identical to a manual tap on that button.
2. **Given** the Ask view is in any other state (idle, waiting, failed) where "Read aloud" is not shown,
   **When** the operator performs a Double Tap, **Then** nothing happens — there is no control for the
   gesture to trigger.

---

### User Story 3 - Corner complications on an Infograph watch face (Priority: P2)

An operator with an Infograph (or Infograph Modular) watch face wants to place NetGeniusClaw's Border-health and
pending-approval status in one of that face's four corner slots — prime, always-visible real estate that
was previously unavailable to these two complications.

**Why this priority**: Genuinely useful and low-risk (both complications already render content in a
shape a corner slot can use), but purely a new placement option, not new information — secondary to the
safety-relevant work in User Story 1.

**Independent Test**: On a supporting watch, add both the "NetGeniusClaw Status" (heartbeat) and "Pending
Approvals" complications to corner slots on an Infograph face and confirm both render legibly and update
consistently with their existing circular/rectangular counterparts.

**Acceptance Scenarios**:

1. **Given** an Infograph (or Infograph Modular) watch face is being edited, **When** the operator opens
   the complication picker for a corner slot, **Then** both "NetGeniusClaw Status" and "Pending Approvals" are
   selectable options, exactly as they already are for the circular/rectangular/inline slots.
2. **Given** either complication is placed in a corner slot, **When** the underlying data changes (a new
   heartbeat arrives, or the pending count changes), **Then** the corner complication updates the same way
   its circular/rectangular/inline counterparts already do — no separate refresh path, no separate data
   source.
3. **Given** no heartbeat has ever been received, **When** the heartbeat complication is shown in a corner
   slot, **Then** it shows the same distinct "no data" state the other families already show — never a
   false "all clear."

### Edge Cases

- What happens if a Double Tap occurs at the exact moment the Approvals list is transitioning (e.g., a
  refresh just removed the topmost approval)? Whatever control SwiftUI has actually rendered as
  `.primaryAction` at that instant is what receives the gesture — no special synchronization is required
  beyond the existing conditional rendering already described in User Story 1's Acceptance Scenario 5,
  since an approval that has already disappeared from the list can no longer have a button in the tree at
  all.
- What happens on a watch that supports Double Tap as a system gesture but is running a watchOS version
  below 11 (the version this spec's API requires)? Per User Story 1's Acceptance Scenario 6, the app
  behaves exactly as it does today — no crash, no partial gesture support, manual taps unaffected.
- What happens if both a corner and a circular slot on the same face show the same complication
  simultaneously? Each instance renders and updates independently from the same underlying store — this is
  standard WidgetKit behavior for any complication placed in multiple slots and requires no special
  handling in this spec.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: On a device and OS version that supports it, a Double Tap gesture performed while the
  Approvals view is showing at least one pending approval MUST trigger the identical passcode-confirmation
  flow (`resolve(_:action: "approve")`) that manually tapping that approval's "Approve" button already
  triggers — never a separate, less-gated path to approval.
- **FR-002**: Double Tap MUST target only the topmost (first) pending approval in the list, never any
  other approval, and never both the Approve and Deny action for the same approval — matching the
  single-control constraint on `.handGestureShortcut(.primaryAction)`.
- **FR-003**: If the Approvals view has no pending approval to target (empty list, or a connection-error
  state), Double Tap MUST have no effect — it MUST NOT crash, MUST NOT show an error, and MUST NOT target
  any other control on screen.
- **FR-004**: On a device or OS version that does not support the App used for Double Tap
  (`.handGestureShortcut(.primaryAction)`, watchOS 11+), the Approvals view MUST behave exactly as it does
  today — manual Approve/Deny taps MUST be unaffected, and no crash or degraded behavior MUST occur.
- **FR-005**: While the Ask view is showing a completed answer with the "Read aloud" button visible, Double
  Tap MUST trigger the identical read-aloud action that button already triggers. In every other Ask view
  state, Double Tap MUST have no effect.
- **FR-006**: This spec MUST NOT raise `WATCHOS_DEPLOYMENT_TARGET` beyond its current value — the Double
  Tap capability MUST be gated by a runtime OS-version check, not a deployment-target floor change, so that
  watches below watchOS 11 continue to build and run identically to today.
- **FR-007**: Both `HeartbeatComplication` and `PendingApprovalComplication` MUST support the
  `.accessoryCorner` family in addition to their existing `.accessoryCircular`/`.accessoryRectangular`/
  `.accessoryInline` support, using the same underlying data source and refresh mechanism (`WidgetCenter
  .shared.reloadAllTimelines()`) already used by every other supported family — no new data path.
- **FR-008**: A corner-placed heartbeat complication MUST distinguish "no heartbeat ever received" from
  "all systems normal," matching the existing distinction already made for every other supported family.
- **FR-009**: Neither this spec's Double Tap change nor its corner-complication change MUST require a new
  Xcode target, a new entitlement, or a new App Group.

### Key Entities

- **`ApprovalsView` (existing, modified)**: gains a `.handGestureShortcut(.primaryAction)` modifier applied
  conditionally to only the topmost approval row's Approve button, gated by `if #available(watchOS 11.0,
  *)`.
- **`AskView` (existing, modified)**: gains the same modifier on its "Read aloud" button, under the same
  availability gate.
- **`HeartbeatComplication` / `PendingApprovalComplication` (existing, modified)**: each gains
  `.accessoryCorner` in its `supportedFamilies` array — no new entity, no schema change, no new Widget
  type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a supporting watch with a pending approval showing, an operator can go from a Double Tap
  gesture to a passcode prompt for that specific approval, with no manual screen touch required.
- **SC-002**: No Double Tap gesture, under any Approvals-view state (one approval, several approvals, no
  approvals, connection error), ever resolves an approval without a passcode confirmation having
  succeeded first.
- **SC-003**: An operator can place both NetGeniusClaw complications into a corner slot on an Infograph face and
  see them render and update exactly as their existing circular/rectangular/inline placements already do.
- **SC-004**: A watch that does not support Double Tap (pre-Series-9/Ultra 2 hardware, or watchOS below 11)
  shows zero behavior change from before this spec — verified by exercising the Approvals and Ask views
  normally on such a device or OS version.
- **SC-005**: `flutter analyze` reports zero issues and the full `flutter test` suite passes with zero
  regressions (this spec touches no Dart code, so this is a pure regression guarantee); the native Swift
  portion is verified via `xcodebuild` compiling the `WatchApp`/`WatchComplication` targets successfully
  and, separately and explicitly, via real on-device Double Tap and corner-complication placement
  (🔌 DEVICE) — not claimed done from either alone.

## Assumptions

- Scope is exactly B4 and B5 of `NETCLAW-MOBILE-1.0.1-BRIEF.md`'s Phase B, bundled per that phase's own
  suggested ordering ("the smallest headline items, watch-side only"). Neither item touches any Dart/phone
  code, any new Xcode target, or any entitlement.
- The existing passcode-confirmation gate in `ApprovalsView.resolve(_:action:)` is treated as the
  authoritative safety mechanism this spec must route through, not something to add to or duplicate — per
  research performed before writing this spec (Context), a gesture-triggered approval and a manually-tapped
  approval share the exact same code path and therefore the exact same safety guarantee.
- No deployment-target change is made for either item — `.accessoryCorner` already fits under the existing
  watchOS 10.0 floor, and Double Tap's watchOS 11 requirement is handled with a runtime availability check
  per FR-006, consistent with the brief's own "nothing breaks on older watches" acceptance bar.
- "Verified" for the native Swift portion of this spec means compiling successfully via `xcodebuild` for
  the `WatchApp` and `WatchComplication` targets; actual Double Tap invocation and real Infograph
  corner-slot placement are 🔌 **DEVICE**-only and require a physical Series 9/Ultra 2-or-later watch —
  neither is simulatable, and neither will be claimed done without the operator's own hardware.
