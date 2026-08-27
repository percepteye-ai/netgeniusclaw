# Feature Specification: Border Agent Turn Latency + Voice-Aware Answers (Pass 2 of 3)

**Feature Branch**: `116-border-turn-latency`
**Created**: 2026-08-16
**Status**: Draft
**Input**: Border-side follow-up to `specs/115-siri-reliability-fix` (Pass 1, mobile-side, complete). Pass 1's handoff assumed the Border was slow because of how it *composes* answers. Border-side measurement on the live host disproves that and identifies a fixed per-turn startup cost instead.

## Context: what was measured

This spec exists because of evidence gathered on the running Border on 2026-08-16, not from a hypothesis:

| Observation | Measurement |
|---|---|
| A controlled question whose entire answer was the two characters "OK" | **37.9 seconds** end-to-end |
| Fixed preparation phase within that run | **26.9s**, of which **26.8s (99.6%)** was assembling the agent's tool set |
| The same conversation asked five separate questions | Paid the full ~27s **every** time — staying in one conversation does not amortize it |
| Every question ever asked from a phone (20 recorded) | **36s to 452s**. Not one finished inside the mobile side's 18-second spoken-answer window |
| Preparation cost across 30 sampled turns | 26.4s–29.8s — remarkably constant, independent of the question |

The decisive data point is the two-character answer. Because a reply of "OK" still took 37.9 seconds, **the length or style of the answer cannot be the cause**. The operator is paying a flat, unavoidable startup toll on every single interaction, before NetGeniusClaw begins thinking about the question at all.

This is not a voice-only problem. Every way an operator reaches NetGeniusClaw — chat in the mobile app, Slack, the command line, scheduled heartbeats — pays the same toll. Voice is simply where it became impossible to ignore, because a spoken assistant abandons the conversation while it waits.

## Clarifications

### Session 2026-08-16

- Q: May a capability become available only after a short first-use delay (lazy loading), provided nothing is permanently lost? → A: Yes — a capability may load on first use within a session, adding a one-time delay to the turn that first needs it, provided nothing is permanently lost and the delay is paid once.
- Q: How is the one-to-two-sentence limit on voice answers enforced? → A: By instruction at composition time — the agent is told to answer briefly and plainly for voice-marked requests and trusted to summarise honestly. No hard post-hoc truncation, which could invert an answer's meaning.
- Q: What form must the before-and-after measurement take? → A: A committed, repeatable measurement script reporting fixed preparation time, trivial-turn end-to-end time, and recent real phone-question durations — runnable by Pass 3 and any later session.
- Q: If part of the root cause lies in the agent runtime rather than NetGeniusClaw's own code, is the feature still "done"? → A: No — the measured targets are binding. Pass 2 uses every lever NetGeniusClaw controls (its own servers' startup cost, its configuration, how it invokes the agent); anything genuinely requiring an upstream change is documented with evidence but does not excuse missing the target.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - NetGeniusClaw answers without a fixed startup delay (Priority: P1)

An operator asks NetGeniusClaw anything, through any channel. Today, regardless of how trivial the question is, roughly half a minute passes before NetGeniusClaw can begin answering, because it rebuilds its entire toolkit from scratch first. The operator experiences this as NetGeniusClaw being uniformly sluggish — a question with a one-word answer feels no faster than one requiring real investigation. The operator needs the fixed toll removed so that simple questions come back quickly and the time NetGeniusClaw takes reflects the difficulty of the question asked.

**Why this priority**: This is the actual root cause and it degrades every single NetGeniusClaw interaction, not just voice. Nothing else in this spec produces a noticeable improvement while a ~27s toll remains on every turn, and no amount of shortening answers can pay it down.

**Independent Test**: Ask a question with a trivially short answer and measure wall-clock time from asking to answer. Compare against the recorded 37.9s baseline. Ask the same question again in the same conversation and confirm the second turn is not slower than the first.

**Acceptance Scenarios**:

