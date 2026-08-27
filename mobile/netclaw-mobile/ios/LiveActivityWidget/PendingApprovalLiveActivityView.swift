import ActivityKit
import SwiftUI
import WidgetKit

/// Lock Screen / Dynamic Island presentation (099/FR-017). Shows only that a
/// pending approval exists and its non-sensitive target name -- no approval
/// payload, no requesting-agent detail, nothing an unlocked-phone screen
/// alone would reveal.
@available(iOS 16.2, *)
struct PendingApprovalLiveActivityView: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: PendingApprovalActivityAttributes.self) { context in
            VStack(alignment: .leading) {
                HStack {
                    Image(systemName: "checkmark.shield")
                    VStack(alignment: .leading) {
                        Text("Pending approval")
                            .font(.headline)
                        Text(context.state.targetName)
                            .font(.subheadline)
                    }
                    Spacer()
                }
                // 113/FR-001/FR-002: interactive only on iOS 17+ -- on
                // earlier OS versions this activity renders exactly as it
                // did before this spec (informational only).
                if #available(iOS 17.0, *) {
                    HStack {
                        Button("Approve", intent: ApprovalActionIntent())
                        Button("Deny", intent: ApprovalActionIntent())
                    }
                }
            }
            .padding()
            .activityBackgroundTint(Color.black.opacity(0.8))
            .activitySystemActionForegroundColor(Color.white)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.center) {
                    VStack {
                        Text("Pending approval")
                            .font(.headline)
                        Text(context.state.targetName)
                            .font(.subheadline)
                    }
                }
                DynamicIslandExpandedRegion(.bottom) {
                    if #available(iOS 17.0, *) {
                        HStack {
                            Button("Approve", intent: ApprovalActionIntent())
                            Button("Deny", intent: ApprovalActionIntent())
                        }
                    }
                }
            } compactLeading: {
                Image(systemName: "checkmark.shield")
            } compactTrailing: {
                Text("•")
            } minimal: {
                Image(systemName: "checkmark.shield")
            }
        }
    }
}

@available(iOS 16.2, *)
@main
struct LiveActivityWidgetBundle: WidgetBundle {
    var body: some Widget {
        PendingApprovalLiveActivityView()
        AskLiveActivityView()
    }
}
