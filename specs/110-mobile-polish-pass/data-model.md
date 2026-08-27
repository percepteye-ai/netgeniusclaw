# Data Model: NetGeniusClaw Mobile 1.0.1 Polish Pass (Phase A + C1)

Only one story introduces genuinely new persisted state (US4). Everything
else either reuses existing entities unchanged or introduces purely
in-memory, non-persisted state.

## App-lock preference (NEW — US4)

Two new keys in the existing `flutter_secure_storage` instance:

| Key | Type | Default | Notes |
|---|---|---|---|
| `app_lock_enabled` | `bool` | `false` | Whether Face ID (or passcode fallback) is required to open the app (FR-008). |
| `app_lock_grace_period_seconds` | `int` | `60` | Operator-selected grace period (Clarifications, 2026-08-14). Restricted to a small fixed set of choices at the UI level (research.md R5) — e.g. 0/30/60/300 — not a free-form number, though the stored value itself is a plain integer. |

Plus one **volatile, non-persisted** field held in app memory for the
lifetime of the process: the wall-clock timestamp of the last time the app
was foregrounded/authenticated, used only to compute whether the current
resume falls inside or outside the grace period (FR-009). This is
deliberately not persisted — a killed-and-relaunched app is always a cold
start, which already requires authentication regardless of any grace period
(Acceptance Scenario 2, User Story 4).

State transitions:

```
[unlocked, cold start, toggle off]  -> HomeShell shown immediately (unchanged today)
[unlocked, cold start, toggle on]   -> lock screen shown -> auth succeeds -> HomeShell shown, "last foregrounded" stamped
[unlocked, backgrounded < grace]    -> resume -> HomeShell shown immediately, no re-prompt
[unlocked, backgrounded >= grace]   -> resume -> lock screen shown -> auth succeeds -> HomeShell shown, "last foregrounded" re-stamped
[locked, auth fails/cancelled]      -> lock screen remains, no state change, no content exposed
```

## ColorScheme (light/dark) — US1

Not persisted data — a compile-time/runtime pair of `ColorScheme` values
derived from the existing single brand seed color (`lib/main.dart:64` today,
moving to `lib/theme.dart`). `themeMode: ThemeMode.system` means Flutter
itself, not this app, decides which of the two applies at any moment based
on the OS setting — no new field to track "which theme is active."

## ConversationTurn / EdgeMessage (EXISTING — US2, US6)

No schema change. Both entities already carry every field these two stories
need:

- `ConversationTurn.requestText` / `.answerText` — read (not written) by
  US2's selectable/copyable/shareable/markdown rendering and US6's search.
- `ConversationTurn.origin` (`'phone'` | `'watch'`) — already exists
  (spec 073), surfaced in UI for the first time by US6's origin filter chip.
- `ConversationTurn.acknowledged` / turn `state` — read by US6's state
  filter chips; US6 does not change how or when either field is written.
- `ConversationTurn.photoPath` — read by US2's share action, unchanged.

US2 adds exactly one new **derived, non-persisted** value per displayed
turn/message: the `looksLikeMarkdown(String text)` boolean (research.md R3),
computed on demand from `answerText`/message body at render time — not
stored anywhere, and (per Clarifications, 2026-08-14) computed only once the
turn reaches a terminal state, not on every partial update.

## Search/filter state (NEW, transient — US6)

Held entirely in each screen's own widget state, not in any store:

| Field | Type | Scope | Persisted? |
|---|---|---|---|
| query | `String` | Chat screen, Feed screen (separate instances) | No (FR-015) |
| selected state filters | `Set<TurnState>` | Chat screen only | No (FR-015) |
| selected origin filters | `Set<String>` (`'phone'`/`'watch'`) | Chat screen only | No (FR-015) |

Explicitly reset to empty on every fresh screen mount / app launch — there is
no "remember my last search" feature in this spec.

## Notification interruption level (US3)

Not a stored entity — a parameter passed at the moment a notification is
constructed (`DarwinNotificationDetails.interruptionLevel` /
`AndroidNotificationDetails.importance`/`.priority` in
`lib/ncfed/local_notifications.dart`). No new persisted preference; the
operator's own OS-level Focus/notification settings (outside this app
entirely) are what ultimately govern delivery, per spec.md's Assumptions.

## Dashboard tap-through callbacks (US7)

Not data at all — three new `VoidCallback` parameters on `DashboardScreen`
(`onOpenFeed`, `onOpenChat`, `onOpenApprovals`), wired at the call site in
`main.dart` to the existing `_selectTab`-style tab-switch logic
(research.md R7). `DashboardScreen` already receives `UnreadPendingSnapshot`
with `unreadFeed`/`unreadChat` broken out separately (`dashboard_data.dart`,
unchanged) — no new field needed to decide which callback a tap should
invoke.
