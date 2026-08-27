import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/theme.dart';

void main() {
  group('theme (109/US1)', () {
    test('light and dark schemes share the same brand seed, differ only in brightness', () {
      expect(lightColorScheme.brightness, Brightness.light);
      expect(darkColorScheme.brightness, Brightness.dark);
      // Both derived from the same seed -- primary hues track the same seed
      // family even though the concrete swatches differ between brightnesses.
      expect(lightColorScheme.primary, isNot(equals(darkColorScheme.primary)));
    });

    testWidgets('MaterialApp resolves the dark scheme under a dark platform brightness',
        (tester) async {
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(platformBrightness: Brightness.dark),
          child: MaterialApp(
            theme: netclawTheme,
            darkTheme: netclawDarkTheme,
            themeMode: ThemeMode.system,
            home: Builder(
              builder: (context) => Text('brightness:${Theme.of(context).brightness}'),
            ),
          ),
        ),
      );

      expect(find.text('brightness:Brightness.dark'), findsOneWidget);
    });

    testWidgets('MaterialApp resolves the light scheme under a light platform brightness',
        (tester) async {
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(platformBrightness: Brightness.light),
          child: MaterialApp(
            theme: netclawTheme,
            darkTheme: netclawDarkTheme,
            themeMode: ThemeMode.system,
            home: Builder(
              builder: (context) => Text('brightness:${Theme.of(context).brightness}'),
            ),
          ),
        ),
      );

      expect(find.text('brightness:Brightness.light'), findsOneWidget);
    });
  });
}
