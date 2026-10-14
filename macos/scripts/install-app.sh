#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/build-app.sh"
mkdir -p "$HOME/Applications"
rm -rf "$HOME/Applications/Plex Curator.app"
cp -R "$ROOT/dist/Plex Curator.app" "$HOME/Applications/Plex Curator.app"
open "$HOME/Applications/Plex Curator.app"
