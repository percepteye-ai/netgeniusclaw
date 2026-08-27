import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/theme_preference.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('ThemePreference', () {
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

    test('defaults to ThemeMode.system when nothing has ever been saved', () async {
      final pref = ThemePreference();
      expect(await pref.load(), ThemeMode.system);
    });

    test('round trips ThemeMode.light', () async {
      final pref = ThemePreference();
      await pref.save(ThemeMode.light);
      expect(await pref.load(), ThemeMode.light);
    });

    test('round trips ThemeMode.dark', () async {
      final pref = ThemePreference();
      await pref.save(ThemeMode.dark);
      expect(await pref.load(), ThemeMode.dark);
    });

    test('round trips ThemeMode.system explicitly (not just the default)', () async {
      final pref = ThemePreference();
      await pref.save(ThemeMode.dark);
      await pref.save(ThemeMode.system);
      expect(await pref.load(), ThemeMode.system);
    });
  });
}
