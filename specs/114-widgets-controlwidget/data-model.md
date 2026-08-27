# Data Model: NetGeniusClaw Mobile Home Screen, Lock Screen, and Control Center Widgets (B1b+B2)

No new source of truth. Every value mirrored here already exists elsewhere on the phone; this spec adds
only a cross-process mirror and the widget/control surfaces that read it.

## `WidgetDataStore` (new, App Group `UserDefaults`)

| Key | Type | Mirrors | Notes |
|---|---|---|---|
| `borderHealthSummary` | `String` | `DeviceHeartbeatStatus.summary` | Same free-text summary `BorderHealthIntent` (spec 111) already speaks. |
| `borderHealthPushedAt` | `Double` (epoch seconds) | `DeviceHeartbeatStatus.pushedAt` | Feeds every widget's age display (FR-004). |
| `borderHealthIsAlarm` | `Bool` | `DeviceHeartbeatStatus.isAlarm` | Same distinction the watch complications already render. |
| `pendingApprovalCount` | `Int` | `ApprovalClient.pending`'s latest emission's `.length` | Read by the home-screen widget, the Lock Screen widget, and the Control Center control's value provider (research.md R5) — one value, three readers. |
| `unreadFeedCount` | `Int` | `MessageFeedStore.unreadCount` | Home-screen widget only, per spec.md's User Stories (Lock Screen/Control Center scope is health + pending count). |

`read()` for the health fields returns `nil` (not a zero-valued struct) when `borderHealthPushedAt` was
never written — the same "no data yet" distinction `HeartbeatStatusStore`/`BorderHealthIntent` already
make, satisfying FR-007. `pendingApprovalCount`/`unreadFeedCount` default to `0` on first read, which is
already an honest value (zero pending approvals is a real, valid state — unlike "no heartbeat ever
received," there is no ambiguous zero case for a count).

## `WidgetBridgePlugin` (new, `FlutterPlugin`, `Runner`-only)

Method channel `ca.automateyournetwork.netclaw/widget_data`, mirroring `LiveActivityBridge`'s shape:

| Method | Arguments | Effect |
|---|---|---|
| `writeHealth` | `{summary, pushedAt, isAlarm}` | `WidgetDataStore.write(health:)` + `WidgetCenter.shared.reloadAllTimelines()` |
| `writePendingCount` | `{count}` | `WidgetDataStore.write(pendingCount:)` + `reloadAllTimelines()` |
| `writeUnreadCount` | `{count}` | `WidgetDataStore.write(unreadCount:)` + `reloadAllTimelines()` |

## `widget_data.dart` (new, Dart)

A small set of pure mirror functions (`mirrorHealth(DeviceHeartbeatStatus)`, `mirrorPendingCount(int)`,
`mirrorUnreadCount(int)`), each just calling the matching `WidgetBridgePlugin` method — no new
stream/callback of its own. Three existing call sites in `main.dart`, confirmed directly (no new hook
needed on any store):

| Value | Existing call site | Fires |
|---|---|---|
| Border health | `main.dart`'s `wireMessageFeed(...)`'s `onMessage` branch, right where `looksLikeDeviceHeartbeat(message)` is already true and `DeviceHeartbeatStore(dir).save(...)` already runs | Every real heartbeat |
| Pending count | `main.dart`'s existing `approvalClient.pending.listen((pending) { ... })` block (the same one spec 113 already extended for the Live Activity) | Every pending-list change |
| Unread count | `main.dart`'s existing `_recomputeBadge()` (already called "on every new arrival... and every acknowledge/delete," per its own doc comment) | Every point unread count could change |

## `netgeniusclaw://` deep-link shapes (existing scheme, two new shapes)

| Shape | Parsed by | Resolves to |
|---|---|---|
| `netgeniusclaw://dashboard` | New sibling function in `device_deep_link.dart` | `_selectTab(0)` (Dashboard) |
| `netgeniusclaw://chat` (no path segment) | New sibling function, distinguished from the existing `netgeniusclaw://chat/<taskId>` by an empty path | Opens Chat with no specific turn highlighted — just the tab, compose field ready |

## `NetClawWidget` / `NetClawWidgetControl` (existing scaffolding, rewritten — no new type)

`NetClawWidgetEntryView` (home screen: `.systemSmall`/`.systemMedium`) and new Lock Screen views
(`.accessoryCircular`/`.accessoryRectangular`/`.accessoryInline`) all render from the same
`WidgetDataStore.read()` call — one `TimelineProvider`, `supportedFamilies` covering all five. No
per-family data shape difference; only layout differs, exactly like `HeartbeatComplication`'s existing
one-view-many-families pattern (spec 112 research.md R4).

`NetClawWidgetControl`'s `AppIntentControlValueProvider.currentValue(configuration:)` returns
`WidgetDataStore.read().pendingCount` — no `configuration` parameter is meaningfully used (no
per-instance customization this spec needs), and its action intent is the new Chat-deep-link `AppIntent`
(research.md R2), not `AskBorderIntent`.
