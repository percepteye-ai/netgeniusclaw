# Research: iOS App Store Submission Readiness, Phase 1

## R1: How to detect "no enrollment yet" for the explainer screen (US1)

**Decision**: Reuse `EnrollmentStore.load()` returning `null` — no new detection
mechanism needed.

**Rationale**: `EnrollmentGate` (`lib/main.dart`) already calls
`EnrollmentStore(dir).load()` on every launch and branches on whether it
returns a `StoredEnrollment` or `null`. The `null` branch is exactly "no
enrollment exists" — the same condition FR-001/FR-002 need. The explainer
screen is inserted as a step in that existing `null` branch, before
`EnrollmentScreen` is shown, not as a new state-detection mechanism.

**Alternatives considered**: A separate "have I shown the explainer before"
flag (e.g. a boolean in shared preferences) was considered so the explainer
could be shown exactly once ever, even across a de-enroll/re-enroll cycle.
Rejected: spec.md's edge cases explicitly resolve this — the explainer is an
"unenrolled-state" screen, not a "seen once" screen, so tying it to the
existing enrollment-presence check is correct by design, not a shortcut.

## R2: How to gate device removal behind biometric re-authentication (US2)

**Decision**: Reuse the exact `local_auth` pattern from
`lib/ncfed/approval_confirmation.dart`'s `confirmAndResolve()` — call
`LocalAuthentication().authenticate(localizedReason: ...)` (injectable for
tests, matching that file's own `authenticate` parameter), and only clear the
enrollment on a `true` result.

**Rationale**: The Clarifications session (2026-08-11) explicitly resolved
this as "same security posture as approvals." `approval_confirmation.dart`
is already the app's one designated place biometric code lives, is already
unit-testable via its injectable `authenticate` callback, and already
defines the fallback behavior (cancelled/unavailable auth → treated as "do
nothing," never a crash or silent bypass) that edge case 2a in spec.md
asks this feature to reuse rather than reinvent.

**Alternatives considered**: A bespoke `local_auth` call inline in the
Settings screen. Rejected: would duplicate the existing
cancelled/unavailable-handling logic instead of reusing a single, already-
tested implementation, and would create a second place biometric code exists
in the app, contradicting `approval_confirmation.dart`'s own stated role.

## R3: How to produce a distribution-signed build without repeating this session's Xcode GUI friction

**Decision**: Use `flutter build ipa` (Flutter's own command-line path to a
distribution-ready `.xcarchive` + `.ipa`) rather than Xcode's Product → Archive
menu action.

**Rationale**: Every build this project has produced successfully, all
session, went through `flutter build ios`/`flutter run` — the command-line
path. Every failure was in Xcode's own GUI build/attach flow (a stale
provisioning-profile cache, a missing `SystemCapabilities` project-level
entry, Swift Package Manager re-resolution after a DerivedData clear — none
of it a code defect, all of it GUI-specific state). `flutter build ipa` is
Flutter's documented, first-class command for producing an App Store-ready
archive and continues to drive `xcodebuild` under the hood the same way
`flutter build ios` already does successfully — it is the same proven
mechanism, pointed at Release/distribution configuration instead of Debug.

**Alternatives considered**: Xcode's Organizer-driven Archive (Product →
Archive → Distribute App). Rejected as the *primary* path given this
session's direct, repeated experience of that GUI surfacing
signing/capability state that the command-line path never hit — not rejected
as impossible, since it remains the fallback if `flutter build ipa` surfaces
something it cannot resolve (e.g. an interactive distribution-certificate
creation prompt), consistent with FR-007's requirement being about the
archive succeeding, not about which tool produces it.

## R4: How to upload the archive to App Store Connect

**Decision**: `xcrun altool --upload-app` using an App Store Connect API key
(not an Apple ID + app-specific password), invoked from the command line
after `flutter build ipa` produces the `.ipa`.

**Rationale**: Keeps the entire pipeline (build → archive → upload) in the
command line, consistent with R3's reasoning and this session's demonstrated
preference for avoiding Xcode's own GUI wherever an equivalent CLI path
exists. An API key (generated once in App Store Connect → Users and Access →
Integrations) avoids two-factor-authentication prompts that an Apple ID
password would trigger interactively, which matters for the same reason GUI
attach flows caused friction this session — anything requiring an
interactive human-present prompt at exactly the wrong moment is a repeat
failure mode worth designing around up front.

**Alternatives considered**: Transporter.app (Apple's GUI upload tool) and
Xcode Organizer's own upload step. Both remain valid fallbacks — Transporter
in particular is simple and low-risk if the CLI path hits an API-key
permissions issue — but are not the first choice given R3's reasoning applies
equally here.

## R5: Whether any new third-party package is needed

**Decision**: None. Everything in this spec — the explainer screen, the
Settings control, the biometric re-auth call, the build/upload tooling — uses
either existing app code (`EnrollmentStore`, `approval_confirmation.dart`'s
pattern) or existing OS/toolchain-level commands (`flutter build ipa`,
`xcrun altool`). Consistent with every prior mobile spec in this project
(066–103), none of which added a package for comparable UI or tooling work.

**Alternatives considered**: `fastlane` (a popular third-party CI/CD tool
that wraps exactly this archive-and-upload sequence). Rejected for this
phase: it would be a new dependency (a Ruby toolchain, a `Fastfile`) for a
one-time/low-frequency manual process that `flutter build ipa` + `xcrun
altool` already covers without adding anything to the project. Worth
revisiting if a future spec needs *repeated, automated* releases (e.g. CI-
driven TestFlight builds on every merge) rather than this phase's one-time
readiness milestone.
