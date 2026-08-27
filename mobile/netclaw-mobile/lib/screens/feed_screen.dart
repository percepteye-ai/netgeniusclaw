import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';

import '../ncfed/conversation_search.dart';
import '../ncfed/message_feed.dart';
import 'answer_body.dart';
import 'empty_state.dart';

/// Renders messages the Border has explicitly pushed (US2/T026), in
/// chronological order. `voice` playback is out of scope here (shown as a
/// placeholder chip) — a dedicated audio player is a follow-up, not part of
/// this feature's minimum feed rendering requirement.
class FeedScreen extends StatefulWidget {
  final MessageFeedStore store;

  /// When a push notification is tapped (T032, `NotificationDeepLink`), the
  /// message it referred to is scrolled into view and highlighted. Identified
  /// by `pushedAt` because that is the field the FCM/APNs `data` payload
  /// carries — see `findMessageForNotificationData`.
  final DateTime? highlightPushedAt;

  /// Fires after an acknowledge or delete action (073/FR-012/FR-013) so
  /// `main.dart` can recompute the combined app badge (FR-008) — the
  /// screen itself has no notion of what the badge should be, just that it
  /// changed.
  final VoidCallback? onChanged;

  /// Injectable so tests never touch the real share platform channel
  /// (109/research.md R4).
  final Future<ShareResult> Function(ShareParams params)? shareAction;

  const FeedScreen({
    super.key,
    required this.store,
    this.highlightPushedAt,
    this.onChanged,
    this.shareAction,
  });

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  bool _loading = true;
  final _highlightKey = GlobalKey();

  /// 109/US6: transient search state -- never persisted (FR-015).
  final _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    widget.store.load().then((_) {
      if (mounted) setState(() => _loading = false);
      _scrollToHighlight();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(FeedScreen old) {
    super.didUpdateWidget(old);
    // A second notification tap while the feed is already open.
    if (widget.highlightPushedAt != old.highlightPushedAt) _scrollToHighlight();
  }

  /// Deferred to the next frame: the target tile only has a render object
  /// once the list has been laid out.
  void _scrollToHighlight() {
    if (widget.highlightPushedAt == null) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final ctx = _highlightKey.currentContext;
      if (ctx != null) Scrollable.ensureVisible(ctx, alignment: 0.3);
    });
  }

  /// 109/US6: live text search over message bodies (FR-012). No filter
  /// chips here -- FR-013 scopes those to Chat only, since state/origin are
  /// turn concepts a Feed push doesn't carry.
  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
      child: TextField(
        controller: _searchController,
        decoration: InputDecoration(
          hintText: 'Search feed',
          prefixIcon: const Icon(Icons.search),
          isDense: true,
          suffixIcon: _searchQuery.isEmpty
              ? null
              : IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _searchController.clear();
                    setState(() => _searchQuery = '');
                  },
                ),
          border: const OutlineInputBorder(),
        ),
        onChanged: (value) => setState(() => _searchQuery = value),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    final allMessages = List.of(widget.store.messages)
      ..sort((a, b) => a.pushedAt.compareTo(b.pushedAt));
    if (allMessages.isEmpty) {
      return const EmptyState(
        asset: 'assets/illustrations/empty_feed.png',
        text: 'No messages from the Border yet.',
      );
    }
    final messages = filterMessages(allMessages, query: _searchQuery);
    final filtering = _searchQuery.trim().isNotEmpty;
    return Column(
      children: [
        _buildSearchBar(),
        Expanded(
          child: messages.isEmpty
              ? const Center(child: Text('No matching messages.'))
              : ListView.builder(
                  itemCount: messages.length,
                  itemBuilder: (context, index) {
                    final message = messages[index];
                    final highlighted = !filtering &&
                        widget.highlightPushedAt != null &&
                        message.pushedAt == widget.highlightPushedAt;
                    return _MessageTile(
                      key: highlighted ? _highlightKey : null,
                      message: message,
                      highlighted: highlighted,
                      onAcknowledge: () async {
                        await widget.store.acknowledge(message.pushedAt);
                        if (mounted) setState(() {});
                        widget.onChanged?.call();
                      },
                      onDelete: () async {
                        await widget.store.delete(message.pushedAt);
                        if (mounted) setState(() {});
                        widget.onChanged?.call();
                      },
                      shareAction: widget.shareAction,
                      highlightQuery: _searchQuery,
                    );
                  },
                ),
        ),
      ],
    );
  }
}

enum _MessageAction { copy, share }

