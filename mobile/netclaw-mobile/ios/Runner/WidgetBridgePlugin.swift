import Flutter
import Foundation
import WidgetKit

private let widgetDataChannel = "ca.automateyournetwork.netclaw/widget_data"

/// Mirrors Dart-side state changes into `WidgetDataStore` and requests a
/// timeline reload (114/FR-001) -- no Border/approval/feed logic of its own,
/// exactly mirroring how `LiveActivityBridge`/`WatchRelayPlugin` have none
/// of their own either (research D1, spec 072).
public class WidgetBridgePlugin: NSObject, FlutterPlugin {
    public static func register(with registrar: FlutterPluginRegistrar) {
        let channel = FlutterMethodChannel(name: widgetDataChannel, binaryMessenger: registrar.messenger())
        let instance = WidgetBridgePlugin()
        registrar.addMethodCallDelegate(instance, channel: channel)
    }

    public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "writeHealth":
            writeHealth(call, result: result)
        case "writePendingCount":
            writePendingCount(call, result: result)
        case "writeUnreadCount":
            writeUnreadCount(call, result: result)
        default:
            result(FlutterMethodNotImplemented)
        }
    }

    private func writeHealth(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        guard let args = call.arguments as? [String: Any],
              let summary = args["summary"] as? String,
              let pushedAtEpoch = args["pushedAt"] as? Double,
              let isAlarm = args["isAlarm"] as? Bool
        else {
            result(FlutterError(code: "BAD_ARGS", message: "summary/pushedAt/isAlarm required", details: nil))
            return
        }
        WidgetDataStore.writeHealth(
            summary: summary, pushedAt: Date(timeIntervalSince1970: pushedAtEpoch), isAlarm: isAlarm)
        WidgetCenter.shared.reloadAllTimelines()
        result(nil)
    }

    private func writePendingCount(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        guard let args = call.arguments as? [String: Any], let count = args["count"] as? Int else {
            result(FlutterError(code: "BAD_ARGS", message: "count required", details: nil))
            return
        }
        WidgetDataStore.writePendingCount(count)
        WidgetCenter.shared.reloadAllTimelines()
        result(nil)
    }

    private func writeUnreadCount(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        guard let args = call.arguments as? [String: Any], let count = args["count"] as? Int else {
            result(FlutterError(code: "BAD_ARGS", message: "count required", details: nil))
            return
        }
        WidgetDataStore.writeUnreadCount(count)
        WidgetCenter.shared.reloadAllTimelines()
        result(nil)
    }
}
