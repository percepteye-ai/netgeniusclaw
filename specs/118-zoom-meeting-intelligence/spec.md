# Feature Specification: NetGeniusClaw for Zoom — Meeting Intelligence (MVP)

**Feature Branch**: `118-zoom-meeting-intelligence`
**Created**: 2026-08-17
**Status**: Draft
**Input**: User description: "NetGeniusClaw for Zoom — Meeting Intelligence (MVP pass). Give the Border Claw a new sensory/human-interface surface: Zoom meetings, built on Realtime Media Streams (RTMS) rather than a Meeting SDK bot participant — Zoom now reserves Meeting SDK for human use and directs AI applications to RTMS instead. Five components: (1) an RTMS live-context listener that captures transcript, meeting chat, active speaker, and screen-share/content signals into a bounded live-context buffer; (2) an official Zoom Meetings MCP connection for historical meeting search/assets/recordings; (3) a zoom-meeting-context skill that recognizes investigation intent (location/technology/time-window) in live speech/chat and routes it into the existing NCFED/Border architecture to Member Claws (pyATS, NetBox, Splunk, etc.); (4) a NetGeniusClaw Zoom App side-panel surface showing live status/topic/investigation progress/evidence, usable by all meeting participants via Collaborate Mode/Guest Mode without requiring install; (5) a safety gate ensuring meeting speech follows the existing READ-vs-WRITE / HumanRail approval model — diagnostic requests execute directly, anything write/config-changing heard in conversation requires explicit approval, GAIT-audited like every other write path. Explicitly out of scope for this pass: an autonomous video-tile participant, animated/lip-synced avatar, or any injection of synthesized audio/video into the live meeting — deferred to a later pass since Zoom's current avatar features represent a human user or produce async clips, not a live autonomous participant, and Meeting SDK (the only route to injecting a live audio/video stream) is closed to AI applications."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a live network question during a meeting and get an evidence-backed answer (Priority: P1)

