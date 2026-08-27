# Implementation Plan: NetGeniusClaw Mobile 1.0.1 Polish Pass (Phase A + C1)

**Branch**: `110-mobile-polish-pass` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/110-mobile-polish-pass/spec.md`

## Summary

Seven independently shippable polish items for NetGeniusClaw Mobile 1.0.1: dark
mode support (US1), selectable/copyable/shareable/markdown-aware chat answers
and feed messages (US2), Time Sensitive approval notifications (US3), an
operator-adjustable Face ID app-lock (US4), distinct haptic feedback on six
key events (US5), live search/filter across Chat and Feed (US6), and making
the Dashboard's "Unread"/"Pending approvals" rows actually navigate somewhere
(US7, added during planning at the operator's request — not part of the
original brief). Two new dependencies (`flutter_markdown_plus`, `share_plus`
— see research.md R1/R2), no new persisted server-side or cross-device state,
no new Xcode target or capability.

## Technical Context

**Language/Version**: Dart 3.x / Flutter (SDK `^3.12.2` per `mobile/netclaw-mobile/pubspec.yaml`), Swift 5.0 (`ios/WatchApp Watch App/*.swift`, US5's watch-side haptics only) — same stack as specs 066–108, unchanged.
**Primary Dependencies**: Two new: `flutter_markdown_plus` (^1.0.12, US2 — see research.md R1) and `share_plus` (^13.3.0, US2 — see research.md R2). Everything else reuses existing dependencies: `flutter_secure_storage` (US4's app-lock preference), `local_auth` (US4, already used by `approval_confirmation.dart`), `flutter_local_notifications` (US3).
**Storage**: `flutter_secure_storage` gains two new keys (US4: app-lock enabled/disabled boolean, grace-period duration in seconds — research.md R5). No other new persisted state; US6's search/filter state is explicitly transient (FR-015) and US7 adds no state at all, only wiring.
**Testing**: `flutter test` (existing suite, 289 tests passing on this branch as of 2026-08-14) — new unit/widget tests added per story; `flutter analyze` must stay at zero issues throughout.
**Target Platform**: iOS 15+ / Android / watchOS (existing deployment targets, unchanged). US5's watch-side haptics are the only native-platform-only surface in this spec — everything else is pure Dart/Flutter.
**Project Type**: Mobile app (existing `mobile/netclaw-mobile/`) — no new project, no new target.
**Performance Goals**: N/A for six of seven stories (UI/preference/search polish, not throughput-sensitive). US2's long-answer scroll scenario has an explicit qualitative (not automated-benchmark) bar per Clarifications (2026-08-14) — see research.md and spec.md Context.
**Constraints**: FR-006's Markdown/preformatted classification MUST run only at terminal turn state, never on streaming partial text (Clarifications, 2026-08-14). FR-010 MUST NOT double-prompt biometrics between US4's app-lock and the existing per-approval confirmation flow. FR-011 MUST NOT repeat the connection-lost haptic across a bounded retry loop.
**Scale/Scope**: Seven user stories, six existing files modified (`lib/main.dart`, `lib/screens/chat_screen.dart`, `lib/screens/feed_screen.dart`, `lib/screens/settings_screen.dart`, `lib/screens/dashboard_screen.dart`, `lib/ncfed/local_notifications.dart`) plus two watch-side Swift files (`ApprovalsView.swift`, `WatchDataStore.swift`), five new Dart files (`lib/theme.dart`, `lib/ncfed/haptics.dart`, `lib/ncfed/app_lock.dart`, `lib/ncfed/conversation_search.dart`, `lib/ncfed/answer_format.dart`), `pubspec.yaml` (two new deps + version bump).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

This is a mobile-app UI/UX polish feature with no new MCP server, skill, or
network-automation capability — the majority of `.specify/memory/
constitution.md`'s principles (I–X, safety/ITSM/GAIT/MCP/vendor-neutrality/
observability) govern device-automation capabilities and do not apply here,
consistent with how every prior mobile spec (066–108) has been evaluated.

| Principle | Applicable? | Status |
|---|---|---|
| I–X (device automation, ITSM, MCP, observability) | No | N/A — no device automation or MCP capability added |
| XI. Full-Stack Artifact Coherence | No | N/A — that principle's checklist (catalog.sh, install-steps.sh, HUD nodes, SOUL.md) governs new MCP servers/skills; this spec adds neither |
| XII. Documentation-as-Code | Yes | Satisfied — spec.md, research.md, data-model.md, quickstart.md all written in this same change; README's platform-notes section updated at close per FR/Clarifications (US2's manual perf check, any watch-hardware haptic verification) |
| XIII. Credential Safety | Yes | Satisfied — no new credentials of any kind; US4's app-lock preference is local device state, not a secret |
| XIV. Human-in-the-Loop for External Communications | Yes | Satisfied — nothing in this spec sends external messages or creates tickets |
| XV. Backwards Compatibility | Yes | Satisfied — every story is additive (new screen state, new Settings controls, new callbacks) or a narrowly-scoped bugfix (US7); no existing wire contract, stored-data shape, or public method signature changes incompatibly |
| XVI. Spec-Driven Development | Yes | Satisfied — this plan is the direct output of `/speckit.specify` → `/speckit.clarify` → `/speckit.plan`, in order, with no implementation started first |
| XVII. Milestone Documentation via WordPress | Yes | Deferred to close-out, not this planning step — applies once all seven stories are implemented and merged, per the principle's own "at completion of a milestone" trigger |

No violations. No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/110-mobile-polish-pass/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── checklists/
│   └── requirements.md   # Written during /speckit.specify
└── tasks.md               # Phase 2 output (/speckit.tasks — not yet created)
```

No `contracts/` directory: this spec adds no new wire protocol, RPC method,
or external interface — every story is either purely local UI/preference
logic (US1, US2, US4, US5, US6, US7) or a change to locally-constructed
notification payloads that never leaves the device (US3).

### Source Code (repository root)

Existing Flutter/iOS/watchOS mobile app structure — no new top-level
directories, no new Xcode target:

```text
mobile/netclaw-mobile/
├── lib/
│   ├── main.dart                       # US1 (theme/themeMode), US4 (EnrollmentGate lock-screen insertion, app-lock wiring), US7 (_selectTab factor-out, DashboardScreen callbacks)
│   ├── theme.dart                      # NEW (US1) — light/dark ColorScheme pair extracted from main.dart
│   ├── ncfed/
│   │   ├── haptics.dart                # NEW (US5) — injectable phone-side haptic wrapper
│   │   ├── app_lock.dart               # NEW (US4) — grace-period logic (pure) + local_auth wrapper
│   │   ├── conversation_search.dart    # NEW (US6) — pure filter function over turns/messages
│   │   ├── answer_format.dart          # NEW (US2) — looksLikeMarkdown() classifier (research.md R3)
│   │   # (lib/screens/answer_body.dart, below, is the shared AnswerBody widget both
│   │   #  chat_screen.dart and feed_screen.dart render through -- discovered during
│   │   #  implementation to avoid duplicating the Markdown/copy-button wiring twice)
│   │   ├── approval_client.dart        # US5 — haptic call sites
│   │   ├── enrollment_flow.dart        # US5 — haptic call site (enrollment succeeds)
│   │   ├── reconnect_supervisor.dart   # US5 — haptic call site (connection-lost transition)
│   │   ├── local_notifications.dart    # US3 — interruptionLevel/Importance changes only
│   │   ├── conversation_store.dart     # unchanged — ConversationTurn already carries requestText/answerText/origin/acknowledged used by US2/US6
│   │   ├── message_feed.dart           # unchanged — MessageFeedStore already carries the shape US6 filters
│   │   └── dashboard_data.dart         # unchanged — UnreadPendingSnapshot already exposes unreadFeed/unreadChat separately, used by US7
│   └── screens/
│       ├── answer_body.dart            # NEW (US2) — shared AnswerBody widget (Markdown-or-preformatted, long-press context menu)
│       ├── chat_screen.dart            # US2 (SelectableText, overflow menu + long-press, markdown rendering), US6 (search field + filter chips)
│       ├── feed_screen.dart            # US2 (same treatment for message bodies), US6 (search field)
│       ├── settings_screen.dart        # US4 (Face ID toggle + grace-period control)
│       └── dashboard_screen.dart       # US7 (onOpenFeed/onOpenChat/onOpenApprovals callbacks + onTap wiring)
├── test/
│   ├── theme_test.dart                          # NEW (US1)
│   ├── no_hardcoded_colors_test.dart            # NEW (US1) — repo-hygiene scan of lib/screens/
│   ├── haptics_test.dart                        # NEW (US5)
│   ├── app_lock_test.dart                       # NEW (US4) — grace-period pure logic
│   ├── conversation_search_test.dart            # NEW (US6)
│   ├── answer_format_test.dart                  # NEW (US2) — classifier unit tests
│   ├── chat_screen_test.dart                    # extended (US2, US6)
│   ├── feed_screen_test.dart                    # extended (US2, US6) — create if none exists yet
│   ├── settings_screen_test.dart                # extended (US4)
│   ├── local_notifications_test.dart            # extended (US3) — create if none exists yet
│   └── dashboard_screen_test.dart               # extended (US7) — create if none exists yet
├── ios/WatchApp Watch App/
│   ├── ApprovalsView.swift             # US5 — watch-side haptic calls (🔌 DEVICE)
│   └── WatchDataStore.swift            # US5 — watch-side haptic calls (🔌 DEVICE)
└── pubspec.yaml                        # version 1.0.0+1 -> 1.0.1+2 (FR-016); + flutter_markdown_plus, share_plus
```

**Structure Decision**: Everything lands inside the existing
`mobile/netclaw-mobile/` project, following the exact file-organization
convention every prior mobile spec (066–108) already used (`lib/screens/`
for UI, `lib/ncfed/` for shared client logic, `test/` mirroring `lib/`
one-to-one). No new project, package, or top-level directory. The one
native-only surface (US5's watch-side haptics) is a small, targeted change
to two already-existing Swift files, not a new target — consistent with
research.md R6's decision not to introduce a Dart-to-watch haptic bridge.
