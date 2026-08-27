import 'package:flutter/services.dart';

/// 109/US5: distinct, short haptic feedback for six key events. Injectable
/// (research.md R4's pattern) so tests never touch the real haptic platform
/// channel — each event is its own function so a recording fake can assert
/// exactly which one fired, and how many times.
class Haptics {
  final void Function() _heavyImpact;
  final void Function() _mediumImpact;
  final void Function() _lightImpact;
  final void Function() _vibrate;

  Haptics({
    void Function()? heavyImpact,
    void Function()? mediumImpact,
    void Function()? lightImpact,
    void Function()? vibrate,
  })  : _heavyImpact = heavyImpact ?? (() => _tryPlatformHaptic(HapticFeedback.heavyImpact)),
        _mediumImpact = mediumImpact ?? (() => _tryPlatformHaptic(HapticFeedback.mediumImpact)),
        _lightImpact = lightImpact ?? (() => _tryPlatformHaptic(HapticFeedback.lightImpact)),
        _vibrate = vibrate ?? (() => _tryPlatformHaptic(HapticFeedback.vibrate));

  void approvalArrived() => _heavyImpact();
  void approvalResolvedSuccessfully() => _mediumImpact();
  void approvalResolveFailed() => _vibrate();
  void chatAnswerCompleted() => _lightImpact();
  void enrollmentSucceeded() => _mediumImpact();

  /// 109/FR-011: fires only on the transition INTO the disconnected state,
  /// never on subsequent retry attempts within the same disconnected
  /// period — callers are responsible for that debounce (see
  /// `reconnect_supervisor.dart`), this method itself fires unconditionally
  /// whenever called.
  void connectionLost() => _vibrate();
}

/// User Story 5, Acceptance Scenario 4: haptics being unavailable (disabled
/// system-wide, no platform binding at all, or any other platform failure)
/// MUST NOT crash or otherwise affect app behavior -- no caller's logic may
/// depend on a haptic having actually fired. `HapticFeedback`'s own
/// `OptionalMethodChannel` already tolerates a genuinely missing platform
/// plugin, but not an uninitialized Flutter binding (a real state, not just
/// a test artifact, on some platform/embedding combinations) -- so this is
/// a real best-effort call, not merely defensive test scaffolding.
void _tryPlatformHaptic(Future<void> Function() call) {
  // ignore: discarded_futures
  call().catchError((_) {});
}
