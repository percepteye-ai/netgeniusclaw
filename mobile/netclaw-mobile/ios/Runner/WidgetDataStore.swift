import Foundation

/// Bridges the phone's own Border health, pending-approval count, and
/// unread-feed count to the `NetClawWidgetExtension` (114/FR-001) via the
/// new phone-only App Group -- a widget/control extension has no way to
/// read another process's in-memory state directly. Mirrors
/// `HeartbeatStatusStore.swift`/`PendingApprovalCountStore.swift`'s existing
/// watch-side pattern exactly (research.md R1), using a DIFFERENT App Group
/// (`group.ca.automateyournetwork.netclaw.mobile.ios`) -- never the existing
/// watch-only one. A member of BOTH the `Runner` and `NetClawWidgetExtension`
/// targets, same reason `PendingApprovalActivityAttributes.swift` is shared
/// between `Runner` and `LiveActivityWidget`.
enum WidgetDataStore {
    private static let appGroupID = "group.ca.automateyournetwork.netclaw.mobile.ios"
    private static let healthSummaryKey = "borderHealthSummary"
    private static let healthPushedAtKey = "borderHealthPushedAt"
    private static let healthIsAlarmKey = "borderHealthIsAlarm"
    private static let pendingCountKey = "pendingApprovalCount"
    private static let unreadCountKey = "unreadFeedCount"

    struct HealthStatus {
        let summary: String
        let pushedAt: Date
        let isAlarm: Bool
    }

    static func writeHealth(summary: String, pushedAt: Date, isAlarm: Bool) {
        let defaults = UserDefaults(suiteName: appGroupID)
        defaults?.set(summary, forKey: healthSummaryKey)
        defaults?.set(pushedAt.timeIntervalSince1970, forKey: healthPushedAtKey)
        defaults?.set(isAlarm, forKey: healthIsAlarmKey)
    }

    /// `nil` when no heartbeat has ever been written (114/FR-007) --
    /// distinct from a real reading, never a false "all clear."
    static func readHealth() -> HealthStatus? {
        guard let defaults = UserDefaults(suiteName: appGroupID),
              let summary = defaults.string(forKey: healthSummaryKey),
              defaults.object(forKey: healthPushedAtKey) != nil
        else { return nil }
        return HealthStatus(
            summary: summary,
            pushedAt: Date(timeIntervalSince1970: defaults.double(forKey: healthPushedAtKey)),
            isAlarm: defaults.bool(forKey: healthIsAlarmKey))
    }

    static func writePendingCount(_ count: Int) {
        UserDefaults(suiteName: appGroupID)?.set(count, forKey: pendingCountKey)
    }

    /// Zero is already an honest value here (no ambiguous "never written"
    /// case, unlike health) -- defaults to 0 on a fresh install.
    static func readPendingCount() -> Int {
        UserDefaults(suiteName: appGroupID)?.integer(forKey: pendingCountKey) ?? 0
    }

    static func writeUnreadCount(_ count: Int) {
        UserDefaults(suiteName: appGroupID)?.set(count, forKey: unreadCountKey)
    }

    static func readUnreadCount() -> Int {
        UserDefaults(suiteName: appGroupID)?.integer(forKey: unreadCountKey) ?? 0
    }
}
