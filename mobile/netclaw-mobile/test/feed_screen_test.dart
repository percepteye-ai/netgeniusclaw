import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/message_feed.dart';
import 'package:netclaw_mobile/screens/feed_screen.dart';
import 'package:share_plus/share_plus.dart';

/// Builds a FeedScreen wired to a store pre-seeded with one text message.
/// Real dart:io (Directory/MessageFeedStore) is used, so setup runs inside
/// `runAsync()` — mirrors `chat_screen_test.dart`'s `_buildChatScreen`.
Future<Widget> _buildFeedScreen(WidgetTester tester,
    {String content = 'All healthy.',
    Future<ShareResult> Function(ShareParams)? shareAction}) async {
  late Directory dir;
  late MessageFeedStore store;
  await tester.runAsync(() async {
    dir = await Directory.systemTemp.createTemp('ncfed_feed_test_');
    store = MessageFeedStore(dir);
    await store.append(EdgeMessage(
      contentType: MessageContentType.text,
      content: content,
      designatedBy: 'agent',
      pushedAt: DateTime.now().toUtc(),
    ));
  });
  addTearDown(() => dir.delete(recursive: true));
  return MaterialApp(
    home: Scaffold(body: FeedScreen(store: store, shareAction: shareAction)),
  );
}

/// Seeds several messages with distinct bodies, for the search tests
/// (109/US6) below.
Future<Widget> _buildFeedScreenWithMessages(WidgetTester tester) async {
  late Directory dir;
  late MessageFeedStore store;
  await tester.runAsync(() async {
    dir = await Directory.systemTemp.createTemp('ncfed_feed_search_test_');
    store = MessageFeedStore(dir);
    for (final content in ['All healthy.', 'BGP flapped on core-1.', 'Interface down.']) {
      await store.append(EdgeMessage(
        contentType: MessageContentType.text,
        content: content,
        designatedBy: 'agent',
        pushedAt: DateTime.now().toUtc().add(Duration(seconds: content.length)),
      ));
    }
  });
  addTearDown(() => dir.delete(recursive: true));
  return MaterialApp(home: Scaffold(body: FeedScreen(store: store)));
}

void main() {
  group('message copy/share/select/markdown (109/US2)', () {
    Future<String?> copiedText(WidgetTester tester, Future<void> Function() action) async {
      String? copied;
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
        SystemChannels.platform,
        (call) async {
          if (call.method == 'Clipboard.setData') {
            copied = (call.arguments as Map)['text'] as String?;
          }
          return null;
        },
      );
      addTearDown(() => tester.binding.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, null));
      await action();
      return copied;
    }

    testWidgets('a text message body is selectable', (tester) async {
      await tester.pumpWidget(await _buildFeedScreen(tester));
      await tester.pump();

      expect(find.byType(SelectableText), findsOneWidget);
    });

    testWidgets('the overflow menu Copy action copies the message content', (tester) async {
      await tester.pumpWidget(await _buildFeedScreen(tester));
      await tester.pump();

      final copied = await copiedText(tester, () async {
        await tester.tap(find.byTooltip('Message actions'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Copy'));
        await tester.pumpAndSettle();
      });

      expect(copied, 'All healthy.');
    });

    testWidgets('the Share action is wired through the injected shareAction', (tester) async {
      ShareParams? shared;
      await tester.pumpWidget(await _buildFeedScreen(
        tester,
        shareAction: (params) async {
          shared = params;
          return ShareResult('', ShareResultStatus.success);
        },
      ));
      await tester.pump();

      await tester.tap(find.byTooltip('Message actions'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Share'));
      await tester.pumpAndSettle();

      expect(shared?.text, 'All healthy.');
    });

    testWidgets('a fenced-block message renders via Markdown', (tester) async {
      await tester.pumpWidget(
          await _buildFeedScreen(tester, content: 'result:\n```\ninterface up\n```'));
      await tester.pump();

      expect(find.textContaining('interface up'), findsOneWidget);
    });

    testWidgets('bare CLI-like content with no fence/table stays plain preformatted',
        (tester) async {
      const cli = 'interface # note\n * bullet\nsnake_case=1';
      await tester.pumpWidget(await _buildFeedScreen(tester, content: cli));
      await tester.pump();

      expect(find.text(cli), findsOneWidget);
    });
  });

  group('search (109/US6)', () {
    testWidgets('typing a query narrows the list live', (tester) async {
      await tester.pumpWidget(await _buildFeedScreenWithMessages(tester));
      await tester.pump();

      expect(find.text('All healthy.'), findsOneWidget);
      expect(find.text('BGP flapped on core-1.'), findsOneWidget);
      expect(find.text('Interface down.'), findsOneWidget);

      await tester.enterText(find.byType(TextField), 'BGP');
      await tester.pump();

      expect(find.text('All healthy.'), findsNothing);
      expect(find.text('BGP flapped on core-1.'), findsOneWidget);
      expect(find.text('Interface down.'), findsNothing);
    });

    testWidgets('clearing the query restores the full list', (tester) async {
      await tester.pumpWidget(await _buildFeedScreenWithMessages(tester));
      await tester.pump();

      final searchField = find.byType(TextField);
      await tester.enterText(searchField, 'BGP');
      await tester.pump();
      await tester.enterText(searchField, '');
      await tester.pump();

      expect(find.text('All healthy.'), findsOneWidget);
      expect(find.text('BGP flapped on core-1.'), findsOneWidget);
      expect(find.text('Interface down.'), findsOneWidget);
    });

    testWidgets('a query matching nothing shows an explicit empty state', (tester) async {
      await tester.pumpWidget(await _buildFeedScreenWithMessages(tester));
      await tester.pump();

      await tester.enterText(find.byType(TextField), 'nonexistent');
      await tester.pump();

      expect(find.text('No matching messages.'), findsOneWidget);
    });
  });
}
