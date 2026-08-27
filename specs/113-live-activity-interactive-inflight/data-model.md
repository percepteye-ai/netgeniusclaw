# Data Model: NetGeniusClaw Mobile Interactive and In-Flight Live Activity (B3)

No new persisted store. Every entity below is either an extension of an existing in-memory/wire-only
shape, or a new one that lives for the duration of a single Live Activity's lifetime and is discarded when
it ends.

## `PendingApprovalActivityAttributes` / `ContentState` (existing, unchanged)

No field change. `approvalId`, `targetName`, `status` (`"pending"`|`"resolved"`) already carry everything
B3a needs — the new Approve/Deny buttons read `context.state`/`context.attributes.approvalId` from the
same existing shape, and `update()` (research.md R3 of spec.md's Context) writes the same `status` field
the existing `end()` already does.

## `AskActivityAttributes` (NEW)

| Field | Type | Notes |
|---|---|---|
| `taskId` | `String` | The `EdgeAskClient.ask()` return value — the same identifier `ConversationTurn.taskId` already uses. Fixed for the activity's lifetime (an `ActivityAttributes`, not `ContentState`). |
| `questionPreview` | `String` | The submitted question text, truncated to a reasonable Live Activity display length. Fixed for the activity's lifetime. |

`ContentState` (mutable, updated over the activity's life):

| Field | Type | Notes |
|---|---|---|
| `startedAt` | `Date` | Set once at activity start — feeds `Text(timerInterval:)`'s continuously-ticking elapsed display (FR-005); never itself displayed as a raw value. |
| `progressDetail` | `String?` | The most recent `task_progress` notification's free-text `detail`, verbatim — `nil` until the first one arrives, if any (research.md R1: deliberately never a member count). |
| `state` | `String` | `"working"` \| `"completed"` \| `"failed"` \| `"cancelled"` — mirrors `ConversationTurn.state`'s existing vocabulary exactly, so no new state-naming scheme is introduced. |

No `respondedMembers`/`expectedMembers` field exists on this type at all (research.md R1) — not merely
left empty, genuinely absent from the shape.

## `LiveActivity` (existing Dart class, extended)

Currently: `start({approvalId, targetName})` / `end()` — implicitly single-activity (one `currentActivity`
on the Swift side). Extended with:

| Member | Signature | Notes |
|---|---|---|
| `update(...)` | `Future<void> Function({required int approvalId, required String status})` | NEW (FR-003) — tells the approval activity to reflect a resolution from any surface. |
| `startAsk(...)` | `Future<void> Function({required String taskId, required String questionPreview})` | NEW (FR-004) — starts a per-task in-flight activity, keyed by `taskId`. |
| `updateAsk(...)` | `Future<void> Function({required String taskId, required String progressDetail})` | NEW (FR-006) — updates one specific task's activity by id. |
| `endAsk(...)` | `Future<void> Function({required String taskId, required String state})` | NEW (FR-007) — ends one specific task's activity by id, reflecting its terminal state first. |

The existing `start`/`end` (no arguments beyond `approvalId`/`targetName`) are unchanged — they continue
to address the single aggregate approval activity exactly as today.

## `LiveActivityBridge` (existing Swift class, extended)

Currently: `currentActivity: Activity<PendingApprovalActivityAttributes>?` (single). Extended with:

| Field | Type | Notes |
|---|---|---|
| `askActivities` | `[String: Activity<AskActivityAttributes>]` | Keyed by `taskId` (FR-004) — replaces a single optional with a dictionary, since multiple in-flight asks are supported independently (spec.md Context: "per-question, not aggregated"). |

## `ConversationStore` (existing, extended — no schema change)

Two new callback fields, alongside the existing `onCompleted`:

| Field | Type | Fires |
|---|---|---|
| `onAdded` | `void Function(ConversationTurn turn)?` | At the end of `addPending()` — regardless of which call site invoked it (research.md R4). |
| `onTerminal` | `void Function(ConversationTurn turn)?` | In `updateState()`, when the new state is any of `completed`/`failed`/`cancelled` (distinct from `onCompleted`'s completed-only trigger). |

No change to `ConversationTurn`'s own persisted JSON shape — both callbacks are purely in-memory wiring,
identical in kind to the existing `onCompleted`.

## `netgeniusclaw://` deep-link shapes (existing scheme, two new shapes)

| Shape | Parsed by | Resolves to |
|---|---|---|
| `netgeniusclaw://approvals` | New sibling function to `parseDeviceDeepLink` in `device_deep_link.dart` | Calls `_selectTab(3)` (Approvals) — the same navigation `DashboardScreen.onOpenApprovals` already triggers. |
| `netgeniusclaw://chat/<taskId>` | New sibling function, extracting `taskId` from the path | Calls `NotificationDeepLink`'s existing `openChatTurn` callback with the matching `ConversationTurn` (`findTurnForIdentifier`, already exists). |
