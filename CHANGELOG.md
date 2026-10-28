# Changelog

This project uses milestone tags for major Plex Curator releases.

## 13.2.17

- Introduced the approved dark navy, amber, and light-content visual system across the macOS interface.
- Refined Dashboard, Health, Stations, Schedules, Playlists, Settings, and Automation layouts.
- Added a generated multi-resolution film-reel app icon to Direct Download and App Store builds.

## 13.2.16

- Fixed false Health failures for FastAPI and Uvicorn in packaged Direct Download installs.
- Health now verifies the actual running packaged API on localhost instead of trying to import API-only libraries from the separate CLI executable.
- FastAPI/Uvicorn are reported as healthy when the packaged API responds successfully.
- Added focused regression tests for packaged API runtime health detection.

## 13.2.15

- Fixed the packaged plex-curator-api executable incorrectly re-executing through a colocated Python virtual environment.
- Frozen PyInstaller builds now stay inside the packaged executable and no longer try to open a temporary _MEI.../plex-curator-api.py path.
- Installer builds now launch the frozen API, wait for it to answer on a temporary localhost port, and fail if the packaged runtime cannot actually start.
- This strengthens release validation beyond the previous --help-only smoke test.

## 13.2.14

- Reworked Direct Download first-run Step 2 so Plex setup no longer depends on the local Plex Curator API or port 8765.
- The macOS app now validates the Plex server/token directly and writes the shared ~/.config/plex-curator/.env configuration itself.
- Added explicit macOS local-network usage metadata for the Direct Download app.
- Step 2 now always shows the installed app version and separately reports whether a backend was detected.
- This removes API startup, stale backend, and internal API-key state from the initial Plex connection path.

## 13.2.13

- Fixed upgrades that could leave an orphaned or manually started older plex-curator-api process listening on port 8765.
- Installer now stops only stale Plex Curator API processes before reconciling the current background service.
- Step 2 now displays the connected Plex Curator backend version so stale-backend situations are visible.
- First-run setup reports a specific error when the GUI is connected to an older backend that does not support the current bootstrap endpoint.

## 13.2.12

- Fixed first-run Step 2 so saving/testing Plex credentials no longer depends on the app's internal Plex Curator API key.
- Added a dedicated localhost-only bootstrap endpoint for initial Plex server/token setup.
- Kept authenticated mutation protection for normal post-setup settings changes.
- Added regression coverage for the first-run bootstrap route.
- Preserved the URL/token normalization and token-help improvements introduced in 13.2.10.

## 13.2.11

- Added automatic cleanup of stale Plex Curator LaunchAgent/background-item registrations left by older installs.
- Installer upgrades now reconcile Plex Curator background services before and after replacing the backend.
- Existing current automation jobs are preserved and refreshed in place.
- Required API server and log-cleanup services are reinstalled using the current labels instead of accumulating duplicates.
- Added regression tests for background-item cleanup and reconciliation.

## 13.2.10

- Fixed first-run Plex connection handling for common server-address formats, including bare IP/hostname input, missing port 32400, and Plex /web URLs.
- Plex token entry now accepts a raw token, an X-Plex-Token= value, or a full Plex URL containing the token.
- Added clearer connection diagnostics for invalid tokens, timeouts, refused connections, and bad hostnames.
- Added built-in first-run instructions showing how to retrieve an X-Plex-Token, with a link to Plex's official support article.
- Added regression tests for Plex URL and token normalization.

## 13.2.9

- Added a Copy Command button to the Dashboard when the local API is unavailable.
- Split the direct macOS installer into selectable Plex Curator App and API Backend & Automation components.
- Both installer components are selected by default; users can use Customize to update only the app or only the backend.
- Kept backend setup, API service registration, automation tooling, and 30-day log cleanup with the backend installer component.
- Updated installer validation and documentation for component-level upgrades.

## 13.2.8

- Added a Universal Installer DMG containing clearly labeled Intel and Apple Silicon installers with no Terminal required.
- Release workflow now requires both architecture-specific installer packages before publishing.
- Added automatic version tagging and explicit release workflow dispatch so GitHub Releases track APP_VERSION changes.
- Added App Store security-scoped Media Organizer folder authorization with persisted bookmarks.
- Added App Store-safe ServiceManagement launch-at-login controls and scheduled automation execution.
- Added Store automation job dashboard with schedules, last-run status, and Run Now validation.
- Preserved the Direct Download edition's existing LaunchAgent automation path.

