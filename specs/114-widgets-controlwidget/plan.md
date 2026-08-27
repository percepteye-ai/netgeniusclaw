# Implementation Plan: NetGeniusClaw Mobile Home Screen, Lock Screen, and Control Center Widgets (B1b+B2)

**Branch**: `114-widgets-controlwidget` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/114-widgets-controlwidget/spec.md`

## Summary

A phone-side `WidgetDataStore` (dual `Runner`/`NetClawWidgetExtension` membership) mirrors Border health,
pending-approval count, and unread-feed count into a new phone-only App Group — the exact pattern
`HeartbeatStatusStore`/`PendingApprovalCountStore` already prove out on the watch side (research.md R1).
Home-screen (`systemSmall`/`systemMedium`) and Lock Screen (`accessoryCircular`/`accessoryRectangular`/
`accessoryInline`) widgets read that store, always showing a reading's age, never per-approval detail. The
Control Center control shows the same cached pending count (research.md R5) and, on tap, foregrounds Chat
via the existing `openAppWhenRun`+`netgeniusclaw://` deep-link pattern — corrected during planning from the
brief's original "invoke AskBorderIntent directly" framing, which doesn't hold up against that intent's
actual required `question: String` parameter (research.md R2). The `NetClawWidgetExtension` target's own
real setup defects (wrong embedding, wrong bundle id, wrong App Group, missing iOS 18 floor) were already
found and fixed in this branch's setup commit, prior to this plan.

## Technical Context

