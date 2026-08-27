import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// 109/FR-002: no screen may render a fixed gray/black/white color literal
/// that ignores the active theme. Exception (FR-002's own carve-out):
/// enrollment_screen.dart and device_scan_screen.dart draw a semi-transparent
/// scrim over a live camera viewfinder, contrasting against unpredictable
/// camera footage rather than the app's own background -- intentionally
/// theme-independent, and excluded here.
const _excludedFiles = {'enrollment_screen.dart', 'device_scan_screen.dart'};

final _forbidden = RegExp(r'Colors\.(grey|black|white)\b');

void main() {
  test('lib/screens/ contains no hardcoded Colors.grey/black/white literals', () {
    final dir = Directory('lib/screens');
    final offenders = <String>[];

    for (final entity in dir.listSync(recursive: true)) {
      if (entity is! File || !entity.path.endsWith('.dart')) continue;
      final fileName = entity.uri.pathSegments.last;
      if (_excludedFiles.contains(fileName)) continue;

      final lines = entity.readAsLinesSync();
      for (var i = 0; i < lines.length; i++) {
        if (_forbidden.hasMatch(lines[i])) {
          offenders.add('${entity.path}:${i + 1}: ${lines[i].trim()}');
        }
      }
    }

    expect(offenders, isEmpty,
        reason: 'Found hardcoded color literal(s) that ignore the active '
            'theme:\n${offenders.join('\n')}');
  });
}
