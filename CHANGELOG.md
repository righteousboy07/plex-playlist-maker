# Changelog

This project uses milestone tags for major Plex Curator releases.

## Unreleased

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
