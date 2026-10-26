#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${PLEX_CURATOR_VERSION:-$(sed -n 's/^APP_VERSION = "\([^"]*\)"/\1/p' "$ROOT/backend/plex_curator.py" | head -1)}"
INPUT_DIR="${1:-$ROOT/dist/installer}"
OUTDIR="${2:-$ROOT/dist/universal-installer}"
WORK="$ROOT/.build/universal-installer"
VOLUME="$WORK/Plex Curator Installer"
DMG="$OUTDIR/Plex-Curator-$VERSION-macOS-Universal-Installer.dmg"

[[ "$(uname -s)" == "Darwin" ]] || {
  echo "Universal installer DMG must be built on macOS." >&2
  exit 1
}

command -v hdiutil >/dev/null 2>&1 || {
  echo "Missing required build tool: hdiutil" >&2
  exit 1
}

INTEL_PKG="$(find "$INPUT_DIR" -maxdepth 1 -type f -name "Plex-Curator-$VERSION-macOS-intel.pkg" -print -quit)"
APPLE_PKG="$(find "$INPUT_DIR" -maxdepth 1 -type f -name "Plex-Curator-$VERSION-macOS-apple-silicon.pkg" -print -quit)"

[[ -n "$INTEL_PKG" && -f "$INTEL_PKG" ]] || {
  echo "Missing Intel installer: Plex-Curator-$VERSION-macOS-intel.pkg" >&2
  exit 1
}

[[ -n "$APPLE_PKG" && -f "$APPLE_PKG" ]] || {
  echo "Missing Apple Silicon installer: Plex-Curator-$VERSION-macOS-apple-silicon.pkg" >&2
  exit 1
}

rm -rf "$WORK"
mkdir -p "$VOLUME" "$OUTDIR"

cp "$INTEL_PKG" "$VOLUME/Install Plex Curator - Intel Mac.pkg"
cp "$APPLE_PKG" "$VOLUME/Install Plex Curator - Apple Silicon Mac.pkg"

cat > "$VOLUME/READ ME - WHICH INSTALLER.txt" <<'EOF'
PLEX CURATOR — WHICH INSTALLER SHOULD I USE?

APPLE SILICON MAC
Use:
  Install Plex Curator - Apple Silicon Mac.pkg

This is for Macs with an Apple M-series chip:
M1, M2, M3, M4, M5, or newer.

INTEL MAC
Use:
  Install Plex Curator - Intel Mac.pkg

This is for Macs that show an Intel processor, including the 2013 Mac Pro.

NOT SURE?
Choose Apple menu > About This Mac.

If it says "Chip: Apple M..." use the Apple Silicon installer.
If it says "Processor: Intel..." use the Intel installer.

No Terminal commands are required. Double-click the correct .pkg and follow
the standard macOS Installer screens.
EOF

cat > "$VOLUME/START HERE.txt" <<'EOF'
1. Open "READ ME - WHICH INSTALLER.txt" if you are unsure which Mac you have.
2. Double-click the installer for your Mac.
3. Follow the standard macOS Installer prompts.

No Terminal is required.
EOF

rm -f "$DMG"
hdiutil create   -volname "Plex Curator Installer"   -srcfolder "$VOLUME"   -ov   -format UDZO   "$DMG"

echo
echo "Built universal installer DMG:"
echo "  $DMG"
