# Feature Specification: iOS App Store Submission Readiness, Phase 1

**Feature Branch**: `105-ios-appstore-readiness`
**Created**: 2026-08-11
**Status**: Draft
**Input**: User description: "iOS App Store submission readiness, phase 1: (1) add a first-launch onboarding/explainer screen shown before the QR-scan enrollment gate, making clear this is a companion app requiring a self-hosted NetGeniusClaw Border server; (2) add an in-app 'Remove this device / un-enroll' control in the Settings screen that calls the existing EnrollmentStore.clear() and returns to the enrollment gate — closing the Apple Guideline 5.1.1(v) account-deletion gap (there is currently no operator-initiated way to de-enroll, only Border-initiated revocation); (3) get the app through one real Xcode Archive build under distribution signing (not the development signing used all session) and upload it to App Store Connect via Transporter/Xcode Organizer, then create an External Testing group in TestFlight so known testers can install the real build without a public App Store release. Explicitly out of scope for this spec: standing up a demo Border for Apple's reviewers (separate, being handled independently), and the App Store Connect public-listing metadata (privacy policy, App Privacy questionnaire, screenshots, description) — those come after this spec closes."

## Clarifications

### Session 2026-08-11

- Q: Does this spec's completion require Apple's Beta App Review to have actually passed for the TestFlight External Testing group, or is submitting for review sufficient? → A: Done once the build is archived, uploaded, and submitted for External Testing review — the review's outcome is tracked separately, not blocking.
- Q: Should removing a device's enrollment require biometric (Face ID/Touch ID) re-authentication, consistent with the app's existing approval-confirmation pattern, or is a plain confirmation dialog sufficient? → A: Require the same biometric re-authentication as approvals — consistent security posture for all destructive/irreversible actions in the app.
- Q: Does this spec need to guarantee the paired watch is actively/immediately notified when the phone de-enrolls, or is it acceptable for the watch to simply learn this the next time it asks? → A: No new requirement needed — the watch already re-queries the phone regularly, and every existing relay method already answers `enrolled: false` correctly when nothing is enrolled.

## Context

This spec exists because a readiness review of the existing NetGeniusClaw Mobile app
(specs 066–103) found three concrete gaps standing between "the app works"
and "the app is ready to submit to Apple," verified directly against the
running code rather than assumed:

1. A brand-new installer is shown a camera pointed at "Scan Border QR Code"
   with no prior explanation of what a Border is or that one is required —
   confirmed by reading `EnrollmentScreen`/`EnrollmentGate` directly.
2. There is no operator-initiated way to remove an enrollment. The only
   existing path that clears a device's stored identity is Border-initiated
   revocation — confirmed by reading `SettingsScreen` and every call site of
   `EnrollmentStore.clear()`. Apple Guideline 5.1.1(v) requires self-service
   account deletion for apps that support account creation, and enrolling a
   device against a Border plausibly qualifies.
3. The app has only ever been built and run under development signing this
   entire project. Distribution signing (the certificate/profile type Apple
   requires for TestFlight and the App Store) has never been exercised, and
   prior sessions on this same project encountered multiple Xcode
   signing/capability surprises specific to *development* signing — there is
   no reason to assume distribution signing will be friction-free on the
   first attempt, and every subsequent App Store step depends on it working.

Two things this spec deliberately does NOT attempt, because they are already
being handled elsewhere or come logically after this spec closes:

- Standing up a Border instance for Apple's own reviewers to test against
  (separate, operator-led effort).
- App Store Connect's public-listing content — privacy policy, the App
  Privacy questionnaire, screenshots, description (comes after this spec,
  once a distribution-signed build exists to describe accurately).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A first-time installer understands what they're looking at (Priority: P1)

Someone installs the app — a real user, or an Apple reviewer — without
already knowing what NetGeniusClaw or a "Border" is. Today they see a camera
scanner and nothing else. This story adds one screen, shown before the
scanner, that plainly states the app is a companion client for a
self-hosted NetGeniusClaw Border and that a Border must already be running before
enrollment can succeed.

