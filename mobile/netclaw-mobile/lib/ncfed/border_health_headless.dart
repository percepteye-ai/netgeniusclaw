import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:path_provider/path_provider.dart';

import 'device_heartbeat.dart';
import 'edge_client.dart';
import 'headless_connect.dart';

const _channel = MethodChannel('ca.automateyournetwork.netclaw/border_health');

/// Entry point for the headless `FlutterEngine` `BorderHealthIntent.swift`
/// spins up (spec 111, User Story 3). Unlike the other two intents,
/// "Border health" in this system is a periodic passive push, not a
/// request/response query (research.md R4) -- there is no Border-side call
/// to make for the health data itself. Connecting still matters: it is what
/// proves the Border is reachable at all (FR-008's failure path), and it
/// reuses the SAME cold-connect classification (not-enrolled/timeout) as
/// the other two intents for consistency, even though the connected
/// [EdgeClient] is otherwise unused once `connectHeadless()` succeeds.
@pragma('vm:entry-point')
Future<void> borderHealthMain() async {
  WidgetsFlutterBinding.ensureInitialized();
  _channel.setMethodCallHandler((call) async {
    if (call.method != 'submit') return null;
    final dir = await getApplicationDocumentsDirectory();
    final EdgeClient client;
    try {
      client = await connectHeadless(directory: dir);
    } on NotEnrolledError {
      throw PlatformException(code: 'not_enrolled');
    } on ConnectTimeoutError {
      throw PlatformException(code: 'timeout');
    }
    await client.close();
    try {
      return await runBorderHealth(DeviceHeartbeatStore(dir));
    } on NoHealthDataError {
      throw PlatformException(code: 'no_data');
    } catch (e) {
      throw PlatformException(code: 'failed', message: '$e');
    }
  });
}

/// No heartbeat has ever been received on this device (spec 111, User Story
/// 3 AS3) -- deliberately distinct from a connect failure: the Border was
/// reachable, there just isn't a cached value yet (e.g. immediately after
/// enrollment).
class NoHealthDataError implements Exception {
  const NoHealthDataError();
  @override
  String toString() => 'NoHealthDataError: no cached heartbeat has ever been received';
}

/// The testable core of [borderHealthMain]: reads the last cached heartbeat
/// (research.md R4) and speaks its summary folded together with a
/// human-readable age, or throws [NoHealthDataError] if none has ever been
/// received (FR-007) -- this is never conflated with a connection failure.
Future<String> runBorderHealth(DeviceHeartbeatStore store) async {
  final status = await store.load();
  if (status == null) {
    throw const NoHealthDataError();
  }
  return 'As of ${_formatAge(status.pushedAt)}: ${status.summary}';
}

String _formatAge(DateTime pushedAt) {
  final age = DateTime.now().toUtc().difference(pushedAt.toUtc());
  if (age.inMinutes < 1) return 'just now';
  if (age.inMinutes == 1) return '1 minute ago';
  if (age.inMinutes < 60) return '${age.inMinutes} minutes ago';
  if (age.inHours == 1) return '1 hour ago';
  if (age.inHours < 24) return '${age.inHours} hours ago';
  final days = age.inDays;
  return days == 1 ? '1 day ago' : '$days days ago';
}