## Unreleased

- App Store Phase 2/3: embedded a signed sandbox-inheriting backend helper inside the Store app, added container-aware backend/config/log paths, separated Direct (8765) and Store (8766) localhost APIs for side-by-side installs, disabled external LaunchAgent behavior in Store mode, and added CI startup/signing verification for the bundled runtime.
- Added a shared Direct/App Store distribution architecture: compile-time build flavors, App Sandbox entitlements, direct-only UI capability gating, a sandboxed App Store build/CI target, and an explicit App Store migration roadmap without forking the product codebase.
- Added a native first-run onboarding wizard that walks fresh installs through Plex connection and verification, while existing configured users bypass it automatically.
- Upgraded the macOS package to a branded distribution installer with Welcome, installation-details, and completion screens, plus a startup wait so slower Macs do not open the app before the local API is ready.
- Added self-contained one-click macOS installer packaging for Intel and Apple Silicon, including standalone backend/API/LaunchAgent executables, automatic API/log-retention setup, and in-app first-time Plex URL/token configuration.
- Added default 30-day launchd log retention: a daily maintenance job tracks a retention cycle and safely truncates Plex Curator stdout/stderr logs every 30 days, including continuously written API logs.
- Improved History and Logs workflows in the macOS app with station/job pickers, configurable history/log limits, search, history metrics, direct Automation-to-Logs navigation, log severity highlighting, copy controls, and Finder reveal for loaded log files.
- Improved diagnostics and recovery UX: Health now has summary metrics, issue/pass filtering, search, rerun controls, and links to Automation/Logs; Settings now shows live API/Plex state, API-key file status, safe copy/reveal utilities, and recovery shortcuts.
- Upgraded the macOS Playlist browser with managed/interstitial/smart/empty filters, sorting, usage badges, update dates, and playlist diagnostics for runtime, watched state, media mix, year range, and duplicate entries.
- Made Dashboard attention cards actionable with direct navigation to Health, Automation, Media Organizer, or Settings, and added a New Station quick action.
- Rebuilt the macOS Dashboard into an operational control center with health/attention cards, automation and library metrics, recent programming history, quick navigation, Dry Run All, and confirmed refresh-all controls.
- Added native station creation, duplication, and deletion to the macOS app, backed by authenticated local API endpoints and safety-backup deletion that preserves Plex playlists and station history.
- Added runtime-aware broadcast blocks with 30/60/90/custom-minute targets, multi-block station builds, nearest-item boundary fitting, and block runtime summaries in macOS previews.
- Added cyclic station break patterns so stations can alternate short and long breaks with different program-item intervals and ordered clip sequences.
- Added ordered station break sequences so interstitials can follow a deliberate pattern such as Station ID → Commercial → Commercial → Bumper, while preserving weighted-mix behavior for existing stations.
- macOS Media Organizer now uses background scan jobs with live discovery/analyze/finalize progress, elapsed time, current-file detail, and Cancel Scan controls instead of one long-running HTTP request.
- Added cancellable Media Organizer scan jobs with discovery/analyze/finalize progress, elapsed time, result polling, and bounded completed-job retention. The legacy synchronous scan endpoint remains available.
- macOS Media Organizer can now load, create, update, duplicate, and delete persistent exclusion presets. The destructive Delete Excluded Files option remains runtime-only and is never saved in a preset.
- Added persistent named Media Organizer exclusion presets, including a safe default Movie Cleanup preset. Presets store only exclusion rules; destructive delete settings are never persisted.
- Fixed Media Organizer Apply so the exact exclusion rules used during preview are preserved when rebuilding the apply plan.
- Media Organizer now supports case-insensitive exclude globs (including a Sample preset), excludes matches before metadata analysis, previews excluded files separately, and can explicitly delete matched exclusions on confirmed apply.
- Media Organizer now has a large-library review queue with Needs Review, Ready to Apply, Already Organized, and All filters plus filename/title/folder search.
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
