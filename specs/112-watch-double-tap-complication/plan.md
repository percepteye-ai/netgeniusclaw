# Implementation Plan: NetGeniusClaw Mobile Watch Double Tap and Corner Complication (B4+B5)

**Branch**: `112-watch-double-tap-complication` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/112-watch-double-tap-complication/spec.md`

## Summary

Two small, additive watch-only changes bundled per the brief's own suggested ordering. B4: Double Tap
(Series 9/Ultra 2+, watchOS 11+) triggers the exact same passcode-gated "Approve" action the topmost
pending approval's existing button already calls (research.md R1/R2), gated by a runtime availability
check rather than a deployment-target bump so watches below watchOS 11 are unaffected (research.md R3);
the same treatment is applied to the low-stakes "Read aloud" button in the Ask view. B5: both existing
watch complications (`HeartbeatComplication`, `PendingApprovalComplication`) gain `.accessoryCorner`
support — a one-line addition each, since their existing shared view already renders in the shape that
family expects (research.md R4). No new Xcode target, no new entitlement, no Dart code touched at all.

## Technical Context

**Language/Version**: Swift 5.0 (`ios/WatchApp Watch App/ApprovalsView.swift`, `AskView.swift`; `ios/WatchComplication/HeartbeatComplication.swift`, `PendingApprovalComplication.swift`) — same stack as specs 072/099, unchanged. No Dart/Flutter changes in this spec.
**Primary Dependencies**: None new. `SwiftUI`'s `handGestureShortcut(_:)` (watchOS 11+, system framework) and `WidgetKit`'s `.accessoryCorner` `WidgetFamily` case (watchOS 9+, system framework) — both ship with the SDK, not package dependencies.
**Storage**: N/A — neither item reads or writes any new state. Both complications continue reading `HeartbeatStatusStore`/`PendingApprovalCountStore` exactly as today.
**Testing**: No automated test added (research.md R5) — no `XCTest` target exists for watch SwiftUI views in this repo today, matching spec 072's own established, real-hardware-only verification convention. `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme WatchApp -sdk watchsimulator -configuration Debug build CODE_SIGNING_ALLOWED=NO` is the compile-verification vehicle for BOTH targets: `WatchApp` embeds and builds `WatchComplication.appex` as part of the same scheme (confirmed in this spec's own implementation), so a separate standalone `-scheme WatchComplication -sdk watchsimulator` invocation is unnecessary — and, confirmed via a clean `git stash` check, that standalone invocation fails on completely unmodified code too, hitting the exact same "cross-SDK build trap" README's spec 072 entry already documents (`-sdk` as a blunt flag forces every workspace target, including phone-only plugins like `mobile_scanner`/`local_auth_darwin` with no watchOS platform support at all, onto the watch SDK). `flutter analyze`/`flutter test` re-run only as a regression guard, since neither is expected to change (no Dart code touched). Real gesture/complication behavior is 🔌 **DEVICE**-only (Series 9/Ultra 2+ physical watch — Double Tap is a hardware-gated system gesture, unavailable in the Simulator).
**Target Platform**: watchOS 10.0+ (existing `WATCHOS_DEPLOYMENT_TARGET`, unchanged per FR-006/research.md R3) — the new Double Tap surface is itself gated to watchOS 11+ at runtime, not at the deployment-target level.
**Project Type**: Mobile app, watch companion (existing `mobile/netclaw-mobile/ios/WatchApp Watch App/` and `ios/WatchComplication/`) — no new target, no new project.
**Performance Goals**: N/A — both changes are static view/configuration wiring, not throughput-sensitive.
**Constraints**: FR-002 — exactly one control (the topmost approval's Approve button) may claim `.handGestureShortcut(.primaryAction)` at any given render; claiming it on more than one control silently disables Double Tap entirely (research.md R2). FR-006 — no `WATCHOS_DEPLOYMENT_TARGET` change.
**Scale/Scope**: Two existing files modified for B4 (`ApprovalsView.swift`, `AskView.swift`), two existing files modified for B5 (`HeartbeatComplication.swift`, `PendingApprovalComplication.swift`) — four files total, zero new files, zero Dart changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This is a small watch-app UI/UX feature with no new MCP server, skill, or device-automation capability —
evaluated the same way specs 066–111 were:

| Principle | Applicable? | Status |
|---|---|---|
| I–X (device automation, ITSM, MCP, observability) | No | N/A — no network-device automation or MCP tool added |
| XI. Full-Stack Artifact Coherence | No | N/A — that checklist (catalog.sh, install-steps.sh, HUD nodes, SOUL.md) governs new MCP servers/skills; this spec adds neither |
| XII. Documentation-as-Code | Yes | Satisfied — spec.md, research.md, data-model.md, quickstart.md all written in this change; README's platform-notes section updated at close with what was and was not device-verified |
| XIII. Credential Safety | Yes | Satisfied — no new credentials, no new entitlement; the existing passcode-confirmation gate is reused unchanged (research.md R1) |
| XIV. Human-in-the-Loop for External Communications | Yes | Satisfied — nothing in this spec sends external messages or creates tickets |
| XV. Backwards Compatibility | Yes | Satisfied — both changes are additive and explicitly designed to leave older/unsupported hardware and OS versions completely unaffected (FR-004/FR-006, research.md R3) |
| XVI. Spec-Driven Development | Yes | Satisfied — this plan follows `/speckit.specify` → `/speckit.plan`, in order, with no `[NEEDS CLARIFICATION]` markers and no implementation started first |
| XVII. Milestone Documentation via WordPress | Yes | Deferred to close-out, applies once both items are implemented, merged, and device-verified |

No violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/112-watch-double-tap-complication/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── checklists/
│   └── requirements.md   # Written during /speckit.specify
└── tasks.md               # Phase 2 output (/speckit.tasks — not yet created)
```

No `contracts/` directory: this spec adds no new wire protocol, RPC method, persisted data shape, or
external interface — both items are purely local SwiftUI view/configuration wiring.

### Source Code (repository root)

```text
mobile/netclaw-mobile/ios/
├── WatchApp Watch App/
│   ├── ApprovalsView.swift   # B4 — List restructured with index, ApprovalRow gains isTopApproval,
│   │                         #      .handGestureShortcut(.primaryAction) on the top row's Approve
│   │                         #      button only, under if #available(watchOS 11.0, *)
│   └── AskView.swift         # B4 — same modifier + availability gate on the "Read aloud" button
└── WatchComplication/
    ├── HeartbeatComplication.swift         # B5 — .accessoryCorner added to supportedFamilies
    └── PendingApprovalComplication.swift   # B5 — .accessoryCorner added to supportedFamilies
```

**Structure Decision**: Every change lands in an existing file inside the existing `WatchApp Watch App/`
and `WatchComplication/` source trees — no new file, no new target, no new top-level directory. Matches
the exact file-organization convention every prior watch-app spec (072, 099) already used.
