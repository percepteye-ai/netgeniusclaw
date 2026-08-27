# Feature Specification: NetGeniusClaw Mobile Siri / App Intents Integration (B1a)

**Feature Branch**: `111-siri-app-intents`
**Created**: 2026-08-15
**Status**: Draft
**Input**: User description: "NetGeniusClaw Mobile App Intents integration (Phase B1a of NETCLAW-MOBILE-1.0.1-BRIEF.md, split from B1). Native Swift AppIntents in the Runner target: AskBorderIntent (submit a question headlessly via the existing background-Flutter-engine pattern, dialing the existing EdgeClient WebSocket, return a brief spoken acknowledgment rather than blocking for the real answer — a real ask can take minutes), PendingApprovalsIntent and BorderHealthIntent (headless-connect and speak the real answer directly, since these are quick queries). An AppShortcutsProvider with natural-language phrases exposes all three with zero user setup, which also lights up the iPhone 15 Pro+ Action Button and Shortcuts automations for free — same underlying intents, no separate implementation. Control Center's `ControlWidget` (iOS 18+) is explicitly out of scope (B1b, future spec) since it needs a new Xcode target and would force a deployment-target bump from the current 16.2 to 18.0. Engine-lifecycle decision already made: headless, not `openAppWhenRun`, confirmed with the operator."

## Context

This spec implements item B1a of `mobile/netclaw-mobile/NETCLAW-MOBILE-1.0.1-BRIEF.md`'s Phase B, split from the brief's original B1 ("App Intents (Siri, Action Button, Control Center, Shortcuts)") per that item's own architectural note: the App Intents themselves, `AppShortcutsProvider`, Siri, the Action Button, and Shortcuts automations are all the *same* underlying implementation — there is no separate work to "add" the Action Button or Shortcuts once the intents exist. Control Center's `ControlWidget` is a genuinely separate iOS 18+ widget-extension target and is deferred to a future B1b spec.

The brief itself flagged "the architectural decision that matters" for this spec: whether `AskBorderIntent` uses `openAppWhenRun = true` (trivial, but Siri just opens the app) or a headless approach (harder, but Siri actually works while the app never opens). This was discussed directly with the operator, who confirmed: **headless**, since a Siri integration that just opens the app defeats the purpose of building it.

Before writing this spec, the codebase was researched directly (not assumed) to ground the headless design in what already exists, rather than inventing a new mechanism:

