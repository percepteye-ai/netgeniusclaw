import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/main.dart';
import 'package:netclaw_mobile/ncfed/app_lock.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('requiresReauth (109/FR-009, pure grace-period logic)', () {
    final now = DateTime.utc(2026, 8, 14, 12, 0, 0);

    test('never authenticated this session (cold start) -- always requires reauth', () {
      expect(
        requiresReauth(now: now, lastForegroundedAt: null, gracePeriod: defaultGracePeriod),
        isTrue,
      );
    });

    test('within the grace period -- no reauth required', () {
      final last = now.subtract(const Duration(seconds: 30));
      expect(
        requiresReauth(now: now, lastForegroundedAt: last, gracePeriod: const Duration(seconds: 60)),
        isFalse,
      );
    });

    test('exactly at the grace period boundary -- requires reauth', () {
      final last = now.subtract(const Duration(seconds: 60));
      expect(
        requiresReauth(now: now, lastForegroundedAt: last, gracePeriod: const Duration(seconds: 60)),
        isTrue,
      );
    });

    test('past the grace period -- requires reauth', () {
      final last = now.subtract(const Duration(minutes: 10));
      expect(
        requiresReauth(now: now, lastForegroundedAt: last, gracePeriod: const Duration(seconds: 60)),
        isTrue,
      );
    });

    test('a zero (immediate) grace period always requires reauth on resume', () {
      final last = now.subtract(const Duration(milliseconds: 1));
      expect(
        requiresReauth(now: now, lastForegroundedAt: last, gracePeriod: Duration.zero),
        isTrue,
      );
    });
  });

  group('AppLockPreference', () {
    const channel = MethodChannel('plugins.it_nomads.com/flutter_secure_storage');
    final backing = <String, String>{};

    setUp(() {
      backing.clear();
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

    test('defaults to disabled with the default grace period when nothing is set yet', () async {
      final pref = AppLockPreference();
      expect(await pref.isEnabled(), isFalse);
      expect(await pref.gracePeriod(), defaultGracePeriod);
    });

    test('enabling persists and is read back', () async {
      final pref = AppLockPreference();
      await pref.setEnabled(true);
      expect(await pref.isEnabled(), isTrue);
    });

    test('a selected grace period persists and is read back', () async {
      final pref = AppLockPreference();
      await pref.setGracePeriod(const Duration(minutes: 5));
      expect(await pref.gracePeriod(), const Duration(minutes: 5));
    });
  });

  group('AppLockGate (109/FR-008/FR-009)', () {
    const channel = MethodChannel('plugins.it_nomads.com/flutter_secure_storage');

    void mockStorage(Map<String, String> backing) {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
        if (call.method == 'read') return backing[call.arguments['key'] as String];
        return null;
      });
      addTearDown(() =>
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
              .setMockMethodCallHandler(channel, null));
    }

    testWidgets('toggle off (default): the child is shown immediately, no lock screen',
        (tester) async {
      mockStorage({});
      await tester.pumpWidget(const MaterialApp(
        home: AppLockGate(child: Text('protected content')),
      ));
      await tester.pumpAndSettle();

      expect(find.text('protected content'), findsOneWidget);
      expect(find.text('NetClaw is locked'), findsNothing);
    });

    testWidgets(
        'toggle on, unauthenticated: no descendant of the child ever renders',
        (tester) async {
      mockStorage({'app_lock_enabled': 'true'});
      await tester.pumpWidget(MaterialApp(
        home: AppLockGate(
          appLockPreference: AppLockPreference(),
          authenticate: (reason) async => false, // cancelled/failed, every attempt
          child: const Text('protected content'),
        ),
      ));
      await tester.pumpAndSettle();

      expect(find.text('protected content'), findsNothing);
      expect(find.text('NetClaw is locked'), findsOneWidget);
    });

    testWidgets('toggle on, successful auth: the child is then shown', (tester) async {
      mockStorage({'app_lock_enabled': 'true'});
      await tester.pumpWidget(MaterialApp(
        home: AppLockGate(
          appLockPreference: AppLockPreference(),
          authenticate: (reason) async => true,
          child: const Text('protected content'),
        ),
      ));
      await tester.pumpAndSettle();

      expect(find.text('protected content'), findsOneWidget);
    });
  });
}
