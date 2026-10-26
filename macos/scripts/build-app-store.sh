#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"
export MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-13.0}"

VERSION="${PLEX_CURATOR_VERSION:-$(sed -n 's/^APP_VERSION = "\([^"]*\)"/\1/p' "$REPO_ROOT/backend/plex_curator.py" | head -1)}"
BUILD_VERSION="$(printf '%s' "$VERSION" | tr -cd '0-9')"
SIGN_IDENTITY="${APP_STORE_SIGN_IDENTITY:--}"

[[ -n "$VERSION" ]] || {
  echo "Could not determine Plex Curator version." >&2
  exit 1
}
[[ -n "$BUILD_VERSION" ]] || BUILD_VERSION=1

cd "$ROOT"

echo "Building Mac App Store flavor..."
swift build -c release -Xswiftc -DAPP_STORE
BIN_DIR="$(swift build -c release -Xswiftc -DAPP_STORE --show-bin-path)"
BIN="$BIN_DIR/PlexCuratorMac"

APP="$ROOT/dist/app-store/Plex Curator.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN" "$APP/Contents/MacOS/PlexCuratorMac"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>PlexCuratorMac</string>
<key>CFBundleIdentifier</key><string>com.ry.plexcurator.appstore</string>
<key>CFBundleName</key><string>Plex Curator</string>
<key>CFBundleDisplayName</key><string>Plex Curator</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>$VERSION</string>
<key>CFBundleVersion</key><string>$BUILD_VERSION</string>
<key>LSMinimumSystemVersion</key><string>13.0</string>
<key>LSApplicationCategoryType</key><string>public.app-category.utilities</string>
<key>NSHighResolutionCapable</key><true/>
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsLocalNetworking</key><true/>
</dict>
</dict></plist>
PLIST

/usr/bin/codesign \
  --force \
  --sign "$SIGN_IDENTITY" \
  --entitlements "$ROOT/PlexCuratorAppStore.entitlements" \
  "$APP"

echo "Verifying App Sandbox entitlements..."
/usr/bin/codesign --verify --deep --strict "$APP"
/usr/bin/codesign -d --entitlements :- "$APP" 2>&1 | grep -q "com.apple.security.app-sandbox"

echo "Built App Store flavor:"
echo "  $APP"
echo
echo "NOTE: This target is the sandbox/build-flavor foundation only."
echo "The bundled backend/helper migration must be completed before App Store submission."
