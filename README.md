# Plex Curator

Plex Curator is a local Plex playlist and channel-programming toolkit. It combines a Python backend, a localhost-only REST API, and a native SwiftUI macOS client.

## Architecture

```text
Plex Media Server
       ↑
Plex Curator Python Engine
       ↑
Local REST API (127.0.0.1:8765)
       ↑
SwiftUI macOS Client
```

## Repository layout

```text
backend/   Python engine, API, launchd tools, tests, examples
macos/     SwiftUI macOS client
/docs      Architecture, API, automation, security and development docs
.github/   CI workflows
```

## Current milestones

- Backend v12: localhost REST API and launchd API service
- macOS v13: initial native SwiftUI client
- Next: v13.1 station editing and automation controls

## Backend quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./plex-curator setup
./plex-curator doctor
```

Persistent configuration is stored outside the repository:

```text
~/.config/plex-curator/
```

The Plex token, API key, state database, backups, logs and exports must never be committed.

## API

```bash
cd backend
./plex-curator-api serve
```

Then visit locally:

```text
http://127.0.0.1:8765/docs
```

## macOS client

Verify the backend is running, then:

```bash
cd macos
./scripts/run-dev.sh
```

Build a standalone app:

```bash
./scripts/build-app.sh
```

## Development

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the full workflow.

## Security

The API binds only to `127.0.0.1`; modifying API operations require a separate local API key. The Swift client never reads the Plex token. See [SECURITY.md](SECURITY.md).

## License

No open-source license has been selected yet. Until one is added, all rights remain with the repository owner.
