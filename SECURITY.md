# Security Policy

## Local secrets

Never commit any of the following:

```text
~/.config/plex-curator/.env
~/.config/plex-curator/api.key
~/.config/plex-curator/state.sqlite3
~/.config/plex-curator/backups/
~/.config/plex-curator/exports/
~/Library/Logs/PlexCurator/
```

The `.gitignore` blocks common copies of these files, but Git history should still be reviewed before publishing.

## Network exposure

The REST API is designed to bind only to:

```text
127.0.0.1:8765
```

Do not change the bind address to `0.0.0.0` without adding proper network authentication, TLS, and threat-model review.

## Authentication

Mutating API endpoints require `X-Plex-Curator-Key`. The API key is separate from the Plex token and is stored with `0600` permissions.

The SwiftUI client reads only the local API key; it does not read the Plex token.

## Reporting

For now, report security issues privately to the repository owner rather than opening a public issue containing secrets or exploit details.
