import AppIntents

/// Spec 111 FR-001: exposes the three headless intents to Siri, the Action
/// Button, and Shortcuts automations with zero manual setup — a compile-time
/// phrase table AppIntents indexes, holding no runtime state of its own
/// (data-model.md). Extended once per user story as each intent lands.
struct NetClawShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: AskBorderIntent(),
            phrases: [
                "Ask \(.applicationName) a question",
                "Ask \(.applicationName) something",
                "Ask \(.applicationName) how BGP is doing",
                "How is \(.applicationName) doing",
            ],
            shortTitle: "Ask NetClaw",
            systemImageName: "antenna.radiowaves.left.and.right"
        )
        AppShortcut(
            intent: PendingApprovalsIntent(),
            phrases: [
                "Ask \(.applicationName) how many approvals are pending",
                "Check pending approvals with \(.applicationName)",
                "How many approvals are pending in \(.applicationName)",
                "Check my pending approvals in \(.applicationName)",
            ],
            shortTitle: "Pending Approvals",
            systemImageName: "checkmark.shield"
        )
        AppShortcut(
            intent: BorderHealthIntent(),
            phrases: [
                "Ask \(.applicationName) for Border health",
                "Check \(.applicationName) Border health",
                "How is the Border health in \(.applicationName)",
                "How is \(.applicationName) Border health",
                "Check Border health in \(.applicationName)",
                "How is the network health in \(.applicationName)",
            ],
            shortTitle: "Border Health",
            systemImageName: "heart.text.square"
        )
    }
}
