import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';

import 'edge_client.dart';
import 'headless_connect.dart';

const _channel = MethodChannel('ca.automateyournetwork.netclaw/pending_approvals');

/// Entry point for the headless `FlutterEngine` `PendingApprovalsIntent.
/// swift` spins up (spec 111, User Story 2). Unlike `askBorderMain`, this is
/// a single round trip: the spoken result IS the direct reply to Dart's
/// `submit` handler, so the engine tears down as soon as it replies — no
/// bounded post-ack wait needed (research.md R3/R6).
@pragma('vm:entry-point')
Future<void> pendingApprovalsMain() async {
  WidgetsFlutterBinding.ensureInitialized();
  _channel.setMethodCallHandler((call) async {
    if (call.method != 'submit') return null;
    final EdgeClient client;
    try {
      client = await connectHeadless();
    } on NotEnrolledError {
      throw PlatformException(code: 'not_enrolled');
    } on ConnectTimeoutError {
      throw PlatformException(code: 'timeout');
    }
    try {
      return await runPendingApprovals(client);
    } catch (e) {
      throw PlatformException(code: 'failed', message: '$e');
    } finally {
      await client.close();
    }
  });
}

/// The testable core of [pendingApprovalsMain]: given an already-connected
/// [rpc], calls the new `n2n/edge/approvals_list` RPC (research.md R3,
/// data-model.md) and speaks the live count, with an explicit zero-case
/// statement rather than a bare "0" (FR-006).
Future<String> runPendingApprovals(
  EdgeRpcSource rpc, {
  Duration timeout = const Duration(seconds: 10),
}) async {
  final result = await rpc.call('n2n/edge/approvals_list', const {}, timeout: timeout);
  final count = result['count'] as int;
  if (count == 0) return 'No approvals are pending.';
  return count == 1 ? '1 approval is pending.' : '$count approvals are pending.';
}
