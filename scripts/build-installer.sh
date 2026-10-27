#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-12.0}"
VERSION="${PLEX_CURATOR_VERSION:-$(sed -n 's/^APP_VERSION = "\([^"]*\)"/\1/p' "$ROOT/backend/plex_curator.py" | head -1)}"
ARCH="$(uname -m)"

case "$ARCH" in
  x86_64) ARCH_LABEL="intel" ;;
  arm64) ARCH_LABEL="apple-silicon" ;;
  *) echo "Unsupported macOS architecture: $ARCH" >&2; exit 1 ;;
esac

[[ "$(uname -s)" == "Darwin" ]] || {
  echo "Installer packages must be built on macOS." >&2
  exit 1
}

for command in python3 swift pkgbuild productbuild codesign; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "Missing required build tool: $command" >&2
    exit 1
  }
done

[[ -n "$VERSION" ]] || {
  echo "Could not determine Plex Curator version." >&2
  exit 1
}

WORK="$ROOT/.build/installer-$ARCH_LABEL"
PYENV="$WORK/pyenv"
BACKEND_DIST="$WORK/backend-dist"
APP_PKGROOT="$WORK/pkgroot-app"
BACKEND_PKGROOT="$WORK/pkgroot-backend"
BACKEND_PKGSCRIPTS="$WORK/pkg-scripts-backend"
COMPONENT_DIR="$WORK/component"
APP_COMPONENT_PKG="$COMPONENT_DIR/PlexCuratorApp.pkg"
BACKEND_COMPONENT_PKG="$COMPONENT_DIR/PlexCuratorBackend.pkg"
RESOURCES="$ROOT/scripts/package/resources"
DISTRIBUTION="$ROOT/scripts/package/Distribution.xml"
OUTDIR="$ROOT/dist/installer"
PKG="$OUTDIR/Plex-Curator-$VERSION-macOS-$ARCH_LABEL.pkg"

rm -rf "$WORK"
mkdir -p "$WORK" "$BACKEND_DIST" \
  "$APP_PKGROOT/Applications" \
  "$BACKEND_PKGROOT/Applications/PlexCurator" \
  "$BACKEND_PKGSCRIPTS" "$COMPONENT_DIR" "$OUTDIR"

[[ -f "$DISTRIBUTION" ]] || {
  echo "Missing installer distribution: $DISTRIBUTION" >&2
  exit 1
}
[[ -d "$RESOURCES" ]] || {
  echo "Missing installer resources: $RESOURCES" >&2
  exit 1
}

echo "Building SwiftUI app..."
PLEX_CURATOR_VERSION="$VERSION" bash "$ROOT/macos/scripts/build-app.sh"

echo "Building self-contained backend executables..."
python3 -m venv "$PYENV"
"$PYENV/bin/python" -m pip install --upgrade pip
"$PYENV/bin/python" -m pip install -r "$ROOT/backend/requirements-build.txt"

PYINSTALLER="$PYENV/bin/pyinstaller"

"$PYINSTALLER" --noconfirm --clean --onefile \
  --name plex-curator \
  --paths "$ROOT/backend" \
  --collect-all plexapi \
  --distpath "$BACKEND_DIST" \
  --workpath "$WORK/pyi/curator" \
  --specpath "$WORK/spec/curator" \
  "$ROOT/backend/plex_curator.py"

"$PYINSTALLER" --noconfirm --clean --onefile \
  --name plex-curator-api \
  --paths "$ROOT/backend" \
  --hidden-import plex_curator \
  --hidden-import plex_curator_api \
  --collect-all plexapi \
  --collect-all uvicorn \
  --collect-all fastapi \
  --collect-all pydantic \
  --distpath "$BACKEND_DIST" \
  --workpath "$WORK/pyi/api" \
  --specpath "$WORK/spec/api" \
  "$ROOT/backend/plex-curator-api"

"$PYINSTALLER" --noconfirm --clean --onefile \
  --name plex-curator-launchd \
  --distpath "$BACKEND_DIST" \
  --workpath "$WORK/pyi/launchd" \
  --specpath "$WORK/spec/launchd" \
  "$ROOT/backend/launchd-manager.py"

