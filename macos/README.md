# Plex Curator v13 — macOS SwiftUI Client

v13 is the first native macOS control app for Plex Curator.

Architecture:

```text
Plex -> Python Curator Engine -> v12 localhost API -> v13 SwiftUI App
```

The app deliberately remains a thin client. It does not contain the Plex token or duplicate playlist logic.

## Requirements

- Plex Curator v12 installed at `/Applications/PlexCurator`
- v12 API running on `127.0.0.1:8765`
- macOS 12 or newer
- Apple's Swift toolchain / Xcode Command Line Tools

The macOS 12 target is intentional for compatibility with the 2013 Mac Pro.

## Verify the backend first

```bash
cd /Applications/PlexCurator
./plex-curator doctor
./plex-curator-api ping
```

If the API is not running:

```bash
./launchd-manager.py install api-server
./plex-curator-api ping
```

## Run the app from source

From this v13 folder:

```bash
./scripts/run-dev.sh
```

or:

```bash
swift run PlexCuratorMac
```

## Build a `.app`

```bash
./scripts/build-app.sh
```

Result:

```text
dist/Plex Curator.app
```

Open it:

```bash
open "dist/Plex Curator.app"
```

## Install for your user

```bash
./scripts/install-app.sh
```

Installs to:

```text
~/Applications/Plex Curator.app
```

No `sudo` required.

## Open in Xcode

```bash
open Package.swift
```

Select the `PlexCuratorMac` executable and Run.

## v13 Screens

### Dashboard
- Plex connection and server/library status
- station, automation, library, and Doctor health metrics
- attention cards for Plex/Doctor/automation problems and active Media Organizer scans
- recent station/schedule build history
- Dry Run All and confirmed Refresh Enabled Stations actions
- quick links to Stations, Automation, Health, and Media Organizer

### Stations
- list configured stations
- station rules
- Preview
- Diff
- Dry Run
- Refresh with confirmation

### History
- recent programmed episodes

### Health
- Doctor results

### Logs
- read `api-server` or other launchd logs

### Settings
- localhost API address
- API-key file path
- backend versions

## Security

The app calls only:

```text
http://127.0.0.1:8765
```

For modifying requests it reads:

```text
~/.config/plex-curator/api.key
```

The app never reads or stores your Plex token.

The first app is intentionally **not App-Sandboxed**. Sandboxing/signing/notarization should happen after this client/API boundary has been tested on the actual server Mac.

## Recommended validation

1. Confirm the v12 API is healthy.
2. Run `./scripts/run-dev.sh`.
3. Dashboard should show `Plex Connected`.
4. Open Health.
5. Open Stations -> Retro Kids.
6. Preview.
7. Diff.
8. Dry Run.
9. Refresh.
10. Check History.
11. Check Logs -> `api-server`.

## v13.1 additions

The current client now includes:

- station profile editing
- station enable/disable
- station and history search/filtering
- launchd Automation management
- native notifications after refresh/automation actions
- friendlier history date formatting

Station creation, duplication, editing, enable/disable, and deletion are now available in the native app. Station deletion creates a backend safety backup and preserves the Plex playlist and station history.

## v13.2 additions

- searchable Plex playlist browser with artwork
- Movie Curator filter/preview/create workflow
- Kids Scary Wishlist with present/missing status
- Schedules screen with block timeline, preview, Build Now, and Automation status
- localhost artwork proxy; Swift never receives the Plex token

## Next improvements

### v13.2 remaining
- Plex artwork/posters
- playlist browser
- movie-curation screen
- kids-scary wishlist
- schedules/calendar view

### v14
- full Xcode app project
- icon/assets
- signing
- notarization
- menu-bar helper
- installer/update strategy


## Distribution flavors

The SwiftUI client now builds in two flavors from the same target.

### Direct

Default development/release build:

```bash
./scripts/build-app.sh
```

This edition keeps the current localhost API + external backend/LaunchAgent architecture.

### Mac App Store scaffold

Sandboxed flavor:

```bash
./scripts/build-app-store.sh
```

This defines `APP_STORE`, applies `PlexCuratorAppStore.entitlements`, uses a separate bundle identifier, and hides direct-only LaunchAgent/log-file controls.

The App Store flavor is a **submission scaffold**, not yet a submission-ready product. The backend/helper still needs to be embedded and sandbox-aware. See `../docs/APP_STORE.md`.

Do not duplicate views or business logic to create Store-specific behavior. Add channel-specific capability switches through `BuildFlavor.current`.
