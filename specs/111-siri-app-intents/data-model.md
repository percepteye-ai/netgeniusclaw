# Data Model: NetGeniusClaw Mobile Siri / App Intents Integration (B1a)

No new persisted store. Every entity below either extends an existing one by one value, or is a new
in-memory/wire-only shape that lives for the duration of a single headless invocation and is discarded.

## ConversationTurn (EXISTING — one new `origin` value)

No schema change to the file format `ConversationStore` already writes. `origin` (`lib/ncfed/
conversation_store.dart:22`, a plain `String`, default `'phone'` on a missing key) gains a third valid
value, `'siri'`, written by the new `ask_border_headless.dart` entrypoint exactly the way `origin: 'watch'`
is already written today for the paired Watch app (spec 073). Existing readers that only know `'phone'`/
`'watch'` are unaffected — they already treat `origin` as an opaque display string, not a closed enum
enforced at the type level (research.md R5).

| Field | Type | Change |
|---|---|---|
| `origin` | `String` | Gains `'siri'` as a third value alongside existing `'phone'`/`'watch'` |

## AppIntent invocation (NEW — Swift, not persisted)

Three `AppIntent` structs, each a thin value type with no stored properties beyond the parameters App
Intents itself manages:

| Intent | Parameters | Result |
|---|---|---|
| `AskBorderIntent` | `question: String` (free text, `@Parameter`) | `some IntentResult & ProvidesDialog` — a brief spoken acknowledgment |
| `PendingApprovalsIntent` | none | `some IntentResult & ProvidesDialog` — the live count, spoken |
| `BorderHealthIntent` | none | `some IntentResult & ProvidesDialog` — the cached heartbeat summary + age, spoken |

`AppShortcutsProvider` (`NetClawShortcuts.swift`, new) is a static, compile-time phrase table mapping each
intent to one or more natural-language phrases — it holds no runtime state of its own.

## Headless engine session (NEW — Dart, in-memory only, one per invocation)

Each of the three new `@pragma('vm:entry-point')` entrypoints constructs its own object graph from scratch
(no shared state across invocations, no shared state with a foreground app instance, per research.md R1/
Edge Cases) and discards it once the `FlutterMethodChannel` result is sent:

| Entrypoint | Objects constructed | Lives until |
|---|---|---|
| `askBorderMain` | `EdgeClient`, `EdgeAskClient`, `ConversationStore`, `LocalNotifications` | The `ask_result` is persisted + notification posted, or FR-008's bound is hit |
| `pendingApprovalsMain` | `EdgeClient` | The `approvals_list` response is spoken, or FR-008's bound is hit |
| `borderHealthMain` | `EdgeClient`, `DeviceHeartbeatStore` | The cached summary is spoken, or FR-008's bound is hit |

None of these three sessions is itself a durable entity — nothing about "a Siri ask happened" is queryable
after the fact except through the one persisted side effect each already produces on success (a
`ConversationTurn` for `AskBorderIntent`; nothing at all for the other two, which are pure reads).

## `n2n/edge/approvals_list` (NEW — Border-side wire method)

The one genuinely new interface this spec adds. Mirrors the existing `n2n/edge/approval_resolve`
(spec 068) in shape and location (`bgp/federation/edge.py`'s method allowlist, a handler in
`bgp/federation/service.py`), wired to the existing, unmodified `Authorizer.pending_approvals()`
(`bgp/federation/authorization.py:176-181`).

**Request**: `{}` (no parameters — scope is risk-wide, matching how approvals are already delivered to a
single admin-operated edge member per risk, research.md R3).

**Response**: `{"count": <int>}` — deliberately minimal, since FR-006 only requires a spoken count, not a
list of individual approvals (no need to expose `remote_invocation_record` details to a voice intent that
can't act on them anyway).

**Auth**: Identical to every other `n2n/edge/*` method — the calling member's channel is already
authenticated at connect time (pinned-key challenge/response, unchanged); no new authorization check is
introduced.

## DeviceHeartbeatStatus / DeviceHeartbeatStore (EXISTING — read-only for this spec)

No change. `BorderHealthIntent` reads `DeviceHeartbeatStore.load()` (`lib/ncfed/device_heartbeat.dart:68-85`)
exactly as the Dashboard/Feed screens already do, and reuses the existing pure `heartbeatSummary()`/
`heartbeatIsAlarm()` functions unchanged. The only new derived value is the spoken phrasing that folds in
`pushedAt`'s age (e.g. "As of 4 minutes ago: ...") — computed at speak-time, not stored.