echo "Smoke-testing frozen backend executables..."
"$BACKEND_DIST/plex-curator" --help >/dev/null
"$BACKEND_DIST/plex-curator-api" --help >/dev/null
"$BACKEND_DIST/plex-curator-launchd" list >/dev/null

echo "Frozen binary architectures:"
/usr/bin/file "$BACKEND_DIST/plex-curator" "$BACKEND_DIST/plex-curator-api" "$BACKEND_DIST/plex-curator-launchd"
echo "Frozen binary build metadata:"
/usr/bin/vtool -show-build "$BACKEND_DIST/plex-curator" || true
/usr/bin/vtool -show-build "$BACKEND_DIST/plex-curator-api" || true
/usr/bin/vtool -show-build "$BACKEND_DIST/plex-curator-launchd" || true

echo "Assembling split package payloads..."
/usr/bin/ditto "$ROOT/macos/dist/Plex Curator.app" "$APP_PKGROOT/Applications/Plex Curator.app"

/bin/cp "$BACKEND_DIST/plex-curator" "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator"
/bin/cp "$BACKEND_DIST/plex-curator-api" "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator-api"
/bin/cp "$BACKEND_DIST/plex-curator-launchd" "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator-launchd"
/usr/bin/ditto "$ROOT/backend/examples" "$BACKEND_PKGROOT/Applications/PlexCurator/examples"
/bin/chmod 755 "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator" \
  "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator-api" \
  "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator-launchd"

if [[ -n "${APP_SIGN_IDENTITY:-}" ]]; then
  echo "Signing backend executables and app..."
  /usr/bin/codesign --force --options runtime --timestamp --sign "$APP_SIGN_IDENTITY" \
    "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator"
  /usr/bin/codesign --force --options runtime --timestamp --sign "$APP_SIGN_IDENTITY" \
    "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator-api"
  /usr/bin/codesign --force --options runtime --timestamp --sign "$APP_SIGN_IDENTITY" \
    "$BACKEND_PKGROOT/Applications/PlexCurator/plex-curator-launchd"
  /usr/bin/codesign --force --deep --options runtime --timestamp --sign "$APP_SIGN_IDENTITY" \
    "$APP_PKGROOT/Applications/Plex Curator.app"
fi

/bin/cp "$ROOT/scripts/package/preinstall" "$BACKEND_PKGSCRIPTS/preinstall"
/bin/cp "$ROOT/scripts/package/postinstall" "$BACKEND_PKGSCRIPTS/postinstall"
/bin/chmod 755 "$BACKEND_PKGSCRIPTS/preinstall" "$BACKEND_PKGSCRIPTS/postinstall"

echo "Building application component package..."
/usr/bin/pkgbuild \
  --root "$APP_PKGROOT" \
  --identifier "com.ry.plexcurator.app.component" \
  --version "$VERSION" \
  --install-location / \
  "$APP_COMPONENT_PKG"

echo "Building API backend component package..."
/usr/bin/pkgbuild \
  --root "$BACKEND_PKGROOT" \
  --scripts "$BACKEND_PKGSCRIPTS" \
  --identifier "com.ry.plexcurator.backend.component" \
  --version "$VERSION" \
  --install-location / \
  "$BACKEND_COMPONENT_PKG"

echo "Building branded distribution package..."
PRODUCTBUILD_ARGS=(
  --distribution "$DISTRIBUTION"
  --package-path "$COMPONENT_DIR"
  --resources "$RESOURCES"
)

if [[ -n "${PKG_SIGN_IDENTITY:-}" ]]; then
  PRODUCTBUILD_ARGS+=(--sign "$PKG_SIGN_IDENTITY")
fi

/usr/bin/productbuild "${PRODUCTBUILD_ARGS[@]}" "$PKG"

if [[ -n "${APPLE_NOTARY_PROFILE:-}" ]]; then
  echo "Submitting installer for notarization..."
  /usr/bin/xcrun notarytool submit "$PKG" \
    --keychain-profile "$APPLE_NOTARY_PROFILE" \
    --wait
  /usr/bin/xcrun stapler staple "$PKG"
fi

echo
echo "Built installer:"
echo "  $PKG"
