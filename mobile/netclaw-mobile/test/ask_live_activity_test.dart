import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/ask_live_activity.dart';
import 'package:netclaw_mobile/ncfed/conversation_store.dart';
import 'package:netclaw_mobile/ncfed/edge_ask_client.dart';
import 'package:netclaw_mobile/ncfed/edge_client.dart';
import 'package:netclaw_mobile/ncfed/live_activity.dart';

class _FakeRpc implements EdgeRpcSource {
  EdgeMethodHandler? askResultHandler;
  EdgeMethodHandler? progressHandler;

  @override
  void on(String method, EdgeMethodHandler handler) {
    if (method == 'n2n/edge/ask_result') askResultHandler = handler;
    if (method == 'n2n/edge/task_progress') progressHandler = handler;
  }

  @override
  Future<Map<String, dynamic>> call(String method, Map<String, dynamic> params,
      {Duration timeout = const Duration(seconds: 30)}) async =>
      {};

  Future<void> deliverProgress(Map<String, dynamic> params) async => progressHandler!(params);
  Future<void> deliverAskResult(Map<String, dynamic> params) async => askResultHandler!(params);
}

class _RecordedCall {
  final String method;
  final Map<String, dynamic> args;
  _RecordedCall(this.method, this.args);
}

class _FakeLiveActivity implements LiveActivityLike {
  final calls = <_RecordedCall>[];

  @override
  Future<void> startAsk({required String taskId, required String questionPreview}) async {
    calls.add(_RecordedCall('startAsk', {'taskId': taskId, 'questionPreview': questionPreview}));
  }

  @override
  Future<void> updateAsk({required String taskId, required String progressDetail}) async {
    calls.add(_RecordedCall('updateAsk', {'taskId': taskId, 'progressDetail': progressDetail}));
  }

  @override
  Future<void> endAsk({required String taskId, required String state}) async {
    calls.add(_RecordedCall('endAsk', {'taskId': taskId, 'state': state}));
  }
}

void main() {
  late Directory dir;
  late ConversationStore store;
  late _FakeRpc rpc;
  late EdgeAskClient askClient;
  late _FakeLiveActivity liveActivity;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('ask_live_activity_test');
    store = ConversationStore(dir);
    rpc = _FakeRpc();
    askClient = EdgeAskClient(rpc);
    liveActivity = _FakeLiveActivity();
    wireAskLiveActivity(store: store, askClient: askClient, liveActivity: liveActivity);
  });

  tearDown(() async {
    if (await dir.exists()) await dir.delete(recursive: true);
  });

  test('onAdded starts an activity for the new turn (FR-004)', () async {
    await store.addPending('task-1', 'is BGP up on the core switch');

    expect(liveActivity.calls, hasLength(1));
    expect(liveActivity.calls.single.method, 'startAsk');
    expect(liveActivity.calls.single.args['taskId'], 'task-1');
    expect(liveActivity.calls.single.args['questionPreview'], 'is BGP up on the core switch');
  });

  test('a progress notification updates the matching activity (FR-006), never a member count',
      () async {
    await store.addPending('task-1', 'is BGP up');
    await rpc.deliverProgress({'task_id': 'task-1', 'detail': 'Still working — 47s so far.'});
    await Future<void>.delayed(const Duration(milliseconds: 50));

    final updateCalls = liveActivity.calls.where((c) => c.method == 'updateAsk');
    expect(updateCalls, hasLength(1));
    expect(updateCalls.single.args['progressDetail'], 'Still working — 47s so far.');
  });

  test('a completed ask_result ends the activity via onTerminal (FR-007)', () async {
    await store.addPending('task-1', 'is BGP up');
    await rpc.deliverAskResult(
        {'task_id': 'task-1', 'state': 'completed', 'output_text': 'Yes, BGP is up.'});
    await Future<void>.delayed(const Duration(milliseconds: 50));

    final endCalls = liveActivity.calls.where((c) => c.method == 'endAsk');
    expect(endCalls, hasLength(1));
    expect(endCalls.single.args['taskId'], 'task-1');
    expect(endCalls.single.args['state'], 'completed');
  });

  test('a failed ask_result also ends the activity (FR-007)', () async {
    await store.addPending('task-1', 'is BGP up');
    await rpc.deliverAskResult({'task_id': 'task-1', 'state': 'failed', 'error': 'timed out'});
    await Future<void>.delayed(const Duration(milliseconds: 50));

    final endCalls = liveActivity.calls.where((c) => c.method == 'endAsk');
    expect(endCalls, hasLength(1));
    expect(endCalls.single.args['state'], 'failed');
  });

  test('two concurrent asks each get independent start/end calls (FR-004)', () async {
    await store.addPending('task-1', 'first question');
    await store.addPending('task-2', 'second question');

    final startCalls = liveActivity.calls.where((c) => c.method == 'startAsk').toList();
    expect(startCalls, hasLength(2));
    expect(startCalls.map((c) => c.args['taskId']), containsAll(['task-1', 'task-2']));
  });
}
