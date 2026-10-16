# Changelog

This project uses milestone tags for major Plex Curator releases.

## Unreleased

- Analyze Mystery Clip now uses Apple's local Vision text recognition on extracted frames to suggest network/title/type values while still requiring explicit review before rename.
- Media Organizer bulk scans now parallelize metadata inspection, defer expensive frame extraction, use longer scan/apply request timeouts, and provide per-file deep analysis for mystery clips. This makes large recursive folders practical.
- Mystery clips in the macOS Media Organizer can now be given a reviewed title/type and explicitly approved; reviewed items apply safely without enabling bulk low-confidence renames.
- Media review now finds ffmpeg/ffprobe in common Homebrew paths even when the macOS app or launchd does not inherit the shell PATH, and Doctor reports availability.
- macOS Media Organizer now shows cached early/middle/late thumbnails for low-confidence mystery clips.
- Low-confidence Media Organizer clips now get cached early/middle/late review frames so mystery videos can be identified visually before renaming.
- Added a native macOS Media Organizer with folder selection, scan preview, confidence/type review, and confirmed safe apply controls.
- Added a local interstitial media organizer that scans video folders, cleans names from embedded metadata or filenames, classifies clips, previews changes, and safely moves/renames approved-confidence files.
- macOS Station Editor now supports interstitial pool types and relative weights, including live approximate mix percentages.
- Interstitial sources can now be typed and weighted, allowing station IDs, bumpers, commercials, promos, and general clips to appear in configurable proportions.
- macOS Station Editor can now select Plex video playlists as interstitial pools and configure break frequency and clips per break.
- Stations can now insert clips from one or more Plex video playlists as interstitial pools for bumpers, station IDs, and commercials.
- Plex watch synchronization now resumes partially watched episodes using `viewOffset` instead of treating only completed episodes as progress.
- Scoped episode cursors by channel/station so independent playlists no longer move each other's show position.
- Cursor advancement now reflects only episodes that remain in the final playlist after interleaving, seasonal inserts, and truncation.

## v13.2.3 — 2026-10-15

- Re-published the API runtime hotfix from the correct release-prep commit so backend and macOS embedded versions match the release tag.
- Includes the macOS API virtualenv handoff fix and expanded Doctor dependency checks.

## v13.2.2 — 2026-10-15

- Fixed macOS API wrapper virtualenv detection so `plex-curator-api` reliably re-execs into the application `.venv`.
- Added Doctor checks for `requests`, FastAPI, Uvicorn, and the API wrapper.
- Improved detection of incomplete API runtime environments before launchd startup.

## v13.2.1 — 2026-10-15

- Fixed macOS Bash 3.2 installer failure caused by empty-array expansion under `set -u`.
- Reworked optional sudo handling to avoid the same Bash 3.2 failure path.
- Added macOS system-Bash regression coverage for installer argument handling.
- Removed duplicate tagged-release workflow and made release publishing idempotent.

## v13.2.0 — 2026-10-14

### Schedules

- Native Schedules browser with programming-block timeline and total duration.
- Schedule cards show matching LaunchAgent automation state.
- Read-only lineup preview grouped by programming block.
- Authenticated Build Now / Replace action with cursor/history commit only after successful playlist creation.
- Build options mirror the CLI defaults for recent avoidance, show gap, seasonal mode, specials, unwatched preference, and Plex watch progress.
- Clock-time automation remains centralized in the Automation screen.

### Movie curator and wishlist

- Native Movie Curator filter/preview screen using the existing Python movie-filter engine.
- Authenticated create/replace Plex playlist action with rollback-safe replacement.
- Native Kids Scary Wishlist with All / Missing / Found filters.
- Wishlist matches display actual Plex titles and artwork when present.
- Packaged alias map prevents known renamed/remastered titles from becoming false misses.

### Playlist browser and artwork

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

### v13.1 search and notifications included

- Search stations by name, playlist, preset, description, and included/excluded shows.
- Filter station list by All / Enabled / Disabled.
- Search history by show, episode, station, or episode code.
- Friendlier formatted history timestamps.
- Native macOS notifications after successful station refresh and automation actions.

### v13.1 automation controls included

- Launchd manager JSON status output for GUI/API clients.
- Local API endpoints for automation job list/status and authenticated install, uninstall, and run-now actions.
- Native SwiftUI Automation screen with LaunchAgent state and controls.
- Self-protection prevents the API service from uninstalling its own LaunchAgent through the GUI.
- Automation API safety tests.

### v13.1 station editor included

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
