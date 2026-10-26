#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"
VERSION="${PLEX_CURATOR_VERSION:-$(sed -n 's/^APP_VERSION = "\([^"]*\)"/\1/p' "$REPO_ROOT/backend/plex_curator.py" | head -1)}"
BUILD_VERSION="$(printf '%s' "$VERSION" | tr -cd '0-9')"
[[ -n "$VERSION" ]] || { echo "Could not determine Plex Curator version." >&2; exit 1; }
[[ -n "$BUILD_VERSION" ]] || BUILD_VERSION=1
cd "$ROOT"
swift build -c release
BIN_DIR="$(swift build -c release --show-bin-path)"
BIN="$BIN_DIR/PlexCuratorMac"
APP="$ROOT/dist/Plex Curator.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN" "$APP/Contents/MacOS/PlexCuratorMac"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>PlexCuratorMac</string>
<key>CFBundleIdentifier</key><string>com.ry.plexcurator.mac</string>
<key>CFBundleName</key><string>Plex Curator</string>
<key>CFBundleDisplayName</key><string>Plex Curator</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>$VERSION</string>
<key>CFBundleVersion</key><string>$BUILD_VERSION</string>
<key>LSMinimumSystemVersion</key><string>12.0</string>
<key>NSHighResolutionCapable</key><true/>
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsLocalNetworking</key><true/>
</dict>
</dict></plist>
PLIST
echo "Built: $APP"
echo "Open with: open \"$APP\""
