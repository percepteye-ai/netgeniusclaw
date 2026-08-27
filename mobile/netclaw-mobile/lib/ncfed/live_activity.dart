import 'package:flutter/services.dart';

/// The narrow in-flight-activity surface `ask_live_activity.dart`'s
/// `wireAskLiveActivity` needs -- lets tests substitute a fake recorder
/// instead of a real platform channel (this codebase's established
/// injectable-dependency convention).
abstract class LiveActivityLike {
  Future<void> startAsk({required String taskId, required String questionPreview});
  Future<void> updateAsk({required String taskId, required String progressDetail});
  Future<void> endAsk({required String taskId, required String state});
}

/// Bridges to `LiveActivityBridge.swift` for the Lock Screen Live Activity
/// (099/FR-017/FR-018, extended by spec 113). Best-effort like push
/// registration (`_tryRegisterPush`) -- Android has no equivalent and
/// there's no platform implementation there, so a failure here must never
/// crash or block anything else; the approval and ask/answer flows both
/// work fully with or without this (113/FR-009).
class LiveActivity implements LiveActivityLike {
  static const _channel = MethodChannel('ca.automateyournetwork.netclaw/live_activity');

  Future<void> start({required int approvalId, required String targetName}) async {
    try {
      await _channel.invokeMethod('start', {'approvalId': approvalId, 'targetName': targetName});
    } catch (_) {
      // No Live Activity support on this platform/OS version -- nothing to do.
    }
  }

  /// Tells the pending-approval activity it was resolved, from any surface
  /// (113/FR-003) -- in-app button, notification action, or the watch.
  Future<void> update({required int approvalId, required String status}) async {
    try {
      await _channel.invokeMethod('update', {'approvalId': approvalId, 'status': status});
    } catch (_) {}
  }

  Future<void> end() async {
    try {
      await _channel.invokeMethod('end');
    } catch (_) {}
  }

  /// Starts a new, per-question in-flight activity keyed by [taskId]
  /// (113/FR-004) -- independent of every other in-flight ask.
  @override
  Future<void> startAsk({required String taskId, required String questionPreview}) async {
    try {
      await _channel.invokeMethod('startAsk', {'taskId': taskId, 'questionPreview': questionPreview});
    } catch (_) {}
  }

  /// Updates one specific in-flight activity's status text with the
  /// Border's own free-text progress detail (113/FR-006) -- never a member
  /// count, since no such structured data exists in this system.
  @override
  Future<void> updateAsk({required String taskId, required String progressDetail}) async {
    try {
      await _channel.invokeMethod('updateAsk', {'taskId': taskId, 'progressDetail': progressDetail});
    } catch (_) {}
  }

  /// Ends one specific in-flight activity, reflecting its terminal state
  /// first (113/FR-007) -- `state` is one of the same
  /// completed/failed/cancelled vocabulary `ConversationTurn.state` uses.
  @override
  Future<void> endAsk({required String taskId, required String state}) async {
    try {
      await _channel.invokeMethod('endAsk', {'taskId': taskId, 'state': state});
    } catch (_) {}
  }
}
