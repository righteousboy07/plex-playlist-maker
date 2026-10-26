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

for command in python3 swift pkgbuild codesign; do
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
PKGROOT="$WORK/pkgroot"
PKGSCRIPTS="$WORK/pkg-scripts"
OUTDIR="$ROOT/dist/installer"
PKG="$OUTDIR/Plex-Curator-$VERSION-macOS-$ARCH_LABEL.pkg"

rm -rf "$WORK"
mkdir -p "$WORK" "$BACKEND_DIST" "$PKGROOT/Applications/PlexCurator" "$PKGSCRIPTS" "$OUTDIR"

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

echo "Assembling package payload..."
/usr/bin/ditto "$ROOT/macos/dist/Plex Curator.app" "$PKGROOT/Applications/Plex Curator.app"
/bin/cp "$BACKEND_DIST/plex-curator" "$PKGROOT/Applications/PlexCurator/plex-curator"
/bin/cp "$BACKEND_DIST/plex-curator-api" "$PKGROOT/Applications/PlexCurator/plex-curator-api"
/bin/cp "$BACKEND_DIST/plex-curator-launchd" "$PKGROOT/Applications/PlexCurator/plex-curator-launchd"
/usr/bin/ditto "$ROOT/backend/examples" "$PKGROOT/Applications/PlexCurator/examples"
/bin/chmod 755 "$PKGROOT/Applications/PlexCurator/plex-curator" \
  "$PKGROOT/Applications/PlexCurator/plex-curator-api" \
  "$PKGROOT/Applications/PlexCurator/plex-curator-launchd"

if [[ -n "${APP_SIGN_IDENTITY:-}" ]]; then
  echo "Signing backend executables and app..."
  /usr/bin/codesign --force --options runtime --timestamp --sign "$APP_SIGN_IDENTITY" \
    "$PKGROOT/Applications/PlexCurator/plex-curator"
  /usr/bin/codesign --force --options runtime --timestamp --sign "$APP_SIGN_IDENTITY" \
    "$PKGROOT/Applications/PlexCurator/plex-curator-api"
  /usr/bin/codesign --force --options runtime --timestamp --sign "$APP_SIGN_IDENTITY" \
    "$PKGROOT/Applications/PlexCurator/plex-curator-launchd"
  /usr/bin/codesign --force --deep --options runtime --timestamp --sign "$APP_SIGN_IDENTITY" \
    "$PKGROOT/Applications/Plex Curator.app"
fi

/bin/cp "$ROOT/scripts/package/preinstall" "$PKGSCRIPTS/preinstall"
/bin/cp "$ROOT/scripts/package/postinstall" "$PKGSCRIPTS/postinstall"
/bin/chmod 755 "$PKGSCRIPTS/preinstall" "$PKGSCRIPTS/postinstall"

echo "Building installer package..."
PKGBUILD_ARGS=(
  --root "$PKGROOT"
  --scripts "$PKGSCRIPTS"
  --identifier "com.ry.plexcurator"
  --version "$VERSION"
  --install-location /
)

if [[ -n "${PKG_SIGN_IDENTITY:-}" ]]; then
  PKGBUILD_ARGS+=(--sign "$PKG_SIGN_IDENTITY")
fi

/usr/bin/pkgbuild "${PKGBUILD_ARGS[@]}" "$PKG"

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
