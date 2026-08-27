import 'package:flutter/material.dart';

/// 105/US1/FR-001/FR-002: shown before `EnrollmentScreen`'s QR scanner on
/// every launch where nothing is enrolled yet (an "unenrolled-state" screen,
/// not a "seen once, never again" one — see spec.md's edge cases). Never
/// shown once a valid enrollment is persisted. Makes no camera, network, or
/// permission calls of its own — purely explanatory copy plus one action.
class OnboardingExplainerScreen extends StatelessWidget {
  final VoidCallback onContinue;

  const OnboardingExplainerScreen({super.key, required this.onContinue});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(Icons.hub_outlined, size: 64),
              const SizedBox(height: 24),
              const Text(
                'NetClaw Mobile is a companion app',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              const Text(
                'It connects to a self-hosted NetClaw Border server that you '
                '(or your operator) already run — it does not work as a '
                'standalone consumer app, and there is no NetClaw service to '
                'sign up for.\n\n'
                "If you don't already have a Border running, set one up "
                'first, then come back here to scan its enrollment QR code.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16),
              ),
              const SizedBox(height: 32),
              FilledButton(
                onPressed: onContinue,
                child: const Text('Continue'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
