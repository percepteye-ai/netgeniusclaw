import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/device_heartbeat.dart';
import 'package:netclaw_mobile/ncfed/widget_data.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('ca.automateyournetwork.netclaw/widget_data');

  final calls = <MethodCall>[];
  var shouldThrow = false;

  setUp(() {
    calls.clear();
    shouldThrow = false;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call);
      if (shouldThrow) throw PlatformException(code: 'FAIL');
      return null;
    });
  });

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  test('mirrorHealth invokes writeHealth with summary/pushedAt/isAlarm', () async {
    final pushedAt = DateTime.utc(2026, 8, 15, 12, 0, 0);
    await mirrorHealth(DeviceHeartbeatStatus(
      summary: 'All systems normal',
      pushedAt: pushedAt,
      isAlarm: false,
    ));

    expect(calls, hasLength(1));
    expect(calls.single.method, 'writeHealth');
    expect(calls.single.arguments, {
      'summary': 'All systems normal',
      'pushedAt': pushedAt.millisecondsSinceEpoch / 1000,
      'isAlarm': false,
    });
  });

  test('mirrorPendingCount invokes writePendingCount with the count', () async {
    await mirrorPendingCount(3);

    expect(calls.single.method, 'writePendingCount');
    expect(calls.single.arguments, {'count': 3});
  });

  test('mirrorUnreadCount invokes writeUnreadCount with the count', () async {
    await mirrorUnreadCount(5);

    expect(calls.single.method, 'writeUnreadCount');
    expect(calls.single.arguments, {'count': 5});
  });

  test('a channel exception on any mirror call is swallowed', () async {
    shouldThrow = true;
    await mirrorHealth(DeviceHeartbeatStatus(
      summary: 'x', pushedAt: DateTime.now().toUtc(), isAlarm: false));
    await mirrorPendingCount(1);
    await mirrorUnreadCount(1);

    expect(calls, hasLength(3)); // all three attempted; none threw
  });
}