1. **Given** a Border that has been running long enough to have served at least one prior request, **When** the operator asks a question that requires no external lookups, **Then** the complete answer arrives substantially faster than the 37.9-second baseline, with the fixed preparation phase no longer dominating the total.
2. **Given** the same Border, **When** the operator asks several questions in a row in the same conversation, **Then** no turn pays a full toolkit-rebuild cost, and later turns are no slower than the first.
3. **Given** a question that genuinely requires investigation (querying a lab, a device, or an external service), **When** it is asked, **Then** the time taken reflects that real work, and the operator is no longer additionally charged the fixed startup toll on top of it.
4. **Given** any channel the operator uses (phone chat, voice, Slack, command line, scheduled checks), **When** a request is made, **Then** the improvement applies there too — this is not a voice-only fast path.

---

### User Story 2 - A spoken question gets an answer shaped for speech (Priority: P2)

An operator asks NetGeniusClaw a question by voice. Today NetGeniusClaw composes every answer identically — structured for reading on a screen, with headers, bullet lists, and multiple paragraphs — because it has no idea the question arrived by voice. The operator needs NetGeniusClaw to know when a request came from a voice assistant and to answer in one or two plain spoken sentences instead.

**Why this priority**: A genuine quality improvement to the voice experience, and it becomes worth having only once User Story 1 makes answers arrive in time to be spoken at all. It is deliberately ranked below the latency work because a beautifully phrased spoken answer that arrives 37 seconds late is still never heard.

**Independent Test**: Submit a request marked as voice-originated and a functionally identical request with no marking. Confirm the first returns a short, plainly worded answer suitable for reading aloud, and the second returns exactly what NetGeniusClaw returns today.

**Acceptance Scenarios**:

1. **Given** a request that carries no origin marking (every request sent today), **When** it is answered, **Then** the answer is identical in form to today's — this change is invisible to existing callers.
2. **Given** a request marked as originating from a voice assistant, **When** it is answered, **Then** the answer is one or two short sentences of plain prose, with no headers, bullet lists, or emphasis markup.
3. **Given** a voice-marked request whose honest answer genuinely cannot fit in one or two sentences, **When** it is answered, **Then** the operator gets a truthful short summary rather than a truncated or misleading one.
4. **Given** a request marked with an origin value NetGeniusClaw does not recognize, **When** it is answered, **Then** NetGeniusClaw answers normally rather than failing the request.

---

### User Story 3 - A person waiting on an answer is served before background work (Priority: P3)

An operator asks a question while NetGeniusClaw is already busy with unattended background work. The operator, who is standing there waiting, needs their request to be worked on ahead of work nobody is watching.

**Why this priority**: Genuinely second-order, and the measurements say so: the 37.9-second baseline was recorded on a completely idle Border with nothing competing for attention. Prioritisation cannot explain or fix the observed problem — it only protects the improvement from being eroded later, under load.

**Independent Test**: Occupy the Border with background work, then ask an interactive question and confirm it is picked up ahead of the queued background work.

**Acceptance Scenarios**:

1. **Given** background work already in progress, **When** an operator asks a question interactively, **Then** their request begins being worked on without waiting for that background work to finish.
2. **Given** no competing work, **When** a request is prioritised, **Then** it behaves exactly as it would without prioritisation — no added overhead in the common idle case.

---

### Edge Cases

- **A tool NetGeniusClaw needs is slow or broken at the moment it is needed.** If the toolkit is no longer assembled up front on every turn, a faulty tool's failure surfaces at a different moment than it does today. NetGeniusClaw must still report such a failure clearly to the operator rather than hanging or silently answering as though the tool did not exist.
- **The very first request after the Border restarts.** Some warming cost may be unavoidable immediately after a restart. That first request may be slower, but it must not fail, and the operator should not be left without an answer.
- **Two operators (or an operator and a scheduled check) ask at the same moment.** Neither may block the other for the duration of a full toolkit rebuild.
- **NetGeniusClaw's own configuration changes while it is running** (a tool is added, removed, or reconfigured). NetGeniusClaw must pick up the change without requiring a restart and without serving a stale toolkit indefinitely.
- **A voice-marked question that returns an error or a refusal.** The short-spoken-answer rule must apply to that too — an error spoken aloud must be a plain sentence, not a formatted diagnostic block.
- **A request arrives marked as voice-originated but is very long or carries an attachment.** Origin marking must not change what NetGeniusClaw is willing to accept, only how it phrases the reply.

