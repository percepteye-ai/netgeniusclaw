# Data Model: NetGeniusClaw Mobile Siri Reliability Fix + Two-Way Voice + Theme Toggle (Pass 1 of 3)

No new database, no new document schema. One new persisted preference value.

## AppearancePreference (new)

A single stored value representing the operator's explicit appearance choice.

| Field | Type | Values | Notes |
|-------|------|--------|-------|
| `mode` | enum-as-string | `"system"` \| `"light"` \| `"dark"` | Default `"system"` if never set (preserves today's behavior for operators who never touch the new control). |

- **Persistence**: `flutter_secure_storage`, one key, mirroring `AppLockPreference`'s existing
  shape exactly (research.md R6).
- **Lifecycle**: Read once at app startup into an in-memory `ValueNotifier<ThemeMode>`; written
  whenever the operator changes the Settings control. No migration needed (new key, no prior
  value to interpret).

## Conversation Turn (existing — no schema change)

Already defined by `ConversationStore`/`turn_reconciler.dart` prior to this spec. This feature
does not add fields; it only guarantees (FR-007) that a turn answered via the new fast-voice path
is recorded through the exact same `store.updateState(...)` call the existing slow/notify path
already uses, so no dual-write or divergent-shape risk is introduced.

## Voice/Shortcuts Action Invocation (conceptual — not a stored entity)

Not persisted. Exists only as the on-device diagnostic evidence trail used to verify this
feature (native+Dart diagnostic log files, pulled `.ips` crash reports, Border-side mesh logs) —
described in quickstart.md, not modeled as application data.
