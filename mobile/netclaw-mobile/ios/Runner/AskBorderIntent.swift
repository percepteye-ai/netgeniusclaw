import AppIntents
import Foundation

/// Siri/Action Button/Shortcuts entry point for "ask NetClaw a question"
/// (spec 111, User Story 1). Launches a headless `FlutterEngine` running
/// `askBorderMain` (`lib/ncfed/ask_border_headless.dart`) rather than opening
/// the app (FR-002) — the acknowledgment is spoken as soon as the question
/// has been submitted (FR-003), never waiting for the real answer, which the
/// headless engine posts as a local notification independently once it
/// arrives (FR-004) or, if it doesn't land within the bounded post-ack
/// window, on a later reconnect via `reconcileStaleTurns` (research.md R8).
struct AskBorderIntent: AppIntent {
    static var title: LocalizedStringResource = "Ask NetClaw"
    static var description = IntentDescription(
        "Send a question to your NetClaw Border and hear a quick acknowledgment — the real answer arrives later as a notification.")

    /// AppIntents needs no capability entitlement (unlike legacy SiriKit/
    /// INIntent) — FR-012, unaffected by this spec.
    static var openAppWhenRun: Bool = false

    @Parameter(title: "Question")
    var question: String

    static var parameterSummary: some ParameterSummary {
        Summary("Ask NetClaw \(\.$question)")
    }

    /// How long this process is given a best-effort chance to stay alive
    /// past `perform()` returning, hoping to catch a fast `ask_result` and
    /// post its notification before the OS reclaims it (research.md R8).
    /// `ProcessInfo.performExpiringActivity` is a REQUEST, not a guarantee —
    /// iOS may grant far less than this, in which case the turn is simply
    /// left pending for `reconcileStaleTurns` to finish later. 🔌 DEVICE:
    /// the actual grant length is unverified without a real device (T013).
    private let postAckExtensionBudget: TimeInterval = 25

    func perform() async throws -> some IntentResult & ProvidesDialog {
        let runner = await HeadlessEngineRunner(
            entrypoint: "askBorderMain",
            libraryURI: "package:netclaw_mobile/ncfed/ask_border_headless.dart",
            channelName: "ca.automateyournetwork.netclaw/ask_border")
        do {
            let ack = try await runner.submit(["question": question], timeout: 50)
            beginBestEffortCompletion(runner: runner)
            return .result(dialog: IntentDialog(stringLiteral: ack))
        } catch HeadlessIntentError.notEnrolled {
            return .result(dialog: IntentDialog(stringLiteral: "NetClaw isn't set up on this device yet."))
        } catch HeadlessIntentError.timedOut {
            return .result(dialog: IntentDialog(
                stringLiteral: "Couldn't reach your NetClaw Border. Please try again later."))
        } catch {
            return .result(dialog: IntentDialog(
                stringLiteral: "Something went wrong sending that to NetClaw."))
        }
    }

    /// Keeps [runner] (and the engine it owns) alive on a background thread
    /// for up to [postAckExtensionBudget], waiting for Dart to report the
    /// bounded post-acknowledgment window's own outcome (research.md R8),
    /// then releases it — the last strong reference going away is this
    /// app's only teardown mechanism for a headless `FlutterEngine`
    /// (FR-009, mirroring `AppDelegate.swift`'s `backgroundRefreshEngine =
    /// nil` precedent).
    private func beginBestEffortCompletion(runner: HeadlessEngineRunner) {
        let semaphore = DispatchSemaphore(value: 0)
        Task.detached {
            await runner.waitForFinished(timeout: postAckExtensionBudget)
            semaphore.signal()
        }
        ProcessInfo.processInfo.performExpiringActivity(
            withReason: "ca.automateyournetwork.netclaw.ask-border-notify"
        ) { expired in
            if expired { return }
            _ = semaphore.wait(timeout: .now() + postAckExtensionBudget)
            _ = runner // keep the engine alive until this scope ends
        }
    }
}