## Requirements *(mandatory)*

### Functional Requirements

**Latency (User Story 1)**

- **FR-001**: NetGeniusClaw MUST NOT rebuild its full tool set on every request. The preparation work that today accounts for ~27 seconds of every turn MUST be either reused across requests, performed concurrently rather than one item at a time, or deferred until actually needed.
- **FR-002**: The time NetGeniusClaw takes to answer MUST be dominated by the actual work the question requires, not by fixed preparation. Specifically, the fixed portion MUST become a small minority of a trivial request's total time, where today it is 99.6% of preparation and the clear majority of the whole.
- **FR-003**: The improvement MUST apply to every channel through which a request can arrive — phone chat, voice, Slack, command line, and scheduled/automated checks — not to a special-cased fast path for one of them.
- **FR-004**: NetGeniusClaw MUST retain access to every capability it has today. Reducing latency by permanently removing operator-facing capability is not an acceptable trade.
- **FR-004a**: A capability MAY be made ready on first use rather than before every turn. Where it is, the resulting delay MUST be paid once and MUST NOT recur on subsequent turns using that capability. Deferral may change *when* readiness is paid for, never *whether* the capability exists.
- **FR-004b**: A turn that triggers first-use readiness MUST still complete successfully and MUST NOT present to the operator as a hang. Such a turn being noticeably slower than a warm one is acceptable, provided FR-004a's once-only property holds.
- **FR-005**: When a capability cannot be made ready, NetGeniusClaw MUST surface that failure to the operator in the answer rather than silently proceeding as though the capability did not exist.
- **FR-006**: NetGeniusClaw MUST reflect changes to its own tool configuration without requiring a full restart, and MUST NOT serve an indefinitely stale tool set as a side effect of reusing preparation work.

**Voice-aware answers (User Story 2)**

- **FR-007**: A request reaching the Border MUST be able to carry an optional indication of where it originated.
- **FR-008**: A request that carries no origin indication MUST be handled exactly as it is today, with no observable difference in behaviour or in the shape of the answer — existing callers MUST NOT need to change.
- **FR-009**: The origin indication MUST be carried through from the point the request is received to the point the answer is composed, so composition can act on it.
- **FR-010**: When a request is marked as originating from a voice assistant, the answer MUST be composed as one or two short sentences of plain spoken prose, free of headers, list markers, and emphasis markup.
- **FR-011**: A shortened spoken answer MUST remain truthful and complete enough to stand on its own; where the full answer cannot fit, it MUST summarise honestly rather than mislead by omission.
- **FR-011a**: Brevity MUST be achieved by composing the answer short in the first place, NOT by mechanically shortening an answer after it is written. Cutting an answer to length after composition can invert its meaning (a status report truncated before its qualifying clause reads as its own opposite) and is therefore prohibited as the enforcement mechanism.
- **FR-012**: An unrecognised origin value MUST be treated as though no origin were supplied, and MUST NOT cause the request to fail.
- **FR-013**: The record of the request MUST retain its origin, so that after the fact an operator can tell how a given question reached NetGeniusClaw.

**Prioritisation (User Story 3)**

- **FR-014**: A request with a person actively waiting on it MUST be able to be worked on ahead of unattended background work.
- **FR-015**: Prioritisation MUST NOT add measurable overhead when nothing is competing, which is the common case.

**Verification**

- **FR-016**: The improvement MUST be demonstrable using the same measurements that identified the problem: the fixed preparation time per turn, the end-to-end time for a trivially-answerable question, and the recorded start-to-finish durations of real questions asked from a phone.
- **FR-016a**: Those three measurements MUST be produced by a committed, repeatable tool that any later session can run unaided, not by ad-hoc commands reconstructed from memory. It MUST be runnable by Pass 3 on demand and MUST report all three figures in one invocation.
- **FR-017**: A before-and-after comparison against the recorded 37.9-second baseline MUST be captured so Pass 3 can judge, on evidence, whether the mobile side's spoken-answer window is now appropriate.
- **FR-018**: The latency targets are binding regardless of where the cost originates. Every lever NetGeniusClaw controls — the startup cost of its own capability servers, its configuration, and how it invokes the agent — MUST be used as needed to meet them. Any residual portion that provably requires a change outside NetGeniusClaw MUST be documented with reproducible evidence, but does NOT excuse missing the targets.

