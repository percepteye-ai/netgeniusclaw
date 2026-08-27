import 'package:flutter/material.dart';

/// Shared "nothing here yet" layout for Feed/Approvals — a small brand
/// illustration above the existing plain-text message, not a replacement
/// for it.
class EmptyState extends StatelessWidget {
  final String asset;
  final String text;

  const EmptyState({super.key, required this.asset, required this.text});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 109/FR-002 edge case: these illustrations are light-background
          // PNGs. A theme-aware backdrop keeps them legible under dark mode
          // without needing separate dark-variant image assets.
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Image.asset(asset, width: 140),
          ),
          const SizedBox(height: 16),
          Text(text, style: Theme.of(context).textTheme.bodyMedium),
        ],
      ),
    );
  }
}
