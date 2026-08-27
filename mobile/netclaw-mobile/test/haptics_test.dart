import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/haptics.dart';

void main() {
  group('Haptics (109/US5/FR-011)', () {
    test("each event maps to exactly the haptic call spec.md's table defines", () {
      final calls = <String>[];
      final haptics = Haptics(
        heavyImpact: () => calls.add('heavy'),
        mediumImpact: () => calls.add('medium'),
        lightImpact: () => calls.add('light'),
        vibrate: () => calls.add('vibrate'),
      );

      haptics.approvalArrived();
      expect(calls, ['heavy']);

      haptics.approvalResolvedSuccessfully();
      expect(calls, ['heavy', 'medium']);

      haptics.approvalResolveFailed();
      expect(calls, ['heavy', 'medium', 'vibrate']);

      haptics.chatAnswerCompleted();
      expect(calls, ['heavy', 'medium', 'vibrate', 'light']);

      haptics.enrollmentSucceeded();
      expect(calls, ['heavy', 'medium', 'vibrate', 'light', 'medium']);

      haptics.connectionLost();
      expect(calls, ['heavy', 'medium', 'vibrate', 'light', 'medium', 'vibrate']);
    });

    test('each event call produces exactly one haptic, not zero or more than one', () {
      var count = 0;
      final haptics = Haptics(
        heavyImpact: () => count++,
        mediumImpact: () => count++,
        lightImpact: () => count++,
        vibrate: () => count++,
      );

      haptics.approvalArrived();
      expect(count, 1);
      haptics.chatAnswerCompleted();
      expect(count, 2);
    });

    test('the production default does not throw even with no Flutter binding initialized',
        () {
      // Regression guard (discovered during implementation): the default
      // HapticFeedback-backed implementation must be fully best-effort --
      // this test file deliberately never calls
      // TestWidgetsFlutterBinding.ensureInitialized(), mirroring the several
      // plain-unit-test files (approval_client_test.dart and friends) that
      // construct ApprovalClient/ReconnectSupervisor without one.
      expect(() => Haptics().approvalArrived(), returnsNormally);
    });
  });
}
