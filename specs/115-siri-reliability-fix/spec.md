# Feature Specification: NetGeniusClaw Mobile Siri Reliability Fix + Two-Way Voice + Theme Toggle (Pass 1 of 3)

**Feature Branch**: `115-siri-reliability-fix`
**Created**: 2026-08-16
**Status**: Draft
**Input**: User description: "NetGeniusClaw Mobile Siri App Intents Reliability Fix + Two-Way Voice + Theme Toggle (Pass 1 of 3, Mac + phone access)..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Siri/Shortcuts actually reach NetGeniusClaw (Priority: P1)

An operator says "Hey Siri, check NetGeniusClaw Border health" (or uses the equivalent Shortcuts action for Border Health, Pending Approvals, or Ask NetGeniusClaw). Today, on a fresh release build, none of these three actions ever reach NetGeniusClaw's own code at all — Siri silently falls back to a web search, or the Shortcuts app reports a generic "could not run" error, regardless of retries, reinstalls, or device reboots. The operator needs these three actions to reliably invoke NetGeniusClaw every time the app is installed, with no manual workaround.

**Why this priority**: This is the entire foundation spec 111 promised (hands-free Siri access to NetGeniusClaw) and it does not work at all in its current shipped state. Nothing else in this spec matters if this doesn't work.

**Independent Test**: Install a fresh release build, do not open the app's UI first, and say "Hey Siri, check NetGeniusClaw Border health." The Border's last cached health status must be spoken aloud. Repeat for "Pending Approvals" and "Ask NetGeniusClaw."

**Acceptance Scenarios**:

1. **Given** a freshly installed release build with no prior foreground launch, **When** the operator says "Hey Siri, check NetGeniusClaw Border health," **Then** Siri speaks the real, currently-cached Border health status (not a web search, not a generic error).
2. **Given** the same fresh install, **When** the operator taps "Pending Approvals" in the Shortcuts app, **Then** Siri/Shortcuts speaks or shows the real current pending-approval count from the Border.
3. **Given** the same fresh install, **When** the operator says "Hey Siri, ask NetGeniusClaw a question" and states a question, **Then** the question is captured, sent to the Border, and recorded in the app's conversation history tagged as originating from Siri.

---

### User Story 2 - A fast answer is spoken directly, not just acknowledged (Priority: P2)

When an operator asks NetGeniusClaw a question via Siri and the Border's answer is ready quickly enough, the operator wants to actually hear the answer, not just an acknowledgment that it was sent. Today, "Ask NetGeniusClaw" always speaks a generic "Sent to NetGeniusClaw, I'll let you know when it answers" regardless of how fast the real answer arrives, and the real answer is only ever visible later inside the app.

**Why this priority**: This is the difference between "voice-activated messaging" and genuine "talk to your network." It's a significant experience upgrade but depends on User Story 1 already working.

**Independent Test**: Ask a question whose answer is known to compose quickly (e.g., a status check backed by a fast API). Confirm Siri speaks the real answer text aloud, not the generic acknowledgment, and that the answer is not garbled by leftover formatting markup.

**Acceptance Scenarios**:

