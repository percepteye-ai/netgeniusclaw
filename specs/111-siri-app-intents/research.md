# Research: NetGeniusClaw Mobile Siri / App Intents Integration (B1a)

**Feature**: `111-siri-app-intents` | **Date**: 2026-08-15

All unknowns below were resolved by reading the actual codebase (Dart client, Swift host app, Border-side
Python), not by assumption. Two of the three intents (`AskBorderIntent`, `PendingApprovalsIntent`) needed
this treatment the most, since the spec's Context section already nailed down the headless-engine mechanics
(carried over verbatim into R1) but left the *data-sourcing* question for the two "quick query" intents open.

## R1: Headless engine invocation pattern

- **Decision**: Each intent's Swift `perform()` launches a plain `FlutterEngine` (never `FlutterEngineGroup` —
  unused anywhere in this codebase), selectively registers only `EdgeIdentityPlugin`, runs a dedicated
  `@pragma('vm:entry-point')` Dart entrypoint per intent, and awaits a result over a dedicated
  `FlutterMethodChannel`. This is `background_refresh.dart`/`AppDelegate.swift:67-108`'s existing pattern,
  reused as-is for a third, fourth, and fifth entrypoint (`askBorderMain`, `pendingApprovalsMain`,
  `borderHealthMain`) rather than inventing a new mechanism.
- **Rationale**: Already proven in production for spec 099's background refresh; reusing it means zero new
  categories of failure mode to reason about (engine teardown, plugin registration, ARC lifetime are all
  solved problems in this codebase already).
- **Alternatives considered**: `openAppWhenRun = true` — rejected by the operator before this spec was
  written (Context/Assumptions: defeats the purpose). `FlutterEngineGroup` — rejected because it would be a
  second, inconsistent pattern alongside the existing plain-`FlutterEngine` one for no benefit at this scale
  (three intents, not dozens).

## R2: AskBorderIntent — submit, acknowledge, notify independently

- **Decision**: `askBorderMain` opens a headless `EdgeClient` connection (10s connect timeout, matching
  `background_refresh.dart`), calls `EdgeAskClient.ask(question)` (returns `task_id` fast — `n2n/edge/ask`
  never blocks on the real answer), reports the spoken acknowledgment back over the method channel
  immediately, then — independently, still inside the same headless engine's Dart isolate — listens on
  `EdgeAskClient`'s `updates` stream for the matching `ask_result`, persists it into `ConversationStore`
  with `origin: 'siri'` (R5), and calls `LocalNotifications.postChatNotification(...)` directly. It does
  **not** wait for this second phase before letting Siri speak the acknowledgment (FR-003).
- **Rationale**: `lib/main.dart:580-593`'s `ConversationStore.onCompleted → postChatNotification` wiring is
  scoped to `_HomeShellState` and is `null` until `HomeShell` builds — a headless engine never builds one, so
  it gets none of that wiring for free (spec Context's own corrected-assumption finding). The headless
  entrypoint must reproduce the two calls (`postChatNotification`, `ConversationStore` write) directly, the
  same way `backgroundRefreshMain` already does for feed notifications after draining the feed queue.
- **Alternatives considered**: Block the intent until the real answer arrives — rejected outright by FR-003
  and User Story 1 (`Priority: P1`)'s own stated reason for existing: a real ask can take minutes (README
  documents 2m13s), and `AppIntent.perform()` running that long risks the extension being killed by iOS
  before it can speak anything at all.

## R3: PendingApprovalsIntent — needs one new Border-side RPC; passive sources are provably insufficient

- **Decision**: Add one new Border-side method, `n2n/edge/approvals_list`, wired to the existing
  `Authorizer.pending_approvals()` (`bgp/federation/authorization.py:176-181`) unchanged, returning
  `{"count": len(rows)}`. `pendingApprovalsMain` opens a headless connection and calls this new method
  directly, then speaks the count (or the explicit zero-case wording FR-006 requires).
