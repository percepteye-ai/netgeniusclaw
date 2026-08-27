# Implementation Plan: iOS App Store Submission Readiness, Phase 1

**Branch**: `105-ios-appstore-readiness` | **Date**: 2026-08-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/105-ios-appstore-readiness/spec.md`

## Summary

Close three verified, concrete gaps between "the app works" and "the app is
ready to submit to Apple": (1) a first-launch explainer screen before the QR
scanner, so a stranger — human or Apple reviewer — understands this is a
companion app requiring a self-hosted NetGeniusClaw Border before they're handed a
camera; (2) an in-app, biometric-gated "Remove this device" control in
Settings, closing the Guideline 5.1.1(v) account-deletion gap that today
only Border-initiated revocation satisfies; (3) one real distribution-signed
build, produced and uploaded via the command line (not Xcode's GUI, which
caused every piece of friction encountered on this project so far), and
submitted to a TestFlight External Testing group. No new dependencies, no
new persisted data — see research.md and data-model.md.

## Technical Context

**Language/Version**: Dart 3.x / Flutter (SDK per `mobile/netclaw-mobile/pubspec.yaml`), Swift 5.0 (`ios/Runner/*.swift`) — same stack as specs 066–103, unchanged.
**Primary Dependencies**: None new. `local_auth` (already a dependency, already used by `approval_confirmation.dart`) covers US2's biometric gate. US1 is pure Flutter widget code. US3 uses Flutter's and Xcode's existing command-line toolchain (`flutter build ipa`, `xcrun altool`) — no package added.
**Storage**: No new storage. US1/US2 read/write the existing `EnrollmentStore` (`ncfed_enrollment.json`) exactly as today; nothing new is persisted.
**Testing**: `flutter test` (existing suite, 239 tests passing as of spec 103's close) — new widget/unit tests added for the explainer gating logic and the removal-confirmation flow, following the same patterns as `test/enrollment_screen_test.dart`-style existing coverage.
**Target Platform**: iOS 15+ / watchOS (existing `IPHONEOS_DEPLOYMENT_TARGET`/`WATCHOS_DEPLOYMENT_TARGET`, unchanged) — US3 additionally targets Apple's distribution/App Store Connect pipeline specifically, not just a physical device.
**Project Type**: Mobile app (existing `mobile/netclaw-mobile/`) — no new project, no new target.
**Performance Goals**: N/A — this spec is two UI screens and a one-time build/upload process, not a performance-sensitive path.
**Constraints**: US3's archive MUST succeed under distribution signing for every embedded target (Runner, WatchApp, WatchComplication, LiveActivityWidget) — see spec.md FR-007. The Clarifications session bounds US3's completion at "submitted for Beta App Review," not "review passed," since the latter is an external dependency outside this project's control.
**Scale/Scope**: Two new/modified screens (an explainer screen, one addition to Settings) plus a one-time manual build/upload procedure. Not a recurring pipeline in this phase (research.md R5 explicitly defers CI/fastlane-style automation).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This is a mobile-app UI/tooling feature with no new MCP server, skill, or
network-automation capability — the majority of `.specify/memory/
constitution.md`'s principles (I–X, safety/ITSM/GAIT/MCP/vendor-neutrality/
observability) govern device-automation capabilities and do not apply here,
consistent with how every prior mobile spec (066–103) has been evaluated.

| Principle | Applicable? | Status |
|---|---|---|
| I–X (device automation, ITSM, MCP, observability) | No | N/A — no device automation or MCP capability added |
| XI. Full-Stack Artifact Coherence | No | N/A — that principle's checklist (catalog.sh, install-steps.sh, HUD nodes, SOUL.md) governs new MCP servers/skills; this spec adds neither |
| XII. Documentation-as-Code | Yes | Satisfied — spec.md, research.md, data-model.md, quickstart.md all written in this same change; no follow-up doc PR needed |
| XIII. Credential Safety | Yes | Satisfied — the App Store Connect API key (research.md R4) is a local credential passed to `xcrun altool` at invocation time, never committed; `GoogleService-Info.plist`-style gitignore precedent already established in this same mobile project |
| XIV. Human-in-the-Loop for External Communications | Yes | Satisfied — inviting a TestFlight tester and submitting for Beta App Review are both explicit, operator-initiated actions in this plan, not autonomous ones |
| XV. Backwards Compatibility | Yes | Satisfied — US1/US2 are additive (a new screen shown only pre-enrollment; a new Settings control); no existing relay method, wire contract, or stored-data shape changes |
| XVI. Spec-Driven Development | Yes | Satisfied — this plan is the direct output of `/speckit.specify` → `/speckit.clarify` → `/speckit.plan`, in order, with no implementation started first |
| XVII. Milestone Documentation via WordPress | Yes | Deferred to close-out, not this planning step — applies once US1–US3 are implemented and merged, per the principle's own "at completion of a milestone" trigger |

No violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/105-ios-appstore-readiness/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── checklists/
│   └── requirements.md   # Written during /speckit.specify
└── tasks.md               # Phase 2 output (/speckit.tasks — not yet created)
```

No `contracts/` directory: this spec adds no new wire protocol, RPC method,
or external interface (unlike spec 103's `watch/heartbeat/latest`). US1/US2
are self-contained UI changes against existing local state; US3 is a build/
upload procedure against Apple's own, unmodified App Store Connect API.

### Source Code (repository root)

Existing Flutter/iOS mobile app structure — no new top-level directories:

```text
mobile/netclaw-mobile/
├── lib/
│   ├── main.dart                      # EnrollmentGate — insert US1's explainer step here
│   ├── ncfed/
│   │   ├── enrollment_store.dart      # EnrollmentStore.clear() — reused as-is by US2
│   │   └── approval_confirmation.dart # biometric pattern — reused by US2 (research.md R2)
│   └── screens/
│       ├── enrollment_screen.dart     # existing QR-scan screen — unchanged, shown AFTER the new explainer
│       ├── onboarding_explainer_screen.dart  # NEW (US1)
│       └── settings_screen.dart       # add "Remove this device" control here (US2)
├── test/
│   ├── onboarding_explainer_screen_test.dart  # NEW
│   └── settings_screen_test.dart              # extended, or new if none exists yet
└── ios/
    └── ExportOptions.plist            # NEW (US3) — checked in once, generated per quickstart.md
```

**Structure Decision**: Everything lands inside the existing
`mobile/netclaw-mobile/` project, following the exact file-organization
convention every prior mobile spec (066–103) already used (`lib/screens/`
for UI, `lib/ncfed/` for shared client logic, `test/` mirroring `lib/`
one-to-one). No new project, package, or top-level directory.