1. **Given** the Border finishes composing a real answer within the fast-response window, **When** the operator has asked a question via Siri, **Then** Siri speaks that real answer text aloud, with any text formatting markup (bold markers, bullet points, headers) stripped so it reads naturally.
2. **Given** the Border has not finished composing an answer within the fast-response window, **When** the fast-response window elapses, **Then** the operator hears the existing "Sent to NetGeniusClaw, I'll let you know when it answers" acknowledgment, and the real answer is delivered later exactly as it is today (via notification if it arrives soon after, or via the app's own conversation history once reopened).
3. **Given** a fast answer was spoken aloud to the operator, **When** the operator later opens the app, **Then** that same answer also appears correctly in the conversation history (no duplicate entries, no missing entries).

---

### User Story 3 - Choose light or dark appearance manually (Priority: P3)

An operator wants NetGeniusClaw's appearance to match their own preference rather than always following the phone's system-wide setting. Today the app only ever follows the system Light/Dark setting, with no override inside the app.

**Why this priority**: Pure visual preference/polish, independent of the Siri reliability work and lowest-impact of the three stories.

**Independent Test**: Open Settings, change the appearance preference, and confirm the whole app (not just one screen) immediately reflects the chosen appearance and keeps it across an app restart, independent of the system-wide setting.

**Acceptance Scenarios**:

1. **Given** the operator is on a phone set to system Dark mode, **When** they choose "Light" in NetGeniusClaw's own Settings, **Then** the entire app immediately displays in light appearance and stays that way even if the system setting later changes.
2. **Given** the operator has chosen an explicit appearance preference, **When** they force-quit and reopen the app, **Then** the previously chosen appearance is still in effect.
3. **Given** the operator wants to defer to the system again, **When** they choose "System" in Settings, **Then** the app immediately starts following the phone's system-wide Light/Dark setting again.

---

### Edge Cases

- What happens when Siri asks a question but the phone has no enrolled Border connection at all? (Existing "NetGeniusClaw isn't set up on this device yet" behavior is retained, unaffected by this spec.)
- What happens when the Border's answer contains only formatting markup and no actual prose (e.g., a bare bullet list)? Stripped output must still be non-empty and intelligible when spoken.
- What happens when the operator asks a question, gets a fast spoken answer, and then asks a second, unrelated question moments later before the first is ever opened in the app? Both must be recorded distinctly and correctly, with no cross-contamination of answers.
- What happens if the appearance preference is changed while another part of the app is actively showing an in-progress action (e.g., mid-conversation)? The visual change applies without disrupting or losing any in-progress state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST make the "Border Health," "Pending Approvals," and "Ask NetGeniusClaw" voice/Shortcuts actions reach NetGeniusClaw's own logic on every install, including a completely fresh install with no prior foreground app launch.
- **FR-002**: The system MUST NOT depend on the main app being open, foregrounded, or recently launched for any of the three voice/Shortcuts actions to work.
- **FR-003**: The system MUST NOT destabilize or crash the main app process as a side effect of handling a voice/Shortcuts action while the main app may also be running.
- **FR-004**: When a question asked via "Ask NetGeniusClaw" receives a real, finished answer from the Border within a bounded fast-response window, the system MUST speak that real answer aloud instead of a generic acknowledgment.
- **FR-005**: The system MUST remove text-formatting markup (at minimum: bold/emphasis markers, bullet/list markers, and heading markers) from an answer before it is spoken aloud, so it reads as natural speech.
- **FR-006**: When no real answer is ready within the fast-response window, the system MUST fall back to today's acknowledgment-now / notify-or-reconcile-later behavior unchanged.
- **FR-007**: A question asked via Siri MUST be recorded in the operator's conversation history exactly once, correctly reflecting its final state (answered, still pending, or failed) regardless of whether it was answered within the fast-response window or later.
- **FR-008**: The system MUST provide a way for the operator to explicitly choose Light, Dark, or "follow system" appearance from within the app's own settings.
- **FR-009**: The chosen appearance preference MUST persist across app restarts until the operator changes it again.
- **FR-010**: Changing the appearance preference MUST take visible effect across the entire app immediately, without requiring an app restart.
- **FR-011**: Temporary diagnostic instrumentation added solely to debug the Siri reliability issue MUST be removed once the underlying reliability fixes are verified working, leaving no diagnostic-only code paths in the shipped app.

### Key Entities

- **Voice/Shortcuts Action Invocation**: A single instance of the operator triggering "Border Health," "Pending Approvals," or "Ask NetGeniusClaw" via Siri or the Shortcuts app; has an outcome (spoken result, acknowledgment, or error) and, for "Ask NetGeniusClaw," an associated question and eventual answer.
- **Conversation Turn**: An operator question and its answer (or pending/failed state), already tracked by the app; gains no new fields in this spec beyond ensuring exactly-once, correct recording regardless of which response path (fast-spoken vs. later-delivered) served it.
- **Appearance Preference**: A single operator-chosen setting (Light / Dark / System) that determines the app's visual theme, persisted across sessions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a freshly installed build, all three voice/Shortcuts actions (Border Health, Pending Approvals, Ask NetGeniusClaw) succeed on first real attempt in at least 9 out of 10 tries, without opening the app's UI first.
- **SC-002**: When the Border answers a Siri-originated question within the fast-response window, the operator hears the real answer spoken aloud, free of formatting artifacts, in at least 9 out of 10 tries.
- **SC-003**: No conversation turn originated via Siri is ever lost, duplicated, or stuck permanently unresolved due to how it was answered (fast-spoken vs. later-delivered).
- **SC-004**: The operator can switch the app's appearance between Light, Dark, and System, and the choice is honored immediately and remembered after the app is fully closed and reopened, 100% of the time.
- **SC-005**: Zero app crashes attributable to handling a voice/Shortcuts action occur during a full verification pass covering repeated invocations under realistic conditions (app foregrounded, backgrounded, and fully closed).

## Assumptions

- This spec covers only the mobile app side of the Siri/Shortcuts experience ("Pass 1"). Any change to how the Border composes or prioritizes answers for Siri-originated requests specifically is out of scope here and deferred to a later pass against the Border codebase.
- The three underlying root-cause fixes (missing entry-point compilation, unsafe duplicate plugin registration, and incorrect engine/library resolution) described in the input are the complete and correct fix for FR-001–FR-003; this spec formalizes and verifies that work rather than re-deriving it.
- "Fast-response window" is a bounded, tunable duration chosen empirically against the voice assistant's own observed patience for waiting on a spoken response; the exact duration is an implementation detail, not a fixed requirement, provided it is comfortably long enough to catch realistically fast answers without so long a wait that the voice assistant abandons the request before any response — including the fallback acknowledgment — is given.
- "Formatting markup" refers to the lightweight text-formatting conventions the Border's answers are already composed in; no new answer-formatting convention is introduced by this spec.
- The three-way appearance preference reuses the persistence approach already established for other simple app settings, requiring no new storage mechanism.
