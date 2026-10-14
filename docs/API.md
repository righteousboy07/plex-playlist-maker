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
GET  /api/v1/playlist?name=...
GET  /api/v1/playlists/{name}
GET  /api/v1/artwork/{rating_key}
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
PUT  /api/v1/stations/{id}
POST /api/v1/stations/{id}/refresh
POST /api/v1/stations/refresh-all
POST /api/v1/backups
```


## Update station profile

```text
PUT /api/v1/stations/{id}
```

This authenticated endpoint accepts partial station updates and persists a normalized profile back to `stations.json`. It is used by the v13.1 macOS station editor.

Example body:

```json
{
  "name": "Retro Kids",
  "enabled": true,
  "total": 72,
  "seasonal": "auto",
  "year_min": 1980,
  "year_max": 1999,
  "include_shows": ["DuckTales", "Darkwing Duck"]
}
```

Send `null` for `year_min` or `year_max` to clear that limit.


## Playlist browser and artwork

Playlist metadata:

```text
GET /api/v1/playlists
```

Playlist detail uses a query parameter so titles containing punctuation or slashes are safe:

```text
GET /api/v1/playlist?name=Retro%20Kids%20Channel
```

Artwork is proxied through the localhost API:

```text
GET /api/v1/artwork/{rating_key}?width=240&height=360
```

The backend resolves the media item in Plex, requests/transcodes the thumbnail server-side, and returns the image bytes. The Plex token is never sent to the Swift client.


## Movie curator

Read-only filter preview:

```text
POST /api/v1/movies/preview
```

Example:

```json
{
  "library": "Movies",
  "genre": "Animation",
  "year_min": 1980,
  "year_max": 1999,
  "max_runtime": 120,
  "content_ratings": ["G", "PG"],
  "min_audience": 7.0,
  "unwatched": true,
  "random": false,
  "limit": 50
}
```

Authenticated playlist creation/replacement:

```text
POST /api/v1/movies/playlist
```

The body uses the same filters plus:

```json
{
  "playlist": "Family Movie Night",
  "replace": true
}
```

Replacement uses the backend's rollback-safe playlist replacement path.

## Kids Scary Wishlist

```text
GET /api/v1/wishlist/kids-scary
```

Returns requested title/year, whether the title is currently in Plex, the actual matched Plex title, and media metadata/artwork information when found.

Known renamed titles can be resolved through:

```text
backend/examples/title-aliases.json
```


## Schedules

List schedule definitions:

```text
GET /api/v1/schedules
```

Get one schedule:

```text
GET /api/v1/schedules/{id}
```

Read-only lineup preview:

```text
POST /api/v1/schedules/{id}/preview
```

Authenticated build:

```text
POST /api/v1/schedules/{id}/build
```

Preview/build options mirror the CLI schedule defaults:

```json
{
  "playlist": "Saturday Morning TV",
  "avoid_recent": 150,
  "min_show_gap": 2,
  "seasonal": "auto",
  "special_every": 8,
  "unwatched": false,
  "ignore_watch_progress": false
}
```

Build requests also accept:

```json
{
  "replace": true
}
```

Preview does not commit episode cursors/history. A successful build writes the playlist first, then applies pending episode cursors and build/history records.

Clock-time scheduling remains owned by launchd/Automation rather than the schedule-definition API.
