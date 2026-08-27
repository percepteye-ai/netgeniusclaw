# The Safest Feature Is the One That Reuses a Safety Check It Didn't Build

**Draft for review — not published.** Constitution Principle XVII requires John's sign-off first.

*By John Capobianco and the agent · 2026-08-15*

Right after finishing Siri integration, John wanted to keep moving through the rest of the NetGeniusClaw Mobile
1.0.1 wish list rather than stop for device testing — two of the smallest remaining items, bundled
together: Double Tap gesture support on the Apple Watch, and a new corner slot for the two existing
complications.

## The brief asked for a safety mechanism that already existed

The source brief for Double Tap was explicit about the risk: "Approving a network change with an
accidental finger pinch is a bad outcome." Its own recommendation was that Double Tap should only surface
a confirmation prompt, never resolve an approval outright — treat the gesture as a shortcut to asking, not
a shortcut to answering.

Reading `ApprovalsView.swift` before writing anything showed that distinction had already been made,
just not by this feature. Every single approve or deny action — regardless of what triggers it — already
routes through a fresh, uncached Face ID/passcode-equivalent prompt before anything is sent to the Border.
There is no code path where tapping a button (or, now, performing a gesture) resolves an approval directly.
That meant the real design question wasn't "how do we make Double Tap safe" — it was already safe by
construction — but "which single control, on a screen that can show several pending approvals at once,
gets to claim the gesture at all." Apple's own rule is unforgiving here: claim `.handGestureShortcut` on
more than one visible button and the system silently disables Double Tap for all of them, with no warning.
The fix was scoping the gesture to exactly the topmost approval's Approve button, restructuring the list to
carry an index specifically so exactly one row could make that claim.

## Corner complication support turned out to already be built

The two existing complications — device heartbeat and pending-approval count — already paired a small
glyph or number with a `.widgetLabel` curved-caption modifier, because that pairing is what looks right on
a circular watch face slot. It also happens to be exactly the layout Apple's newer corner slot expects.
Adding `.accessoryCorner` to each complication's supported-family list turned out to be a two-line change,
with the same view WidgetKit was already rendering for every other slot simply adapting to the new one.

## An old build trap resurfaced, and its own documentation solved it

Verifying the watch complication target hit a familiar-shaped error — a Swift Package resolution failure,
this time about watchOS platform versions rather than iOS ones. Rather than re-diagnosing it from scratch,
a `git stash` back to completely unmodified code reproduced the identical failure, confirming it predated
this feature entirely. This repo's own README already had the answer, written after a real debugging
session on the watch companion app itself: passing `-sdk` directly to `xcodebuild` forces that SDK onto
*every* target in the whole workspace's build graph, including phone-only plugins that were never meant to
compile for a watch at all. The fix wasn't a new investigation — it was trusting the `WatchApp` scheme,
which correctly scopes its own dependencies and already embeds the complication extension as part of the
same build, instead of trying to build the complication target in isolation.

## What's left

Both changes ship without a single Dart line touched and without moving the watch app's deployment target
— older watches get no new capability and no new risk. What remains, as with Siri last time, is entirely
🔌 device work: a real Double Tap on a real wrist, and a real look at how a corner glyph reads on an actual
Infograph face.
