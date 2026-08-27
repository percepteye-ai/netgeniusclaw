# Data Model: iOS App Store Submission Readiness, Phase 1

This spec introduces no new persisted entity and no new fields on an
existing one. It is documented here for completeness, per spec.md's Key
Entities section.

## Enrollment (existing — `StoredEnrollment` / `EnrollmentStore`)

No schema change. This spec adds a new way for the *lifecycle* of an
enrollment to end (operator-initiated, local-only) alongside the two that
already exist:

| Lifecycle end | Trigger | Initiated by | Existing/new |
|---|---|---|---|
| Border-side rejection on reconnect (`-32023`) | Border no longer trusts this device's pinned key | Border | Existing (`main.dart:121`) |
| Border-side revocation mid-session | Operator removed the member Border-side | Border | Existing (`main.dart:672`, `_handleRevoked`) |
| **Operator-initiated removal (this spec)** | Operator taps "Remove this device" in Settings and completes biometric re-auth | Phone, local-only | **New (US2)** |

All three converge on the same effect: `EnrollmentStore.clear()`, followed by
`EnrollmentGate` returning to its unenrolled state. This spec's new path is
purely additive — it does not change what happens when the existing two
paths fire.

## First-launch explainer state (US1)

Not a new persisted entity. Whether the explainer screen shows is fully
derived from the existing `EnrollmentStore.load()` result being `null` (per
research.md R1) — there is no new flag, table, or file to track "has this
device seen the explainer." This is a deliberate consequence of the
Clarifications/edge-case decision that the explainer is tied to enrollment
state, not to a one-time-ever "seen it" marker.

## Distribution build / TestFlight group (US3)

Neither is app-persisted state — both live entirely in Apple's App Store
Connect, external to this codebase. Nothing in `mobile/netclaw-mobile/` reads
or writes anything about which builds exist or which testers are in a group;
this spec's User Story 3 is a one-time operational/tooling activity (research
R3/R4), not a new data model.
