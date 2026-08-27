import 'conversation_store.dart';
import 'message_feed.dart';

/// 109/US6: pure filter functions over the existing in-memory lists --
/// search is a client-side filter, not a query engine (spec.md's own scope
/// note: no full-text indexing, no pagination). Both functions return the
/// SAME underlying objects (never copies), so a caller acting on a filtered
/// result (acknowledge/delete) always affects the correct underlying item
/// regardless of any active filter (FR-014).
///
/// [query] matches case-insensitively as a substring; an empty/blank query
/// matches everything. [states] and [origins], when non-null and non-empty,
/// further restrict the result to turns whose `state`/`origin` is a member
/// of the given set (FR-013 -- Chat-only; there is no Feed equivalent).
List<ConversationTurn> filterTurns(
  List<ConversationTurn> turns, {
  String query = '',
  Set<String>? states,
  Set<String>? origins,
}) {
  final needle = query.trim().toLowerCase();
  return turns.where((t) {
    if (states != null && states.isNotEmpty && !states.contains(t.state)) return false;
    if (origins != null && origins.isNotEmpty && !origins.contains(t.origin)) return false;
    if (needle.isEmpty) return true;
    return t.requestText.toLowerCase().contains(needle) ||
        (t.answerText?.toLowerCase().contains(needle) ?? false);
  }).toList();
}

/// Feed's counterpart to [filterTurns] -- text search only (FR-013 scopes
/// state/origin filter chips to Chat; Feed messages carry neither concept).
List<EdgeMessage> filterMessages(List<EdgeMessage> messages, {String query = ''}) {
  final needle = query.trim().toLowerCase();
  if (needle.isEmpty) return List.of(messages);
  return messages.where((m) => m.content.toLowerCase().contains(needle)).toList();
}
