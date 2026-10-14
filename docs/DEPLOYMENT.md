# Deployment and Releases

GitHub is the source of truth for Plex Curator. The live backend remains installed at:

```text
/Applications/PlexCurator
```

Persistent runtime data remains outside the repository:

```text
~/.config/plex-curator/
```

The deployment scripts never replace that configuration directory.

## First deployment from a clone

```bash
git clone https://github.com/righteousboy07/plex-playlist-maker.git
cd plex-playlist-maker

./scripts/install-backend.sh
./scripts/install-macos-app.sh
```

Or install both:

```bash
./scripts/install-all.sh
```

Preview the deployment without changing anything:

```bash
./scripts/install-all.sh --dry-run
```

## Backend safety behavior

Before updating `/Applications/PlexCurator`, the installer:

1. creates a timestamped copy of the current live application;
2. asks the existing Curator installation to create its own config/state backup when available;
3. preserves the existing backend `.venv/`;
4. copies the repository `backend/` tree into the live location;
5. installs/updates Python dependencies;
6. runs `./plex-curator doctor` when the permanent `.env` exists;
7. reloads the `api-server` LaunchAgent when it was already installed;
8. pings the localhost API after reload.

Deployment backups are stored at:

```text
~/.config/plex-curator/deployment-backups/
```

The following are not overwritten by deployment:

```text
~/.config/plex-curator/.env
~/.config/plex-curator/api.key
~/.config/plex-curator/stations.json
~/.config/plex-curator/schedules.json
~/.config/plex-curator/state.sqlite3
~/.config/plex-curator/backups/
```

## Updating an existing Git clone

From a clean working tree:

```bash
./scripts/update-from-git.sh
```

That performs:

```text
git pull --ff-only
backend deployment
macOS app build/install
```

To update without automatically opening the GUI:

```bash
./scripts/update-from-git.sh --no-open
```

## Backend only

```bash
./scripts/install-backend.sh
```

Custom target for testing:

```bash
./scripts/install-backend.sh --target "$HOME/Applications/PlexCurator-Test"
```

Do not point launchd production jobs at the test target.

## macOS app only

```bash
./scripts/install-macos-app.sh
```

Default destination:

```text
~/Applications/Plex Curator.app
```

## Rollback

Every backend deployment snapshots the previous live application.

To roll back code manually:

1. stop or reload the `api-server` LaunchAgent;
2. move the current `/Applications/PlexCurator` aside;
3. restore the desired timestamped `PlexCurator` directory from `deployment-backups`;
4. run `./install.sh`;
5. run `./plex-curator doctor`;
6. reinstall/reload `api-server`.

Persistent state/config backups created by the Curator backup command remain under:

```text
~/.config/plex-curator/backups/
```

## Tagged releases

Tags matching `v*` run the Release Artifacts workflow.

The workflow builds:

- a backend source archive;
- a compiled macOS `.app` ZIP;
- a GitHub Release with generated release notes.

Before tagging a release, make sure backend tests and macOS build CI are green.
