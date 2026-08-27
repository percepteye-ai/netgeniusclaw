# Implementation Plan: NetGeniusClaw Mobile Interactive and In-Flight Live Activity (B3)

**Branch**: `113-live-activity-interactive-inflight` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/113-live-activity-interactive-inflight/spec.md`

## Summary

Two related additions to the existing Lock Screen Live Activity infrastructure (spec 099). B3a: Approve/
Deny buttons on the pending-approval activity via a new `ApprovalActionIntent` (`LiveActivityIntent`,
iOS 17+) that foregrounds the app to Approvals through the existing `netgeniusclaw://` deep-link mechanism
(research.md R2) rather than resolving headlessly — preserving the spec-073 biometric-confirmation
invariant untouched. B3b: a new, per-question in-flight Live Activity (`AskActivityAttributes`) showing an
elapsed timer and the Border's existing free-text progress detail — deliberately never a fabricated member
count, after research found the brief's original `respondedMembers`/`expectedMembers` design describes a
concept that does not exist in the Border's actual sequential-delegation model (research.md R1). No
deployment-target change; the new interactive surface is gated by `if #available(iOS 17.0, *)`.

## Technical Context

**Language/Version**: Swift 5.0 (`ios/LiveActivityWidget/*.swift`, new + existing; `ios/Runner/LiveActivityBridge.swift`), Dart 3.x / Flutter (`lib/ncfed/live_activity.dart`, `lib/ncfed/conversation_store.dart`, `lib/ncfed/device_deep_link.dart`, `lib/screens/chat_screen.dart`) — same stack as specs 099/109–112, unchanged.
**Primary Dependencies**: None new for the app itself. `ActivityKit`'s `LiveActivityIntent` protocol (iOS 17+, system framework) and `Text(timerInterval:)` (system SwiftUI API) — both ship with the SDK. Build-time only: the `xcodeproj` Ruby gem (already available in this environment, already used for the identical class of problem in spec 071) to add the three new Swift files to the correct Xcode target(s) (research.md R5).
**Storage**: N/A — no new persisted state. `ConversationStore`'s two new callbacks (`onAdded`, `onTerminal`, research.md R4) are settable function references, exactly like the existing `onCompleted`, not stored data.
**Testing**: `flutter test` for `live_activity.dart`'s start/update/end sequencing against a fake `MethodChannel` (research.md R8, the spec's own flagged highest-risk area) and for the new `netgeniusclaw://approvals`/`netgeniusclaw://chat/<taskId>` deep-link parsing functions; `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` for the app-side Swift, and the `LiveActivityWidget` extension target's own compile (embedded in the `Runner` scheme build, matching how spec 112 verified `WatchComplication` via the `WatchApp` scheme rather than a standalone extension-scheme build, research.md R8/spec 112 precedent). Real Live Activity rendering, the interactive button's foreground behavior, and the ticking timer are 🔌 **DEVICE**-only.
**Target Platform**: iOS 16.2+ (existing `IPHONEOS_DEPLOYMENT_TARGET`, unchanged per FR-010/research.md R6) — the new interactive-button surface is itself gated to iOS 17+ at runtime.
**Project Type**: Mobile app (existing `mobile/netclaw-mobile/`, extending the existing `LiveActivityWidget` extension target established in spec 099) — no new Xcode target.
**Performance Goals**: FR-011's staleness bound is the only quantified constraint — the in-flight activity's `staleDate` matches the Border's own existing ask-timeout ceiling (research.md R7), not an arbitrary client-side guess.
**Constraints**: FR-009 — neither Live Activity type may ever block, delay, or degrade the underlying approval-resolution or ask/answer flow on failure to start/update (matches `live_activity.dart`'s existing best-effort try/catch). FR-006 — no member-count field, computed or displayed, anywhere in the in-flight activity.
**Scale/Scope**: Three new Swift files (`AskActivityAttributes.swift`, `AskLiveActivityView.swift`, `ApprovalActionIntent.swift`), three existing Swift files modified (`PendingApprovalActivityAttributes.swift` doc-comment only if needed, `PendingApprovalLiveActivityView.swift`, `LiveActivityBridge.swift`), one `project.pbxproj` edit (via `xcodeproj` gem, research.md R5). Four existing Dart files modified (`lib/ncfed/live_activity.dart`, `lib/ncfed/conversation_store.dart`, `lib/ncfed/device_deep_link.dart`, `lib/screens/chat_screen.dart`), one new Dart file if the in-flight activity's own start/update/end orchestration needs a dedicated home distinct from `chat_screen.dart` (decided at Phase 1/task-writing time based on how many call sites need to react to `ConversationStore`'s two new hooks — likely `lib/ncfed/ask_live_activity.dart`, mirroring `ask_border_headless.dart`'s naming convention from spec 111).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This is a mobile-app feature extending existing Lock Screen Live Activity infrastructure — no new MCP
server, skill, or device-automation capability. Evaluated the same way specs 066–112 were:

| Principle | Applicable? | Status |
|---|---|---|
| I–X (device automation, ITSM, MCP, observability) | No | N/A — no network-device automation or MCP tool added |
| XI. Full-Stack Artifact Coherence | No | N/A — that checklist (catalog.sh, install-steps.sh, HUD nodes, SOUL.md) governs new MCP servers/skills; this spec adds neither |
| XII. Documentation-as-Code | Yes | Satisfied — spec.md, research.md, data-model.md, quickstart.md all written in this change; README's platform-notes section updated at close with what was and was not device-verified |
| XIII. Credential Safety | Yes | Satisfied — no new credentials, no new entitlement; the existing biometric-confirmation invariant is reused, never weakened (research.md R2's whole point) |
| XIV. Human-in-the-Loop for External Communications | Yes | Satisfied — nothing in this spec sends external messages or creates tickets |
| XV. Backwards Compatibility | Yes | Satisfied — the approval activity's existing informational-only behavior is fully preserved on iOS below 17 (FR-002); the in-flight activity is entirely new/additive, no existing behavior changes shape |
| XVI. Spec-Driven Development | Yes | Satisfied — this plan follows `/speckit.specify` → `/speckit.plan`, in order, with no `[NEEDS CLARIFICATION]` markers and no implementation started first |
| XVII. Milestone Documentation via WordPress | Yes | Deferred to close-out, applies once both B3a and B3b are implemented, merged, and device-verified |

No violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/113-live-activity-interactive-inflight/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── checklists/
│   └── requirements.md   # Written during /speckit.specify
└── tasks.md               # Phase 2 output (/speckit.tasks — not yet created)
```

No `contracts/` directory: this spec adds no new Border-side wire method (unlike spec 111) — both pieces
are entirely local to the phone (Dart) and its existing Live Activity extension (Swift), consuming only
data the Border already sends (`n2n/edge/ask`'s existing `task_id`/`ask_result`/`task_progress`).

### Source Code (repository root)

```text
mobile/netclaw-mobile/
├── lib/
│   ├── ncfed/
│   │   ├── live_activity.dart          # gains update() + a second, per-task-id start/end pair (research.md R1/R4)
│   │   ├── conversation_store.dart     # gains onAdded, onTerminal callbacks (research.md R4)
│   │   ├── device_deep_link.dart       # gains netgeniusclaw://approvals + netgeniusclaw://chat/<taskId> parsing (research.md R2/R3)
│   │   └── ask_live_activity.dart      # NEW — wires ConversationStore.onAdded/onTerminal + EdgeAskClient.updates to LiveActivity's per-task start/update/end
│   └── screens/
│       └── chat_screen.dart            # wired to ask_live_activity.dart's orchestration (no direct LiveActivity calls added here)
├── ios/
│   ├── Runner/
│   │   ├── LiveActivityBridge.swift    # gains update() handling + per-task-id Activity<AskActivityAttributes> tracking
│   │   └── ApprovalActionIntent.swift  # NEW — LiveActivityIntent, iOS 17+, opens netgeniusclaw://approvals; DUAL membership (Runner + LiveActivityWidget, research.md R5) + IS_EXTENSION_TARGET compile guard around UIApplication.shared
│   └── LiveActivityWidget/
│       ├── PendingApprovalActivityAttributes.swift   # unchanged (dual-target membership already correct)
│       ├── PendingApprovalLiveActivityView.swift     # gains Approve/Deny Button(intent:) under if #available(iOS 17.0, *)
│       ├── AskActivityAttributes.swift               # NEW — dual membership (Runner + LiveActivityWidget), research.md R5
│       └── AskLiveActivityView.swift                 # NEW — LiveActivityWidget-only, added to WidgetBundle
└── test/
    ├── live_activity_test.dart              # NEW — start/update/end sequencing against a fake MethodChannel (research.md R8)
    └── device_deep_link_test.dart           # extended — netgeniusclaw://approvals + netgeniusclaw://chat/<taskId> parsing
```

**Structure Decision**: Every Swift addition lands inside the existing `Runner`/`LiveActivityWidget`
targets established by spec 099 — no new Xcode target. Every Dart addition follows the existing
`lib/ncfed/` convention (one file per bridge/concern) every prior mobile spec already used. The one new
Dart file, `ask_live_activity.dart`, exists because the in-flight activity's start/update/end orchestration
needs to react to `ConversationStore`'s two new hooks regardless of which of `chat_screen.dart`'s three
`addPending()` call sites (plus `main.dart`'s) triggered them — the exact same "single hook, not
duplicated wiring" reasoning that already justifies `onCompleted`'s own existence (research.md R4).
