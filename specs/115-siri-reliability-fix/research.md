# Research: NetGeniusClaw Mobile Siri Reliability Fix + Two-Way Voice + Theme Toggle (Pass 1 of 3)

**Feature**: `115-siri-reliability-fix` | **Date**: 2026-08-16

All decisions below were reached empirically, on a real connected device, during the session
that produced this spec — not from documentation review alone. Each is stated as it would be
for any other spec's research.md, with the on-device evidence as rationale.

## R1: Missing `main.dart` imports, not a build-configuration issue

- **Decision**: Add plain `import` statements for `ask_border_headless.dart`,
  `border_health_headless.dart`, and `pending_approvals_headless.dart` directly into
  `lib/main.dart`, matching the exact pattern `background_refresh.dart` already used (spec 073) —
  no new mechanism.
- **Rationale**: `grep`-confirmed zero references to any of the three files anywhere else in
  `lib/`. Flutter's AOT compiler only includes code reachable from the entry file it's told to
  compile (`lib/main.dart`); `@pragma('vm:entry-point')` only protects an *already-included*
  function from tree-shaking, it cannot pull in a file the compiler never reaches. Verified via
  `strings` on the compiled `App.framework` binary: the three entrypoint symbol names
  (`askBorderMain`, `borderHealthMain`, `pendingApprovalsMain`) were absent before this fix and
  present after.
- **Alternatives considered**: A build-script post-processing step to force-include the files —
  rejected; the one-line import fix is simpler, matches existing precedent exactly, and needs no
  new tooling.

## R2: `FlutterEngineGroup`, not a raw second `FlutterEngine`

- **Decision**: `HeadlessEngineRunner` creates engines via a single, lazily-initialized
  `FlutterEngineGroup`, not `FlutterEngine(name:)` directly, and registers only
  `FlutterSecureStorageDarwinPlugin`, `FlutterLocalNotificationsPlugin`, and the app's own
  `EdgeIdentityPlugin` — not the full `GeneratedPluginRegistrant.register(with:)` sweep.
- **Rationale**: A pulled `.ips` crash report from the device showed `EXC_CRASH`/`SIGKILL` with
  `RBSTerminateContext 0x8BADF00D`: `"scene-update watchdog transgression: exhausted real (wall
  clock) time allowance of 10.00 seconds"`, main thread blocked in `pthread_cond_wait` inside
  `-[UIApplication _applicationDidEnterBackground]`. `GeneratedPluginRegistrant.register(with:)`
  registers *every* plugin in the app — including `FLTFirebaseCorePlugin`/
  `FLTFirebaseMessagingPlugin` — into the new engine while the main engine's own Firebase
  instance is still alive in the same process; Firebase's SDKs are documented as unsafe to
  configure/register twice per process and hold internal locks around exactly the app-lifecycle
  notification implicated in the crash's stack trace. None of the three headless entrypoints call
  anything Firebase-, Camera-, LocalAuth-, MobileScanner-, or SpeechToText-related, so none of
  those plugins are needed in this second engine at all.
- **Alternatives considered**: Keeping the raw `FlutterEngine` but only skipping Firebase
  specifically — rejected in favor of an explicit allow-list (only what's actually used) rather
  than a deny-list, since a deny-list silently breaks again the next time an unrelated plugin is
  added to the app and happens to also hold lifecycle-notification locks.

## R3: `libraryURI` is required for any entrypoint outside `main.dart`

- **Decision**: Every `HeadlessEngineRunner` call site passes the entrypoint's real Dart package
  URI (e.g. `package:netclaw_mobile/ncfed/border_health_headless.dart`) as `libraryURI`, not
  `nil`.
- **Rationale**: After fixing R1/R2, on-device testing still showed every intent invocation
  producing zero observable effect. A temporary on-disk diagnostic log (`bh_diag_native.log`,
  written directly by Swift since `idevicesyslog`/NSLog output proved unreliable to capture on
  this device post-reboot) showed the *native* side completing every step — engine created,
  plugins registered, method channel created, `submit` invoked — while the *Dart* side's own
  diagnostic file (`bh_diag.log`, written as literally the first line of `borderHealthMain()`)
  never existed at all. `FlutterEngineGroup.makeEngine(withEntrypoint:libraryURI:)` silently fails
  to resolve an entrypoint outside the main library when `libraryURI` is `nil` — unlike plain
  `FlutterEngine.run(withEntrypoint:)`, which resolves by bare name against the whole compiled
  program. Confirmed as the actual fix: after adding the correct `libraryURI` per entrypoint, the
  same diagnostic file showed the full, correct Dart-side execution sequence ending in a genuine
  Border round trip, in under one second.
- **Alternatives considered**: Moving the three entrypoint functions into `main.dart` itself to
  avoid needing `libraryURI` at all — rejected; it would scatter headless-engine-specific logic
  into the app's main UI entry file and break the established one-file-per-concern convention
  every other headless entrypoint (`background_refresh.dart`) already follows.

## R4: Two-way voice fast-response window tuned empirically, not from a documented Siri spec

- **Decision**: `AskBorderIntent`'s Dart-side `runAskBorder` first waits up to a tunable
  `askBorderFastWindow` (currently 18s) for a terminal `ask_result`; if one arrives in time, it is
  returned directly as the function's result — which Siri speaks verbatim — instead of the
  generic acknowledgment. If not, today's unchanged behavior (acknowledge now, keep listening in
  the background for `askBorderPostAckWindow`, notify-or-leave-pending) takes over.
