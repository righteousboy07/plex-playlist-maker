# v13 Quick Start

Backend:

```bash
cd /Applications/PlexCurator
./plex-curator doctor
./plex-curator-api ping
```

If needed:

```bash
./launchd-manager.py install api-server
```

Run GUI:

```bash
./scripts/run-dev.sh
```

Build `.app`:

```bash
./scripts/build-app.sh
```

Install:

```bash
./scripts/install-app.sh
```

Open in Xcode:

```bash
open Package.swift
```
