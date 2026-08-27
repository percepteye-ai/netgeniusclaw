# Pass 2 Handoff: Border-side awareness of Siri-originated requests

**For**: a fresh Claude Code session on the Linux Border host
**From**: Pass 1, completed on the Mac (branch `115-siri-reliability-fix`, already pushed)
**Read first**: `specs/115-siri-reliability-fix/spec.md`, `research.md` (especially R4 and R5) —
this file is a pointer into that context, not a replacement for it.

## What Pass 1 already did (mobile side, done, do not redo)

Fixed three real bugs that made Siri/Shortcuts never reach NetGeniusClaw at all on a fresh install
(missing entry-point imports, unsafe duplicate Firebase plugin registration causing an on-device
crash, and a missing `libraryURI` on `FlutterEngineGroup.makeEngine`). Also added:

- **True two-way voice**: `AskBorderIntent` now waits up to `askBorderFastWindow` (currently 18s,
  tuned empirically against this Siri's real observed patience) for a real, finished answer it can
  hand straight back for Siri to speak, instead of always saying a generic "Sent to NetGeniusClaw, I'll
  let you know when it answers." Falls back to that acknowledgment + background notify/reconcile
  only if the agent hasn't finished in time.
- **Markdown stripping**: whatever answer text *is* spoken by the fast path has `**bold**`,
  `# headers`, and `- ` bullet markers stripped client-side by a regex
  (`stripMarkdownForSpeech` in `mobile/netclaw-mobile/lib/ncfed/ask_border_headless.dart`) before
  Siri says it aloud.
- Every Siri-originated request is already tagged `origin: 'siri'` in the phone's conversation
  store — this was already true before Pass 1, not new.

## What's actually still a problem (this is Pass 2's job)

The client-side markdown strip is a blunt fix for a Border-side problem: **the agent composes
every answer the same way regardless of who's asking**, optimized for reading in the app's Chat
screen (headers, bullet lists, multi-paragraph structure), not for being spoken aloud by Siri in
under ~18 seconds. Two concrete, real consequences observed live tonight:

1. Even "fast" questions (e.g. a simple CML API status check) regularly took *longer than 18
   seconds* for the agent to compose an answer for — not because the underlying tool call was
   slow, but because the agent's normal answer-composition style (multi-paragraph, structured)
   takes real LLM generation time on top of the tool call itself.
2. When an answer *did* arrive in time, it was still full-length prose written for reading, and
   the client-side regex strip is a crude patch — it removes markdown syntax but doesn't shorten
   the answer or make it read naturally as speech (e.g. it won't turn a 4-sentence status report
   into a 1-sentence spoken summary).

## The two things worth investigating and building here

1. **Origin-aware answer composition.** Wherever the Border currently composes the final answer
   text for a task (this needs to be located in this codebase — it wasn't touched or explored
   during Pass 1, which was entirely mobile-side), check whether the originating request's
   `origin` field (`siri` vs. `phone`/other) is available at that point, and if so, thread through
   an instruction like "if origin is siri, answer in 1-2 plain spoken sentences, no markdown, no
   lists" specifically for Siri-tagged turns. If `origin` isn't currently threaded that far into
   the composition step, that's the first real piece of Pass 2 work — it already exists at the
   mobile-to-Border request boundary (the phone tags it), so this is very likely a matter of
   passing an existing field one or two layers further than it currently goes, not inventing new
   plumbing.
2. **Priority for Siri-tagged tasks**, so they get worked on ahead of other queued work when the
   queue isn't empty — directly improves the odds of finishing inside the mobile side's fast-voice
   window. Investigate the task queue/scheduling code to see whether this is a small priority-field
   addition or a bigger scheduling change before committing to scope.

## What to explicitly NOT do here

- Don't touch anything on the mobile side — Pass 1 is done and verified; re-touching it risks
  regressing a hard-won fix.
- Don't change the mobile-side `askBorderFastWindow` value from here — if Border-side changes
  make answers reliably faster, that's a mobile-side follow-up (Pass 3) to reconsider, not
  something to tune blind from the Border.
- Don't assume specific Border file paths — this handoff deliberately doesn't name them because
  Pass 1 never explored the Border codebase; locate the actual answer-composition and
  task-scheduling code fresh, on the Linux host, before proposing a design.

## Suggested next step

Run `/speckit.specify` fresh, in this new session, with something like: "NetGeniusClaw Border-side
handling of Siri-tagged requests (Pass 2 of 3, Linux Border host). Following up on
specs/115-siri-reliability-fix (Pass 1, mobile-side): every Siri-originated request is already
tagged origin='siri'. Investigate where the Border composes a task's final answer text and
whether that composition can be made voice-friendly (short, no markdown) specifically for
origin='siri' turns, and whether Siri-tagged tasks can be prioritized in the queue to more often
finish within the mobile side's ~18s fast-voice window (mobile side is out of scope; do not modify
it)." — then let `/speckit.plan`/`/speckit.tasks`/`/speckit.analyze` run their normal course
against whatever the Border codebase actually looks like.

## Pass 3 (back on the Mac, after Pass 2 lands)

Once Pass 2 ships, come back to the Mac (or wherever the phone is reachable) to re-verify the
full loop end-to-end: does a real, in-the-wild Siri question now more reliably land inside
`askBorderFastWindow` and get spoken instead of falling back to the acknowledgment? If Pass 2's
answers are meaningfully faster/shorter, this is also the point to reconsider whether 18s is
still the right value, or whether it can be safely lowered again now that the Border itself is
doing more of the work.
