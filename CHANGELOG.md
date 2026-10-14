# Changelog

This project uses milestone tags for major Plex Curator releases.

## Unreleased

### v13.2 playlist browser and artwork

- Native searchable Plex playlist browser.
- Playlist detail grid with movie posters and episode thumbnails.
- Watched state, runtime, content rating, and summaries in playlist cards.
- Localhost artwork proxy with size-limited image transcoding.
- Plex credentials remain entirely in the backend.
- macOS app bundle explicitly allows local-network HTTP for the localhost API.

### Deployment and releases

- Safe GitHub-to-Mac backend installer with timestamped live-code backup.
- Persistent config/state remains outside the deployed source tree.
- Post-deploy Doctor verification and automatic API LaunchAgent reload.
- Native macOS app install/update script with rollback copy.
- Dry-run deployment mode.
- One-command clean-clone updater.
- Tagged release workflow for backend archives and compiled macOS app artifacts.
- Fixed API wrapper to re-exec inside the project virtualenv.
- Fixed kids-scary wishlist LaunchAgent path for the monorepo layout.

### v13.1 search and notifications

- Search stations by name, playlist, preset, description, and included/excluded shows.
- Filter station list by All / Enabled / Disabled.
- Search history by show, episode, station, or episode code.
- Friendlier formatted history timestamps.
- Native macOS notifications after successful station refresh and automation actions.

### v13.1 automation controls

- Launchd manager JSON status output for GUI/API clients.
- Local API endpoints for automation job list/status and authenticated install, uninstall, and run-now actions.
- Native SwiftUI Automation screen with LaunchAgent state and controls.
- Self-protection prevents the API service from uninstalling its own LaunchAgent through the GUI.
- Automation API safety tests.

### v13.1 station editor

- Authenticated `PUT /api/v1/stations/{id}` station update endpoint.
- Native SwiftUI station editor for identity, programming, audience, progress, and show overrides.
- Station enable/disable control from the macOS client.
- Explicit clearing of optional year limits.
- Backend tests for normalized station profile writes and invalid year ranges.

### Repository foundation

- Monorepo structure for backend + macOS client.
- CI smoke tests for Python backend and SwiftUI build.
- Consolidated project documentation and security guidance.

## v13.0.0 — Initial macOS client

- Native SwiftUI client targeting macOS 12+.
- Dashboard, Stations, Preview, Diff, Dry Run, Refresh, History, Health, Logs and Settings.
- Client talks only to the localhost API.

## v12.0.0 — Local REST API

- FastAPI localhost service on `127.0.0.1:8765`.
- Separate API key for mutating operations.
- Read endpoints for status, stations, previews, diffs, playlists, history, backups and logs.
- launchd `api-server` job.

## v11.0.0 — Reliability and safety

- `station-diff`.
- Real dry-run behavior.
- Backups and safer playlist replacement.
- Log viewer and `doctor --json`.
- Preview/diff state-mutation bug fixed.

## v10.0.0 — Station profiles

- Persistent station profiles in `stations.json`.
- Create, update, clone, enable, disable and refresh stations.
- Station-specific history namespaces.

## v9.0.0 — Watch-aware programming

- Plex watch-progress-aware sequencing.
- Seasonal inserts and show-spacing rules.
- Consolidated playlist/channel/schedule features.
