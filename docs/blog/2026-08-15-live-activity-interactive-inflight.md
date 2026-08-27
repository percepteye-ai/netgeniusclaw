# The Feature the Brief Asked For Doesn't Exist — Here's What Does

**Draft for review — not published.** Constitution Principle XVII requires John's sign-off first.

*By John Capobianco and Claude · 2026-08-15*

Third feature in a row today, and the biggest one: Approve/Deny buttons on NetGeniusClaw's Lock Screen Live
Activity, and a brand-new Live Activity that watches a submitted question while it's being answered. The
second half of that sentence almost shipped something that would have been quietly, permanently wrong.

## The member count the brief wanted was never real

The brief's design for the in-flight activity called for showing "3 of 5 members responded" — a live
fan-out counter. Before writing a line of Swift, that claim got checked against the actual Border code
that handles a submitted question, not assumed from the brief's own mockup. `_edge_on_ask`'s own docstring
says the quiet part out loud: the agent's existing tool-using behavior decides whether to delegate, one
call at a time, as it reasons — there is no branching logic for fan-out anywhere in the Border, because
there is no fan-out. A real captured trace settled it completely: one delegation to `cml` finishes at
13:04:46, and only *then* does the router pick `pyats`, a full 13 seconds later. That's a single agent
having a second thought, not two requests running in parallel. There was never a number to show.

Building a real one would have meant new correlation IDs linking a top-level ask to whatever it triggers,
plus counting logic for a total that's genuinely only knowable in hindsight — the system can't say
"expects 3" before it's decided to ask 3, and it decides one at a time. That's a real, separate feature,
not a checkbox inside this one. What shipped instead is honest about what the phone actually knows: the
question, a timer that's been running since submission, and the same free-text "still working" line the
Border already sends at a stall checkpoint. Nothing invented, nothing implied that isn't true.

## The safety property was already built; the job was routing around a wall, not through it

The buttons ask a harder question than "can I put buttons on a Live Activity." An `AppIntent` triggered
from a Live Activity runs while the phone is still locked, and there is no supported way to raise a real
Face ID prompt from that context — Apple simply doesn't expose it. The existing app already has a hard
rule from months ago: every single approval, no exceptions, goes through a fresh biometric check
immediately before it's sent. Weakening that to make a Lock Screen button feel more magical was never on
the table. So the button doesn't approve anything. It opens the app to the Approvals tab, through the same
`netgeniusclaw://` link scheme already wired up for a completely different feature, and the exact same
biometric-gated code that's always been there runs exactly as if the operator had opened the app and
tapped Approve themselves. One tap gets you to the Face ID prompt instead of three; the prompt itself
never got any less real.

## One target membership mistake, caught twice, by the build and not by guessing

The new intent type needs to exist inside two different compiled targets — the app, and the widget
extension that renders the Lock Screen content — because the button's `Button(intent:)` reference lives in
the extension's own code. Adding it to only the app target compiled clean by itself and then failed with
`cannot find 'ApprovalActionIntent' in scope` the moment the extension tried to reference it. Fixing that
opened a second door: `UIApplication.shared`, which the button needs to actually open the deep link, is
flatly forbidden inside app extensions — a rule the extension's own copy of the exact same source file now
had to obey, even though that copy never actually runs (the OS always executes the real one inside the
app). The fix was a small, honest one: a build flag that exists on the extension target and nowhere else,
wrapped around the one line that only makes sense in the app. Neither mistake showed up in a syntax check.
Both showed up the moment a real, full build ran — which is exactly the argument for insisting on one
before calling anything done, rather than trusting a green single-file check.

## What's left

Three intents that talk to Siri, a gesture on a watch, and now a Lock Screen you can act on without
unlocking — all from one afternoon's work, all still waiting on the one thing none of it can prove by
itself: a real phone in a real hand, saying the phrase, feeling the tap, watching the timer count up.
