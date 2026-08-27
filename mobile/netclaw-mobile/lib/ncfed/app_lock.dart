import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

const _enabledKey = 'app_lock_enabled';
const _gracePeriodSecondsKey = 'app_lock_grace_period_seconds';

/// 109/research.md R5: a small fixed choice set, not a free-form duration.
const List<Duration> gracePeriodChoices = [
  Duration.zero,
  Duration(seconds: 30),
  Duration(seconds: 60),
  Duration(minutes: 5),
];

const defaultGracePeriod = Duration(seconds: 60);

/// 109/FR-009: pure grace-period arithmetic, fully unit-testable without a
/// platform channel or a clock dependency. `lastForegroundedAt == null`
/// means "never authenticated this session" (e.g. a cold start) -- always
/// requires re-auth regardless of the configured grace period.
bool requiresReauth({
  required DateTime now,
  required DateTime? lastForegroundedAt,
  required Duration gracePeriod,
}) {
  if (lastForegroundedAt == null) return true;
  return now.difference(lastForegroundedAt) >= gracePeriod;
}

/// Persisted app-lock preference (109/FR-008), backed by the same
/// `flutter_secure_storage` instance style already declared for this app.
/// The enabled flag and its grace-period duration are one cohesive
/// preference and belong in the same store (research.md R5).
class AppLockPreference {
  final FlutterSecureStorage _storage;

  AppLockPreference({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  Future<bool> isEnabled() async => (await _storage.read(key: _enabledKey)) == 'true';

  Future<void> setEnabled(bool enabled) =>
      _storage.write(key: _enabledKey, value: enabled.toString());

  Future<Duration> gracePeriod() async {
    final raw = await _storage.read(key: _gracePeriodSecondsKey);
    final seconds = raw == null ? null : int.tryParse(raw);
    return seconds == null ? defaultGracePeriod : Duration(seconds: seconds);
  }

  Future<void> setGracePeriod(Duration gracePeriod) =>
      _storage.write(key: _gracePeriodSecondsKey, value: gracePeriod.inSeconds.toString());
}

/// Injectable so tests never touch the real biometric platform channel --
/// same pattern as `approval_confirmation.dart`'s `authenticate` parameter
/// (109/research.md R4). `biometricOnly: false` (the plugin's own default,
/// matching `approval_confirmation.dart`'s own call) is what already gives
/// every caller a device-passcode fallback; FR-008 requires it here too, so
/// a device with no biometric enrolled can never end up permanently locked
/// out.
Future<bool> authenticateForAppLock(String reason, {Future<bool> Function(String)? authenticate}) {
  final auth = authenticate ??
      (String r) => LocalAuthentication().authenticate(localizedReason: r, biometricOnly: false);
  return auth(reason).catchError((_) => false);
}
