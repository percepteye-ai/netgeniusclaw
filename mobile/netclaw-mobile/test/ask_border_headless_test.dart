import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/ask_border_headless.dart';
import 'package:netclaw_mobile/ncfed/conversation_store.dart';
import 'package:netclaw_mobile/ncfed/edge_client.dart';

class _FakeRpc implements EdgeRpcSource {
  final String taskId;
  EdgeMethodHandler? askResultHandler;
  final List<String> methodsCalled = [];
  final List<Map<String, dynamic>> paramsCalled = [];

  _FakeRpc(this.taskId);

  @override
  void on(String method, EdgeMethodHandler handler) {
    if (method == 'n2n/edge/ask_result') askResultHandler = handler;
  }

  @override
  Future<Map<String, dynamic>> call(String method, Map<String, dynamic> params,
      {Duration timeout = const Duration(seconds: 30)}) async {
    methodsCalled.add(method);
    paramsCalled.add(params);
    if (method == 'n2n/edge/ask') return {'task_id': taskId};
    return {};
  }

  Future<void> deliverAskResult(Map<String, dynamic> params) async {
    await askResultHandler!(params);
  }
}

class _RecordedNotification {
  final String identifier;
  final String preview;
  final int badgeCount;
  _RecordedNotification(this.identifier, this.preview, this.badgeCount);
}

