import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/screens/answer_body.dart';

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

void main() {
  group('AnswerBody (109/FR-006, Clarifications 2026-08-14)', () {
    testWidgets('terminal + markdown-looking text renders via MarkdownBody', (tester) async {
      await tester.pumpWidget(_wrap(const AnswerBody(
        text: 'result:\n```\ninterface up\n```',
        isTerminal: true,
      )));

      expect(find.byType(MarkdownBody), findsOneWidget);
    });

    testWidgets('terminal + non-markdown text renders as plain preformatted SelectableText',
        (tester) async {
      const cli = 'interface # note\n * bullet\nsnake_case=1';
      await tester.pumpWidget(_wrap(const AnswerBody(text: cli, isTerminal: true)));

      expect(find.byType(MarkdownBody), findsNothing);
      expect(find.text(cli), findsOneWidget);
    });

    testWidgets(
        'non-terminal text NEVER renders via Markdown, even if it looks like Markdown mid-stream',
        (tester) async {
      const midStreamFence = 'here:\n```\nnot closed yet';
      await tester.pumpWidget(_wrap(const AnswerBody(
        text: midStreamFence,
        isTerminal: false,
      )));

      expect(find.byType(MarkdownBody), findsNothing);
      expect(find.text(midStreamFence), findsOneWidget);
    });
  });
}