- **A headless Flutter engine pattern already exists** for spec 099's background refresh: `lib/ncfed/background_refresh.dart`'s `backgroundRefreshMain()` (a `@pragma('vm:entry-point')` Dart entrypoint with no widget tree) is launched from `ios/Runner/AppDelegate.swift:67-108`'s `handleBackgroundRefresh(task:)` via a plain `FlutterEngine` (**not** `FlutterEngineGroup` — that API is not used anywhere in this codebase today, so this spec follows the established plain-`FlutterEngine`-per-invocation pattern rather than introducing a new one). The Swift side selectively registers only the plugins the headless task needs (`EdgeIdentityPlugin`, skipping `WatchRelayPlugin`/`LiveActivityBridge`), holds a strong reference to the engine so ARC doesn't tear it down mid-flight, and reports completion back over a dedicated `FlutterMethodChannel`.
- **Submitting a question is already fast and non-blocking**: `EdgeAskClient.ask()` (`lib/ncfed/edge_ask_client.dart:97-107`) calls `n2n/edge/ask` with a 30s timeout and returns a `task_id` immediately: the Border acknowledges fast and never blocks the RPC on the real answer. The eventual answer arrives asynchronously via `n2n/edge/ask_result`, delivered on the existing `updates` broadcast stream.
- **A cold connection is already a proven, timed operation**: `EdgeClient.reconnect()` (`lib/ncfed/edge_client.dart:298-331`) opens the `wss://` socket, waits up to 10s for the Border's challenge, signs it via `EdgeIdentityPlugin`'s Secure Enclave access, and completes the handshake — exactly what `background_refresh.dart` already does today (with a `.timeout(Duration(seconds: 10))` wrapped around the call), using the same `StoredEnrollment` JSON file (`lib/ncfed/enrollment_store.dart:62`, a plain file under the app's documents directory, not secure storage) that the main app itself reads on cold start.
- **Correction to an initial assumption, load-bearing for this spec's design**: a completed chat answer does **not** automatically produce a local notification independent of the UI. `lib/main.dart:580-593` wires `ConversationStore.onCompleted` to `LocalNotifications.postChatNotification(...)` *inside* `_HomeShellState` — that callback is `null` until `HomeShell` actually builds. A headless engine constructing its own `ConversationStore`/`EdgeAskClient` object graph gets none of that wiring for free. The correct model, and the one this spec adopts, is for the headless entrypoint to **directly** construct and use its own `LocalNotifications` instance and call `postChatNotification(...)` itself once its own `updates` stream reports the `ask_result` — precisely mirroring what `backgroundRefreshMain` already does for `postFeedNotification` after draining the feed queue (`background_refresh.dart:112-119`). This spec's acceptance criteria and success criteria are written against that corrected model, not the "reuses the existing notification path" framing this spec started from.
- **No new entitlement is required**: modern `AppIntents`/`AppShortcutsProvider` (iOS 16+) need no capability entitlement, unlike legacy `SiriKit`/`INIntent` (which needed `com.apple.developer.siri`). `Runner.entitlements` is unaffected by this spec.
- `IPHONEOS_DEPLOYMENT_TARGET` is confirmed `16.2` across all Runner build configurations — comfortably above the iOS 16 minimum `AppIntents` needs, and unaffected by this spec (only B1b's Control Center `ControlWidget` would force a bump to 18.0).

This repo's verification standard (specs 072/073, most recently reaffirmed in spec 110) applies unchanged: invoking a real App Intent via Siri, the Action Button, or the Shortcuts app is 🔌 **DEVICE**-only — it cannot be simulated meaningfully and is not claimed done from a green `flutter test`/Xcode-build alone. The Dart-side pure logic and the headless-engine wiring's *structure* are unit-testable; the actual voice interaction is not.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask NetGeniusClaw a question by voice, without opening the app (Priority: P1)

An operator says "Hey Siri, ask NetGeniusClaw if BGP is up on the core switch" (or triggers the same phrase via the iPhone 15 Pro+ Action Button, or a Shortcuts automation). Siri responds immediately with a brief spoken acknowledgment that the question has been sent — it does **not** wait for the real answer, since a real fan-out across risk members can take minutes (the README documents a real 2m13s example). The main app never opens. Once the Border actually responds, the phone posts a local notification with the real answer, exactly as it would if the same question had been typed into Chat — the operator taps it to read the full answer.

**Why this priority**: This is the entire point of building Siri integration at all — a "Hey Siri" that just opens the app to let you type is not meaningfully better than opening the app directly. This is also the story the operator specifically wants to see working today.

**Independent Test**: With the app fully backgrounded (not force-quit) or terminated, invoke the Siri phrase with a real question, confirm a spoken acknowledgment arrives within a few seconds without the app opening, then confirm a local notification with the real answer arrives once the Border responds (verifiable by checking Chat afterward — the turn is there with `origin` reflecting this was a Siri-originated ask, per FR-011).

**Acceptance Scenarios**:

1. **Given** the device is enrolled and the Border is reachable, **When** the operator invokes "Ask NetGeniusClaw [question]" via Siri with the app not running, **Then** Siri speaks a brief acknowledgment (not the real answer) within a few seconds, and the main app UI never opens.
2. **Given** the same setup, **When** the Border later responds with the real answer, **Then** a local notification is posted with that answer, indistinguishable in kind from a notification produced by asking the same question through the in-app Chat screen.
3. **Given** the device is enrolled but the Border is unreachable (network down, Border offline), **When** the operator invokes the Siri phrase, **Then** Siri speaks a clear, distinct failure message within a bounded time (FR-008) — it does not hang indefinitely, and does not claim the question was sent when it was not.
4. **Given** the device has never been enrolled at all, **When** the operator invokes the Siri phrase, **Then** Siri speaks a clear message that the device isn't set up yet, rather than attempting a connection that can only fail or silently doing nothing.
5. **Given** the Siri phrase is invoked while the main app is already open and connected in the foreground, **When** the question is submitted, **Then** it still succeeds via the same headless path (this spec does not require detecting or reusing an already-live in-app connection — see Edge Cases) and the operator sees the turn appear in Chat once resolved, the same as any other ask.

---

### User Story 2 - Ask how many approvals are pending, by voice (Priority: P2)

An operator says "Hey Siri, ask NetGeniusClaw how many approvals are pending." Siri connects headlessly and speaks the real, current count directly — no acknowledgment-then-notification pattern, since this is a fast, single round-trip query, not a long-running fan-out.

**Why this priority**: Genuinely useful (checking on pending changes hands-free) but secondary to the core "ask anything" capability in User Story 1.

**Independent Test**: With the app backgrounded/terminated and at least one real pending approval on the Border, invoke the Siri phrase and confirm the spoken count matches what the Approvals tab shows.

**Acceptance Scenarios**:

1. **Given** the device is enrolled and the Border is reachable, **When** the operator invokes the phrase, **Then** Siri speaks the current pending-approval count within a bounded time (FR-008), reflecting live Border state, not a stale/cached value.
2. **Given** zero approvals are pending, **When** invoked, **Then** Siri says so explicitly (e.g., "No approvals are pending"), not a bare "0" with no context.
3. **Given** the Border is unreachable or the device isn't enrolled, **When** invoked, **Then** the same distinct failure/not-set-up messages as User Story 1's Acceptance Scenarios 3–4 apply.

---

### User Story 3 - Ask for Border health status, by voice (Priority: P2)

An operator says "Hey Siri, ask NetGeniusClaw for Border health." Siri connects headlessly (proving the Border is reachable) and speaks the most recently received heartbeat/health summary together with how long ago it was received — the same cached value the Dashboard's own connection-status display already reads, not a freshly-generated one.

**Why this priority**: Same tier as User Story 2 — useful, fast, secondary to User Story 1.

**Independent Test**: With the app backgrounded/terminated, invoke the Siri phrase and confirm the spoken summary matches the Dashboard's own connection-status display.

**Acceptance Scenarios**:

1. **Given** the device is enrolled and the Border is reachable, **When** the operator invokes the phrase, **Then** Siri speaks the most recently received health summary together with its age (e.g. "As of 4 minutes ago: All systems normal") within a bounded time (FR-008) — reachability is proven by the connection succeeding, not by the summary itself being freshly generated.
2. **Given** the Border is unreachable or the device isn't enrolled, **When** invoked, **Then** the same distinct failure/not-set-up messages as User Story 1's Acceptance Scenarios 3–4 apply.
3. **Given** the device is enrolled and reachable but has never received a heartbeat at all (e.g. immediately after enrollment), **When** invoked, **Then** Siri speaks a distinct "no health data yet" message — this is not treated as a connection failure.

### Edge Cases

- What happens if the Siri phrase is invoked while the app is already open and holding a live `EdgeClient` connection? Per Acceptance Scenario 5 (User Story 1), this spec does **not** attempt to detect or reuse that live connection — every invocation opens its own fresh headless connection, exactly matching `background_refresh.dart`'s own existing precedent of never coordinating with a foreground app instance. The two connections are independent; the Border sees two separate authenticated sessions from the same pinned key, which it already supports (nothing about this is new to the Border). This may mean the notification the headless path posts arrives independently of anything the foreground app is doing with the same question — a known, accepted limitation, not a defect this spec needs to close.
- What happens if the same question is asked via Siri twice in quick succession (double invocation, or a Siri retry)? Each invocation is an independent headless connection and an independent `ask()` call — no deduplication across invocations is required by this spec (each is a genuinely new, operator-initiated ask, not a re-delivery of the same event, unlike `NotificationDedup`'s existing purpose for the same message arriving twice).
- What happens if the operator's phone has no network at all (airplane mode, no signal) when Siri invokes the intent? The headless connection attempt fails immediately (no route), and this collapses into the same "Border unreachable" failure path as Acceptance Scenario 3 — no special-casing required.
- What happens if the headless engine's work outlives the time iOS is willing to keep the process alive to finish it (a genuine constraint for background execution, distinct from `BGAppRefreshTask`'s explicit `expirationHandler`)? `AskBorderIntent`'s own bounded timeout (FR-008) must be shorter than what App Intents extensions can reasonably expect to run, and the engine must be torn down deterministically (FR-009) regardless of whether the ask succeeded, failed, or timed out — never left running past the intent's own completion.
- What happens to `PendingApprovalsIntent` if the Border responds but with unexpected/malformed data? Speak a generic failure message (FR-008's bounded-time guarantee still applies) rather than crash or hang parsing a response that doesn't match the expected shape.
- What happens to `BorderHealthIntent` if the on-device cached heartbeat data is unexpectedly malformed (not a Border response — `BorderHealthIntent` never queries the Border for health data, see User Story 3)? Speak the same generic failure message rather than crash or hang, treating a corrupt local cache the same as "no health data yet."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST expose three App Intents — `AskBorderIntent` (free-text question parameter), `PendingApprovalsIntent` (no parameters), and `BorderHealthIntent` (no parameters) — via an `AppShortcutsProvider` with natural-language phrases, discoverable and invokable through Siri with no per-operator setup (no manual Shortcuts-app configuration required to make the phrases work).
- **FR-002**: `AskBorderIntent` MUST submit the operator's question to the Border using a headless Flutter engine (following the existing `backgroundRefreshMain`/plain-`FlutterEngine` pattern, `background_refresh.dart`/`AppDelegate.swift:67-108`) — the main app's UI MUST NOT be opened or brought to the foreground as part of handling the intent.
- **FR-003**: `AskBorderIntent` MUST return a spoken acknowledgment as soon as the question has been successfully submitted (i.e., once `EdgeAskClient.ask()` returns a `task_id`) — it MUST NOT block waiting for the Border's actual answer.
- **FR-004**: If the Border's `ask_result` for a Siri-submitted question arrives within that same invocation's bounded engine lifetime (FR-008/FR-009), the headless engine handling it MUST independently post a local notification carrying the real answer, using the same `LocalNotifications` mechanism `backgroundRefreshMain` already uses for feed notifications — this MUST work correctly whether or not the main app is running, since it MUST NOT depend on `HomeShell`'s `ConversationStore.onCompleted` wiring (Context: that wiring is UI-scoped and unavailable to a headless engine). A slower answer that outlives this bounded window MUST NOT be lost: the turn stays persisted as pending (FR-005) and is finalized the same way any other still-pending ask already is in this app — via the existing `reconcileStaleTurns` (`lib/ncfed/turn_reconciler.dart`) reconciliation on a later reconnect (research.md R8) — rather than requiring a new mechanism to hold the headless engine open for the full duration, which no App Intents background-execution primitive available to this spec actually supports.
- **FR-005**: A Siri-submitted question MUST be persisted into the same `ConversationStore` the in-app Chat screen reads, so it appears in Chat history once resolved, the same as any other turn.
- **FR-006**: `PendingApprovalsIntent` MUST headlessly connect to the Border and speak the current live pending-approval count directly (no acknowledge-then-notify pattern) — a zero count MUST be spoken as an explicit statement, not a bare number.
- **FR-007**: `BorderHealthIntent` MUST headlessly connect to the Border (to confirm reachability) and speak the most recently received cached heartbeat/health summary together with its age — the same value the Dashboard's own connection-status display already reads (Context: "Border health" in this system is a periodic passive push, not a request/response query; there is no existing or planned mechanism for the Border to compute and return a summary on demand). If no heartbeat has ever been received, a distinct "no health data yet" message MUST be spoken instead, and MUST NOT be conflated with a connection failure.
- **FR-008**: All three intents MUST complete (success, or a clear spoken failure) within a bounded overall time and MUST NOT hang indefinitely — the cold-connect step MUST time out (matching `background_refresh.dart`'s existing 10-second precedent) and each intent's own Border round-trip MUST also be bounded, with a distinct spoken failure message when a timeout or connection failure occurs.
- **FR-009**: Every headless engine instance created to service one of these three intents MUST be torn down deterministically once that intent's work concludes (success, failure, or timeout) — never left running past the intent's own completion, regardless of outcome.
- **FR-010**: If the device has no enrollment at all, all three intents MUST speak a clear "not set up yet" message rather than attempting a connection that can only fail.
- **FR-011**: A turn created via `AskBorderIntent` MUST be distinguishable, in the persisted `ConversationStore` data, from a turn created via the in-app Chat screen or the watch (mirroring the existing `origin` field's `'phone'`/`'watch'` distinction, spec 073) — so a future surface (e.g., Chat's own UI) could show "asked via Siri" if desired, even though this spec does not require building that UI itself.
- **FR-012**: This spec MUST NOT add, modify, or depend on any new entitlement in `Runner.entitlements`, and MUST NOT change `IPHONEOS_DEPLOYMENT_TARGET`.

### Key Entities

- **AskBorderIntent / PendingApprovalsIntent / BorderHealthIntent (new)**: native `AppIntent` structs, each a thin Swift entry point that launches a headless Flutter engine, invokes a corresponding new Dart `@pragma('vm:entry-point')` function, and awaits its result over a dedicated `FlutterMethodChannel` (mirroring `background_refresh.dart`'s existing pattern) before returning/speaking a result to the intent framework.
- **ConversationTurn (existing, no schema change beyond an `origin` value)**: a Siri-submitted ask reuses the existing entity exactly as `origin: 'watch'` already does for the paired Watch app (spec 073) — this spec adds a new `origin` value (e.g., `'siri'`) rather than a new field or a new store.
- **AppShortcutsProvider (new)**: a static Swift declaration of the natural-language phrases mapping to each intent — no persisted data, purely a compile-time registration Siri indexes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can go from "Hey Siri, ask NetGeniusClaw [question]" to hearing a spoken acknowledgment in a few seconds, with the app never opening, in the common case (device enrolled, Border reachable).
- **SC-002**: The real answer to a Siri-submitted question reaches the operator via a local notification without requiring them to have opened the app at any point after asking.
- **SC-003**: An operator can check pending-approval count (a live, freshly-queried value) or Border health (the most recently received cached value, with its age) by voice and receive a value matching what the in-app Approvals tab / Dashboard shows at that same moment.
- **SC-004**: No invocation of any of the three intents — success, failure, offline, or unenrolled — ever leaves the operator waiting with no spoken response at all; every path resolves to either a real answer/count/summary or a clear, distinct spoken explanation of why not, within a bounded time (FR-008).
- **SC-005**: `flutter analyze` reports zero issues and the full `flutter test` suite passes with zero regressions once this spec's Dart-side code (the new headless entrypoints, the `origin` value addition) is implemented; the native Swift/AppIntents portion is verified via `xcodebuild` compiling successfully and, separately and explicitly, via real on-device Siri/Action-Button/Shortcuts invocation (🔌 DEVICE) — not claimed done from either alone.

## Assumptions

- Scope is exactly B1a of `NETCLAW-MOBILE-1.0.1-BRIEF.md`'s Phase B: the three App Intents plus the `AppShortcutsProvider` that exposes them to Siri, the Action Button, and Shortcuts automations. Control Center's `ControlWidget` (B1b) is explicitly out of scope and will be its own future spec once B1a is proven working.
- The engine-lifecycle decision (headless, not `openAppWhenRun`) was made explicitly with the operator before this spec was written, per the brief's own instruction not to let it be decided implicitly by whatever compiled first.
- `AskBorderIntent`'s "brief spoken acknowledgment, not the real answer" design is itself a direct consequence of that headless decision plus the corrected notification model discovered during research (Context) — it is not a scope reduction imposed for convenience, it is the only design that keeps Siri responsive for a question that can legitimately take minutes to answer.
- No coordination between a headless intent invocation and an already-running foreground app instance is attempted (Edge Cases) — each invocation is fully independent, matching `background_refresh.dart`'s own existing precedent.
- The exact bounded-time values in FR-008 (cold-connect timeout, per-intent round-trip timeout) are implementation details to be finalized in planning against `background_refresh.dart`'s existing 10-second connect-timeout precedent, not fixed numerically in this spec.
- "Verified" for the native Swift/App Intents portion of this spec means compiling successfully via `xcodebuild` for the `Runner` scheme; actual Siri/Action Button/Shortcuts invocation is 🔌 **DEVICE**-only and will be exercised directly with the operator (phone connected, Xcode open) during implementation, not simulated.
