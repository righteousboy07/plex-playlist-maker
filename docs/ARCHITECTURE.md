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


## Distribution architecture

Plex Curator uses one shared application codebase with compile-time distribution capabilities.

### Direct Download

```text
Plex Curator.app
        ↓ localhost
/Applications/PlexCurator/plex-curator-api
        ↓
Python Curator engine
        ↓
Plex
```

The Direct edition may use external LaunchAgents, external logs, and `~/.config/plex-curator/` state.

### Mac App Store

```text
Sandboxed Plex Curator.app
        ↓
Bundled/signed helper runtime (planned Phase 2)
        ↓
Shared Curator engine
        ↓
Plex
```

The Store edition is compiled with `-DAPP_STORE` and capabilities are exposed through `BuildFlavor.current`.

It must not install executables in shared locations or manage external LaunchAgent plist files. App-owned state belongs inside the App Sandbox container, and user media directories require explicit user selection plus security-scoped access.

See [APP_STORE.md](APP_STORE.md).