- **Rationale**: Apple does not publish a fixed hard timeout for how long Siri/`AppIntents` will
  wait on a `perform()` call before abandoning the request. On-device testing this session showed
  both ends of the real range: a request that received *no* response at all for the full original
  30-50s Swift-side backstop reliably caused Siri to fall back to a web search; a request that
  took the full 12s fast window to fall through to the acknowledgment path was still accepted and
  spoken by Siri without issue. 18s was chosen as a value comfortably inside the confirmed-working
  range while giving the Border's agent (which composes answers via real tool calls, not a
  canned lookup) meaningfully more time to finish within the window than 12s did in practice.
- **Alternatives considered**: No fast window at all (always acknowledge immediately, as spec 111
  originally shipped) — this is exactly the behavior being improved on, per User Story 2. A much
  longer fast window (e.g. 25-30s) — rejected as too close to the observed failure boundary; the
  cost of guessing wrong is the *entire* interaction failing (falling back to a web search)
  rather than merely missing the two-way-voice upgrade, so this plan errs conservative.

## R5: Markdown stripping is Dart-side, applied only to the fast-voice path

- **Decision**: A small text-transform function strips the Border's lightweight markdown
  (`**bold**`, `# headers`, `- `/`* ` list markers) from the answer text immediately before it is
  returned from `runAskBorder`'s fast path, leaving the notification/reconciliation paths
  (`_awaitResultAndNotify`, `ConversationStore`, the app's Chat screen) completely untouched —
  those already display the Border's answers as intended, formatted for reading.
- **Rationale**: The fallback acknowledgment string never contains the real answer text at all
  (it's the fixed "Sent to NetGeniusClaw..." string), so stripping is only ever needed on the one path
  where Siri actually speaks Border-composed prose aloud. Stripping in the app rather than asking
  the Border to compose a second, plain-text version of every answer keeps Pass 1 fully
  self-contained on the mobile side, consistent with this spec's explicit Pass 1/Pass 2 boundary
  (Border-side answer composition changes are Pass 2's job).
- **Alternatives considered**: Asking the Border to return a separate `spoken_summary` field
  alongside the full answer — rejected for this pass; it requires a Border-side (Pass 2) change
  and duplicates work that a client-side regex-based strip already solves adequately for the
  common case (bold/lists/headers), which is what the Border's own answers actually use.

## R6: Theme preference reuses the existing settings-persistence pattern, with one small addition for live reactivity

- **Decision**: A new `ThemePreference` class (mirroring `AppLockPreference`'s existing
  `FlutterSecureStorage`-backed shape exactly: constructor-injectable storage, async
  `load()`/`save()`) persists one string value (`system` | `light` | `dark`). Because
  `NetClawMobileApp` (`lib/main.dart`) is currently a `StatelessWidget` with `themeMode:
  ThemeMode.system` hardcoded, and FR-010 requires the change to take effect immediately without
  a restart, a single app-wide `ValueNotifier<ThemeMode>` (created once in `main()`, loaded from
  `ThemePreference` at startup) is threaded through `NetClawMobileApp` via a
  `ValueListenableBuilder` wrapping the existing `MaterialApp`. `SettingsScreen` writes to both
  `ThemePreference` (persistence) and the notifier (immediate effect) when the operator picks a
  new option.
- **Rationale**: Matches the codebase's existing convention of a small, single-purpose preference
  class per setting (`AppLockPreference`) rather than a general-purpose settings blob, and adds
  the minimum possible reactivity primitive (`ValueNotifier` + `ValueListenableBuilder`) rather
  than introducing a new state-management dependency for what is a single boolean-adjacent value.
- **Alternatives considered**: A full `ChangeNotifier`/`Provider`-based settings store — rejected
  as disproportionate scope for one three-way preference, and this codebase has no existing
  `Provider`/`Riverpod`/`Bloc` dependency to build on; introducing one here would be a much larger
  architectural change than this spec calls for.

## R7: Temporary diagnostic logging is removed, not toggled off

- **Decision**: `border_health_headless.dart`'s `_diag()` helper (writes `bh_diag.log`) and
  `HeadlessEngineRunner.swift`'s `diagLog()` (writes `bh_diag_native.log` + `NSLog`) are deleted
  outright, along with every call site, rather than gated behind a debug flag.
- **Rationale**: Both were added explicitly as temporary instrumentation to diagnose the R1-R3
  bugs above, which are now root-caused, fixed, and verified. Leaving them in — even
  flag-gated — would mean shipping unbounded on-device file writes on every single Siri/Shortcuts
  invocation for no ongoing benefit, and FR-011 exists specifically to require their removal.
- **Alternatives considered**: Keeping them behind a `kDebugMode`/build-flavor check for future
  debugging — rejected; if a similar bug resurfaces, the fix demonstrated in this pass (pull a
  native crash report via `idevicecrashreport`, pull an app-container file via `devicectl device
  copy from`) does not require any app-side instrumentation to already be present, so there is no
  ongoing value to weigh against the cost of shipping it permanently.
