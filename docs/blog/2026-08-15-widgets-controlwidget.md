# The Wizard Got the Address Wrong

**Draft for review — not published.** Constitution Principle XVII requires John's sign-off first.

*By John Capobianco and the agent · 2026-08-15*

Fourth NetGeniusClaw Mobile feature today, and the first that started with someone else's mistake — Apple's own
Xcode wizard, not ours, though it took a real build to find it.

## Two clicks in Xcode, one Apple Developer portal step avoided entirely

Home screen and Lock Screen widgets, plus a Control Center control, both needed a new App Group — the
mechanism that lets a widget process read data the main app wrote, since they're separate processes with
no other way to talk. The good news: this project signs automatically, so John never had to open the raw
Apple Developer web portal at all. Two clicks in Xcode's own Signing & Capabilities panel — add the App
Group capability, create the widget extension target — and Xcode registered everything with Apple on its
own.

## The new target came out attached to the wrong app

Verifying what Xcode actually built, rather than assuming the wizard did the obvious thing, turned up a
real problem: the new widget extension had been embedded inside the *Watch* app, not the phone app. Its
bundle identifier gave it away — `...watchapp.NetClawWidget` — and its entitlements file was pointing at
the watch's own App Group, the wrong one entirely. Somewhere in the wizard flow, whichever target happened
to be selected when "New Target" was clicked became the new extension's home, silently, with no warning
that anything unusual had happened.

Untangling it meant moving real Xcode project structure, not just a file: the target dependency and the
"embed this extension" build step both had to move from the Watch app to the phone app, the bundle
identifier had to be renamed into the phone app's own namespace, and the entitlements had to point at the
right App Group. A stray build setting survived even after all of that — `TARGETED_DEVICE_FAMILY` was still
set to the code for "Watch," not "iPhone or iPad" — caught only because a genuinely full build still
produced one warning after everything else looked fixed, and it turned out to be worth chasing down rather
than ignoring.

## The brief's Control Center design didn't survive contact with the actual API

The brief wanted the Control Center button to invoke NetGeniusClaw's existing "ask a question" capability
directly. Checking that intent's actual signature before writing any code found the problem: it requires a
question typed in as text, and Control Center has no keyboard, no text field, nothing to type into. The
button instead does something more honest about what a single tap from Control Center can actually
accomplish: it opens the app straight to the chat screen, cursor already in the compose field, ready for
the question to actually get typed. One less step than opening the app cold, without pretending a tap
alone can submit words nobody wrote.

## What's left

Every scenario in this pass is something you can only really judge by holding the phone: does the widget
actually show up when you long-press the home screen, does the Lock Screen version stay legible at that
size, does tapping Control Center's button really land you in a ready-to-type chat and not somewhere
confusing. Four features finished today, and the same one honest gap behind all four — nothing left that
doesn't need a hand and a real screen to say it's actually done.
