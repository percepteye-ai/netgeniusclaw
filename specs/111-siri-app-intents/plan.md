# Implementation Plan: NetGeniusClaw Mobile Siri / App Intents Integration (B1a)

**Branch**: `111-siri-app-intents` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/111-siri-app-intents/spec.md`

## Summary

Three native Swift `AppIntent`s (`AskBorderIntent`, `PendingApprovalsIntent`, `BorderHealthIntent`) exposed
through one `AppShortcutsProvider`, each launching a headless `FlutterEngine` — the same pattern spec 099's
background refresh already established — rather than opening the app. `AskBorderIntent` submits a question
fast and speaks only an acknowledgment, since the real answer can take minutes; the eventual answer arrives
as a local notification the headless engine posts itself. `PendingApprovalsIntent` and `BorderHealthIntent`
speak a real value directly. Research (research.md R3/R4) found the two "quick query" intents are not
symmetric: `PendingApprovalsIntent` needs one new, narrowly-scoped Border-side RPC
(`n2n/edge/approvals_list`, wired to the already-existing `Authorizer.pending_approvals()`) because no
existing passive/cached source can give a live count without under-counting; `BorderHealthIntent` needs zero
Border-side changes because "Border health" in this system is already a passively-cached on-device value
(`DeviceHeartbeatStore`), not a request/response query. No new entitlement, no deployment-target change.

## Technical Context

**Language/Version**: Dart 3.x / Flutter (SDK `^3.12.2` per `mobile/netclaw-mobile/pubspec.yaml`), Swift 5.0 (`ios/Runner/*.swift`, new `AppIntents` target membership) — same stack as specs 066–110, unchanged. Python 3.10+ for the one Border-side addition (`bgp/federation/*`, matching specs 052–110).
**Primary Dependencies**: No new Dart or Python packages. Swift: Apple's `AppIntents` framework (system framework, iOS 16+, ships with the SDK — not a package dependency). Reuses existing `EdgeClient`, `EdgeAskClient`, `EdgeIdentityPlugin`, `ConversationStore`, `LocalNotifications`, `DeviceHeartbeatStore` (Dart) and `Authorizer` (Python) as-is.
**Storage**: No new store. `ConversationStore`'s existing `origin` field gains one new valid value, `'siri'` (research.md R5) — no schema change, no migration.
**Testing**: `flutter test` (existing suite) for the three new headless Dart entrypoints' pure logic and the `origin: 'siri'` round-trip; `xcodebuild -workspace mobile/netclaw-mobile/ios/Runner.xcworkspace -scheme Runner -sdk iphoneos -configuration Debug build CODE_SIGNING_ALLOWED=NO` to verify the new Swift compiles; `python3 -m pytest tests/n2n/test_edge_approvals_list.py` (repo root) for the one new Border-side RPC; real Siri/Action Button/Shortcuts invocation is 🔌 **DEVICE**-only (spec Context, User Story Independent Tests) and is not claimed done from any automated check alone.
**Target Platform**: iOS 16+ (existing `IPHONEOS_DEPLOYMENT_TARGET = 16.2`, unaffected — `AppIntents` needs 16+, comfortably covered). No Android/watchOS surface in this spec.
**Project Type**: Mobile app (existing `mobile/netclaw-mobile/`) — no new project, no new Xcode target (App Intents live inside the existing `Runner` target, unlike a Control Center `ControlWidget`, which would need one — that's B1b, out of scope here).
**Performance Goals**: FR-008's bounded-time guarantee is the only quantified goal: 10s cold-connect timeout (matching `background_refresh.dart`'s existing precedent, research.md R6), each intent's own Border round-trip separately bounded (30s for `AskBorderIntent`'s ack phase, reusing `EdgeAskClient.ask()`'s existing timeout; 10s for the new `approvals_list` call, matching the connect step).
**Constraints**: FR-002/FR-009 — never open the app UI, always tear down the headless engine deterministically regardless of outcome. FR-012 — no new entitlement, no deployment-target bump. FR-006 — the pending-approval count must be live, not a stale/cached value (research.md R3 is the direct consequence of this constraint).
**Scale/Scope**: Three new Swift `AppIntent` structs + one `AppShortcutsProvider`, three new Dart `@pragma('vm:entry-point')` entrypoints (`lib/ncfed/ask_border_headless.dart`, `lib/ncfed/pending_approvals_headless.dart`, `lib/ncfed/border_health_headless.dart`), one new Border-side RPC handler (`bgp/federation/service.py`, `bgp/federation/edge.py`'s method allowlist), one existing-file edit (`conversation_store.dart`'s `origin` doc comment, no code change beyond accepting the new string value it already does structurally).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This is a mobile-app feature plus one narrowly-scoped Border-side RPC — not a new MCP server, skill, or
device-automation capability. Evaluated the same way specs 066–110 were:

| Principle | Applicable? | Status |
|---|---|---|
| I–X (device automation, ITSM, MCP, observability) | No | N/A — no network-device automation or MCP tool added; the one Border-side change is an internal federation RPC, not an MCP server |
| XI. Full-Stack Artifact Coherence | No | N/A — that checklist (catalog.sh, install-steps.sh, HUD nodes, SOUL.md) governs new MCP servers/skills; this spec adds neither |
| XII. Documentation-as-Code | Yes | Satisfied — spec.md, research.md, data-model.md, quickstart.md all written in this change; the new `n2n/edge/approvals_list` method gets the same doc-comment treatment as its neighbors in `edge.py`/`service.py` |
| XIII. Credential Safety | Yes | Satisfied — no new credentials; reuses the existing pinned-key/Secure Enclave enrollment identity unchanged |
| XIV. Human-in-the-Loop for External Communications | Yes | Satisfied — nothing in this spec sends external messages or creates tickets; a Siri-submitted ask is the operator's own voice command, not an unattended automated action |
| XV. Backwards Compatibility | Yes | Satisfied — `origin` gaining a third valid string value is additive (existing `'phone'`/`'watch'` readers already fall back safely on unknown values, per spec 073's own missing-key-defaults-to-`'phone'` precedent); the new Border RPC is purely additive to the existing `n2n/edge/*` method allowlist |
| XVI. Spec-Driven Development | Yes | Satisfied — this plan follows `/speckit.specify` → `/speckit.clarify` (none needed — no `[NEEDS CLARIFICATION]` markers) → `/speckit.plan`, in order |
| XVII. Milestone Documentation via WordPress | Yes | Deferred to close-out, applies once all three intents are implemented, merged, and device-verified |

No violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/111-siri-app-intents/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # Written during /speckit.specify
└── tasks.md              # Phase 2 output (/speckit.tasks — not yet created)
```

No `contracts/` subdirectory of files, but this spec's one genuine new wire contract — the
`n2n/edge/approvals_list` RPC — is documented directly in data-model.md's Entities section instead of a
separate contracts file, matching the size of the addition (one method, one existing pattern to mirror).

### Source Code (repository root)

```text
mobile/netclaw-mobile/
├── lib/ncfed/
│   ├── ask_border_headless.dart          # NEW — @pragma('vm:entry-point') entrypoint for AskBorderIntent
│   ├── pending_approvals_headless.dart   # NEW — entrypoint for PendingApprovalsIntent
│   ├── border_health_headless.dart       # NEW — entrypoint for BorderHealthIntent
│   ├── edge_ask_client.dart              # unchanged — ask()/updates stream reused as-is (R2)
│   ├── conversation_store.dart           # doc comment only — origin gains 'siri' as a third documented value (R5)
│   ├── device_heartbeat.dart             # unchanged — DeviceHeartbeatStore.load()/heartbeatSummary() reused as-is (R4)
│   └── local_notifications.dart          # unchanged — postChatNotification() reused as-is (R2)
├── ios/Runner/
│   ├── AskBorderIntent.swift             # NEW
│   ├── PendingApprovalsIntent.swift      # NEW
│   ├── BorderHealthIntent.swift          # NEW
│   ├── NetClawShortcuts.swift            # NEW — AppShortcutsProvider, all three phrases
│   └── AppDelegate.swift                 # unchanged — headless engine launch lives in the new intent files themselves, mirroring how handleBackgroundRefresh already owns its own engine rather than routing through AppDelegate
└── test/
    ├── ask_border_headless_test.dart          # NEW
    ├── pending_approvals_headless_test.dart   # NEW
    ├── border_health_headless_test.dart       # NEW
    └── conversation_store_test.dart           # extended — origin: 'siri' persists/round-trips like 'watch' does

mcp-servers/protocol-mcp/bgp/federation/
├── edge.py         # method allowlist gains "n2n/edge/approvals_list"
└── service.py      # new handler wired to self.authz.pending_approvals(), mirroring edge_self_status's shape

tests/n2n/
└── test_edge_approvals_list.py   # NEW — repo-root test location, matching test_edge_approval.py/test_edge_ask.py's existing convention (NOT under mcp-servers/protocol-mcp/)
```

**Structure Decision**: Everything lands inside the existing `mobile/netclaw-mobile/` project and the
existing `mcp-servers/protocol-mcp/` Border codebase — no new project, package, target, or top-level
directory. The three new Swift files live directly in `ios/Runner/` alongside the existing
`EdgeIdentityPlugin.swift`/`AppDelegate.swift`, matching how every native-only surface in specs 066–110 was
added to an existing target rather than a new one. The one Border-side change is the smallest possible
addition to an existing, already-patterned file pair (`edge.py`'s allowlist + one `service.py` handler),
not a new module.
