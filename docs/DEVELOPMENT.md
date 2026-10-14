# Development

## Branching

Use short-lived feature branches and PRs into `main`.

Examples:

```text
feat/station-editor
fix/api-doctor-json
chore/ci-hardening
```

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Syntax check:

```bash
python -m compileall -q plex_curator.py plex_curator_api.py launchd-manager.py
```

CLI parser smoke check:

```bash
python plex_curator.py --help
```

## macOS setup

```bash
cd macos
swift build
```

Run:

```bash
./scripts/run-dev.sh
```

## Release discipline

1. `doctor` healthy on the Plex server.
2. Backend CI passes.
3. macOS build CI passes.
4. Dry-run affected stations.
5. Update `CHANGELOG.md`.
6. Tag semantic release (`v13.1.0`, etc.).

## Design rule

Keep Plex/scheduling logic in the backend. The API and GUI are clients of the same engine.