void main() {
  late Directory dir;
  late ConversationStore store;
  late _FakeRpc rpc;
  final notifications = <_RecordedNotification>[];
  var finishedCalls = 0;
  var closeCalls = 0;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('ask_border_headless_test');
    store = ConversationStore(dir);
    rpc = _FakeRpc('task-1');
    notifications.clear();
    finishedCalls = 0;
    closeCalls = 0;
  });

  tearDown(() async {
    if (await dir.exists()) await dir.delete(recursive: true);
  });

  Future<String> run(
    String question, {
    Duration postAckWindow = const Duration(seconds: 20),
    // Existing tests below exercise the "acknowledge, then background wait"
    // path -- they deliver the fake ask_result only after awaiting the ack,
    // which can't happen until phase 1 (fastWindow) has already elapsed. A
    // zero fastWindow skips straight to that path, preserving their timing.
    Duration fastWindow = Duration.zero,
  }) {
    return runAskBorder(
      question,
      rpc: rpc,
      store: store,
      close: () async => closeCalls++,
      notify: ({required identifier, required preview, required badgeCount}) async {
        notifications.add(_RecordedNotification(identifier, preview, badgeCount));
      },
      onFinished: () => finishedCalls++,
      fastWindow: fastWindow,
      postAckWindow: postAckWindow,
    );
  }

  test('reports the acknowledgment before any ask_result has arrived (FR-003)', () async {
    final ack = await run('is BGP up on the core switch');

    expect(ack, contains('Sent to NetClaw'));
    expect(rpc.methodsCalled, ['n2n/edge/ask']);
    expect(notifications, isEmpty, reason: 'must not wait for the real answer');
  });

  test('persists the turn as pending with origin siri before returning the ack (FR-005/FR-011)',
      () async {
    await run('is BGP up on the core switch');

    final turn = store.turns.single;
    expect(turn.taskId, 'task-1');
    expect(turn.requestText, 'is BGP up on the core switch');
    expect(turn.state, 'pending');
    expect(turn.origin, 'siri');
  });

  test('sends origin: voice on the underlying n2n/edge/ask call (spec 117 FR-002)', () async {
    await run('is BGP up on the core switch');

    expect(rpc.paramsCalled.single['origin'], 'voice');
  });

  test('once ask_result arrives within the window, finalizes the turn and notifies (FR-004)',
      () async {
    await run('is BGP up on the core switch');
    await rpc.deliverAskResult(
        {'task_id': 'task-1', 'state': 'completed', 'output_text': 'Yes, BGP is up.'});
    await Future<void>.delayed(const Duration(milliseconds: 100));

    expect(store.turns.single.state, 'completed');
    expect(store.turns.single.answerText, 'Yes, BGP is up.');
    expect(notifications, hasLength(1));
    expect(notifications.single.identifier, 'task-1');
    expect(notifications.single.preview, 'Yes, BGP is up.');
    expect(finishedCalls, 1);
    expect(closeCalls, 1);
  });

  test('a failed task is also finalized and notified, not left pending', () async {
    await run('is BGP up on the core switch');
    await rpc.deliverAskResult({'task_id': 'task-1', 'state': 'failed', 'error': 'timed out'});
    await Future<void>.delayed(const Duration(milliseconds: 100));

    expect(store.turns.single.state, 'failed');
    expect(notifications, hasLength(1));
  });

  test('if the window elapses first, the turn stays pending for later reconciliation (R8)',
      () async {
    await run('is BGP up on the core switch', postAckWindow: const Duration(milliseconds: 5));
    await Future<void>.delayed(const Duration(milliseconds: 50));

    expect(store.turns.single.state, 'pending');
    expect(notifications, isEmpty);
    expect(finishedCalls, 1, reason: 'onFinished must fire even on timeout, to allow teardown');
    expect(closeCalls, 1);
  });

  test('onFinished fires exactly once even when the result arrives instead of timing out',
      () async {
    await run('is BGP up on the core switch');
    await rpc.deliverAskResult(
        {'task_id': 'task-1', 'state': 'completed', 'output_text': 'ok'});
    await Future<void>.delayed(const Duration(milliseconds: 100));

    expect(finishedCalls, 1);
  });

  test(
      'a real answer arriving within fastWindow is returned directly for Siri to speak '
      '(two-way voice)', () async {
    final resultFuture = runAskBorder(
      'is BGP up on the core switch',
      rpc: rpc,
      store: store,
      close: () async => closeCalls++,
      notify: ({required identifier, required preview, required badgeCount}) async {
        notifications.add(_RecordedNotification(identifier, preview, badgeCount));
      },
      onFinished: () => finishedCalls++,
      fastWindow: const Duration(seconds: 5),
    );
    // Delivered while phase 1 is still listening -- simulates a fast agent
    // reply, distinct from the other tests' zero-fastWindow "slow path".
    await Future<void>.delayed(const Duration(milliseconds: 10));
    await rpc.deliverAskResult(
        {'task_id': 'task-1', 'state': 'completed', 'output_text': 'Yes, BGP is up.'});

    final spoken = await resultFuture;

    expect(spoken, 'Yes, BGP is up.', reason: 'Siri speaks this return value verbatim');
    expect(store.turns.single.state, 'completed');
    expect(notifications, isEmpty, reason: 'no notification needed -- Siri already said it');
    expect(finishedCalls, 1);
    expect(closeCalls, 1);
  });

  test(
      'a markdown-laden answer arriving within fastWindow is stripped for Siri, but stored '
      'unstripped for the Chat screen', () async {
    const raw =
        '**BGP is up.**\n\n# Summary\n- eBGP session to core: established\n- iBGP mesh: full';
    final resultFuture = runAskBorder(
      'is BGP up on the core switch',
      rpc: rpc,
      store: store,
      close: () async => closeCalls++,
      notify: ({required identifier, required preview, required badgeCount}) async {
        notifications.add(_RecordedNotification(identifier, preview, badgeCount));
      },
      onFinished: () => finishedCalls++,
      fastWindow: const Duration(seconds: 5),
    );
    await Future<void>.delayed(const Duration(milliseconds: 10));
    await rpc.deliverAskResult({'task_id': 'task-1', 'state': 'completed', 'output_text': raw});

    final spoken = await resultFuture;

    expect(spoken, isNot(contains('**')));
    expect(spoken, isNot(contains('#')));
    expect(spoken, isNot(contains('- eBGP')));
    expect(spoken, contains('BGP is up.'));
    expect(spoken, contains('eBGP session to core: established'));
    expect(store.turns.single.answerText, raw,
        reason: 'the Chat screen must still see the original, unstripped answer');
  });

  group('askBorderFastWindow', () {
    test('is retuned to 12s against Pass 2\'s measured latency (spec 117 R1)', () {
      expect(askBorderFastWindow, const Duration(seconds: 12));
    });
  });

  group('stripMarkdownForSpeech', () {
    test('removes bold/italic emphasis markers, keeping content', () {
      expect(stripMarkdownForSpeech('**bold** and *italic* text'), 'bold and italic text');
    });

    test('removes headers, keeping content', () {
      expect(stripMarkdownForSpeech('# Title\n## Subtitle\nBody'), 'Title\nSubtitle\nBody');
    });

    test('removes bullet list markers, keeping content', () {
      expect(stripMarkdownForSpeech('- one\n- two\n* three'), 'one\ntwo\nthree');
    });

    test('leaves plain text with no markup unchanged', () {
      expect(stripMarkdownForSpeech('All systems normal.'), 'All systems normal.');
    });

    test('handles a realistic mix of all three without leaving excess blank lines', () {
      const raw = '**Status: OK**\n\n# Summary\n- cml: active\n- pyats: active';
      final result = stripMarkdownForSpeech(raw);
      expect(result, isNot(contains('**')));
      expect(result, isNot(contains('#')));
      expect(result, isNot(matches(RegExp(r'\n{3,}'))));
      expect(result, contains('Status: OK'));
      expect(result, contains('cml: active'));
    });
  });
}