**Why this priority**: This is the first thing anyone new to the app sees,
including the person who decides whether the app is confusing enough to
reject or abandon. It is also a prerequisite for Apple reviewers to
understand what they're being asked to test, regardless of how the demo
Border access itself is arranged.

**Independent Test**: Delete the app's local data (or install fresh), launch
it, and confirm the explainer screen appears before any camera permission
prompt or QR scanner — deliverable and verifiable with no Border, no
enrollment, and no other part of this spec in place.

**Acceptance Scenarios**:

1. **Given** a fresh install with no prior enrollment, **When** the app is
   launched for the first time, **Then** an explainer screen appears before
   the QR scanner, stating that the app requires a self-hosted NetGeniusClaw
   Border server and does not work as a standalone consumer app.
2. **Given** the explainer screen is showing, **When** the person taps
   through (e.g. "Continue" / "I have a Border"), **Then** they land on the
   existing QR-scan screen exactly as it behaves today.
3. **Given** a device that is already enrolled, **When** the app is
   launched, **Then** the explainer screen is skipped entirely and the app
   goes straight to its normal enrolled state — this is a first-launch-only
   screen, not a repeated interruption.

---

### User Story 2 - An operator can remove their own enrollment (Priority: P1)

Today, the only way a device stops being enrolled is if the Border operator
revokes it from the server side. The person holding the phone has no
self-service way to remove that enrollment — not to switch Borders, not to hand the phone
to someone else, not to satisfy Apple's account-deletion requirement. This
story adds a visible, explicit control in Settings that clears the local
enrollment and returns the app to its pre-enrollment state.

**Why this priority**: Equal-P1 with User Story 1 because both are concrete,
named blockers to public submission (Guideline 5.1.1(v) for this one), not
polish. Unlike User Story 1, this one also has ongoing value independent of
Apple's review: an operator switching Borders or handing off a device
currently has no clean way to do it.

**Independent Test**: Enroll a test device, open Settings, trigger the new
control, and confirm the app returns to the same enrollment-gate state a
fresh install would show — independently verifiable without needing a
distribution build or App Store Connect at all.

**Acceptance Scenarios**:

1. **Given** an enrolled device, **When** the operator opens Settings,
   **Then** a clearly labeled "Remove this device" (or equivalent) control is
   visible.
2. **Given** the operator taps that control, **When** they complete the same
   biometric (Face ID/Touch ID) re-authentication the app already requires
   for approvals (Clarifications, 2026-08-11), **Then** the local enrollment
   is cleared and the app returns to the enrollment gate, identical in
   behavior to a fresh install.
3. **Given** the operator's device has no biometric enrolled or biometric
   authentication is unavailable, **When** they trigger the control,
   **Then** the app falls back to whatever the existing approval-confirmation
   flow already does in that situation (device passcode or equivalent) —
   this story does not introduce a new fallback path, it reuses the
   existing one.
4. **Given** the device's Border is unreachable (network down, Border
   offline, or simply out of range), **When** the operator triggers device
   removal and completes biometric re-authentication, **Then** the removal
   still succeeds — per FR-006, this action MUST NOT depend on a live
   connection to the Border.
5. **Given** the enrollment has just been cleared this way, **When** the app
   is relaunched, **Then** it does not attempt to reconnect to the old Border
   and shows the enrollment gate (with User Story 1's explainer, if this is
   also the first launch in a while) rather than any error state.
6. **Given** the operator opens the confirmation prompt, **When** they cancel
   instead of confirming, **Then** nothing changes and the device remains
   enrolled exactly as before.

---

### User Story 3 - Known testers can install a real, distribution-signed build (Priority: P2)

Every build produced so far has been signed for development and run directly
from a development machine to a physically connected device. This story is
the first time the app is packaged the way it will actually ship: archived
under distribution signing, uploaded to App Store Connect, and made
available to a small group of testers through TestFlight — without needing a
public App Store listing to exist yet.