- **Rationale — why the two existing candidate data sources don't work**:
  - `ApprovalClient.currentPending` (`lib/ncfed/approval_client.dart:54`) is populated *only* by live
    `receiveApproval()` pushes arriving on an *already-connected* `EdgeClient`'s `n2n/edge/message` handler
    (content_type `'approval'`, wired by `wireMessageFeed`). A fresh headless connection starts with this
    list empty; it has no bootstrap/hydration call of its own. The watch's own `'watch/approvals/list'`
    relay handler (`watch_relay.dart:39` → `approval_client.dart:71`) looks like a counter-example but isn't:
    it reads the *phone app's own long-running* `ApprovalClient` instance over `WatchConnectivity` — the
    watch has no `EdgeClient` of its own (per the project README) and never faces a cold-start empty list.
  - The Border's queue-replay mechanism (`bgp/federation/service.py:1340-1408`, `_flush_edge_queue`) *does*
    replay any `n2n/edge/message` payload — including `content_type: 'approval'` ones — that were queued
    while the device was unreachable, to any newly-registered channel (any fresh connection, headless or
    not), after a ~3s settle delay (`_edge_replay_settle_s`). This looked promising, but it only covers
    approvals the Border never successfully **delivered** yet. An approval already delivered once (to an
    earlier, since-closed connection — e.g., the main app was open when it was pushed, then backgrounded)
    is marked `delivered` in `EdgeQueue` and will never replay again, even though it may still be
    **unresolved** (still awaiting a yes/no) from the operator's point of view. FR-006 explicitly requires
    "live... not a stale/cached value," and a headless connection relying on replay alone would silently
    under-count in exactly this case.
  - `pending_approvals()` already exists precisely because the Border needs an authoritative, freshly-queried
    answer independent of push/delivery history — it reads `approval_request` directly
    (`status='pending'`), the same table `create_approval`/`resolve_approval` write. It is currently unused
    by any edge-facing RPC (only presumed used by an operator-facing surface such as a CLI/dashboard), so
    exposing it to edge clients is new wiring, not new logic.
- **Alternatives considered**: Rely on `currentPending`/queue-replay alone — rejected per the under-count
  case above, which directly violates FR-006. Filter `pending_approvals()` by `peer_identity` before
  returning a count — considered and rejected for this spec: this repo's model has approvals pushed to a
  single admin-operated edge/phone member per risk (the same assumption `push_to_edge` already makes for
  delivery), so the unfiltered, risk-wide count is already the correct scope; per-member filtering can be
  added later if a risk ever needs multiple independent approvers, but that's speculative scope this spec
  does not need.

## R4: BorderHealthIntent — no live query exists; speak the cached heartbeat with its age instead

- **Decision**: `borderHealthMain` opens a headless connection (this alone satisfies the "Border unreachable
  → distinct failure" acceptance scenario, since the connect step itself fails the same way it would for the
  other two intents), and — once connected — reads the on-device `DeviceHeartbeatStore.load()`
  (`lib/ncfed/device_heartbeat.dart:68-85`, plain JSON file, no network I/O) and speaks its `summary`, folding
  in `pushedAt`'s age (e.g., "As of 4 minutes ago: All systems normal") rather than presenting it as freshly
  generated. If no heartbeat has ever been received, speak a distinct "no health data yet" message rather
  than treating that as a connection failure.
- **Rationale**: "Border health" in this system is not a request/response value at all — it is a periodic,
  passive push. `scripts/edge-heartbeat.py`'s `compose()` runs on its own schedule (Slack delivery + a
  posture/daemon/peer report) and is not designed to be invoked synchronously per-request. Searching the
  Border for a phone-initiated equivalent of "give me your health right now" turned up only the *reverse*
  direction: `n2n/edge/self_status` (`bgp/federation/service.py:1468-1476`) is the **Border calling the
  phone** to ask the phone's own status (used for the BASE_FLOOR liveness guarantee, `risk.py:53`) — there is
  no existing Border-side handler for a phone asking the Border for its status. Inventing one that
  synchronously re-runs `edge-heartbeat.py`'s Slack/posture/daemon collection logic on demand is real new
  Border-side surface area this spec's Assumptions never flagged as in scope, and User Story 3's own
  Independent Test only asks that the spoken summary "match the Dashboard's own connection-status
  display" — which itself is fed by the same cached heartbeat mechanism (`heartbeatSummary`/
  `heartbeatIsAlarm`, the same pure functions this decision reuses), not a live Border query. Reusing the
  cache with its age keeps this intent's Border-side footprint at zero, matching the two-intents-need-new-
  wiring / one-doesn't shape this research turned up rather than assuming symmetry across all three.
- **Alternatives considered**: New Border RPC that reruns `compose()` synchronously — rejected as
  disproportionate new scope (Slack delivery side effects, daemon/peer collection latency) for a feature
  whose own spec never anticipated Border-side changes. Treat "no cached heartbeat yet" as a connection
  failure — rejected as misleading: the connection can succeed perfectly well while genuinely no heartbeat
  has ever arrived (e.g., right after enrollment), and conflating the two would produce a false "Border
  unreachable" message on a reachable Border.

## R8: AskBorderIntent's post-acknowledgment wait is bounded, not indefinite — reuses the existing reconcile-on-reconnect fallback

- **Decision**: After reporting the acknowledgment (FR-003), `askBorderMain` persists the turn into
  `ConversationStore` immediately as `state: 'pending'` (so it survives regardless of what happens next),
  then keeps the headless engine alive listening on `EdgeAskClient.updates` for a **bounded** window
  (~25s) for a matching `ask_result`. If it arrives inside that window, the turn is finalized and
  `LocalNotifications.postChatNotification(...)` is called before teardown (FR-004). If the window elapses
  first, the engine tears down anyway (FR-009) and the turn is left `'pending'` — exactly the state any
  other long-running ask is already left in in this system if the app backgrounds/terminates before the
  answer arrives. It is later finalized (and, if the main app happens to be in the foreground at that
  moment, its notification posted) the same way any other stale-pending turn already is today: by
  `reconcileStaleTurns` (`lib/ncfed/turn_reconciler.dart`), which polls `EdgeAskClient.result(taskId)` for
  every non-terminal turn "on first load, and every reconnect" (its own doc comment) — no new mechanism
  needed.
