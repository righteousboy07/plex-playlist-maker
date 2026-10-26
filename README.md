# Plex Curator

Plex Curator is a local Plex playlist, channel-programming, media-organization, and automation toolkit. It combines a self-contained backend, a localhost-only REST API, and a native SwiftUI macOS client.

## Recommended install: one macOS installer, no Terminal

End users no longer need to clone the repository, create a Python environment, or run setup commands.

Download the installer that matches the Mac from the GitHub Release:

- **Intel Mac** — use `Plex-Curator-<version>-macOS-intel.pkg`. This is the correct package for Intel Macs such as the 2013 Mac Pro.
- **Apple Silicon** — use `Plex-Curator-<version>-macOS-apple-silicon.pkg` for M-series Macs.

Double-click the `.pkg` and follow the macOS Installer screens.

The package installs:

```text
/Applications/Plex Curator.app
/Applications/PlexCurator/plex-curator
/Applications/PlexCurator/plex-curator-api
/Applications/PlexCurator/plex-curator-launchd
```

It also:

1. preserves all existing state under `~/.config/plex-curator/`;
2. creates the initial config if this is a first install;
3. starts the localhost API on `127.0.0.1:8765`;
4. installs the daily log-retention job;
5. keeps Plex Curator logs on a 30-day cleanup cycle by default;
6. opens the native Plex Curator app after installation.

The packaged backend is self-contained. **Python, pip, a virtual environment, Xcode, and Terminal are not required on the destination Mac.**

### First launch

Open **Plex Curator → Settings → Plex Connection**.

1. Enter the Plex server URL. For a Plex server on the same Mac, start with `http://127.0.0.1:32400`.
2. Paste the Plex token.
3. Choose **Save & Test Plex**.
4. Return to Dashboard when Plex shows connected.

The app stores the Plex token in:

```text
~/.config/plex-curator/.env
```

The token is never displayed back in the GUI.

> Development installers are unsigned unless Apple Developer signing credentials are supplied during the build. For frictionless distribution to other Macs, sign the app/package with Developer ID and notarize the final package.

## Architecture

```text
Plex Media Server
       ↑
Plex Curator Engine
       ↑
Local REST API (127.0.0.1:8765)
       ↑
SwiftUI macOS Client
```

Persistent configuration and state live outside the installed application:

```text
~/.config/plex-curator/
```

Logs live in:

```text
~/Library/Logs/PlexCurator/
```

## Current app capabilities

The native macOS app now includes:

- Dashboard/control center with health warnings and quick actions
- native station create, duplicate, edit, enable/disable, preview, refresh, and safe delete
- weighted, ordered, and cyclic interstitial break programming
- runtime-aware 30/60/90/custom-minute broadcast blocks
- playlist usage classification, sorting, filtering, and duplicate/runtime diagnostics
- movie curation and wishlist tools
- schedule programming
- Media Organizer scans with progress, cancellation, exclusions, presets, review frames, and safe apply workflows
- automation/LaunchAgent management
- searchable History with station filtering and copy/export support
- searchable Logs with job selection, stdout/stderr selection, severity highlighting, line limits, copy, and Finder reveal
- Health diagnostics and recovery tools
- in-app Plex connection configuration
- 30-day log cleanup by default

## Repository layout

```text
backend/                 Python engine, API, LaunchAgent manager, tests
macos/                   SwiftUI macOS client
scripts/                 deployment and installer build scripts
scripts/package/         macOS package pre/post-install scripts
docs/                    architecture, deployment, API, security and development docs
.github/workflows/       CI and release packaging
```

## Building a one-click installer

Developers can build a native installer on a Mac:

```bash
bash scripts/build-installer.sh
```

Output:

```text
dist/installer/Plex-Curator-<version>-macOS-<architecture>.pkg
```

The package is architecture-specific. Build on an Intel Mac for the Intel package and Apple Silicon for the Apple Silicon package.

Optional distribution signing:

```bash
APP_SIGN_IDENTITY="Developer ID Application: ..." \
PKG_SIGN_IDENTITY="Developer ID Installer: ..." \
bash scripts/build-installer.sh
```

If `APPLE_NOTARY_PROFILE` names a configured `notarytool` keychain profile, the build script also submits and staples the final package.

GitHub Actions builds both Intel and Apple Silicon installer artifacts. Tagged releases publish both packages automatically.

## Updating an installed copy

For normal users, install a newer `.pkg` over the existing copy. The installer preserves:

```text
~/.config/plex-curator/.env
~/.config/plex-curator/api.key
~/.config/plex-curator/stations.json
~/.config/plex-curator/schedules.json
~/.config/plex-curator/state.sqlite3
~/.config/plex-curator/backups/
~/.config/plex-curator/media-organizer-presets.json
```

The legacy Git-clone update scripts remain available for development.

## Current CLI command reference

The GUI covers the normal workflow. These commands remain useful for development, debugging, scripting, or recovery.