### Key Entities

- **Agent Turn**: One complete cycle of NetGeniusClaw receiving a request, preparing itself, doing the work, and producing an answer. Its total duration currently divides into a large fixed preparation portion and a variable working portion; this feature targets the fixed portion.
- **Tool Set**: The collection of capabilities NetGeniusClaw can draw on to answer a question. Currently assembled in full at the start of every turn; the unit of work this feature makes reusable, concurrent, or deferred.
- **Request Origin**: An optional marker on an incoming request recording how it reached NetGeniusClaw (for example, a voice assistant versus the app's chat screen). Absent on every request sent today. Influences only how an answer is phrased, never what NetGeniusClaw is willing to do.
- **Answer Composition**: The step where NetGeniusClaw decides the wording and shape of its reply. Today identical regardless of origin; gains origin-awareness here.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A question with a trivially short answer is fully answered in **under 12 seconds**, measured the same way as the 37.9-second baseline — at least a 3× improvement.
- **SC-002**: The fixed preparation portion of a turn falls **below 3 seconds**, from the measured 26.8s — at least a 9× reduction, and no longer the dominant cost of a simple request.
- **SC-003**: Consecutive questions in one conversation show **no repeated full preparation cost**; the second and later turns are never slower than the first for equivalent questions.
- **SC-004**: Across a sample of at least 10 real questions asked from a phone after the change, the **median start-to-finish time is at least 3× faster** than the 36s–452s range recorded before it.
- **SC-005**: Every capability available to an operator before the change is still available after it, verified by exercising each one. Where a capability is made ready on first use, exercising it twice shows the readiness cost paid **only on the first** of the two.
- **SC-006**: Requests that carry no origin marking produce answers **indistinguishable from today's** across a representative sample — confirming existing callers are unaffected.
- **SC-007**: Voice-marked requests produce answers of **two sentences or fewer containing no formatting markup**, in at least 9 of 10 tries, and every one of those answers reads as a complete, self-standing statement rather than a sentence cut short.
- **SC-008**: A before-and-after measurement record exists covering fixed preparation time, trivial-question end-to-end time, and real phone-question durations, sufficient for Pass 3 to re-evaluate the spoken-answer window on evidence.
- **SC-009**: A later session with no knowledge of this work can reproduce all three measurements in a single command and get figures comparable to those recorded here.

## Assumptions

- **The mobile app is untouched by this pass.** No change to the NetGeniusClaw Mobile application, including the 18-second spoken-answer window. Re-tuning that window is explicitly a Pass 3 decision, to be made on the Mac against the evidence this pass produces (FR-017, SC-008).
- **The phone does not yet send an origin marker.** Today's requests carry only the question text and any attachment. The Border side is built here to accept the marker; the mobile side begins sending it in Pass 3. Until then User Story 2 is verifiable only by submitting a marked request directly, not through the phone — this is expected, not a defect.
- **Nothing in this spec changes what an answer means, or which capabilities NetGeniusClaw may use for a non-voice request.** Only the speed of getting to an answer, and the phrasing of voice-marked answers, are in scope.
- **The ~27s preparation cost is systemic rather than incidental.** It appeared on all 30 sampled turns within a narrow 26.4–29.8s band, on multiple conversations, on an idle machine. It is treated as a structural property of how a turn starts, not as contention or a transient fault.
- **The root cause may lie partly outside NetGeniusClaw's own code**, in the agent runtime NetGeniusClaw invokes. This does not relax the targets (FR-018). Most of the cost appears to be within reach regardless: the majority of the capability servers involved are NetGeniusClaw's own, and the two slowest load heavy libraries at startup — a cost NetGeniusClaw controls directly. Any residual portion that genuinely requires an upstream change is documented with reproducible evidence, but the targets still bind.
- **A modest first-request warming cost immediately after a restart is acceptable**, provided it is paid once rather than on every request, and provided that first request still succeeds.
- **Prioritisation is protective, not corrective.** It is included to keep the User Story 1 improvement from being eroded under future load, not because contention explains the measured problem — the baseline was recorded on an idle Border.
