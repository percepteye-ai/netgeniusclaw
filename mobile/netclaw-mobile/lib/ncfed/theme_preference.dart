import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const _themeModeKey = 'theme_mode';

/// Persisted appearance preference (spec 115/FR-008), backed by the same
/// `flutter_secure_storage` instance style `AppLockPreference` already
/// established (research.md R6). Defaults to `ThemeMode.system` when no
/// value has ever been saved, preserving today's behavior for operators who
/// never touch the new Settings control.
class ThemePreference {
  final FlutterSecureStorage _storage;

  ThemePreference({FlutterSecureStorage? storage}) : _storage = storage ?? const FlutterSecureStorage();

  Future<ThemeMode> load() async {
    final raw = await _storage.read(key: _themeModeKey);
    return switch (raw) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
  }

  Future<void> save(ThemeMode mode) => _storage.write(key: _themeModeKey, value: switch (mode) {
        ThemeMode.light => 'light',
        ThemeMode.dark => 'dark',
        ThemeMode.system => 'system',
      });
}
