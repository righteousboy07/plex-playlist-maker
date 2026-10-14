# Architecture

Plex Curator intentionally separates programming logic from user interfaces.

```text
Plex Media Server
       ↑
backend/plex_curator.py
       ↑
backend/plex_curator_api.py
       ↑
macos/ SwiftUI client
```

## Core engine

The Python engine owns:

- Plex connection and library discovery
- movie curation
- station profiles
- episode sequencing
- watch-progress synchronization
- seasonal inserts
- schedule building
- history/state
- backups
- launchd automation

## Local API

The API provides a stable localhost contract for desktop clients. It should remain a thin adapter around the engine rather than reimplementing scheduling rules.

## macOS client

The SwiftUI app should remain a client of the API. It should not directly access PlexAPI, SQLite, or the Plex token.

## Persistent state

Runtime state lives under:

```text
~/.config/plex-curator/
```

Application source can therefore be upgraded independently of credentials and station history.
