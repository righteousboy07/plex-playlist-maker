# Automation

Plex Curator uses macOS launchd for scheduled refreshes and for the local API process.

From `backend/`:

```bash
./launchd-manager.py list
./launchd-manager.py install JOB
./launchd-manager.py status JOB
./launchd-manager.py run-now JOB
./launchd-manager.py uninstall JOB
```

The API service job is:

```text
api-server
```

It uses `RunAtLoad` and `KeepAlive` and listens only on loopback.

LaunchAgent logs are stored under:

```text
~/Library/Logs/PlexCurator/
```

or read with:

```bash
./plex-curator logs JOB
./plex-curator logs JOB --errors
```


## Local API

The v13.1 macOS client reads LaunchAgent state through:

```text
GET /api/v1/automation
```

Mutating actions require the local API key:

```text
POST /api/v1/automation/{job}/install
POST /api/v1/automation/{job}/uninstall
POST /api/v1/automation/{job}/run-now
```

The `api-server` job is protected from self-uninstall through the API. Removing it must be done deliberately from Terminal.

## macOS Automation screen

The native client shows:

- loaded/not-loaded state
- plist presence
- launchd state
- last exit code when available
- run count when available
- Install
- Remove
- Run Now

The API server itself is marked Protected in the UI.