class _MessageTile extends StatelessWidget {
  final EdgeMessage message;
  final bool highlighted;
  final VoidCallback onAcknowledge;
  final VoidCallback onDelete;
  final Future<ShareResult> Function(ShareParams params)? shareAction;

  /// 109/US6: the active search query, for highlighting matches in the
  /// message body (when not Markdown-rendered).
  final String highlightQuery;

  const _MessageTile({
    super.key,
    required this.message,
    required this.onAcknowledge,
    required this.onDelete,
    this.highlighted = false,
    this.shareAction,
    this.highlightQuery = '',
  });

  bool get _isText => message.contentType == MessageContentType.text;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      color: highlighted ? scheme.secondaryContainer : null,
      shape: highlighted
          ? RoundedRectangleBorder(
              side: BorderSide(color: scheme.secondary, width: 2),
              borderRadius: BorderRadius.circular(12),
            )
          : null,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Unread indicator (073/FR-011) -- a deliberate, explicit
                // acknowledge clears it (FR-012); merely viewing this tab
                // does not (spec Assumptions).
                if (!message.acknowledged) ...[
                  Icon(Icons.circle, size: 8, color: scheme.primary),
                  const SizedBox(width: 6),
                ],
                Expanded(
                  child: Text(
                    '${message.designatedBy} · ${message.pushedAt.toLocal()}',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          fontWeight: message.acknowledged ? null : FontWeight.bold,
                        ),
                  ),
                ),
                if (!message.acknowledged)
                  IconButton(
                    icon: const Icon(Icons.check_circle_outline, size: 20),
                    tooltip: 'Acknowledge',
                    onPressed: onAcknowledge,
                  ),
                // 109/FR-005, Acceptance Scenario 8: identical copy/share
                // treatment as a chat answer -- no "copy question + answer"
                // here, since a feed push has no question to pair it with.
                if (_isText)
                  IconButton(
                    icon: const Icon(Icons.more_vert, size: 20),
                    tooltip: 'Message actions',
                    onPressed: () => _showMessageActions(context),
                  ),
                IconButton(
                  icon: const Icon(Icons.delete_outline, size: 20),
                  tooltip: 'Delete',
                  onPressed: () => _confirmDelete(context),
                ),
              ],
            ),
            const SizedBox(height: 4),
            _content(context),
          ],
        ),
      ),
    );
  }

  Future<void> _showMessageActions(BuildContext context) async {
    final action = await showModalBottomSheet<_MessageAction>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          ListTile(
            leading: const Icon(Icons.copy),
            title: const Text('Copy'),
            onTap: () => Navigator.pop(ctx, _MessageAction.copy),
          ),
          ListTile(
            leading: const Icon(Icons.share),
            title: const Text('Share'),
            onTap: () => Navigator.pop(ctx, _MessageAction.share),
          ),
        ]),
      ),
    );
    if (action == null || !context.mounted) return;
    await _runMessageAction(context, action);
  }

  Future<void> _runMessageAction(BuildContext context, _MessageAction action) async {
    switch (action) {
      case _MessageAction.copy:
        await Clipboard.setData(ClipboardData(text: message.content));
        if (context.mounted) {
          ScaffoldMessenger.of(context)
              .showSnackBar(const SnackBar(content: Text('Copied')));
        }
      case _MessageAction.share:
        final share = shareAction ?? SharePlus.instance.share;
        await share(ShareParams(text: message.content));
    }
  }

  List<ContextMenuButtonItem> _messageContextMenuItems(BuildContext context) => [
        ContextMenuButtonItem(
          label: 'Copy',
          onPressed: () {
            ContextMenuController.removeAny();
            _runMessageAction(context, _MessageAction.copy);
          },
        ),
        ContextMenuButtonItem(
          label: 'Share',
          onPressed: () {
            ContextMenuController.removeAny();
            _runMessageAction(context, _MessageAction.share);
          },
        ),
      ];

  Future<void> _confirmDelete(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete this message?'),
        content: const Text('This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Delete')),
        ],
      ),
    );
    if (ok ?? false) onDelete();
  }

  Widget _content(BuildContext context) {
    switch (message.contentType) {
      case MessageContentType.text:
        return AnswerBody(
          text: message.content,
          isTerminal: true,
          buildActions: _messageContextMenuItems,
          highlightQuery: highlightQuery,
        );
      case MessageContentType.image:
        try {
          return Image.memory(base64Decode(message.content));
        } catch (_) {
          return const Text('[image could not be decoded]');
        }
      case MessageContentType.voice:
        return const Chip(
          avatar: Icon(Icons.mic, size: 18),
          label: Text('Voice message'),
        );
    }
  }
}
