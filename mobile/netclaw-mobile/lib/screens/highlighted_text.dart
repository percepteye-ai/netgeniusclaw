import 'package:flutter/material.dart';

/// 109/US6: renders [text] with every case-insensitive occurrence of
/// [query] visually highlighted. Shared by Chat's question header and
/// Feed/Chat's plain-preformatted answer/message bodies -- Markdown-rendered
/// answers (FR-006) are not highlighted, a disclosed limitation rather than
/// an attempt to splice spans into `flutter_markdown_plus`'s own rendering.
class HighlightedText extends StatelessWidget {
  final String text;
  final String query;
  final TextStyle? style;
  final bool selectable;

  const HighlightedText(
    this.text, {
    super.key,
    required this.query,
    this.style,
    this.selectable = false,
  });

  @override
  Widget build(BuildContext context) {
    final needle = query.trim();
    final effectiveStyle = DefaultTextStyle.of(context).style.merge(style);
    if (needle.isEmpty) {
      return selectable
          ? SelectableText(text, style: effectiveStyle)
          : Text(text, style: effectiveStyle);
    }

    final spans = buildHighlightSpans(
      text,
      needle,
      effectiveStyle,
      effectiveStyle.copyWith(
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        fontWeight: FontWeight.bold,
      ),
    );

    return selectable
        ? SelectableText.rich(TextSpan(children: spans))
        : Text.rich(TextSpan(children: spans));
  }
}

/// Splits [text] into spans around every case-insensitive occurrence of
/// [query], styling matches with [highlightStyle] and everything else with
/// [style]. Returns a single unstyled span for the whole text when [query]
/// is empty. Shared by [HighlightedText] and `AnswerBody`'s plain-
/// preformatted-text path (`answer_body.dart`).
List<TextSpan> buildHighlightSpans(
  String text,
  String query,
  TextStyle style,
  TextStyle highlightStyle,
) {
  if (query.isEmpty) return [TextSpan(text: text, style: style)];
  final spans = <TextSpan>[];
  final lowerText = text.toLowerCase();
  final lowerNeedle = query.toLowerCase();
  var start = 0;
  while (true) {
    final index = lowerText.indexOf(lowerNeedle, start);
    if (index < 0) {
      spans.add(TextSpan(text: text.substring(start), style: style));
      break;
    }
    if (index > start) {
      spans.add(TextSpan(text: text.substring(start, index), style: style));
    }
    spans.add(TextSpan(text: text.substring(index, index + query.length), style: highlightStyle));
    start = index + query.length;
  }
  return spans;
}
