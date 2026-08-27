import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netclaw_mobile/ncfed/dashboard_data.dart';
import 'package:netclaw_mobile/screens/dashboard_screen.dart';

DashboardSnapshot _snapshot({int unreadFeed = 0, int unreadChat = 0, int pendingApprovals = 0}) =>
    DashboardSnapshot(
      connected: true,
      identity: const FederationIdentitySnapshot(
        enrolled: true,
        memberId: 'risk/1',
        clawDomain: 'example.claw',
      ),
      unreadPending: UnreadPendingSnapshot(
        unreadFeed: unreadFeed,
        unreadChat: unreadChat,
        pendingApprovals: pendingApprovals,
      ),
    );

void main() {
  Widget wrap(DashboardSnapshot snapshot,
      {VoidCallback? onOpenFeed, VoidCallback? onOpenChat, VoidCallback? onOpenApprovals}) {
    return MaterialApp(
      home: Scaffold(
        body: DashboardScreen(
          snapshot: snapshot,
          onOpenFeed: onOpenFeed ?? () {},
          onOpenChat: onOpenChat ?? () {},
          onOpenApprovals: onOpenApprovals ?? () {},
        ),
      ),
    );
  }

  group('Dashboard tap-through (109/US7/FR-017/FR-018)', () {
    testWidgets('tapping Unread with unread Feed messages opens Feed', (tester) async {
      var openedFeed = false;
      await tester.pumpWidget(wrap(
        _snapshot(unreadFeed: 2, unreadChat: 0),
        onOpenFeed: () => openedFeed = true,
      ));

      await tester.tap(find.text('Unread'));
      await tester.pumpAndSettle();

      expect(openedFeed, isTrue);
    });

    testWidgets('tapping Unread with only unread Chat turns opens Chat', (tester) async {
      var openedChat = false;
      await tester.pumpWidget(wrap(
        _snapshot(unreadFeed: 0, unreadChat: 3),
        onOpenChat: () => openedChat = true,
      ));

      await tester.tap(find.text('Unread'));
      await tester.pumpAndSettle();

      expect(openedChat, isTrue);
    });

    testWidgets('Feed takes priority when both Feed and Chat have unread items',
        (tester) async {
      var openedFeed = false;
      var openedChat = false;
      await tester.pumpWidget(wrap(
        _snapshot(unreadFeed: 1, unreadChat: 1),
        onOpenFeed: () => openedFeed = true,
        onOpenChat: () => openedChat = true,
      ));

      await tester.tap(find.text('Unread'));
      await tester.pumpAndSettle();

      expect(openedFeed, isTrue);
      expect(openedChat, isFalse);
    });

    testWidgets('tapping Unread with zero unread anywhere does nothing', (tester) async {
      var openedFeed = false;
      var openedChat = false;
      await tester.pumpWidget(wrap(
        _snapshot(unreadFeed: 0, unreadChat: 0),
        onOpenFeed: () => openedFeed = true,
        onOpenChat: () => openedChat = true,
      ));

      await tester.tap(find.text('Unread'));
      await tester.pumpAndSettle();

      expect(openedFeed, isFalse);
      expect(openedChat, isFalse);
    });

    testWidgets('tapping Pending approvals always opens Approvals, even at zero',
        (tester) async {
      var openedApprovals = false;
      await tester.pumpWidget(wrap(
        _snapshot(pendingApprovals: 0),
        onOpenApprovals: () => openedApprovals = true,
      ));

      await tester.tap(find.text('Pending approvals'));
      await tester.pumpAndSettle();

      expect(openedApprovals, isTrue);
    });
  });
}
