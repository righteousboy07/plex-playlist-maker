# Local API

Default endpoint:

```text
http://127.0.0.1:8765
```

Interactive docs while running:

```text
http://127.0.0.1:8765/docs
```

## Read endpoints

```text
GET  /api/v1/ping
GET  /api/v1/status
GET  /api/v1/doctor
GET  /api/v1/security
GET  /api/v1/stations
GET  /api/v1/stations/{id}
POST /api/v1/stations/{id}/preview
GET  /api/v1/stations/{id}/diff
GET  /api/v1/playlists
GET  /api/v1/playlists/{name}
GET  /api/v1/history
GET  /api/v1/build-history
GET  /api/v1/backups
GET  /api/v1/logs/{job}
```

## Mutating endpoints

These require:

```text
X-Plex-Curator-Key
```

```text
POST /api/v1/stations/{id}/refresh
POST /api/v1/stations/refresh-all
POST /api/v1/backups
```
