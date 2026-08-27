# App Review Notes — Draft for "Please provide instructions to use your app"

Paste into App Store Connect → App Review Information → Notes.

```
NetGeniusClaw Mobile is a companion app for NetGeniusClaw Border — a network-automation assistant that an
operator installs and runs on their own infrastructure (there is no NetClaw-operated cloud
service). The app requires a Border to be enrolled before any of its screens beyond onboarding
become usable. This is by design, described on the app's own first screen.

How the app is used, end to end:

1. FIRST LAUNCH: the app shows an explanatory screen ("NetGeniusClaw Mobile is a companion app") and
   then a QR-code scanner. The operator points their phone's camera at a QR code their own Border
   displays during its own setup process. This QR code contains a one-time enrollment token,
   scoped to that specific Border and that specific phone.

2. AFTER ENROLLMENT: the app unlocks its main tabs:
   - Chat: type or speak a question; the Border's own AI agent answers, with access to whatever
     network tools/devices the operator has configured on their Border.
   - Approvals: the Border can ask the operator to approve a pending automated action before it
     executes; the operator reviews and approves/denies with Face ID/Touch ID.
   - Feed/History: a log of messages and past conversations pushed from the Border.
   - Settings: notification status, app-lock, and enrollment management (including removing the
     device's enrollment).

3. VOICE: the operator can also ask a question via Siri/Shortcuts ("Ask NetGeniusClaw...") without
   opening the app; the answer is spoken back or delivered as a notification.

4. APPLE WATCH: a paired Watch companion mirrors Border health status and lets the operator
   approve/deny pending approvals from their wrist, relayed through the phone.

WHY REVIEW ENVIRONMENT MAY SHOW ONLY THE ONBOARDING SCREEN: because there is no publicly hosted
NetGeniusClaw Border for App Review to enroll against (each operator runs their own, the same way a
home-automation or VPN app requires the user's own hardware/server), the reviewer's device may not
be able to progress past the QR-scan screen without a Border of their own. Screenshots in this
submission show the app's actual in-use screens (Chat, Approvals, Feed) captured from a real,
enrolled device against a live Border, to demonstrate the functionality described above.

If a live demo enrollment is required to complete review, please let us know via this message
thread and we can arrange temporary access to a demo Border.
```

## Notes on this draft

- The last paragraph offers a live demo as a fallback — only include it if you're actually willing
  and able to stand up a reachable demo Border on short notice if Apple takes you up on it. If not,
  cut that paragraph and lean harder on the screenshots + instructions being sufficient on their
  own (many self-hosted/enterprise apps are approved this way without a live demo).
- This complements, not replaces, the screenshot fix (2.3.3) — Apple's own message ties "app in
  use" screenshots directly to understanding functionality, so both fixes reinforce each other.
