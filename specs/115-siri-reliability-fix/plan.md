# Implementation Plan: NetGeniusClaw Mobile Siri Reliability Fix + Two-Way Voice + Theme Toggle (Pass 1 of 3)

**Branch**: `115-siri-reliability-fix` | **Date**: 2026-08-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/115-siri-reliability-fix/spec.md`

## Summary

Three real, on-device-confirmed root causes made every Siri/Shortcuts action into NetGeniusClaw
(`AskBorderIntent`, `PendingApprovalsIntent`, `BorderHealthIntent`) silently no-op on any fresh
release build: (1) their headless Dart entrypoint files were never imported from `lib/main.dart`'s
reachable graph, so Flutter's AOT compiler never included them in the binary at all despite
`@pragma('vm:entry-point')`; (2) `HeadlessEngineRunner` registered every app plugin — including
Firebase Core/Messaging — into a second `FlutterEngine` alongside the still-alive main engine,
deadlocking the main thread during a background-scene transition and triggering a real
watchdog `SIGKILL` (`0x8BADF00D`); (3) after switching to `FlutterEngineGroup` to fix (2),
`makeEngine(withEntrypoint:libraryURI:)` was called with `libraryURI: nil`, which silently fails
to resolve any entrypoint defined outside `lib/main.dart` — confirmed via an on-disk diagnostic
log showing the native Swift side completing every step while the Dart entrypoint never executed
a single line. All three are already fixed, committed, and verified end-to-end on a real device.

This plan formalizes that work and completes Pass 1's two remaining new items: stripping
markdown from any answer text handed to Siri to speak (the two-way-voice fast path already
returns real answer text verbatim, unstripped), and adding a manual Light/Dark/System appearance
toggle in Settings — plus removing the temporary diagnostic logging added while chasing (1)-(3).

## Technical Context

**Language/Version**: Dart 3.x / Flutter (SDK `^3.12.2` per `pubspec.yaml`); Swift 5.0 (`ios/Runner/*.swift`) — same stack as specs 066–114, unchanged.
**Primary Dependencies**: No new dependencies. Reuses `AppIntents` (iOS 16+ system framework, already in place from spec 111), `FlutterEngineGroup` (Flutter SDK, already available, previously unused in this codebase), `flutter_secure_storage` (already a dependency, used for the new theme preference exactly as specs 109/110 already use it for other settings).
**Storage**: `flutter_secure_storage` gains one new key (theme preference: `system` | `light` | `dark`). No other new persisted state — conversation-turn recording reuses the existing `ConversationStore` exactly as today.
**Testing**: `flutter test` (existing `ask_border_headless_test.dart`, `border_health_headless_test.dart`, `pending_approvals_headless_test.dart` suites — the ask-border suite already has 7/7 passing including a new two-way-voice test written during tonight's live session); manual 🔌 DEVICE verification is mandatory for this feature since the entire bug class only reproduces on real hardware (confirmed: Simulator/`flutter run` debug builds cannot exercise `openAppWhenRun: false` App Intents reliably, and the Secure Enclave identity plugin is unavailable off-device).
**Target Platform**: iOS 16+ (existing `AppIntents` deployment floor from spec 111), verified this session against a real device on iOS 26.6.
**Project Type**: Mobile app (`mobile/netclaw-mobile/`), existing structure, no new targets.
**Performance Goals**: The two-way-voice fast-response window must be long enough to catch a realistically-fast Border answer, short enough that Siri does not abandon the whole request first — tuned empirically this session to 18s against this device's observed behavior (12s round-tripped correctly but caught few real answers in practice; the prior default of "wait forever" reliably caused Siri to fall back to a web search).
**Constraints**: No entitlement changes (confirmed unnecessary and risky this session — `AppIntents`/`AppShortcutsProvider` need no Siri capability, unlike legacy SiriKit). No new Xcode targets. Must not regress the already-shipped, already-verified spec 111 behavior for the slow/fallback path.
**Scale/Scope**: Three existing Swift Intent files, three existing Dart headless entrypoint files, one existing Settings screen, one existing theme provider — all touched, none newly created except test additions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle VIII (Verify After Every Change)**: Satisfied by construction — every fix in this
  plan was arrived at via baseline → apply → verify on a real, connected device this session
  (pulled `.ips` crash reports, on-disk diagnostic logs, and Border-side mesh logs as
  verification evidence, not just "build succeeded"). Task list requires a repeat 🔌 DEVICE pass
  once markdown-stripping and the theme toggle land.
- **Principle XII (Documentation-as-Code)**: Satisfied — this spec/plan/tasks trail *is* the
  documentation of tonight's findings, replacing what would otherwise be undocumented tribal
  knowledge from an ad-hoc debugging session.
- **Principle XVI (Spec-Driven Development)**: This is Pass 1 of an explicitly-scoped 3-pass
  plan; Pass 2 (Border-side Siri-tagged-request handling) and Pass 3 (final cross-host
  verification) are out of scope here by design and will be their own specs.
- **Principle XVII (Milestone Documentation via WordPress)**: A blog post draft is owed once
  Pass 1 merges — noted as a closing task, not blocking implementation.
- No other principle applies: this feature touches no network device, no ITSM/CR workflow, no
  new MCP server, and no credential handling. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/115-siri-reliability-fix/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
mobile/netclaw-mobile/
├── lib/
│   ├── main.dart                              # already fixed: imports the 3 headless entrypoints
│   ├── theme.dart                              # extend: read persisted appearance preference
│   ├── screens/settings_screen.dart            # extend: add Light/Dark/System control
│   └── ncfed/
│       ├── ask_border_headless.dart            # already fixed + two-way voice; add markdown-strip
│       ├── border_health_headless.dart         # already fixed; remove temporary bh_diag.log calls
│       ├── pending_approvals_headless.dart     # same fix pattern applies (untouched code, verify)
│       └── theme_preference.dart               # NEW: small persisted-preference helper
├── ios/Runner/
│   ├── HeadlessEngineRunner.swift              # already fixed (FlutterEngineGroup); remove diagLog()
│   ├── AskBorderIntent.swift                   # already fixed (libraryURI)
│   ├── BorderHealthIntent.swift                # already fixed (libraryURI)
│   └── PendingApprovalsIntent.swift            # already fixed (libraryURI)
└── test/
    ├── ask_border_headless_test.dart           # already updated, 7/7 passing
    └── theme_preference_test.dart              # NEW
```

**Structure Decision**: No new directories or targets. All work lands inside the existing
`mobile/netclaw-mobile/` app, following the exact file-per-concern layout specs 066-114 already
established (one Dart file per headless entrypoint, one Swift file per Intent, a small dedicated
helper file for the new theme preference rather than growing `theme.dart` or `settings_screen.dart`
with ad-hoc inline logic).

## Complexity Tracking

*No constitution violations — table intentionally omitted.*
