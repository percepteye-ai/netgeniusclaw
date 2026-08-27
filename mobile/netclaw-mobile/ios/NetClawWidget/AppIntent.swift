import AppIntents
import Foundation
import UIKit

/// The Control Center control's tap action (spec 114, User Story 3).
/// Deliberately carries NO ask/approval logic of its own -- Control Center
/// provides no text-entry surface, so there is no question text to submit
/// without first opening the app (research.md R2). `openAppWhenRun`
/// foregrounds the app, and `perform()` opens the existing `netclaw://chat`
/// deep link (no task id -- just the tab, compose field ready), mirroring
/// `ApprovalActionIntent`'s shape from spec 113 exactly.
///
/// Needs the same dual `Runner`/`NetClawWidgetExtension` membership and the
/// same `IS_EXTENSION_TARGET` compile guard around `UIApplication.shared`
/// that `ApprovalActionIntent` needed (spec 113 research.md R5) -- this
/// type is referenced by `NetClawWidgetControl`'s `Button`/action, compiled
/// into the extension, but `openAppWhenRun` means only the `Runner`-linked
/// copy of `perform()` ever actually executes.
struct OpenChatIntent: AppIntent {
    static var title: LocalizedStringResource = "Open NetClaw Chat"
    static var openAppWhenRun: Bool = true

    func perform() async throws -> some IntentResult {
        #if !IS_EXTENSION_TARGET
        if let url = URL(string: "netclaw://chat") {
            await UIApplication.shared.open(url)
        }
        #endif
        return .result()
    }
}
