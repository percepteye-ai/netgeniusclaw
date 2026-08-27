# Phase 0 Research: NetGeniusClaw Mobile 1.0.1 Polish Pass (Phase A + C1)

All items in this spec's Technical Context were resolved with no
`NEEDS CLARIFICATION` markers — the source brief
(`mobile/netclaw-mobile/NETCLAW-MOBILE-1.0.1-BRIEF.md`) and the
`/speckit.clarify` session already fixed every open decision except the two
package choices below, which required checking current pub.dev status rather
than trusting either this repo's prior knowledge or the brief's own
tentative naming.

## R1: Markdown rendering package

**Decision**: `flutter_markdown_plus` (^1.0.12).

**Rationale**: The brief tentatively suggested `flutter_markdown` "or
`gpt_markdown` if the former's maintenance status is a concern at
implementation time — check before choosing." Checked directly against
pub.dev at plan time:

- `flutter_markdown` (the Flutter team's own package) is confirmed
  **discontinued** — "This project has been discontinued, and will not
  receive further updates," last published 15 months ago (v0.7.7+1). Its own
  package page names `flutter_markdown_plus` as the suggested successor.
- `flutter_markdown_plus` is a direct continuation of the same codebase,
  actively maintained (v1.0.12, published 35 days prior to this plan;
  "bug reports are triaged against the current release... fixes and
  additive features ship regularly as patch releases").

Choosing the named successor of a package this repo would otherwise have
picked keeps the widget API/rendering behavior close to what every existing
Flutter-Markdown code example assumes, versus adopting a differently-shaped
API like `gpt_markdown` for no added benefit here.

**Alternatives considered**:
- `flutter_markdown` (rejected — discontinued, no further updates).
- `gpt_markdown` (rejected — the brief's own fallback option, but
  unnecessary now that a maintained direct successor exists; would mean
  learning a differently-shaped widget API for no benefit).
- `markdown_widget` (not evaluated in depth — `flutter_markdown_plus`'s
  direct lineage from the previously-vetted `flutter_markdown` made it the
  lower-risk choice once confirmed actively maintained).

## R2: Share package

**Decision**: `share_plus` (^13.3.0), exactly as the brief proposed.

**Rationale**: Confirmed actively maintained (published 21 days prior to
this plan, verified `fluttercommunity.dev` publisher), and used on both iOS
and Android via native share sheets (`UIActivityViewController` /
`ACTION_SEND`).

**Correction to the brief's own gotcha**: the brief states `share_plus` "on
iPad requires `sharePositionOrigin` or it throws." Checked directly:
`sharePositionOrigin` is not strictly required — if omitted, the share
popover falls back to anchoring at the screen's center rather than throwing.
It is still worth passing (the brief's underlying intent — a well-anchored
popover rather than a centered fallback — is correct UX), but FR-005/US2's
tests should not assert a thrown exception in its absence, since that is not
this package's actual behavior. This is exactly the kind of Evidence-vs-
reality drift the spec's Context section commits to catching before it
causes wasted implementation time.

## R3: Markdown/preformatted classification policy (FR-006)

**Decision**: A pure Dart function, `bool looksLikeMarkdown(String text)`,
that returns true only if `text` contains either a fenced code block
(a line starting with three backticks, closed by another such line) or at
least one line matching a Markdown pipe-table row pattern (contains `|`
with non-whitespace content on both sides, not inside a fenced block).
Applied only once a turn/message reaches a terminal state (Clarifications,
2026-08-14) — never re-evaluated against partial/streaming text.

**Rationale**: Needs to be conservative (favor plain preformatted text) per
FR-006's explicit requirement not to mangle raw CLI output containing bare
`#`, `*`, `_`, or `|` characters. A pure function taking a `String` and
returning a `bool`/enum is the simplest possible thing that is fully
unit-testable without any widget harness, matching this spec's
Clarifications-confirmed requirement that this decision be provable by
`flutter test` alone.

**Alternatives considered**: Attempting a full Markdown parse and checking
if it "looks reasonable" was rejected as needless complexity — a raw
substring/regex check on two specific signals (fence, pipe-table row) is
sufficient and matches the brief's own stated policy exactly.

## R4: Existing injectable-function pattern for platform-channel wrappers

**Decision**: Follow the pattern already established by
`voice_transcription.dart` and `reconnect_supervisor.dart` — a class or
top-level function accepting an optional injected implementation, defaulting
to the real platform call in production, for `haptics.dart` and `app_lock.dart`
(specifically, `local_auth`'s `authenticate()` call and any platform-channel
haptic call).

**Rationale**: This is the existing, already-code-reviewed convention in
this codebase for anything that would otherwise make a widget test touch a
real platform channel; reusing it keeps `110`'s new files structurally
consistent with `066`–`108`'s prior work rather than introducing a second
pattern for the same problem.

**Alternatives considered**: A mocking/DI framework (e.g. `mocktail` with a
generated interface) was not considered necessary — the codebase has never
used one for this class of problem, and introducing one here for six small
files would be inconsistent with every other file in `lib/ncfed/`.

## R5: Face ID grace-period persistence

**Decision**: Persist both the app-lock enabled/disabled boolean and the
grace-period duration (an integer number of seconds) in
`flutter_secure_storage`, alongside a simple settings UI control (a
`DropdownButton`/segmented choice among a small fixed set of durations —
e.g. 0s/"immediately", 30s, 60s (default), 5 min — rather than a free-form
numeric entry field).

**Rationale**: `flutter_secure_storage` is already a declared dependency
(confirmed unused elsewhere in `lib/` as of this plan — this is its first
real consumer, correcting an earlier assumption that it was already in use
for other sensitive local state); it is still the appropriate choice here
over `SharedPreferences`, since app-lock is itself a security preference. A
fixed small set of duration choices is simpler to build, simpler to test
exhaustively, and
matches how this class of "auto-lock after" setting is presented in
comparable apps (e.g. iOS's own Screen Time/Auto-Lock pickers), versus an
unbounded numeric input whose edge cases (zero, negative, absurdly large)
would need their own validation logic for no real benefit.

**Alternatives considered**: A free-form duration text field (rejected —
adds input validation complexity with no meaningful benefit over a small
fixed choice set); storing the duration in `SharedPreferences` instead of
`flutter_secure_storage` (rejected — the app-lock enabled/disabled flag and
its duration are one cohesive preference and belong in the same store; using
two different storage mechanisms for two halves of one setting would be an
inconsistency with no upside).

## R6: Haptic wrapper scope on the watch side

**Decision**: `lib/ncfed/haptics.dart` covers the phone side only (pure
Dart, `HapticFeedback` calls). The watch-side haptic calls
(`WKInterfaceDevice.current().play(...)`) are added directly in
`ApprovalsView.swift`/`WatchDataStore.swift` as small, targeted Swift
changes — not routed through any Dart abstraction, since the watch app has
no Flutter engine at all (it is a native SwiftUI target, per spec 072).

**Rationale**: Matches the existing architecture exactly — there is no
Dart-to-watch bridge for this kind of local, momentary UI feedback, and
inventing one for haptics alone (when the watch app has never needed one
for anything else) would be needless complexity for a delight-only feature.
This is a native (Swift) change and is explicitly out of the "provable by
`flutter test` alone" claim in spec.md's Context — it must be verified on
real watch hardware before being called done, per specs 072/073's standing
precedent, and called out as such in the README's platform-notes section if
not verified.

**Alternatives considered**: A shared Dart "haptic event" enum sent to the
watch over the existing `WatchConnectivity` relay was rejected — it would
add wire-protocol surface and cross-process latency to what is, on the
watch, already a same-process, same-frame UI action (the watch app renders
its own approval UI natively; it does not need to be told by the phone that
an approval arrived to know to haptic-buzz about it).

## R7: Dashboard unread/pending tap-through (User Story 7)

**Decision**: Factor the existing tab-switch-plus-mark-read logic already
inside `NavigationBar.onDestinationSelected` (`main.dart:710-720`) into a
small reusable method (e.g. `_selectTab(int index)`) on `_HomeShellState`.
Pass two simple `VoidCallback`s into `DashboardScreen` — `onOpenFeed` and
`onOpenChat`, each just `() => _selectTab(<index>)` — plus keep the existing
`onOpenApprovals` for the pending row. `DashboardScreen` itself, which
already receives `UnreadPendingSnapshot`'s `unreadFeed`/`unreadChat`
breakdown, decides the Feed-vs-Chat priority (FR-017) in its own `build()`
and invokes whichever callback applies (or neither, when both are zero).

**Rationale**: `DashboardScreen` is a `StatelessWidget` with no access to
`_HomeShellState`'s `_tab`/`_unreadFeed`/`_highlightPushedAt` fields today; it
only receives a `DashboardSnapshot` value object (`dashboard_data.dart`).
It already conditionally renders based on snapshot fields (the
not-yet-enrolled branch, FR-013), so having it also decide "Feed or Chat"
from the same snapshot it already holds is consistent with how the widget
already works — simpler than routing that decision through
`_HomeShellState` via a more complex callback contract. Reusing the *same*
underlying `_selectTab` method the bottom navigation already calls (rather
than writing a second, parallel "switch to Feed and clear the badge" code
path) is what keeps FR-017's "must also clear the Feed unread badge/
highlight exactly as opening Feed via the bottom navigation does" true by
construction instead of by two independently-maintained implementations
agreeing today and drifting later.

**Alternatives considered**: Baking the Feed-vs-Chat priority decision into
a single combined callback passed from `_HomeShellState` (so
`DashboardScreen` calls one opaque `onOpenUnread()` with no knowledge of
why) was considered and rejected — it would hide a business rule (Feed wins
ties) behind an opaque callback name, whereas keeping the `if
(unreadFeed > 0) ... else if (unreadChat > 0) ...` check inline in
`DashboardScreen`'s own `build()` keeps the rule visible next to the data
it reads, and keeps `_HomeShellState`'s callback surface to the same shape
(one callback per destination) it would need for the "Pending approvals"
row anyway.
