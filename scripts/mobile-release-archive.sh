#!/usr/bin/env bash
# Mobile Release Archive Script (099/FR-008, Story 3)
#
# Produces an App Store Connect-ready .ipa from mobile/netclaw-mobile's
# Runner scheme, once a paid Apple Developer Program account is active.
#
# Usage: ./scripts/mobile-release-archive.sh
#
# Prerequisites:
#   - A paid Apple Developer Program membership, with the Runner target's
#     code signing moved to that team (see docs/MOBILE-RELEASE.md)
#   - mobile/netclaw-mobile/ExportOptions.plist's teamID filled in
#   - Xcode + command line tools installed

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOBILE_DIR="$REPO_ROOT/mobile/netclaw-mobile"
EXPORT_OPTIONS="$MOBILE_DIR/ExportOptions.plist"
ARCHIVE_PATH="$MOBILE_DIR/build/Runner.xcarchive"
EXPORT_PATH="$MOBILE_DIR/build/export"

cd "$MOBILE_DIR"

# This project's Apple ID upgraded from a free/Personal team to the paid
# Apple Developer Program under the SAME team ID (A49777FMJG) -- common for
# an individual account, where enrolling in the paid Program unlocks
# capabilities (push, distribution export) without reassigning a new Team
# ID. The free-vs-paid distinction this script cares about is therefore no
# longer detectable from the Team ID alone, so that check was removed
# (see docs/MOBILE-RELEASE.md). ExportOptions.plist's own teamID placeholder
# check below is the guard that still matters.

if grep -q "REPLACE_WITH_PAID_TEAM_ID" "$EXPORT_OPTIONS"; then
  echo -e "${RED}error:${NC} $EXPORT_OPTIONS still has the placeholder teamID."
  echo "Fill in your paid team ID (developer.apple.com/account -> Membership) and re-run."
  exit 1
fi

echo -e "${GREEN}==>${NC} Archiving Runner (team: A49777FMJG)..."
xcodebuild archive \
  -project ios/Runner.xcodeproj \
  -scheme Runner \
  -configuration Release \
  -archivePath "$ARCHIVE_PATH" \
  -destination "generic/platform=iOS" \
  -allowProvisioningUpdates

echo -e "${GREEN}==>${NC} Exporting for App Store Connect..."
# -allowProvisioningUpdates: automatic signing's App Store distribution
# profiles lag behind newly added capabilities (App Groups, Siri, Time
# Sensitive Notifications -- specs 111/114) and the widget extension target
# may have no Store profile registered at all yet. Without this flag,
# -exportArchive fails outright on stale/missing profiles instead of asking
# Xcode's connected Apple ID to regenerate them.
xcodebuild -exportArchive \
  -archivePath "$ARCHIVE_PATH" \
  -exportPath "$EXPORT_PATH" \
  -exportOptionsPlist "$EXPORT_OPTIONS" \
  -allowProvisioningUpdates

echo -e "${GREEN}==>${NC} Done. Exported .ipa: $EXPORT_PATH"
echo -e "${YELLOW}Next:${NC} upload via Transporter or 'xcrun altool --upload-app', then complete"
echo "App Store Connect's listing (screenshots, privacy-policy URL) per docs/MOBILE-RELEASE.md."
