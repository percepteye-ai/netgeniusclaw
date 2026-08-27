import 'package:flutter/material.dart';

/// The claw mark's own orange (assets/icon/icon.png) — matches the brand,
/// not an arbitrary Material default. Single source of truth for both
/// schemes below (109/FR-001) so light and dark never drift independently.
const Color brandSeedColor = Color(0xFFE65733);

final ColorScheme lightColorScheme = ColorScheme.fromSeed(seedColor: brandSeedColor);

final ColorScheme darkColorScheme = ColorScheme.fromSeed(
  seedColor: brandSeedColor,
  brightness: Brightness.dark,
);

final ThemeData netclawTheme = ThemeData(colorScheme: lightColorScheme);

final ThemeData netclawDarkTheme = ThemeData(colorScheme: darkColorScheme);
