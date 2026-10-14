#!/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required."
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

chmod +x plex-curator launchd-manager.py plex-curator-api

echo
echo "Plex Curator backend installed."
echo "Permanent Plex config: ~/.config/plex-curator/.env"
echo "Persistent state:       ~/.config/plex-curator/state.sqlite3"
echo "Local API key:          ~/.config/plex-curator/api.key"
echo
echo "Run:"
echo "  ./plex-curator doctor"