**Language/Version**: Swift 5.0 (`ios/NetClawWidget/*.swift`, rewriting Xcode's placeholder template content; `ios/Runner/WidgetDataStore.swift`, `ios/Runner/WidgetBridgePlugin.swift`, new), Dart 3.x / Flutter (`lib/ncfed/widget_data.dart`, new; `lib/ncfed/device_deep_link.dart`, extended) — same stack as specs 099/109–113, unchanged.
**Primary Dependencies**: None new. `WidgetKit`'s `ControlWidget`/`AppIntentControlConfiguration` (iOS 18+, system framework, already the reason `NetClawWidgetExtension`'s deployment target was bumped in this branch's setup commit) and `WidgetCenter` (system framework) ship with the SDK.
**Storage**: One new App Group `UserDefaults` store (`group.ca.automateyournetwork.netclaw.mobile.ios`, already registered by the operator) — three keys (health summary/pushedAt/isAlarm, pending count, unread count), mirroring three values that already exist elsewhere on the phone (`DeviceHeartbeatStore`, `ApprovalClient.pending`, `MessageFeedStore.unreadCount`); no new source of truth.
**Testing**: `flutter test` for `widget_data.dart`'s event-to-`WidgetBridgePlugin`-call wiring against a fake `MethodChannel` (research.md R7) and for the two new `netgeniusclaw://dashboard`/`netgeniusclaw://chat` deep-link parsers; `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` for the native side (embeds `NetClawWidgetExtension`, already confirmed working in this branch's setup commit). Real widget/Control Center placement and rendering are 🔌 **DEVICE**-only.
**Target Platform**: iOS 16.2+ for `Runner` (unchanged, FR-010); iOS 18.0 for `NetClawWidgetExtension` specifically (already set in this branch's setup commit, operator-authorized).
**Project Type**: Mobile app (existing `mobile/netclaw-mobile/`), extending the `NetClawWidgetExtension` target the operator already created — no new Xcode target (FR-009).
**Performance Goals**: N/A beyond FR-004's staleness-labeling requirement — no throughput target, since widget/control refresh timing is entirely iOS-budgeted and explicitly not something this spec can or should try to control tightly (research.md R4).
**Constraints**: FR-005 — no per-approval detail in any widget family, matching the existing Live Activity restriction. FR-006 — reuse the existing `netgeniusclaw://` mechanism, no second navigation system. FR-007 — every store's `read()` must distinguish "never written" from a real zero/empty value.
**Scale/Scope**: Two new Swift files (`WidgetDataStore.swift` dual-membership, `WidgetBridgePlugin.swift` Runner-only), three existing Swift files in `NetClawWidget/` rewritten in place (`NetClawWidget.swift`, `NetClawWidgetControl.swift`, `AppIntent.swift` — no gem surgery needed for these, per research.md R6's synchronized-group finding). One new Dart file (`widget_data.dart`), one existing Dart file extended (`device_deep_link.dart`), one existing Dart file wired (`main.dart`, following the exact same "wire once at the `_HomeShellState` level" pattern as `ask_live_activity.dart`/the approval Live Activity listener).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This is a mobile-app feature adding a widget extension's real content to a target the operator already
created via Xcode's own wizard — no new MCP server, skill, or device-automation capability. Evaluated the
same way specs 066–113 were:

| Principle | Applicable? | Status |
|---|---|---|
| I–X (device automation, ITSM, MCP, observability) | No | N/A — no network-device automation or MCP tool added |
| XI. Full-Stack Artifact Coherence | No | N/A — that checklist governs new MCP servers/skills; this spec adds neither |
| XII. Documentation-as-Code | Yes | Satisfied — spec.md, research.md, data-model.md, quickstart.md all written in this change; README's platform-notes section updated at close |
| XIII. Credential Safety | Yes | Satisfied — the one new App Group is local, on-device shared storage, not a credential; already registered by the operator before this plan was written |
| XIV. Human-in-the-Loop for External Communications | Yes | Satisfied — nothing in this spec sends external messages or creates tickets |
| XV. Backwards Compatibility | Yes | Satisfied — `Runner`'s and `WatchApp`'s own deployment targets are unchanged (FR-010); this is a purely additive new surface |
| XVI. Spec-Driven Development | Yes | Satisfied — this plan follows `/speckit.specify` → `/speckit.plan`, in order, with one real design correction (R2) made during planning, before implementation, not after |
| XVII. Milestone Documentation via WordPress | Yes | Deferred to close-out, applies once B1b+B2 are implemented, merged, and device-verified |

No violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/114-widgets-controlwidget/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── checklists/
│   └── requirements.md   # Written during /speckit.specify
└── tasks.md               # Phase 2 output (/speckit.tasks — not yet created)
```

No `contracts/` directory: no new Border-side wire method — everything this spec needs already exists on
the phone (`DeviceHeartbeatStore`, `ApprovalClient`, `MessageFeedStore`).

### Source Code (repository root)

```text
mobile/netclaw-mobile/
├── lib/
│   ├── ncfed/
│   │   ├── widget_data.dart          # NEW — wires DeviceHeartbeatStore/ApprovalClient.pending/MessageFeedStore.unreadCount to WidgetBridgePlugin
│   │   └── device_deep_link.dart     # gains netgeniusclaw://dashboard + netgeniusclaw://chat parsing (research.md R3)
│   └── main.dart                     # wires widget_data.dart's orchestration once, alongside the existing approval/ask Live Activity listeners
├── ios/
│   ├── Runner/
│   │   ├── WidgetDataStore.swift     # NEW — dual membership (Runner + NetClawWidgetExtension), research.md R1/R6
│   │   └── WidgetBridgePlugin.swift  # NEW — Runner-only, FlutterPlugin exposing WidgetDataStore.write(...) + reloadAllTimelines()
│   └── ../NetClawWidgetExtension.entitlements  # already correct (this branch's setup commit)
└── ios/NetClawWidget/                # already exists (operator-created); Xcode's synchronized group needs no manual pbxproj edit for files rewritten in place (research.md R6)
    ├── AppIntent.swift               # REWRITTEN — placeholder ConfigurationAppIntent replaced with the new
    │                                 #   openAppWhenRun Chat-deep-link intent (research.md R2)
    ├── NetClawWidget.swift           # REWRITTEN — placeholder "favorite emoji" replaced with real
    │                                 #   TimelineProvider reading WidgetDataStore, all required WidgetFamily cases
    └── NetClawWidgetControl.swift    # REWRITTEN — placeholder "timer" replaced with a real ControlWidget
                                      #   reading WidgetDataStore's pending count, action from AppIntent.swift
```

**Structure Decision**: Every Swift addition lands inside the existing `Runner` target or the already-
operator-created `NetClawWidgetExtension` target — no new Xcode target (FR-009). Dart additions follow the
existing `lib/ncfed/` convention every prior mobile spec already used. `NetClawWidget/`'s three placeholder
files are rewritten in place, not deleted and recreated, since Xcode's synchronized group already tracks
that directory correctly (research.md R6) — no manual target-membership step needed for edits to files that
already exist there.
