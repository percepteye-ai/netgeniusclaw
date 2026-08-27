import ActivityKit
import Foundation

/// The shape of the Lock Screen Live Activity NetClaw starts for a
/// submitted question that has not yet answered (spec 113, User Story 3,
/// data-model.md). One activity per `taskId`, unlike the aggregate
/// pending-approval activity -- Chat already supports multiple genuinely
/// concurrent in-progress asks.
///
/// Deliberately carries no `respondedMembers`/`expectedMembers` or any
/// other member-count field: research performed before writing spec 113
/// found that concept does not exist anywhere in the Border's actual
/// sequential-delegation model (research.md R1) -- only what the system
/// genuinely knows is shown: the question, an elapsed timer, and the
/// Border's own free-text progress detail.
///
/// This file is a member of BOTH the `Runner` app target (which starts/
/// updates/ends the activity via `LiveActivityBridge.swift`) and the
/// `LiveActivityWidget` extension target (which renders it) -- ActivityKit
/// requires the same concrete `ActivityAttributes` type on both sides of
/// that boundary, exactly like `PendingApprovalActivityAttributes.swift`
/// already does (research.md R5).
@available(iOS 16.2, *)
struct AskActivityAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        var startedAt: Date
        var progressDetail: String? // the Border's own n2n/edge/task_progress detail, verbatim
        var state: String // "working" | "completed" | "failed" | "cancelled"
    }

    var taskId: String
    var questionPreview: String
}
