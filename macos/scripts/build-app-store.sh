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

for command in python3 swift codesign file; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "Missing required build tool: $command" >&2
    exit 1
  }
done

WORK="$ROOT/.build/app-store-backend"
PYENV="$WORK/pyenv"
BACKEND_DIST="$WORK/backend-dist"
PYI_WORK="$WORK/pyinstaller"
SMOKE_CONFIG="$WORK/smoke-config"
SMOKE_LOGS="$WORK/smoke-logs"

APP="$ROOT/dist/app-store/Plex Curator.app"
HELPERS="$APP/Contents/Helpers"
API_RUNTIME="$HELPERS/plex-curator-api"
API_BIN="$API_RUNTIME/plex-curator-api"

rm -rf "$WORK" "$APP"
mkdir -p "$WORK" "$BACKEND_DIST" "$SMOKE_CONFIG" "$SMOKE_LOGS"

echo "Building Mac App Store Swift flavor..."
cd "$ROOT"
swift build -c release -Xswiftc -DAPP_STORE
BIN_DIR="$(swift build -c release -Xswiftc -DAPP_STORE --show-bin-path)"
BIN="$BIN_DIR/PlexCuratorMac"

echo "Building sandbox-contained Python API runtime..."
python3 -m venv "$PYENV"
"$PYENV/bin/python" -m pip install --upgrade pip
"$PYENV/bin/python" -m pip install -r "$REPO_ROOT/backend/requirements-build.txt"

"$PYENV/bin/pyinstaller" \
  --noconfirm \
  --clean \
  --onedir \
  --name plex-curator-api \
  --paths "$REPO_ROOT/backend" \
  --hidden-import plex_curator \
  --hidden-import plex_curator_api \
  --collect-all plexapi \
  --collect-all uvicorn \
  --collect-all fastapi \
  --collect-all pydantic \
  --distpath "$BACKEND_DIST" \
  --workpath "$PYI_WORK/work" \
  --specpath "$PYI_WORK/spec" \
  "$REPO_ROOT/backend/plex-curator-api"

SMOKE_API="$BACKEND_DIST/plex-curator-api/plex-curator-api"
[[ -x "$SMOKE_API" ]] || {
  echo "Frozen API helper was not created." >&2
  exit 1
}

echo "Smoke-testing bundled API with sandbox-style storage..."
PLEX_CURATOR_DISTRIBUTION="app-store" \
PLEX_CURATOR_CONFIG_DIR="$SMOKE_CONFIG" \
PLEX_CURATOR_LOG_DIR="$SMOKE_LOGS" \
PLEX_CURATOR_EXAMPLES_DIR="$REPO_ROOT/backend/examples" \
"$SMOKE_API" serve --port 18765 --no-access-log \
  >"$WORK/smoke-api.out.log" 2>"$WORK/smoke-api.err.log" &
SMOKE_PID=$!

cleanup_smoke() {
  if /bin/kill -0 "$SMOKE_PID" >/dev/null 2>&1; then
    /bin/kill "$SMOKE_PID" >/dev/null 2>&1 || true
    /usr/bin/wait "$SMOKE_PID" 2>/dev/null || true
  fi
}
trap cleanup_smoke EXIT

SMOKE_READY=0
for _attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if PLEX_CURATOR_DISTRIBUTION="app-store" \
     PLEX_CURATOR_CONFIG_DIR="$SMOKE_CONFIG" \
     "$SMOKE_API" ping --port 18765 >/dev/null 2>&1; then
    SMOKE_READY=1
    break
  fi
  /bin/sleep 0.25
done

if [[ "$SMOKE_READY" -ne 1 ]]; then
  echo "Bundled API failed its startup smoke test." >&2
  cat "$WORK/smoke-api.out.log" >&2 || true
  cat "$WORK/smoke-api.err.log" >&2 || true
  exit 1
fi

test -f "$SMOKE_CONFIG/api.key"
cleanup_smoke
trap - EXIT

echo "Assembling App Store app bundle..."
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources" "$HELPERS"
cp "$BIN" "$APP/Contents/MacOS/PlexCuratorMac"
/usr/bin/ditto "$BACKEND_DIST/plex-curator-api" "$API_RUNTIME"
/usr/bin/ditto "$REPO_ROOT/backend/examples" "$API_RUNTIME/examples"

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
<key>NSLocalNetworkUsageDescription</key>
<string>Plex Curator connects to your Plex Media Server on your local network.</string>
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsLocalNetworking</key><true/>
</dict>
</dict></plist>
PLIST

echo "Signing nested Python runtime..."
while IFS= read -r -d '' candidate; do
  if [[ "$candidate" == "$API_BIN" ]]; then
    continue
  fi
  if /usr/bin/file "$candidate" | /usr/bin/grep -q "Mach-O"; then
    /usr/bin/codesign \
      --force \
      --sign "$SIGN_IDENTITY" \
      "$candidate"
  fi
done < <(/usr/bin/find "$API_RUNTIME" -type f -print0)

/usr/bin/codesign \
  --force \
  --identifier "com.ry.plexcurator.appstore.helper.api" \
  --sign "$SIGN_IDENTITY" \
  --entitlements "$ROOT/PlexCuratorHelper.entitlements" \
  "$API_BIN"

echo "Signing sandboxed app..."
/usr/bin/codesign \
  --force \
  --sign "$SIGN_IDENTITY" \
  --entitlements "$ROOT/PlexCuratorAppStore.entitlements" \
  "$APP"

echo "Verifying App Store bundle..."
/usr/bin/codesign --verify --deep --strict "$APP"
/usr/bin/codesign --verify --strict "$API_BIN"
/usr/bin/codesign -d --entitlements :- "$APP" 2>&1 \
  | /usr/bin/grep -q "com.apple.security.app-sandbox"
/usr/bin/codesign -d --entitlements :- "$API_BIN" 2>&1 \
  | /usr/bin/grep -q "com.apple.security.inherit"

echo "Built App Store flavor with bundled backend:"
echo "  $APP"
echo "  helper: $API_BIN"
echo
echo "Remaining App Store work: security-scoped Media Organizer folders and"
echo "optional user-enabled background automation through ServiceManagement."
