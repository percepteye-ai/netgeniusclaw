# Data Model: NetGeniusClaw Mobile Watch Double Tap and Corner Complication (B4+B5)

No new persisted state, no new wire contract, no new entity. Both items are additive modifiers on
existing SwiftUI views/widget configurations.

## `ApprovalsView` row state (existing, one new derived value)

`ApprovalsView` already holds `store.approvals: [WatchApproval]`. B4 adds exactly one new derived
value, computed at render time, never persisted:

| Value | Type | Derivation | Used by |
|---|---|---|---|
| `isTopApproval` | `Bool` | `index == 0` within the currently-rendered `store.approvals` list | Whether this row's "Approve" `Button` gets `.handGestureShortcut(.primaryAction)` applied (research.md R2) |

This value is recomputed on every render from the list's current order — it is not cached, stored, or
tracked as separate state, since "the topmost approval" is already fully determined by
`store.approvals`'s existing ordering.

## `AskView` state (existing, unchanged)

No new state. The existing `state == .answered` condition that already shows the "Read aloud" button is
the same condition that gates whether `.handGestureShortcut(.primaryAction)` is applied to it.

## `HeartbeatComplication` / `PendingApprovalComplication` (existing, no schema change)

`HeartbeatEntry`/`PendingApprovalEntry`, their `TimelineProvider`s, and their underlying stores
(`HeartbeatStatusStore`, `PendingApprovalCountStore`) are all unchanged. `.accessoryCorner` is added
purely to each `Widget`'s `supportedFamilies` array — a `WidgetFamily` enum case, not a data value — so
there is no new field, no new store, and no new read/write path anywhere in this spec.