**Why this priority**: P2, not because it matters less, but because it is
downstream of nothing else in this spec — User Stories 1 and 2 should be
in the build being archived, but the archive/upload/TestFlight mechanics
themselves don't depend on those stories' content, only on their code being
present. It is also the step most likely to surface previously-unseen
distribution-signing friction (this project's history has already run into
several development-signing surprises when moving between build methods) —
better discovered here than during a later, more time-pressured submission
attempt.

**Independent Test**: Produce one Xcode Archive build, upload it to App
Store Connect, and confirm a real external tester (someone who has never
touched the Mac or Xcode) can install it via a shared TestFlight link and
launch the app — independently verifiable without any App Store public
listing or reviewer-facing content existing yet.

**Acceptance Scenarios**:

1. **Given** the current project signed for development, **When** an Xcode
   Archive build is produced instead (via any tooling that yields one —
   command-line or Xcode's own GUI; see plan.md/research.md for which this
   project uses), **Then** the archive succeeds under distribution signing
   for every target that ships (phone app, watch app, watch complication,
   and any other embedded extension) without a development-only capability
   or entitlement blocking it.
2. **Given** a successful archive, **When** it is uploaded to App Store
   Connect, **Then** it appears there as a build associated with the app's
   existing bundle identifier, ready to be attached to a TestFlight group.
3. **Given** an uploaded build, **When** an External Testing group is created
   and a tester is invited, **Then** the invite is submitted for Apple's Beta
   App Review — clearing that review is tracked as a separate, externally-gated
   event, not a blocking condition for calling this story done (Clarifications,
   2026-08-11).
4. **Given** a tester installs the build via TestFlight (once Beta App Review
   has cleared, independent of this spec's own completion), **When** they
   launch it for the first time, **Then** they see User Story 1's explainer
   screen, confirming the same code path tested under development signing
   behaves identically under distribution signing.

### Edge Cases

- What happens if the operator triggers "Remove this device" while the app
  has an active, unresolved approval or in-progress chat request pending?
  (The removal should still succeed — there is no Border-side dependency for
  clearing purely local state — but any in-flight local state tied to that
  enrollment is necessarily discarded along with it.)
- What does the paired Apple Watch see immediately after the phone
  de-enrolls? Resolved (Clarifications, 2026-08-11): nothing new needs to be
  built. The watch has no independent state — it re-queries the phone on its
  normal refresh cadence, and every existing relay method already answers
  `enrolled: false` correctly once there is nothing enrolled. The watch will
  reflect the change on its next ordinary refresh, not instantly, and that
  delay is acceptable.
- What happens if the explainer screen (User Story 1) is dismissed, but the
  operator then cancels out of the QR scanner without enrolling? Relaunching
  the app should show the explainer again, since no enrollment exists yet —
  it is not a "seen it once, never again" screen, it is an
  "unenrolled-state" screen.
- What happens if a distribution-signed build is archived (User Story 3)
  before User Stories 1 and 2 are merged into the same branch? The archive
  step itself does not require them, but the build being handed to testers
  should include them — sequencing this correctly is a delivery concern, not
  a new requirement.
- What happens if Apple's Beta App Review (the lightweight review TestFlight
  external groups go through) rejects the build for a reason unrelated to
  this spec's three items? That is a real possible outcome and is out of
  scope to prevent here — this spec's job is to get a real build in front of
  that review, not to guarantee it passes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: On a fresh install (no prior enrollment persisted), the app
  MUST show an explainer screen, before any camera permission prompt or
  QR-scan UI, stating plainly that the app is a companion client requiring a
  self-hosted NetGeniusClaw Border server.
- **FR-002**: The explainer screen MUST NOT appear on any launch where a
  valid enrollment is already persisted.
- **FR-003**: The Settings screen MUST present a clearly labeled control for
  removing the current device's enrollment.
