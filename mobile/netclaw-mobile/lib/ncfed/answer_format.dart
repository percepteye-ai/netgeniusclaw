/// 109/FR-006: Border answers are not guaranteed to be valid Markdown --
/// raw CLI output containing bare `#`, `*`, `_`, or `|` would be mangled by
/// a Markdown renderer applied unconditionally. This classifier is
/// deliberately conservative: render as Markdown only when the text
/// contains a genuine signal (a closed fenced code block, or a pipe-table
/// row), never on a guess.
final _fencedBlock = RegExp(r'```[\s\S]*?```');

/// A pipe-table row needs non-whitespace content on both sides of at least
/// one `|` -- a bare trailing `|` in CLI output (e.g. a truncated `show`
/// table) must not trip this.
final _pipeTableRow = RegExp(r'\S\s*\|\s*\S');

bool looksLikeMarkdown(String text) {
  if (_fencedBlock.hasMatch(text)) return true;
  return text.split('\n').any((line) => _pipeTableRow.hasMatch(line));
}
