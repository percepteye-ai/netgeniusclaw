# Feature Specification: Siri Voice Window Tuning and Origin Marker (Pass 3 of 3)

**Feature Branch**: `117-siri-voice-tuning`
**Created**: 2026-08-16
**Status**: Draft
**Input**: User description: "NetGeniusClaw mobile-side Pass 3 of 3, following up on specs/115-siri-reliability-fix (Pass 1, mobile) and specs/116-border-turn-latency (Pass 2, Border-side, merged to main via PR #250). Pass 2's PASS3-HANDOFF.md reports the Border's fixed per-turn startup toll dropped from 37.9s to ~9s on a cold/first turn in a session and ~3.9s on every turn after that. Two concrete Pass 3 items, both explicitly deferred by Pass 2: (1) re-tune the phone's flat 18s askBorderFastWindow against the new ~9s cold / ~3.9s warm numbers; (2) wire AskBorderIntent to pass an origin='voice' marker on every Siri-tagged call so the Border's already-built voice-aware answer composition actually gets used. Once both are wired, re-verify the full loop end-to-end with a real, unlocked, connected iPhone. Mobile-side focused — do not modify gateway.py/gateway_ws.py, which Pass 2 already completed and verified."

## Context: what Pass 2 changed and left undone

Pass 2 (spec 116) fixed the Border's fixed per-turn startup cost and, separately, taught
`run_agent_turn()` to accept an optional `origin` parameter that produces a short, plainly worded
answer instead of the usual structured/markdown one. Neither change is visible to a real Siri user
yet, for two independent reasons:

1. **The phone's spoken-answer window was tuned for a world that no longer exists.** Spec 115 (Pass
   1) chose 18 seconds because every turn — first, second, tenth — cost the same ~38 seconds and
   none of them fit inside 18s anyway; 18s was an outer bound before falling back to "I'll let you
   know when it answers," not a real target. Pass 2's own measurements show a cold first-in-session
   turn now lands around 9 seconds and every turn after that under 4 seconds — comfortably inside an
   even shorter window than today's.
2. **Nothing tells the Border a request came from Siri.** `run_agent_turn(origin="voice")` exists and
   is verified to work when called directly, but the phone's outbound `n2n/edge/ask` request carries
   no such marker, and the Border's own handler for that request never reads or forwards one. A real
   Siri question today still gets the full markdown/structured answer style, stripped of markdown
   syntax on-device as a blunt patch (spec 115) rather than composed for speech in the first place.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A cold first Siri question of the day still gets a spoken answer (Priority: P1)

An operator asks Siri a NetGeniusClaw question for the first time since the Border was last restarted (or
since their phone's session went idle). Today this is the worst case: the very turn most likely to
pay the Border's cold-start cost is racing against a window sized for a much slower world. The
operator needs the window re-tuned against Pass 2's real numbers so that even this worst-case turn
still has a realistic chance of finishing in time to be spoken, rather than the window being
needlessly generous now that the underlying wait it was hedging against no longer happens.

**Why this priority**: This is the entire point of Pass 3 — Pass 1's number was correct for the data
it had, and that data is now stale. Getting the window right is what turns Pass 2's latency fix into
something the operator actually experiences on a real device.

**Independent Test**: With the Border freshly restarted (or a phone session that has gone idle long
enough to be "cold"), ask a real question by Siri and time whether a real spoken answer, not the
generic acknowledgment, is heard.

**Acceptance Scenarios**:

1. **Given** a Border that has not yet served a request in the current phone session, **When** the
   operator asks a simple question by Siri, **Then** the answer is spoken aloud rather than replaced
   by the "Sent to NetGeniusClaw, I'll let you know when it answers" fallback, in the large majority of
   real attempts.
2. **Given** the same phone session, **When** the operator asks a second and third question in
   quick succession, **Then** each is at least as likely to be spoken in time as the first, since the
   Border's own warm-turn cost is lower, not higher.
3. **Given** a question that genuinely requires extended investigation (well beyond either the old
   or new window), **When** it is asked by Siri, **Then** the existing fallback-and-notify behavior
   is unchanged — this story narrows how often the fallback is needed, it does not remove it.

---

### User Story 2 - A spoken answer sounds like it was meant to be heard (Priority: P2)

An operator asks NetGeniusClaw a question by Siri. Today the Border has no way to know the request came
from a voice assistant, so it composes the same structured, multi-paragraph answer it would for
someone reading the app's Chat screen — and the phone can only crudely strip markdown syntax
afterward, which does not shorten the answer or make it read naturally. The operator needs the
Border to know, from the moment it starts composing, that this particular answer will be spoken, so
it can write one or two plain sentences instead.

**Why this priority**: A meaningful quality improvement, but it depends on User Story 1 — an answer
composed beautifully for speech that still arrives after the window closes is never heard. Ranked
below the timing fix for that reason, same as it was in Pass 2's own framing.

**Independent Test**: Ask an identical simple question twice — once by Siri, once through the app's
ordinary chat screen — and confirm the Siri-originated answer is shorter, plainer, and free of
markdown syntax at the source, while the chat-screen answer is unchanged from today.

**Acceptance Scenarios**:

1. **Given** the operator asks a simple factual question by Siri, **When** the Border composes its
   answer, **Then** the answer is 1-2 plain spoken sentences with no markdown syntax, composed that
   way by the Border itself rather than only cleaned up afterward on the phone.
2. **Given** the operator asks the identical question through the app's normal chat interface (not
   Siri), **When** the Border composes its answer, **Then** the answer is unchanged from today's
   behavior — structured, full-length, exactly as before.