- **Rationale**: There is a real, physical constraint this spec's own User Story 1 text doesn't fully
  reconcile on its own: an `AppIntent`'s `perform()` returning early (to let Siri speak the acknowledgment
  quickly, FR-003) does not keep the hosting process alive indefinitely — Apple's supported mechanisms for
  a *little* extra background runtime after returning a result (e.g. `ProcessInfo.
  performExpiringActivity(withReason:using:)`) are scoped to a handful of seconds, not the multi-minute
  fan-out the README's own 2m13s example describes. No background-execution primitive available to a plain
  in-app `AppIntent` (this spec explicitly has no separate extension target) can plausibly hold a process
  open for minutes on end. `n2n/edge/ask_result` was already designed around this exact class of problem —
  `edge_ask_client.dart`'s own doc comment calls it "best-effort" and says "a disconnected phone recovers
  via `n2n/tasks/status|result` on reconnect" — and `turn_reconciler.dart` is the already-built, already-
  tested (`test/turn_reconciler_test.dart`) mechanism that does exactly that recovery. Reusing it here means
  a Siri-submitted ask that outlives the headless window degrades to *exactly* the same behavior an in-app
  Chat ask already has if the operator backgrounds the app mid-answer — not a new or worse limitation this
  spec introduces.
- **Alternatives considered**: Hold the engine open indefinitely until `ask_result` arrives — rejected as
  not technically achievable for a multi-minute answer under real iOS background-execution limits; would
  either never post a notification for a slow answer or get the process killed with no visible failure at
  all. Have `askBorderMain` itself poll `EdgeAskClient.result(taskId)` in a retry loop for the full
  duration — rejected for the same reason (still bounded by how long the process can stay alive) and for
  duplicating `turn_reconciler.dart`'s already-solved logic rather than reusing it.

## R5: `origin: 'siri'` on `ConversationTurn`

- **Decision**: Add `'siri'` as a third valid value alongside the existing `'phone'`/`'watch'`
  (`lib/ncfed/conversation_store.dart:22-61`, spec 073's own pattern) — no new field, no schema version bump,
  since `origin` is already a plain `String` with a default-on-missing-key fallback.
- **Rationale**: FR-011 only requires the value be distinguishable in storage, not surfaced in any UI by this
  spec. Matches the exact mechanism already used to distinguish watch-originated turns.
- **Alternatives considered**: A separate boolean flag (`isSiriOriginated`) — rejected as redundant with the
  existing enum-shaped `origin` string and inconsistent with the 073 precedent.

## R6: Bounded timeouts (FR-008)

- **Decision**: Reuse `background_refresh.dart`'s existing 10-second cold-connect timeout unchanged for all
  three intents. Per-intent Border round-trip timeouts: `AskBorderIntent`'s acknowledgment phase uses
  `EdgeAskClient.ask()`'s own existing 30s timeout unchanged (submitting is already bounded); the new
  `n2n/edge/approvals_list` call and the (connection-only, no Border round-trip) health check both use a 10s
  timeout, matching the connect step rather than inventing a new duration class.
- **Rationale**: Every timeout value already exists somewhere in this codebase for an equivalent operation;
  introducing a fourth distinct duration would be undocumented, un-precedented tuning with no evidence behind
  it.
- **Alternatives considered**: A single, shorter global timeout for "the whole intent" — rejected because
  `AskBorderIntent`'s ack phase and its later async ask-result phase have genuinely different, already-
  established time budgets (10s to connect, 30s to submit vs. minutes to actually resolve, which FR-003
  explicitly does not wait for).

## R7: Deterministic engine teardown (FR-009)

- **Decision**: Each Swift `perform()` holds its `FlutterEngine` in a local strong reference for the
  intent's lifetime and calls `engine.destroyContext()`/releases the reference in every exit path (success,
  Dart-side error reported over the method channel, and the Swift-side timeout firing first) — a `defer`
  block in Swift covering all three, rather than only the success path.
- **Rationale**: FR-009 is explicit that this must hold "regardless of outcome"; `AppDelegate.swift:102-106`'s
  existing `BGTaskScheduler` `expirationHandler` is the same shape of problem (must clean up even when the
  work didn't finish normally) and is the closest existing precedent, even though App Intents extensions use
  a different completion mechanism than `BGTaskScheduler`.
- **Alternatives considered**: Rely on ARC alone once the method channel result is sent — rejected because a
  timeout path (Border never responds within FR-008's bound) has no natural "result sent" moment to hang the
  cleanup off of; an explicit `defer`/timeout-triggered teardown is needed for that path specifically.
