import AppIntents
import Foundation

/// Siri/Action Button/Shortcuts entry point for "Border health" (spec 111,
/// User Story 3). Launches a headless `FlutterEngine` running
/// `borderHealthMain` (`lib/ncfed/border_health_headless.dart`), which
/// connects (to prove reachability) then speaks the most recently received
/// cached heartbeat together with its age — "Border health" in this system
/// is a periodic passive push, not a request/response query (research.md
/// R4), so there is no live Border-side call for this intent to make.
struct BorderHealthIntent: AppIntent {
    static var title: LocalizedStringResource = "Border Health"
    static var description = IntentDescription(
        "Check your NetClaw Border's current health status.")
    static var openAppWhenRun: Bool = false

    func perform() async throws -> some IntentResult & ProvidesDialog {
        let runner = await HeadlessEngineRunner(
            entrypoint: "borderHealthMain",
            libraryURI: "package:netclaw_mobile/ncfed/border_health_headless.dart",
            channelName: "ca.automateyournetwork.netclaw/border_health")
        do {
            let spoken = try await runner.submit(nil, timeout: 30)
            return .result(dialog: IntentDialog(stringLiteral: spoken))
        } catch HeadlessIntentError.notEnrolled {
            return .result(dialog: IntentDialog(stringLiteral: "NetClaw isn't set up on this device yet."))
        } catch HeadlessIntentError.timedOut {
            return .result(dialog: IntentDialog(
                stringLiteral: "Couldn't reach your NetClaw Border. Please try again later."))
        } catch HeadlessIntentError.noData {
            return .result(dialog: IntentDialog(
                stringLiteral: "NetClaw hasn't received a health update from your Border yet."))
        } catch {
            return .result(dialog: IntentDialog(
                stringLiteral: "Something went wrong checking Border health."))
        }
    }
}