3. **Given** a Siri question whose honest answer genuinely requires synthesizing a large amount of
   structured data (e.g., a full device health report), **When** the Border composes its answer,
   **Then** it is not truncated or falsified to force brevity — a longer, still-clear answer is
   acceptable in this case, matching Pass 2's own documented decision that honesty outranks the
   brevity instruction.

---

### User Story 3 - The full Siri loop is verified end-to-end on a real phone (Priority: P1)

Before either change above is considered done, an operator with a real, unlocked, connected iPhone
asks NetGeniusClaw genuine questions by Siri and confirms, by listening, that the loop behaves as
intended: a normal question is answered aloud, promptly, in natural spoken language.

**Why this priority**: Every prior pass in this three-part effort (115, 116) was verified against
live measurements or a live device at some point; this is the first time the *combined* effect of
all three passes is heard by an operator asking a real question, not just measured in isolation.
Equal priority to User Story 1 because a change that looks correct on paper but fails live blocks
the other two from being considered complete.

**Independent Test**: With a real device, ask several real NetGeniusClaw questions by Siri across a
range of difficulty (trivial fact, a status check requiring one tool call, something requiring
genuine investigation) and confirm the experience matches what User Stories 1 and 2 describe.

**Acceptance Scenarios**:

1. **Given** a real, unlocked iPhone enrolled with NetGeniusClaw, **When** the operator asks a trivial
   question by Siri, **Then** a real spoken answer, not the acknowledgment fallback, is heard, and it
   is short and plainly worded.
2. **Given** the same device, **When** the operator asks a question that requires one real tool call
   (e.g., a lab or device status check), **Then** the operator can hear whether it lands inside the
   new window or falls back, and that outcome matches what Pass 2's measurements would predict.
3. **Given** the same device, **When** the operator asks a non-Siri question through the app's chat
   screen, **Then** nothing about that experience has changed.

### Edge Cases

- What happens if the phone's session with the Border is not warm (e.g., first launch after a
  restart, or the enrollment reconnects mid-question)? The fallback-and-background-notify path
  (unchanged from Pass 1) must still apply — a shorter window makes the fallback path fire somewhat
  more often for genuinely slow turns, not less reliable.
- What happens if the Border cannot recognize the new marker at all (an older Border build, or a
  request that reaches a code path that never learned to forward it)? The request must still
  succeed and be answered exactly as it is today — an unrecognized or missing marker is not an
  error condition anywhere in this loop.
- What happens when a Siri-marked question's honest answer cannot be reduced to 1-2 sentences
  without losing or distorting meaning? The Border must give a clear, complete answer even if longer
  than ideal for speech — never truncate or simplify in a way that changes what is actually true.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The phone's spoken-answer window (today a flat 18 seconds, `askBorderFastWindow`)
  MUST be re-tuned against Pass 2's measured numbers (~9s for a cold/first turn in a session, ~3.9s
  for every turn after) so that a cold first-in-session turn has a realistic chance of finishing
  inside it, while remaining meaningfully shorter than today's value.
