import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:markdown/markdown.dart' as md;

import '../ncfed/answer_format.dart';
import 'highlighted_text.dart';

/// Shared rendering for chat answers and feed message bodies (109/FR-004,
/// FR-006). Renders as formatted Markdown only once [isTerminal] is true AND
/// the text actually looks like Markdown (`looksLikeMarkdown`) -- otherwise
/// plain monospaced preformatted text, so raw CLI output is never silently
/// mangled and a still-streaming answer never flickers between renderings
/// (Clarifications, 2026-08-14). Always selectable (FR-004).
///
/// Long-press (FR-005's fast-path shortcut, Clarifications 2026-08-14) is
/// wired via [buildActions] into `contextMenuBuilder` rather than an
/// ancestor `GestureDetector.onLongPress` -- `SelectableText`/`MarkdownBody`
/// each register their own internal `LongPressGestureRecognizer` to start
/// text selection, which wins the gesture arena over any ancestor long-press
/// recognizer competing for the same gesture. Overriding the context menu
/// that appears when that native long-press fires is the supported way to
/// customize its content without losing selection itself.
class AnswerBody extends StatelessWidget {
  final String text;
  final bool isTerminal;

  /// Optional text color override (e.g. the failed-state error tint) —
  /// applied to the plain-preformatted-text path only; a Markdown-rendered
  /// answer uses the theme's own Markdown style sheet regardless, since a
  /// failure text is not expected to contain a fenced block/table.
  final Color? textColor;

  /// Builds the long-press context menu's action items (same three actions
  /// as the always-visible overflow menu: Copy / Copy question+answer /
  /// Share). Null skips customization and falls back to the platform's
  /// default Copy/Select-all toolbar.
  final List<ContextMenuButtonItem> Function(BuildContext)? buildActions;

  /// 109/US6: when non-empty, highlights matches in the plain-preformatted-
  /// text path only -- a Markdown-rendered answer is not highlighted, a
  /// disclosed limitation (see class doc comment).
  final String highlightQuery;

  const AnswerBody({
    super.key,
    required this.text,
    required this.isTerminal,
    this.textColor,
    this.buildActions,
    this.highlightQuery = '',
  });

  Widget _contextMenuBuilder(BuildContext context, EditableTextState state) {
    return AdaptiveTextSelectionToolbar.buttonItems(
      anchors: state.contextMenuAnchors,
      buttonItems: buildActions!(context),
    );
  }

  @override
  Widget build(BuildContext context) {
    final contextMenuBuilder = buildActions == null ? null : _contextMenuBuilder;
    if (isTerminal && looksLikeMarkdown(text)) {
      final scheme = Theme.of(context).colorScheme;
      return MarkdownBody(
        data: text,
        selectable: true,
        contextMenuBuilder: contextMenuBuilder,
        styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
          code: const TextStyle(fontFamily: 'monospace'),
          codeblockDecoration: BoxDecoration(
            color: scheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(6),
          ),
        ),
        builders: {'pre': _CodeBlockBuilder()},
      );
    }
    final baseStyle = TextStyle(fontFamily: 'monospace', color: textColor);
    if (highlightQuery.trim().isEmpty) {
      return SelectableText(text, style: baseStyle, contextMenuBuilder: contextMenuBuilder);
    }
    final spans = buildHighlightSpans(
      text,
      highlightQuery.trim(),
      baseStyle,
      baseStyle.copyWith(
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        fontWeight: FontWeight.bold,
      ),
    );
    return SelectableText.rich(
      TextSpan(children: spans),
      contextMenuBuilder: contextMenuBuilder,
    );
  }
}

/// One copy button per fenced code block (FR-006's "single highest-value
/// micro-feature ... for a network engineer") -- replaces the default `pre`
/// rendering entirely rather than layering a button on top of it.
class _CodeBlockBuilder extends MarkdownElementBuilder {
  @override
  Widget? visitElementAfterWithContext(
    BuildContext context,
    md.Element element,
    TextStyle? preferredStyle,
    TextStyle? parentStyle,
  ) {
    final code = element.textContent;
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Stack(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(8, 8, 40, 8),
            decoration: BoxDecoration(
              color: scheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(6),
            ),
            child: SelectableText(code, style: const TextStyle(fontFamily: 'monospace')),
          ),
          Positioned(
            right: 0,
            top: 0,
            child: IconButton(
              icon: const Icon(Icons.copy, size: 16),
              tooltip: 'Copy code block',
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: code));
                if (context.mounted) {
                  ScaffoldMessenger.of(context)
                      .showSnackBar(const SnackBar(content: Text('Code block copied')));
                }
              },
            ),
          ),
        ],
      ),
    );
  }
}
