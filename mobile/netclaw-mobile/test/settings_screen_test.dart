import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/app_lock.dart';
import 'package:netclaw_mobile/ncfed/capability_registration.dart';
import 'package:netclaw_mobile/ncfed/edge_client.dart';
import 'package:netclaw_mobile/screens/settings_screen.dart';

class _RecordingEdgeRpcSource implements EdgeRpcSource {
  @override
  void on(String method, EdgeMethodHandler handler) {}

  @override
  Future<Map<String, dynamic>> call(String method, Map<String, dynamic> params,
      {Duration timeout = const Duration(seconds: 30)}) async {
    return {'registered': true};
  }
}

void main() {
  Widget wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

  group('Remove this device (105/US2/FR-003-FR-006)', () {
    testWidgets('the control is visible', (tester) async {
      var removed = false;
      await tester.pumpWidget(wrap(SettingsScreen(
        capabilities: CapabilityRegistration(_RecordingEdgeRpcSource()),
        onRemoveDevice: () async => removed = true,
        authenticate: (reason) async => true,
      )));

      expect(find.text('Remove this device'), findsOneWidget);
      expect(removed, isFalse);
    });

    testWidgets(
        'FR-004/FR-005: successful biometric re-authentication clears the enrollment',
        (tester) async {
      var removed = false;
      String? reasonGiven;
      await tester.pumpWidget(wrap(SettingsScreen(
        capabilities: CapabilityRegistration(_RecordingEdgeRpcSource()),
        onRemoveDevice: () async => removed = true,
        authenticate: (reason) async {
          reasonGiven = reason;
          return true;
        },
      )));

      await tester.tap(find.text('Remove this device'));
      await tester.pumpAndSettle();

      expect(removed, isTrue);
      expect(reasonGiven, isNotNull);
    });

    testWidgets('a cancelled/failed biometric attempt leaves the enrollment untouched',
        (tester) async {
      var removed = false;
      await tester.pumpWidget(wrap(SettingsScreen(
        capabilities: CapabilityRegistration(_RecordingEdgeRpcSource()),
        onRemoveDevice: () async => removed = true,
        authenticate: (reason) async => false,
      )));

      await tester.tap(find.text('Remove this device'));
      await tester.pumpAndSettle();

      expect(removed, isFalse);
    });

    testWidgets('an authentication error (e.g. biometric unavailable) also leaves it untouched',
        (tester) async {
      var removed = false;
      await tester.pumpWidget(wrap(SettingsScreen(
        capabilities: CapabilityRegistration(_RecordingEdgeRpcSource()),
        onRemoveDevice: () async => removed = true,
        authenticate: (reason) async => throw Exception('no biometric enrolled'),
      )));

      await tester.tap(find.text('Remove this device'));
      await tester.pumpAndSettle();

      expect(removed, isFalse);
    });

    testWidgets('the action never fires without going through authenticate at all', (tester) async {
      var authenticateCalled = false;
      var removed = false;
      await tester.pumpWidget(wrap(SettingsScreen(
        capabilities: CapabilityRegistration(_RecordingEdgeRpcSource()),
        onRemoveDevice: () async => removed = true,
        authenticate: (reason) async {
          authenticateCalled = true;
          return true;
        },
      )));

      await tester.tap(find.text('Remove this device'));
      await tester.pumpAndSettle();

      expect(authenticateCalled, isTrue);
      expect(removed, isTrue);
    });

    testWidgets(
        'FR-006: removal succeeds with no live Border/EdgeClient connection involved at all',
        (tester) async {
      // onRemoveDevice here has no EdgeClient/network access whatsoever --
      // proving structurally that this path cannot depend on a live
      // connection, since it isn't given one to depend on.
      var removed = false;
      await tester.pumpWidget(wrap(SettingsScreen(
        capabilities: CapabilityRegistration(_RecordingEdgeRpcSource()),
        onRemoveDevice: () async => removed = true,
        authenticate: (reason) async => true,
      )));

      await tester.tap(find.text('Remove this device'));
      await tester.pumpAndSettle();

      expect(removed, isTrue);
    });
  });

  group('Face ID app lock (109/US4/FR-008)', () {
    const channel = MethodChannel('plugins.it_nomads.com/flutter_secure_storage');
    late Map<String, String> backing;

    setUp(() {
      backing = {};
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
        switch (call.method) {
          case 'write':
            backing[call.arguments['key'] as String] = call.arguments['value'] as String;
            return null;
          case 'read':
            return backing[call.arguments['key'] as String];
          default:
            return null;
        }
      });
    });

    tearDown(() {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, null);
    });

    Widget buildSettings() => wrap(SettingsScreen(
          capabilities: CapabilityRegistration(_RecordingEdgeRpcSource()),
          onRemoveDevice: () async {},
          authenticate: (reason) async => true,
          appLockPreference: AppLockPreference(),
        ));

    testWidgets('defaults to off, with no grace-period control shown', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pumpAndSettle();

      final toggle =
          tester.widget<SwitchListTile>(find.byType(SwitchListTile).last);
      expect(toggle.value, isFalse);
      expect(find.text('Grace period'), findsNothing);
    });

    testWidgets('toggling on persists and reveals the grace-period control', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Require Face ID to open NetClaw'));
      await tester.pumpAndSettle();

      expect(backing['app_lock_enabled'], 'true');
      expect(find.text('Grace period'), findsOneWidget);
      expect(find.text('1 minute'), findsOneWidget); // default 60s
    });

    testWidgets('selecting a different grace-period duration persists it', (tester) async {
      await tester.pumpWidget(buildSettings());
      await tester.pumpAndSettle();
      await tester.tap(find.text('Require Face ID to open NetClaw'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('1 minute'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('5 minutes').last);
      await tester.pumpAndSettle();

      expect(backing['app_lock_grace_period_seconds'], '${5 * 60}');
    });

    testWidgets('re-opening Settings reflects a previously-enabled toggle', (tester) async {
      backing['app_lock_enabled'] = 'true';
      backing['app_lock_grace_period_seconds'] = '30';

      await tester.pumpWidget(buildSettings());
      await tester.pumpAndSettle();

      final toggle =
          tester.widget<SwitchListTile>(find.byType(SwitchListTile).last);
      expect(toggle.value, isTrue);
      expect(find.text('30 seconds'), findsOneWidget);
    });
  });
}
