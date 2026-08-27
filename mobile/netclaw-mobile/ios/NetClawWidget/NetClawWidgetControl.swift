import AppIntents
import SwiftUI
import WidgetKit

/// Control Center control (spec 114, User Story 3): shows the current
/// pending-approval count and, when tapped, foregrounds Chat ready to type
/// (`OpenChatIntent`, `AppIntent.swift`) -- never a headless, textless
/// `AskBorderIntent` invocation (research.md R2, spec 111's intent requires
/// a question string Control Center has no surface to collect).
struct NetClawWidgetControl: ControlWidget {
    static let kind: String = "ca.automateyournetwork.netclaw.mobile.netclawwidget.control"

    var body: some ControlWidgetConfiguration {
        StaticControlConfiguration(
            kind: Self.kind,
            provider: Provider()
        ) { value in
            ControlWidgetButton(action: OpenChatIntent()) {
                Label("\(value) pending", systemImage: "checkmark.shield")
            }
        }
        .displayName("NetClaw")
        .description("Pending approvals, and a tap to ask NetClaw something.")
    }
}

extension NetClawWidgetControl {
    struct Provider: ControlValueProvider {
        // 114/FR-008/research.md R5: reads the same cached WidgetDataStore
        // value the home-screen and Lock Screen widgets read -- never a
        // fresh network call on every Control Center refresh.
        var previewValue: Int { 0 }

        func currentValue() async throws -> Int {
            WidgetDataStore.readPendingCount()
        }
    }
}