An operator is on a Zoom call — an outage bridge, a standup, a design review — and someone asks a
question about the live network ("Toronto lost its BGP sessions about ten minutes ago, what
happened?"). Without anyone opening a laptop to run commands or leaving the call to check a
dashboard, the question is recognized, investigated using the network's actual current state, and
answered with supporting evidence — visible to the meeting, not just to whoever asked.

**Why this priority**: This is the entire reason for the feature. Every other component exists to
make this one moment possible: hearing the question, knowing what it means, investigating it for
real, and answering back into the room. Without this, NetGeniusClaw for Zoom is just a transcription tool.

**Independent Test**: Start a meeting with listening enabled, have a participant ask a
location+technology+time-bounded question about the network out loud, and confirm an
evidence-backed answer appears in the shared panel within a reasonable time — without any bot
appearing as a video participant.

**Acceptance Scenarios**:

1. **Given** listening is enabled for an active meeting, **When** a participant asks a spoken
   question naming a location, a technology, and an approximate time window, **Then** NetGeniusClaw
   recognizes it as an investigation request and begins routing it to the appropriate existing
   tooling without any participant needing to type a command.
2. **Given** an investigation request has been routed, **When** the underlying tooling returns
   results, **Then** the meeting sees a synthesized answer with supporting evidence (what was
   checked, what was found, what it means) rather than raw tool output.
3. **Given** the same question is asked entirely through meeting chat instead of speech, **When**
   NetGeniusClaw processes the chat message, **Then** it is recognized and routed identically to a spoken
   question.
4. **Given** no bot or avatar has joined the meeting's participant list, **When** the investigation
   completes, **Then** the answer still reaches the meeting through the shared panel, not through a
   simulated voice or video presence.

---

### User Story 2 - Correlate today's discussion with a past meeting or incident (Priority: P2)

An operator recalls that a similar problem came up in a previous meeting ("didn't we have this same
issue when we discussed the Montreal firewall problem last month?") but doesn't remember the
details. NetGeniusClaw searches prior meeting history, retrieves the relevant discussion and any related
assets, and compares what was true then against what's true on the network right now.

**Why this priority**: This turns individual meetings into organizational memory. It's high-value but
depends on User Story 1's live-recognition path already working, so it follows rather than leads.

**Independent Test**: Reference a prior, real meeting by topic during a live call and confirm NetGeniusClaw
retrieves and summarizes the relevant historical content, then states whether the current network
state matches or differs from that prior discussion.

**Acceptance Scenarios**:

1. **Given** a participant references a past discussion by topic or approximate timeframe, **When**
   NetGeniusClaw processes the reference, **Then** it searches historical meeting content and surfaces the
   most relevant match(es).
2. **Given** a relevant past meeting is found, **When** NetGeniusClaw presents it, **Then** it also states
   whether the network's current state matches or differs from what was discussed previously.
3. **Given** no matching past meeting exists, **When** NetGeniusClaw searches, **Then** it says so plainly
   rather than presenting an unrelated result as if it were relevant.

---

### User Story 3 - Every meeting participant can see NetGeniusClaw's status and findings, not just the host (Priority: P2)

Anyone in the meeting — including a guest who was invited to the call but has never installed or
signed into anything NetClaw-related — can see that NetGeniusClaw is listening, what topic it thinks is
under discussion, what it's currently checking, and the results, all inside the meeting itself. This
is presented through a visible avatar persona (not a video-tile participant) so the room reads
NetGeniusClaw as present, not just as a status widget.

**Why this priority**: A live-investigation feature that only one person can see defeats the purpose
of running it during a shared meeting. This is required for the feature to feel like a participant
the whole room can rely on, not a personal tool for whoever set it up.

**Independent Test**: Join a meeting with listening enabled as a guest participant who has not
installed or authenticated anything, open the shared panel, and confirm the same live status,
avatar state, and results are visible as to the meeting's host.

**Acceptance Scenarios**:

1. **Given** listening is enabled for a meeting, **When** any participant opens the shared panel,
   **Then** they see the current listening status, detected topic, an avatar reflecting NetGeniusClaw's
   current activity (listening, thinking, investigating, or answered), and any in-progress or
   completed investigation.
2. **Given** a participant has not installed or authenticated the NetGeniusClaw surface before the
   meeting, **When** they are invited into the shared view during the call, **Then** they can see
   the same live state and avatar as everyone else without a separate install or login step.
3. **Given** an investigation produces evidence or a topology result, **When** it is ready, **Then**
   it appears in the shared panel for all current viewers at the same time, not just the requester,
   and the avatar reflects the "answered" state.
4. **Given** NetGeniusClaw's activity changes state (e.g., moves from listening to actively investigating),
   **When** the change occurs, **Then** the avatar's visual state updates for every current viewer
   within a short, perceptible delay.

---

### User Story 5 - NetGeniusClaw's avatar is visibly present on a presenter's own camera feed, not just in a side panel (Priority: P3)

A participant who is presenting or on camera chooses to let NetGeniusClaw's avatar appear as a small
overlay on their own outgoing video — a visible presence in the actual video grid, layered onto a
real participant's feed, rather than confined to a side panel only the curious open. This makes
NetGeniusClaw feel like it's "in the room" during screen shares and camera-on discussion, without NetGeniusClaw
occupying its own tile in the participant list or injecting any audio of its own.

**Why this priority**: This is a visibility enhancement on top of User Story 3, not a safety- or
correctness-critical path, and it depends on a participant explicitly opting in — it follows behind
the core investigation and safety stories.

**Independent Test**: As a participant with camera on, enable the NetGeniusClaw overlay for your own feed,
confirm the avatar bubble appears on your outgoing video for other participants to see, then disable
it and confirm it disappears — all without NetGeniusClaw ever appearing as a separate participant tile or
producing its own audio.

**Acceptance Scenarios**:

1. **Given** a participant has their camera on, **When** they explicitly enable the NetGeniusClaw overlay
   for their own feed, **Then** the avatar appears as a small overlay on that participant's outgoing
   video, visible to everyone in the meeting.
2. **Given** the overlay is enabled on a participant's feed, **When** NetGeniusClaw's activity state
   changes, **Then** the overlay reflects the same state shown in the shared panel.
3. **Given** a participant enabled the overlay on their own feed, **When** that same participant
   disables it, **Then** the overlay is removed from their video immediately and does not reappear
   without being re-enabled.
4. **Given** the overlay is active, **When** NetGeniusClaw produces a spoken-style answer, **Then** the
   answer is still delivered through the shared panel (text/visual), not through synthesized audio
   mixed into the presenter's microphone or the meeting's audio.
5. **Given** a participant turns their camera off while the overlay is enabled, **When** the camera
   is off, **Then** no overlay is shown (there is no feed to overlay onto), and it resumes
   automatically if the participant turns the camera back on without needing to re-enable it.

---

### User Story 4 - A casual remark in conversation is never treated as authorization to change the network (Priority: P1)

During a meeting, someone says something like "maybe we should just shut that interface" as a
passing thought, not a decision. NetGeniusClaw must never interpret ordinary conversational speech as
approval to make a change. Any actual configuration-changing action heard in a meeting still has to
go through the same explicit human approval step required everywhere else in NetGeniusClaw.

**Why this priority**: This is a safety-critical boundary, not a feature enhancement. Getting User
Story 1 right without this would make the feature actively dangerous — the fastest way to lose trust
in a tool that listens to meetings is for it to act on words that were never meant as instructions.

**Independent Test**: Say a sentence during a meeting that describes a network change in a
hypothetical, past-tense, or suggestive way (not a direct command) and confirm no change is
attempted; separately, issue a direct request for a configuration change and confirm it is held for
explicit approval rather than executed immediately.

**Acceptance Scenarios**:

1. **Given** a participant speaks a sentence describing a configuration change in a hypothetical,
   past-tense, or third-party context ("we could shut that interface", "they shut the interface last
   time"), **When** NetGeniusClaw processes it, **Then** no change is attempted and nothing is queued for
   approval.
2. **Given** a participant directly requests a configuration-changing action during a meeting,
   **When** NetGeniusClaw recognizes the request, **Then** the action is held for explicit human approval
   through the existing approval mechanism before anything executes.
3. **Given** a read-only or diagnostic request is made (checking status, running a non-disruptive
   test), **When** NetGeniusClaw recognizes it, **Then** it executes without requiring the extra approval
   step, consistent with how NetGeniusClaw already treats read vs. write actions elsewhere.
4. **Given** an approval is required, **When** it is granted or denied, **Then** the decision and the
   original meeting request that triggered it are both recorded in the existing audit trail.

---

### Edge Cases

- What happens if the meeting ends (or the operator leaves) while an investigation is still in
  progress? The in-progress work and its eventual result should not be silently lost, but the live
  meeting buffer itself should not persist past the meeting's end.
- What happens when two different questions are asked close together, before the first has finished
  being answered? Each should be tracked and answered distinctly rather than the second overwriting
  or being merged into the first.
- What happens when the recognized location, technology, or time window is ambiguous or unresolvable
  (e.g., a location name that doesn't map to any known site)? NetGeniusClaw should say what it couldn't
  resolve rather than guessing silently or investigating the wrong thing.
- What happens if the connection carrying live meeting signals drops mid-meeting? Listening status
  in the shared panel should reflect the disruption rather than silently appearing to still be
  listening.
- What happens when a participant asks a question that requires tooling that isn't registered/
  available? NetGeniusClaw should say the investigation can't be completed and why, rather than fabricating
  an answer.
- What happens when the same investigation request is detected from both speech and chat within the
  same moment (someone says it and also types it)? It should be treated as one request, not two.
- What happens if a participant enables the camera overlay and then stops sharing their video
  entirely (leaves the meeting, camera fails)? The overlay should not persist or reappear on anyone
  else's feed.
- What happens if more than one participant enables the camera overlay at the same time? Each
  enabling participant's own feed should show the overlay independently; enabling it should never
  require or imply consent from anyone else in the meeting.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow live meeting listening to be enabled for a specific Zoom meeting
  without requiring any bot or avatar to join that meeting's video/participant roster.
- **FR-002**: System MUST maintain a rolling, bounded window of recent meeting transcript, meeting
  chat, active-speaker, and shared-content signals sufficient to interpret "what's been discussed" in
  the recent minutes of a listening-enabled meeting.
- **FR-003**: System MUST recognize when a spoken utterance or chat message expresses a network
  investigation request, extracting at minimum the relevant location, technology/system, and
  approximate time window when present.
- **FR-004**: System MUST route a recognized investigation request to the existing member-tool
  routing path (whichever tools are registered) and MUST NOT attempt investigation using anything
  outside that existing routing path.
- **FR-005**: System MUST return a synthesized, evidence-backed answer for a completed investigation
  rather than raw tool output, and MUST make that answer visible in the meeting's shared panel.
- **FR-006**: System MUST distinguish requests that only read or diagnose network state from requests
  that would change network configuration, using NetGeniusClaw's existing read/write classification.
- **FR-007**: System MUST execute recognized read/diagnostic requests without requiring additional
  approval beyond what NetGeniusClaw already requires for the same request made through any other channel.
- **FR-008**: System MUST hold any recognized write/configuration-changing request for explicit human
  approval through NetGeniusClaw's existing approval mechanism before any such action executes, regardless
  of how directly or casually the request was phrased in conversation.
- **FR-009**: System MUST NOT treat hypothetical, past-tense, third-party-attributed, or otherwise
  non-directive conversational speech as an approval or authorization for any action.
- **FR-010**: System MUST allow historical meeting content (past transcripts, assets, recordings) to
  be searched and retrieved, and MUST be able to state whether current network state matches or
  differs from a retrieved past discussion.
- **FR-011**: System MUST make live listening status, detected topic, in-progress investigation
  steps, and results visible, in a shared view, to every current meeting participant who opens the
  NetGeniusClaw meeting surface — not only the participant who triggered a given request.
- **FR-012**: System MUST allow a meeting participant to view and use the shared NetGeniusClaw meeting
  surface without a prior individual install or authentication step for that participant.
- **FR-013**: System MUST record every recognized investigation request, its routing, its result, and
  any related approval decision in NetGeniusClaw's existing audit trail.
- **FR-014**: System MUST stop listening and discard the live meeting buffer when a meeting ends or
  when listening is explicitly disabled for that meeting.
- **FR-015**: System MUST allow an authorized user to see which meetings currently have listening
  enabled and to disable listening for any of them at any time.
- **FR-016**: System MUST NOT create an independent video-tile participant for NetGeniusClaw and MUST NOT
  inject synthesized audio into the meeting's audio mix, in this pass — this is an explicit scope
  boundary, not a temporary limitation to be silently worked around. This boundary governs
  *audio and independent participant identity*; it does not prohibit the visual avatar surfaces
  described in FR-017–FR-020 below.
- **FR-017**: System MUST present an animated avatar persona, with visually distinct states for at
  least listening, thinking/investigating, and answered, within the shared meeting panel.
- **FR-018**: System MUST allow a participant to explicitly enable an overlay of the avatar persona
  onto that participant's own outgoing camera video, visible to the rest of the meeting.
- **FR-019**: System MUST allow the participant who enabled the camera overlay to disable it at any
  time, with the overlay disappearing from their feed immediately, and MUST NOT enable the overlay on
  any participant's feed without that participant's own explicit action.
- **FR-020**: The camera-overlay avatar MUST reflect the same activity state shown in the shared
  panel and MUST NOT carry or mix in any synthesized audio of its own.

### Key Entities

- **Meeting Session**: A single Zoom meeting for which listening is or was enabled; tracks its
  listening status, start/end time, and which participants have viewed the shared surface. Ceases to
  exist once the meeting ends.
- **Live Context Buffer**: The rolling window of recent transcript, chat, active-speaker, and
  shared-content signals for one Meeting Session; bounded in size/duration; discarded when the
  session ends.
- **Investigation Request**: A recognized instance of meeting speech or chat expressing a network
  question, with its extracted location/technology/time-window, its routing outcome, and its final
  answer or failure reason.
- **Historical Meeting Reference**: A past meeting's transcript/assets/recordings, retrieved by
  search, used for correlating a live discussion against prior discussions or incidents.
- **Approval Decision**: A record of a write/configuration-changing request detected in a meeting,
  the human approval or denial it received, and the outcome — linked to NetGeniusClaw's existing audit
  trail.
- **Avatar State**: The current visual persona state (listening, thinking/investigating, answered)
  shared identically between the meeting panel and any active camera overlays for a given Meeting
  Session.
- **Camera Overlay Enrollment**: A record of which participant has opted their own outgoing video
  feed into the avatar overlay for a Meeting Session; exists only while that participant keeps it
  enabled, and never implies enrollment for any other participant.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A participant asking a clear, location+technology+time-bounded network question out
  loud during a meeting receives a visible, evidence-backed answer in the shared panel without any
  participant leaving the call or typing a command.
- **SC-002**: 100% of recognized write/configuration-changing requests detected from meeting speech
  or chat are held for explicit human approval before any action executes; 0% execute automatically.
- **SC-003**: 100% of hypothetical, past-tense, or third-party-attributed statements about
  configuration changes, exercised in testing, result in no action being attempted and nothing queued
  for approval.
- **SC-004**: Every meeting participant who opens the shared panel — including a guest with no prior
  install or login — sees the same live status and results as the meeting host, with no separate
  setup step visible to them.
- **SC-005**: Referencing a genuinely related past meeting during a live call surfaces that meeting's
  relevant content in the shared panel, and states plainly whether current network state matches or
  differs from it.
- **SC-006**: No meeting's live context buffer remains accessible after that meeting has ended.
- **SC-007**: Every recognized investigation request and every approval decision arising from a
  meeting is independently traceable in the audit trail after the fact.
- **SC-008**: 100% of camera-overlay enable/disable actions taken in testing apply only to the
  enabling participant's own feed and take effect immediately, with 0% of cases requiring or implying
  another participant's consent.
- **SC-009**: The avatar's visual state (panel and, when enabled, camera overlay) reflects a change
  in NetGeniusClaw's activity within 2 seconds of that change occurring, and never shows two different
  states simultaneously across the panel and an active overlay.

## Assumptions

- NetGeniusClaw already has at least one Member Claw capable of answering location/technology-scoped
  network questions (e.g., pyATS, NetBox, Splunk) registered and reachable through the existing
  NCFED/Border routing path; this feature routes to that existing path rather than building new
  investigation tooling.
- NetGeniusClaw's existing READ-vs-WRITE classification and HumanRail approval mechanism, used elsewhere in
  the product, is reused as-is for meeting-sourced requests rather than being redefined for Zoom.
- The existing audit trail (GAIT) is reused as-is to record meeting-sourced requests and approval
  decisions, consistent with how every other write path is already audited.
- A live-context buffer bounded to recent meeting minutes (rather than full meeting duration) is
  sufficient for recognizing and answering in-the-moment questions; the official historical-search
  integration (User Story 2) is the intended path for anything beyond that recent window.
- An autonomous, speaking/video-tile meeting participant is out of scope for this pass; the visible
  surfaces for this pass are the shared panel (User Story 3) and, additionally, an avatar overlay a
  participant opts their own camera feed into (User Story 5) — neither creates an independent
  participant identity or independent audio.
- The camera-overlay avatar is a purely visual layer on a consenting participant's own outgoing
  video; it carries no audio of its own and never appears on a feed its owner did not explicitly
  enable.
- Meeting recording/RTMS access is only ever enabled for meetings where the organization already has
  the authority and Zoom account entitlements to enable it; this feature does not change or bypass
  Zoom's own consent or entitlement requirements for capturing meeting content.