- **FR-002**: Every Siri-originated request the phone sends MUST be marked as voice-originated on
  the wire, in a form the Border can recognize as equivalent to the `origin="voice"` value
  `run_agent_turn()` already accepts.
- **FR-003**: The Border's handler for a phone's ask request MUST read the voice-origin marker, when
  present, and forward it through to the agent-turn composition step so the Border's existing
  voice-aware answer style is actually applied to Siri-originated questions.
- **FR-004**: A request that carries no voice-origin marker (the app's own chat screen, or an older
  phone build) MUST be answered exactly as it is today — no change to non-Siri behavior.
- **FR-005**: A Border build that does not recognize the voice-origin marker MUST still process the
  request normally and answer it — an unrecognized or absent marker is never an error.
- **FR-006**: The fallback-and-background-notify behavior for a turn that does not finish inside the
  (re-tuned) window MUST be unchanged in mechanism — only the window's duration changes, not what
  happens when it elapses.
- **FR-007**: The client-side markdown-stripping behavior introduced in Pass 1 MUST remain in place
  as a safety net, applied to whatever text is handed back for Siri to speak, regardless of whether
  the Border composed it as plain speech-ready text or not.
- **FR-008**: Before this feature is considered complete, the combined effect of the re-tuned window
  and the voice-origin marker MUST be verified against a real, unlocked, connected phone asking
  genuine questions by Siri, covering at least: a trivial question, a question requiring one real
  tool call, and a normal (non-Siri) chat-screen question used as a control.

### Key Entities

- **Spoken-answer window**: The duration the phone waits, after submitting a Siri-originated
  question, for a real finished answer it can hand back for Siri to speak before instead returning a
  generic acknowledgment. Currently a single fixed value; this feature's outcome determines its new
  value.
- **Voice-origin marker**: A piece of information carried on a phone-to-Border ask request
  indicating the request came from Siri, distinct from ordinary chat-screen requests. Consumed by
  the Border's answer-composition step to choose a short, plainly worded style instead of the
  default structured one.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a real device, a trivial Siri question asked as the first question in a fresh phone
  session is answered aloud (not the acknowledgment fallback) in a clear majority of real attempts.
- **SC-002**: On a real device, a trivial Siri question asked as the second or later question in the
  same session is answered aloud in nearly all real attempts.
- **SC-003**: A Siri-originated answer to a simple factual question is noticeably shorter and
  contains no leftover markdown syntax, as heard by the operator, compared to the same question
  asked through the app's chat screen.
- **SC-004**: A non-Siri question asked through the app's chat screen produces an answer
  indistinguishable in length, structure, and content from what it produced before this feature.
- **SC-005**: The re-tuned spoken-answer window value and the rationale for choosing it are recorded
  somewhere a future pass can find without re-deriving Pass 2's measurements from scratch.

## Assumptions

- Pass 2's measured numbers (~9s cold, ~3.9s warm) hold on the same live Border this feature is
  verified against; if a live measurement during this pass disagrees meaningfully, the window is
  tuned against the fresh measurement, not the numbers quoted in Pass 2's handoff.
- The exact new window value (a specific number of seconds) is an implementation decision made
  during planning against live measurement, not fixed by this spec — the spec's requirement is that
  it be re-tuned and meaningfully shorter than 18s, not a specific number.
- The voice-origin marker's on-the-wire shape (parameter name, value) is an implementation detail
  decided during planning to match whatever `run_agent_turn(origin=...)` and the existing
  `n2n/edge/ask` request already expect or can cheaply be extended to carry, not fixed by this spec.
- Threading the marker from the phone's request through to `run_agent_turn()` may require a small
  change to the Border's own ask-request handler (the code that receives `n2n/edge/ask` and calls
  `run_agent_turn()`), since that handler does not read or forward any such marker today. This is
  in scope for this feature even though it touches Border-side code, because Pass 2 built the
  receiving end (`run_agent_turn(origin=...)`) but explicitly left this specific wiring for Pass 3.
  Pass 2's own files that implement the latency fix itself (the persistent WebSocket dispatch
  mechanism) are out of scope and must not be modified.
- This feature does not add prioritization, queueing changes, or any other latency work beyond
  re-tuning the existing window — Pass 2 already investigated and rejected adding queue
  prioritization as unnecessary.
