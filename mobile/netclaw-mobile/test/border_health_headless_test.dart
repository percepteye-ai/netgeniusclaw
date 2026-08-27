import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/border_health_headless.dart';
import 'package:netclaw_mobile/ncfed/device_heartbeat.dart';

void main() {
  late Directory dir;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('border_health_headless_test');
  });

  tearDown(() async {
    if (await dir.exists()) await dir.delete(recursive: true);
  });

  test('speaks the cached summary together with its age (FR-007)', () async {
    final store = DeviceHeartbeatStore(dir);
    await store.save(DeviceHeartbeatStatus(
      summary: 'All systems normal',
      pushedAt: DateTime.now().toUtc().subtract(const Duration(minutes: 4)),
      isAlarm: false,
    ));

    final spoken = await runBorderHealth(store);

    expect(spoken, contains('4 minutes ago'));
    expect(spoken, contains('All systems normal'));
  });

  test('speaks the alarm line verbatim when one is active', () async {
    final store = DeviceHeartbeatStore(dir);
    await store.save(DeviceHeartbeatStatus(
      summary: '⚠ SLACK HEARTBEAT FAILING',
      pushedAt: DateTime.now().toUtc(),
      isAlarm: true,
    ));

    final spoken = await runBorderHealth(store);

    expect(spoken, contains('⚠ SLACK HEARTBEAT FAILING'));
    expect(spoken, contains('just now'));
  });

  test('throws NoHealthDataError when no heartbeat has ever been received — '
      'distinct from a connection failure (User Story 3 AS3)', () async {
    final store = DeviceHeartbeatStore(dir);

    expect(() => runBorderHealth(store), throwsA(isA<NoHealthDataError>()));
  });

  test('formats an hour-scale age correctly', () async {
    final store = DeviceHeartbeatStore(dir);
    await store.save(DeviceHeartbeatStatus(
      summary: 'All systems normal',
      pushedAt: DateTime.now().toUtc().subtract(const Duration(hours: 2)),
      isAlarm: false,
    ));

    final spoken = await runBorderHealth(store);

    expect(spoken, contains('2 hours ago'));
  });
}
