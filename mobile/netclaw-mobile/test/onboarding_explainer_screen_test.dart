import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:netclaw_mobile/main.dart';
import 'package:netclaw_mobile/ncfed/edge_client.dart';
import 'package:netclaw_mobile/ncfed/enrollment_store.dart';

void main() {
  // Same mobile_scanner mocking widget_test.dart already needs -- without
  // this, EnrollmentScreen (shown after the explainer is dismissed) throws
  // MissingPluginException the instant it mounts under flutter_test.
  const scannerMethodChannel = MethodChannel('dev.steenbakker.mobile_scanner/scanner/method');
  const scannerEventChannel = MethodChannel('dev.steenbakker.mobile_scanner/scanner/event');
  const deviceOrientationChannel =
      MethodChannel('dev.steenbakker.mobile_scanner/scanner/deviceOrientation');

  setUp(() {
    debugDefaultTargetPlatformOverride = TargetPlatform.linux;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(scannerMethodChannel, (call) async {
      switch (call.method) {
        case 'state':
          return 1;
        case 'start':
          return <String, Object?>{
            'textureId': 0,
            'cameraDirection': 0,
            'numberOfCameras': 1,
            'currentTorchState': -1,
            'size': {'width': 100.0, 'height': 100.0},
          };
        default:
          return null;
      }
    });
    for (final channel in [scannerEventChannel, deviceOrientationChannel]) {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async => null);
    }
  });

  tearDown(() {
    for (final channel in [scannerMethodChannel, scannerEventChannel, deviceOrientationChannel]) {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, null);
    }
    debugDefaultTargetPlatformOverride = null;
  });

  /// `EnrollmentGate._init()` awaits `documentsDirectory()` then
  /// `store.load()` sequentially, each a real dart:io/Future hop --
  /// mirrors widget_test.dart's own settle loop, needed for the same reason.
  Future<void> settle(WidgetTester tester) async {
    for (var i = 0; i < 10; i++) {
      await Future<void>.delayed(const Duration(milliseconds: 50));
      await tester.pump(const Duration(milliseconds: 20));
    }
  }

  testWidgets('FR-001: a fresh install with no enrollment shows the explainer before the scanner',
      (tester) async {
    late Directory dir;
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp('ncfed_explainer_test_');
      await tester.pumpWidget(MaterialApp(
        home: EnrollmentGate(documentsDirectory: () async => dir),
      ));
      await settle(tester);
    });
    addTearDown(() => dir.delete(recursive: true));

    expect(find.text('Scan Border QR Code'), findsNothing);
    expect(find.textContaining('NetClaw Border server'), findsOneWidget);
    // Must happen before this test function returns -- flutter_test's own
    // end-of-test invariant check runs before tearDown()/addTearDown() fires.
    debugDefaultTargetPlatformOverride = null;
  });

  testWidgets(
      'acceptance scenario 2: tapping continue on the explainer leads to the existing QR scan screen',
      (tester) async {
    late Directory dir;
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp('ncfed_explainer_test_');
      await tester.pumpWidget(MaterialApp(
        home: EnrollmentGate(documentsDirectory: () async => dir),
      ));
      await settle(tester);
    });
    addTearDown(() => dir.delete(recursive: true));

    await tester.tap(find.text('Continue'));
    await tester.pump();

    expect(find.text('Scan Border QR Code'), findsOneWidget);
    debugDefaultTargetPlatformOverride = null;
  });

  testWidgets('FR-002: an already-enrolled launch skips the explainer entirely', (tester) async {
    late Directory dir;
    // Never completes -- this test only needs the gate to reach its
    // "reconnecting" state (set the instant store.load() resolves, before
    // reconnect() is even called), not for reconnection to actually
    // succeed or fail. A real EdgeClient.reconnect() would attempt a real
    // network connection that outlives the test itself.
    final neverCompletes = Completer<EdgeClient>();
    await tester.runAsync(() async {
      dir = await Directory.systemTemp.createTemp('ncfed_explainer_test_');
      await EnrollmentStore(dir).save(const StoredEnrollment(
        memberId: 'risk/test-member',
        keyFingerprint: 'deadbeef',
        borderHost: 'border.example.com',
        borderPort: 8443,
        clawDomain: 'border.example.com',
      ));
      await tester.pumpWidget(MaterialApp(
        home: EnrollmentGate(
          documentsDirectory: () async => dir,
          reconnect: (payload, {required memberId, required keyFingerprint, required identity}) =>
              neverCompletes.future,
        ),
      ));
      await settle(tester);
    });
    addTearDown(() => dir.delete(recursive: true));

    expect(find.textContaining('NetClaw Border server'), findsNothing);
    expect(find.text('Continue'), findsNothing);
    debugDefaultTargetPlatformOverride = null;
  });
}
