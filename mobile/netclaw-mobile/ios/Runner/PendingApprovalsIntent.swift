import AppIntents
import Foundation

/// Siri/Action Button/Shortcuts entry point for "how many approvals are
/// pending" (spec 111, User Story 2). Launches a headless `FlutterEngine`
/// running `pendingApprovalsMain` (`lib/ncfed/pending_approvals_headless.
/// dart`), which calls the new `n2n/edge/approvals_list` Border RPC
/// (research.md R3) and speaks the live count directly — no acknowledge-
/// then-notify pattern, since this is a single fast round trip. Unlike
/// `AskBorderIntent`, there is no post-reply phase: the engine tears down as
/// soon as the single `submit` call replies (FR-009).
struct PendingApprovalsIntent: AppIntent {
    static var title: LocalizedStringResource = "Pending Approvals"
    static var description = IntentDescription(
        "Check how many approvals are pending on your NetClaw Border.")
    static var openAppWhenRun: Bool = false

    func perform() async throws -> some IntentResult & ProvidesDialog {
        let runner = await HeadlessEngineRunner(
            entrypoint: "pendingApprovalsMain",
            libraryURI: "package:netclaw_mobile/ncfed/pending_approvals_headless.dart",
            channelName: "ca.automateyournetwork.netclaw/pending_approvals")
        do {
            let spoken = try await runner.submit(nil, timeout: 30)
            return .result(dialog: IntentDialog(stringLiteral: spoken))
        } catch HeadlessIntentError.notEnrolled {
            return .result(dialog: IntentDialog(stringLiteral: "NetClaw isn't set up on this device yet."))
        } catch HeadlessIntentError.timedOut {
            return .result(dialog: IntentDialog(
                stringLiteral: "Couldn't reach your NetClaw Border. Please try again later."))
        } catch {
            return .result(dialog: IntentDialog(
                stringLiteral: "Something went wrong checking pending approvals."))
        }
    }
}
