import 'package:flutter/services.dart';

import 'device_heartbeat.dart';

/// Bridges to `WidgetBridgePlugin.swift` (114/FR-001). Best-effort like
/// `LiveActivity`/push registration -- Android has no equivalent, so a
/// failure here must never crash or block anything else; the underlying
/// app flows (heartbeat storage, approval handling, feed unread tracking)
/// all work fully with or without this.
const _channel = MethodChannel('ca.automateyournetwork.netclaw/widget_data');

Future<void> mirrorHealth(DeviceHeartbeatStatus status) async {
  try {
    await _channel.invokeMethod('writeHealth', {
      'summary': status.summary,
      'pushedAt': status.pushedAt.millisecondsSinceEpoch / 1000,
      'isAlarm': status.isAlarm,
    });
  } catch (_) {}
}

Future<void> mirrorPendingCount(int count) async {
  try {
    await _channel.invokeMethod('writePendingCount', {'count': count});
  } catch (_) {}
}

Future<void> mirrorUnreadCount(int count) async {
  try {
    await _channel.invokeMethod('writeUnreadCount', {'count': count});
  } catch (_) {}
}
