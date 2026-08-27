import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/conversation_search.dart';
import 'package:netclaw_mobile/ncfed/conversation_store.dart';
import 'package:netclaw_mobile/ncfed/message_feed.dart';

ConversationTurn _turn(String taskId, String request,
        {String? answer, String state = 'completed', String origin = 'phone'}) =>
    ConversationTurn(
      taskId: taskId,
      requestText: request,
      submittedAt: DateTime.utc(2026, 8, 14),
      answerText: answer,
      state: state,
      origin: origin,
    );

EdgeMessage _message(String content) => EdgeMessage(
      contentType: MessageContentType.text,
      content: content,
      designatedBy: 'agent',
      pushedAt: DateTime.utc(2026, 8, 14),
    );

void main() {
  group('filterTurns (109/US6/FR-012/FR-013/FR-014)', () {
    late List<ConversationTurn> turns;

    setUp(() {
      turns = [
        _turn('t1', 'is BGP up on the core switch', answer: 'Yes, BGP is established.'),
        _turn('t2', 'check interface status', answer: 'All interfaces up.', state: 'failed'),
        _turn('t3', 'reboot the router', origin: 'watch', state: 'cancelled'),
      ];
    });

    test('an empty query returns everything', () {
      expect(filterTurns(turns), turns);
    });

    test('a query matching nothing returns an empty list', () {
      expect(filterTurns(turns, query: 'nonexistent'), isEmpty);
    });

    test('a query matching a subset returns only that subset, case-insensitively', () {
      final result = filterTurns(turns, query: 'BGP');
      expect(result, [turns[0]]);
    });

    test('the query also matches against answer text, not just the question', () {
      final result = filterTurns(turns, query: 'established');
      expect(result, [turns[0]]);
    });

    test('a state filter alone narrows to matching turns', () {
      final result = filterTurns(turns, states: {'failed'});
      expect(result, [turns[1]]);
    });

    test('an origin filter alone narrows to matching turns', () {
      final result = filterTurns(turns, origins: {'watch'});
      expect(result, [turns[2]]);
    });

    test('a state filter and an origin filter combine via AND with an active query', () {
      // t2 matches the query and the state filter, but not the origin filter.
      final result = filterTurns(turns, query: 'interface', states: {'failed'}, origins: {'watch'});
      expect(result, isEmpty);
    });

    test('filters compose: query AND state both narrow together', () {
      final result = filterTurns(turns, query: 'interface', states: {'failed'});
      expect(result, [turns[1]]);
    });

    test('returns the SAME underlying objects, never copies (FR-014)', () {
      final result = filterTurns(turns, query: 'BGP');
      expect(identical(result.first, turns[0]), isTrue);
    });
  });

  group('filterMessages (109/US6)', () {
    late List<EdgeMessage> messages;

    setUp(() {
      messages = [_message('All healthy.'), _message('BGP flapped on core-1.')];
    });

    test('an empty query returns everything', () {
      expect(filterMessages(messages), messages);
    });

    test('a query matching nothing returns an empty list', () {
      expect(filterMessages(messages, query: 'nonexistent'), isEmpty);
    });

    test('a query matching a subset returns only that subset, case-insensitively', () {
      final result = filterMessages(messages, query: 'bgp');
      expect(result, [messages[1]]);
    });

    test('returns the SAME underlying objects, never copies (FR-014)', () {
      final result = filterMessages(messages, query: 'healthy');
      expect(identical(result.first, messages[0]), isTrue);
    });
  });
}