### Setup and diagnostics

```bash
plex-curator setup
plex-curator config
plex-curator test
plex-curator doctor
plex-curator doctor --json
plex-curator doctor --fix
plex-curator libraries
plex-curator state-info
```

### Backups

```bash
plex-curator backup --reason manual
plex-curator backup-list
```

### Logs and retention

Read logs:

```bash
plex-curator logs
plex-curator logs api-server
plex-curator logs api-server --errors
plex-curator logs api-server --lines 1000
plex-curator logs api-server --follow
```

30-day retention is installed automatically. Manual controls:

```bash
plex-curator logs-cleanup
plex-curator logs-cleanup --force
plex-curator logs-cleanup --retention-days 30
plex-curator logs-cleanup --json
```

### Stations

```bash
plex-curator station-list
plex-curator station-show retro-kids
plex-curator station-preview retro-kids
plex-curator station-diff retro-kids
plex-curator station-refresh retro-kids
plex-curator station-refresh retro-kids --dry-run
plex-curator station-refresh-all
plex-curator station-refresh-all --dry-run
```

Create, clone, update, and delete profiles:

```bash
plex-curator station-create my-station --name "My Station"
plex-curator station-clone retro-kids retro-kids-copy
plex-curator station-update my-station --name "Updated Station"
plex-curator station-delete my-station --yes
```

Ordered break example:

```bash
plex-curator station-update retro-kids \
  --interstitial-step station-id \
  --interstitial-step commercial \
  --interstitial-step commercial \
  --interstitial-step bumper \
  --interstitial-every 1
```

Cyclic break example:

```bash
plex-curator station-update retro-kids \
  --interstitial-break "1|station-id,bumper" \
  --interstitial-break "2|station-id,commercial,commercial,bumper"
```

Runtime-aware blocks:

```bash
plex-curator station-update retro-kids \
  --runtime-block-minutes 30 \
  --runtime-block-count 8
```

Return to the legacy weighted break mode:

```bash
plex-curator station-update retro-kids \
  --clear-interstitial-sequence \
  --clear-interstitial-break-pattern
```

### Schedules and history

```bash
plex-curator schedule-list
plex-curator schedule-show saturday-morning
plex-curator schedule-build saturday-morning --create --replace
plex-curator history --limit 100
plex-curator build-history --limit 20
```

### Playlists and curation

```bash
plex-curator playlists
plex-curator show-playlist "Retro Kids Channel"
plex-curator delete-playlist "Old Playlist" --dry-run
plex-curator delete-playlist "Old Playlist" --yes
plex-curator presets
plex-curator preset kids-scary
plex-curator curate --library Movies --unwatched --limit 25
```

### Media Organizer

Preview a scan:

```bash
plex-curator media-organize "/path/to/media"
```

Apply safe medium/high-confidence moves:

```bash
plex-curator media-organize "/path/to/media" --apply
```

Use exclusion rules:

```bash
plex-curator media-organize "/path/to/media" \
  --exclude "sample.*" \
  --exclude "*/sample/*"
```

Saved exclusion presets:

```bash
plex-curator media-preset-list
plex-curator media-preset-save "Movie Cleanup" \
  --exclude "sample.*" \
  --exclude "*/sample/*"
plex-curator media-preset-delete <preset-id>
```

### LaunchAgent automation manager

The packaged command is:

```bash
plex-curator-launchd list
plex-curator-launchd list-json
plex-curator-launchd status api-server
plex-curator-launchd install stations-nightly
plex-curator-launchd uninstall stations-nightly
plex-curator-launchd run-now stations-nightly
```

The native Automation screen performs these operations without Terminal.

## Local API

The installer starts the API automatically at:

```text
http://127.0.0.1:8765
```

Interactive API documentation is available locally at:

```text
http://127.0.0.1:8765/docs
```

All modifying operations require the local API key stored at:

```text
~/.config/plex-curator/api.key
```

The API binds only to localhost.

## Source/development setup

End users should use the `.pkg`. Developers can still run from source:

```bash
git clone https://github.com/righteousboy07/plex-playlist-maker.git
cd plex-playlist-maker
bash scripts/install-all.sh
```

Backend tests:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Run the Swift client in development:

```bash
cd macos
./scripts/run-dev.sh
```

Legacy deployment scripts:

```bash
bash scripts/install-all.sh --dry-run
bash scripts/install-all.sh
bash scripts/update-from-git.sh
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Security

- API binds only to `127.0.0.1`.
- Mutating requests require a separate local API key.
- Plex credentials remain in the user's private config directory.
- The Swift client never exposes the Plex token after it is saved.
- Installer updates preserve persistent state rather than replacing it.
- Station deletion creates a safety backup and preserves the Plex playlist/history.

See [SECURITY.md](SECURITY.md).

## License

No open-source license has been selected yet. Until one is added, all rights remain with the repository owner.
