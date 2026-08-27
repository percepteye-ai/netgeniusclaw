# Three Things You Can Ask NetGeniusClaw Without Touching Your Phone

**Draft for review — not published.** Constitution Principle XVII requires John's sign-off first.

*By John Capobianco and the agent · 2026-08-15*

John wanted to talk to NetGeniusClaw the way he already talks to everything else on his phone — "Hey Siri" —
and asked for it the same day he was sitting at his Mac with an iPhone plugged in and a watch charging
nearby. The one real design question, "does this open the app or actually run headless," got settled with
him directly before a line of code existed: headless, because a "Hey Siri" that just unlocks your phone to
let you type isn't worth building.

## The two "quick" intents weren't actually the same shape

The brief described `AskBorderIntent` (ask a real question, get a spoken acknowledgment, the real answer
lands later as a notification) alongside two smaller siblings — pending-approval count and Border health —
as though all three just needed "connect and ask." Research before writing the spec caught that
`AskBorderIntent`'s design was sound, but it didn't catch that the other two weren't twins of each other
until implementation forced the question: *where does each one's answer actually come from?*

`PendingApprovalsIntent` needed a Border-side change that didn't exist yet. The obvious-looking shortcut —
read `ApprovalClient.currentPending`, the same in-memory list the phone's own Approvals tab uses — would
have been wrong for a headless intent: that list only fills up from live pushes received *after* a
connection is already open, so a fresh headless connection starts empty regardless of what's genuinely
still pending. The Border's own queue-replay mechanism looked like a fallback, but only covers approvals
never yet delivered — one already pushed to an earlier, since-closed connection but still unresolved would
silently be missed by both. The fix was one new RPC, `n2n/edge/approvals_list`, wired to a
`pending_approvals()` method that turned out to already exist on the Border for exactly this kind of
freshly-queried answer — it just had never been exposed to an edge client before.

`BorderHealthIntent` went the opposite direction. "Ask NetGeniusClaw for Border health" sounds like it should
work the same way — connect, query, speak the answer — but there is no Border-side "give me your health
right now" method at all. Health is a periodic push the Border sends on its own schedule; the phone (and
the watch, and the Dashboard) has only ever read the *last one it received*, cached on disk. Building a
live query would have meant adding a new synchronous entry point into a script that currently does Slack
delivery and posture collection on its own timer — real new surface area the spec never asked for. The
intent instead connects (which is what proves the Border is reachable at all) and speaks the cached
summary with its age: "As of 4 minutes ago: all systems normal," honest about what it actually knows rather
than pretending a decision-and-answer round trip nothing supports.

## The acknowledgment can't outlive the process, so it doesn't try to

`AskBorderIntent`'s hardest constraint wasn't the Border side at all — it was Apple's own rules about how
long a backgrounded, Siri-triggered process gets to keep running. The spec's own example cites a real
2-minute-13-second answer. No documented App Intents mechanism keeps a process alive that long after
`perform()` has already returned to let Siri speak. Something already in this codebase solved almost the
same problem: `reconcileStaleTurns`, built for the case where a phone disconnects mid-answer and the result
sits on the Border with nowhere to land. The headless engine now does the fast case itself — up to a
25-second best-effort window via `ProcessInfo.performExpiringActivity`, catching the common quick answer —
and simply leaves the turn `pending` if the window closes first, trusting the exact same recovery path an
in-app Chat ask already relies on. Nothing new needed inventing for the slow case; it already existed.

## A stale cache almost got blamed for something it didn't do

The final `xcodebuild` run failed immediately with a familiar-looking error: `firebase-core requires
minimum platform version 15.0... but this target supports 13.0`. This exact failure had been reported as
an apparently permanent, unfixable Flutter/SwiftPM limitation in two previous specs. This time, with real
Xcode finally available instead of a description of the problem, it was worth one more look before writing
the same conclusion a third time — and `AppFrameworkInfo.plist` already had the correct fix in it,
`MinimumOSVersion` set to `16.2`, documented in spec 099's own blog post as exactly this problem's
solution. `flutter pub get` simply doesn't regenerate the file that matters; `flutter build ios
--config-only` does. One command, and the whole workspace — three new intents, the shortcuts provider,
the existing watch app and Live Activity extension all embedded alongside — built clean. Two prior specs'
worth of "this can't be verified automatically" turned out to be one missing regeneration step, not a real
wall.

## What's next

Siri, the Action Button, and Shortcuts automations all light up from the same three intents with zero
additional work — that was the whole point of building App Intents instead of legacy SiriKit. Control
Center's own widget is a separate iOS 18+ extension target and stays its own future spec. What's left here
is entirely 🔌 device work: actually saying "Hey Siri" to a real, enrolled phone and hearing it work.
