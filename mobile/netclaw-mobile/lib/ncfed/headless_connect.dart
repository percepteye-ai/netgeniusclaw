import 'dart:async';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

import 'edge_client.dart';
import 'edge_identity.dart';
import 'enrollment_qr_payload.dart';
import 'enrollment_store.dart';

/// No `EnrollmentStore` file exists on this device (spec 111 FR-010).
class NotEnrolledError implements Exception {
  const NotEnrolledError();
  @override
  String toString() => 'NotEnrolledError: this device has no stored enrollment';
}

/// The cold-connect step did not complete within [connectHeadless]'s timeout
/// (spec 111 FR-008) — the Border is unreachable, or unresponsive.
class ConnectTimeoutError implements Exception {
  const ConnectTimeoutError();
  @override
  String toString() => 'ConnectTimeoutError: connecting to the Border timed out';
}

typedef ReconnectFn = Future<EdgeClient> Function(
  EnrollmentQrPayload payload, {
  required String memberId,
  required String keyFingerprint,
  required EdgeIdentity identity,
});

/// Opens a fresh, authenticated [EdgeClient] connection for a headless App
/// Intents entrypoint, using this device's persisted enrollment — the same
/// cold-connect mechanics `background_refresh.dart` already performs
/// (research.md R1/R6), extracted here so `AskBorderIntent`/
/// `PendingApprovalsIntent`/`BorderHealthIntent` share one not-enrolled/
/// timeout classification instead of tripling it (FR-008/FR-010).
///
/// [reconnect] defaults to [EdgeClient.reconnect] — overridable so tests can
/// exercise the timeout/error-classification behavior without real network
/// I/O (matching this codebase's existing injectable-function-with-
/// production-default convention, e.g. `reconnect_supervisor.dart`).
Future<EdgeClient> connectHeadless({
  Duration timeout = const Duration(seconds: 15),
  Directory? directory,
  ReconnectFn reconnect = EdgeClient.reconnect,
}) async {
  final dir = directory ?? await getApplicationDocumentsDirectory();
  final stored = await EnrollmentStore(dir).load();
  if (stored == null) throw const NotEnrolledError();
  try {
    return await reconnect(
      stored.toPayload(),
      memberId: stored.memberId,
      keyFingerprint: stored.keyFingerprint,
      identity: const EdgeIdentity(),
    ).timeout(timeout);
  } on TimeoutException {
    throw const ConnectTimeoutError();
  }
}
