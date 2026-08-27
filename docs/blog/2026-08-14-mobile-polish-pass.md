# Seven Small Fixes, One Bug Only a Tester Could Have Found

**Draft for review — not published.** Constitution Principle XVII requires John's sign-off first.

*By John Capobianco and Claude · 2026-08-14*

John handed over a brief with seven independent polish items for NetGeniusClaw Mobile 1.0.1 — dark mode, real
haptics, selectable/shareable chat answers, Time Sensitive approval notifications, a Face ID app lock,
search across Chat and Feed, and (added mid-flight, at his own request) making the Dashboard's "Unread"
and "Pending approvals" rows actually navigate somewhere instead of doing nothing. None of the seven
needed a new server, a new entitlement, or a new Xcode target — the whole pass lived inside the existing
app.

## The one story that wasn't in the brief

Partway through implementation, John noticed something the brief never mentioned: tapping the unread badge
on the Dashboard did nothing. That became User Story 7, added on the spot rather than filed away for a
future pass — a live spec absorbing a real bug report while the ink is still wet is exactly what
spec-driven development is supposed to make easy, not awkward.

## Markdown answers needed a gesture-arena fight, not a bigger font

The brief called for selectable, shareable, Markdown-aware chat answers. The straightforward version —
wrap the answer in a `GestureDetector` for long-press, render Markdown underneath — silently did nothing.
`SelectableText` and `MarkdownBody` both register their own long-press recognizers for text selection, and
Flutter's gesture arena lets the descendant win every time; an ancestor's `onLongPress` never even fires.
The fix wasn't a bigger gesture detector, it was routing through `contextMenuBuilder` instead — the
selection toolbar Flutter already owns, extended with a Share item, rather than fighting Flutter's own
widget for the same tap.

## A haptic can crash a test suite that wasn't touching haptics

Wiring up "distinct haptic feedback on six key events" broke roughly 40 unrelated tests the moment it
landed, all with the same complaint: a Flutter binding that had "not yet been initialized." Plain `test()`
files that never call `TestWidgetsFlutterBinding.ensureInitialized()` don't expect a platform channel call
to reach for real infrastructure — and `HapticFeedback`, it turns out, does exactly that even when wrapped
in a channel that's supposed to tolerate a missing platform plugin. The fix was a one-line
`.catchError((_) {})` around every haptic call, which fixed the test suite and happens to also be the
correct production behavior: a haptic that fails should never take anything else down with it.

## The last discovery didn't come from a test at all

Late in the pass, re-reading `Runner.entitlements` for an unrelated reason turned up its own comment
claiming `CODE_SIGN_ENTITLEMENTS` was "deliberately not set" — directly contradicted by three lines in
`project.pbxproj` that set it. The comment was simply stale, left over from before a real signing
migration. Worse, the Time Sensitive notification capability this same pass had just built needed an
entitlement key that had never actually been added, because nobody had circled back to check what the
file actually said versus what a comment claimed it said. Fixed with one new key and one corrected
comment — the kind of bug that a green test suite will never catch, because the test suite has no opinion
about whether a code comment is telling the truth.

## What's still open

Long-answer scroll performance, Focus-mode delivery for Time Sensitive notifications, real Face ID
prompts, and how all six haptics actually feel on a wrist and in a hand — none of that is provable from
`flutter test`, and none of it has been checked on real hardware yet. That's the honest state of this pass:
seven stories code-complete and automatically verified, with a known, explicit list of what a person still
has to go feel for themselves.
