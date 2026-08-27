import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/live_activity.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('ca.automateyournetwork.netclaw/live_activity');

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  test('start() with no platform implementation never throws (best-effort)', () async {
    // No mock handler registered -- mirrors Android/no-op reality.
    await expectLater(
      LiveActivity().start(approvalId: 42, targetName: 'reboot-router'),
      completes,
    );
  });

  test('end() with no platform implementation never throws (best-effort)', () async {
    await expectLater(LiveActivity().end(), completes);
  });

  test('start() invokes the channel with the correct method and arguments', () async {
    MethodCall? received;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      received = call;
      return null;
    });

    await LiveActivity().start(approvalId: 42, targetName: 'reboot-router');

    expect(received?.method, 'start');
    expect(received?.arguments, {'approvalId': 42, 'targetName': 'reboot-router'});
  });

  test('end() invokes the channel', () async {
    MethodCall? received;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      received = call;
      return null;
    });

    await LiveActivity().end();

    expect(received?.method, 'end');
  });

  group('with a recording mock handler', () {
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

    group('update (spec 113, FR-003)', () {
      test('invokes the update method with the given arguments', () async {
        await LiveActivity().update(approvalId: 42, status: 'resolved');

        expect(calls, hasLength(1));
        expect(calls.single.method, 'update');
        expect(calls.single.arguments, {'approvalId': 42, 'status': 'resolved'});
      });

      test('a channel exception is swallowed, matching start/end', () async {
        shouldThrow = true;
        await LiveActivity().update(approvalId: 42, status: 'resolved');
        expect(calls, hasLength(1)); // the call was attempted; failure didn't throw
      });
    });

    group('startAsk/updateAsk/endAsk (spec 113, FR-004/FR-006/FR-007)', () {
      test('startAsk invokes with taskId and questionPreview', () async {
        await LiveActivity().startAsk(taskId: 'task-1', questionPreview: 'is BGP up?');

        expect(calls.single.method, 'startAsk');
        expect(calls.single.arguments, {'taskId': 'task-1', 'questionPreview': 'is BGP up?'});
      });

      test('updateAsk invokes with taskId and progressDetail', () async {
        await LiveActivity()
            .updateAsk(taskId: 'task-1', progressDetail: 'Still working — 47s so far.');

        expect(calls.single.method, 'updateAsk');
        expect(calls.single.arguments,
            {'taskId': 'task-1', 'progressDetail': 'Still working — 47s so far.'});
      });

      test('endAsk invokes with taskId and state', () async {
        await LiveActivity().endAsk(taskId: 'task-1', state: 'completed');

        expect(calls.single.method, 'endAsk');
        expect(calls.single.arguments, {'taskId': 'task-1', 'state': 'completed'});
      });

      test('a channel exception on startAsk/updateAsk/endAsk is swallowed', () async {
        shouldThrow = true;
        final activity = LiveActivity();
        await activity.startAsk(taskId: 't', questionPreview: 'q');
        await activity.updateAsk(taskId: 't', progressDetail: 'd');
        await activity.endAsk(taskId: 't', state: 'failed');
        expect(calls, hasLength(3)); // all three attempted; none threw
      });
    });
  });
}