- **FR-004**: Triggering that control MUST require the same biometric
  (Face ID/Touch ID) re-authentication step the app already uses to confirm
  approvals before taking effect (Clarifications, 2026-08-11) — it must not
  be possible to clear an enrollment with a single accidental tap, and the
  security posture for this destructive/irreversible action must match the
  app's existing convention rather than introduce a weaker one.
- **FR-005**: Confirming device removal MUST clear the locally persisted
  enrollment and return the app to the same state a fresh install would show
  (enrollment gate, with FR-001's explainer if applicable).
- **FR-006**: Device removal MUST work entirely from local state — it MUST
  NOT require a live connection to the Border to complete (an operator must
  be able to remove a device's local enrollment even if that Border is
  unreachable, since the point is to escape from a bad or unwanted
  enrollment, not to renegotiate with it).
- **FR-007**: The project MUST be capable of producing a successful Xcode
  Archive build, under distribution (not development) code signing, for
  every target that ships inside the app bundle — via any tooling that
  produces one (command-line or GUI); see plan.md/research.md for which
  this project uses and why.
- **FR-008**: A successful archive MUST be uploaded to App Store Connect and
  associated with the app's existing bundle identifier.
- **FR-009**: An External Testing group in TestFlight MUST be created against
  that uploaded build, capable of accepting at least one tester who has no
  access to the development machine or source code.

### Key Entities

- **Enrollment (existing entity, no new fields required)**: the locally
  persisted record of which Border a device is paired with. This spec adds a
  new way to *end* its lifecycle (operator-initiated) alongside the existing
  ways (Border-initiated revocation, Border-initiated rejection on
  reconnect) — it does not change what the record contains.
- **Distribution build**: a single Xcode Archive artifact produced under
  distribution signing and uploaded to App Store Connect. Distinct from
  every build produced earlier in this project, which used development
  signing and never left a directly-connected physical device.
- **TestFlight External Testing group**: an App Store Connect construct that
  gates who can install a given distribution build via a shareable link or
  invite, without requiring a public App Store listing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person with no prior context on NetGeniusClaw can read the
  explainer screen and correctly state, without being told, that the app
  requires a separately-run server they don't yet have.
- **SC-002**: An operator can go from "enrolled" to "back at the enrollment
  gate" using only in-app controls, in under 30 seconds, with zero
  Border-side action required.
- **SC-003**: A distribution-signed archive of the full app (phone + watch +
  complication) is produced and uploaded to App Store Connect at least once,
  with zero manual workarounds required on a repeat attempt (i.e. any
  signing/capability issue hit on the first attempt is durably fixed, not
  worked around by hand each time).
- **SC-004**: A distribution build reaches the point of being submitted for
  Apple's Beta App Review under an External Testing group (Clarifications,
  2026-08-11). Once that review clears — tracked separately, not blocking
  this spec's completion — at least one person outside the development
  machine should be able to install and launch the app via the shared
  TestFlight link without any assistance beyond the link itself.

## Assumptions

- The existing paid Apple Developer Program membership (confirmed active as
  of spec 103) covers distribution signing and TestFlight — no additional
  Apple-side enrollment is needed for this spec specifically.
- "Companion app" framing (User Story 1) is the correct, honest description
  of this app for both the explainer screen and, later, the public listing —
  this spec does not revisit that framing, only implements the screen that
  states it.
- Clearing an enrollment locally (User Story 2) does not need to notify the
  Border at all; the Border's own member record is untouched by this action
  and remains exactly what it is until removed Border-side (via the existing
  `./scripts/netclaw risk remove <member_id>` or the FR-017 tooling from
  spec 103) — from the app's point of view this is purely a local reset.
- One TestFlight External Testing group is sufficient for this spec's goal
  of "known testers can install the real build" — this spec does not address
  eventual public/unlimited TestFlight distribution or the App Store listing
  itself.
- The demo-Border-for-reviewers effort and the App Store Connect
  public-listing metadata are being tracked and delivered outside this spec,
  per the explicit scope exclusion in the Input description above.
