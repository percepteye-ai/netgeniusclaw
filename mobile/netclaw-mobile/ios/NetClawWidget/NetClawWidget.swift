import SwiftUI
import WidgetKit

/// Home-screen (`.systemSmall`/`.systemMedium`) and Lock Screen
/// (`.accessoryCircular`/`.accessoryRectangular`/`.accessoryInline`) NetClaw
/// status widget (spec 114, User Stories 1 and 2). Reads `WidgetDataStore`
/// only -- no network call of its own, no polling (114/FR-002/FR-003).
struct NetClawEntry: TimelineEntry {
    let date: Date
    let health: WidgetDataStore.HealthStatus?
    let pendingCount: Int
    let unreadCount: Int
}

struct NetClawTimelineProvider: TimelineProvider {
    func placeholder(in context: Context) -> NetClawEntry {
        NetClawEntry(date: Date(), health: nil, pendingCount: 0, unreadCount: 0)
    }

    func getSnapshot(in context: Context, completion: @escaping (NetClawEntry) -> Void) {
        completion(currentEntry())
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<NetClawEntry>) -> Void) {
        // `.never` -- WidgetBridgePlugin's reloadAllTimelines() (triggered by
        // real Dart-side state changes) is the only thing that should
        // refresh this, not a periodic policy guessing when something
        // changed (research.md R4, matching HeartbeatComplication's
        // existing precedent).
        completion(Timeline(entries: [currentEntry()], policy: .never))
    }

    private func currentEntry() -> NetClawEntry {
        NetClawEntry(
            date: Date(),
            health: WidgetDataStore.readHealth(),
            pendingCount: WidgetDataStore.readPendingCount(),
            unreadCount: WidgetDataStore.readUnreadCount())
    }
}

/// 114/FR-004: every reading is labeled with its age -- never implied live,
/// since widget timeline refreshes are budgeted by iOS and cannot be forced
/// on demand. Mirrors `border_health_headless.dart`'s `_formatAge` exactly.
func formatReadingAge(_ pushedAt: Date) -> String {
    let seconds = Date().timeIntervalSince(pushedAt)
    let minutes = Int(seconds / 60)
    if minutes < 1 { return "just now" }
    if minutes == 1 { return "1 minute ago" }
    if minutes < 60 { return "\(minutes) minutes ago" }
    let hours = minutes / 60
    if hours == 1 { return "1 hour ago" }
    if hours < 24 { return "\(hours) hours ago" }
    let days = hours / 24
    return days == 1 ? "1 day ago" : "\(days) days ago"
}

struct NetClawWidgetEntryView: View {
    @Environment(\.widgetFamily) var family
    var entry: NetClawEntry

    var body: some View {
        switch family {
        case .accessoryCircular:
            circularView
        case .accessoryRectangular:
            rectangularView
        case .accessoryInline:
            inlineView
        default:
            homeScreenView
        }
    }

    // 114/FR-005: no per-approval detail in ANY family -- a bare health
    // summary and/or count only, matching PendingApprovalLiveActivityView's
    // identical restriction.

    private var homeScreenView: some View {
        VStack(alignment: .leading, spacing: 6) {
            healthLine
            Text("\(entry.pendingCount) pending approval\(entry.pendingCount == 1 ? "" : "s")")
                .font(.subheadline)
            if family == .systemMedium {
                Text("\(entry.unreadCount) unread in Feed")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .widgetURL(URL(string: "netclaw://dashboard"))
    }

    @ViewBuilder
    private var healthLine: some View {
        if let health = entry.health {
            VStack(alignment: .leading, spacing: 2) {
                Text(health.isAlarm ? "⚠ \(health.summary)" : health.summary)
                    .font(.headline)
                    .foregroundStyle(health.isAlarm ? .red : .primary)
                Text("As of \(formatReadingAge(health.pushedAt))")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        } else {
            Text("No health data yet")
                .font(.headline)
                .foregroundStyle(.secondary)
        }
    }

    private var circularView: some View {
        VStack {
            if let health = entry.health {
                Image(systemName: health.isAlarm ? "exclamationmark.triangle.fill" : "checkmark.circle.fill")
                    .foregroundStyle(health.isAlarm ? .red : .green)
            } else {
                Image(systemName: "questionmark.circle")
            }
            Text("\(entry.pendingCount)")
                .font(.caption2)
        }
        .widgetURL(URL(string: "netclaw://approvals"))
    }

    private var rectangularView: some View {
        VStack(alignment: .leading) {
            Text(entry.health?.summary ?? "No health data yet")
                .font(.headline)
                .lineLimit(1)
            Text("\(entry.pendingCount) pending")
                .font(.caption)
        }
        .widgetURL(URL(string: "netclaw://approvals"))
    }

    private var inlineView: some View {
        Text(entry.health?.isAlarm == true
            ? "⚠ \(entry.pendingCount) pending"
            : "\(entry.pendingCount) pending")
            .widgetURL(URL(string: "netclaw://approvals"))
    }
}

struct NetClawWidget: Widget {
    let kind: String = "ca.automateyournetwork.netclaw.mobile.netclawwidget.status"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: NetClawTimelineProvider()) { entry in
            NetClawWidgetEntryView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("NetClaw Status")
        .description("Border health and pending approvals at a glance.")
        .supportedFamilies([
            .systemSmall, .systemMedium,
            .accessoryCircular, .accessoryRectangular, .accessoryInline,
        ])
    }
}

#Preview(as: .systemSmall) {
    NetClawWidget()
} timeline: {
    NetClawEntry(
        date: .now,
        health: WidgetDataStore.HealthStatus(summary: "All systems normal", pushedAt: .now, isAlarm: false),
        pendingCount: 2,
        unreadCount: 1)
}
