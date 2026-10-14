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
