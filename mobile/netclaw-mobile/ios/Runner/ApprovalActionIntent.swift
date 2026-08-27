import AppIntents
import Foundation
import UIKit

/// The pending-approval Live Activity's Approve/Deny buttons (spec 113,
/// User Story 1). Deliberately carries NO approval-resolution logic of its
/// own -- a `LiveActivityIntent` cannot reliably present the biometric/
/// passcode confirmation `ApprovalsScreen`'s existing resolve flow requires
/// (spec 073, FR-003) while the phone is locked or the app is backgrounded,
/// so this spec does not weaken that invariant to make the button "work."
/// `openAppWhenRun` foregrounds the app, and `perform()` opens the existing
/// `netclaw://approvals` deep link (research.md R2) to land on the Approvals
/// tab, where the unmodified, fully-gated resolve flow runs exactly as it
/// does today.
///
/// This type needs dual membership in BOTH the `Runner` app target and the
/// `LiveActivityWidget` extension target -- `PendingApprovalLiveActivityView
/// .swift`'s `Button(intent: ApprovalActionIntent())` calls, compiled into
/// the extension, need the concrete type available there too (research.md
/// R5's dual-membership reasoning applies here, not just to
/// `AskActivityAttributes.swift`). But `UIApplication.shared` is unavailable
/// in application extensions -- and `openAppWhenRun = true` means the ONLY
/// copy of `perform()` that ever actually executes at runtime is the one
/// linked into `Runner` itself (the system dispatches execution there, not
/// into the extension process), so the `IS_EXTENSION_TARGET` compilation
/// condition (set only on `LiveActivityWidget`'s build settings) excludes
/// the unavailable call from that target's build -- dead code there either
/// way, just code the extension-target compiler must never be asked to
/// accept.
@available(iOS 17.0, *)
struct ApprovalActionIntent: LiveActivityIntent {
    static var title: LocalizedStringResource = "Open NetClaw Approvals"
    static var openAppWhenRun: Bool = true

    func perform() async throws -> some IntentResult {
        #if !IS_EXTENSION_TARGET
        if let url = URL(string: "netclaw://approvals") {
            await UIApplication.shared.open(url)
        }
        #endif
        return .result()
    }
}
