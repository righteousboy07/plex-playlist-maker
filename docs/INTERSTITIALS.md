# Station Interstitials

Plex Curator can insert short video clips between normal station programs. This is intended for station IDs, bumpers, vintage commercials, promos, and similar material.

## Source pools

Create one or more **video playlists in Plex** containing the clips you want Curator to use. A station references those playlist names rather than requiring a dedicated Plex library.

Example pools:

- `Retro Kids Bumpers`
- `80s Commercials`
- `Station IDs`

Curator combines the configured playlists into one pool, removes duplicate items, skips recently used clips based on the station's existing `avoid_recent` history, randomizes the remaining pool, and avoids repeating a clip within the same build.

## Station configuration

Three station fields control the feature:

- `interstitial_playlists`: Plex video playlist names used as source pools.
- `interstitial_every`: insert a break after this many program items. `0` disables interstitials.
- `interstitial_count`: clips inserted at each break.

Interstitials count toward the station's existing `total`, matching the behavior of seasonal inserts. Episode cursors only advance for episodes that remain in the final lineup after insertion and truncation.

## CLI example

```bash
./plex-curator station-update retro-kids \
  --interstitial-playlist "Retro Kids Bumpers" \
  --interstitial-playlist "Vintage Commercials" \
  --interstitial-every 3 \
  --interstitial-count 1
```

Preview without changing Plex:

```bash
./plex-curator station-preview retro-kids --total 30
```

Disable and clear the source pools:

```bash
./plex-curator station-update retro-kids \
  --clear-interstitials \
  --interstitial-every 0
```

## API fields

The station update API accepts the same settings:

```json
{
  "interstitial_playlists": ["Retro Kids Bumpers", "Vintage Commercials"],
  "interstitial_every": 3,
  "interstitial_count": 1
}
```


## Typed and weighted pools

For more realistic programming, each interstitial source can have a type and weight. Supported types are:

- `station-id`
- `bumper`
- `commercial`
- `promo`
- `general`

Weights are relative rather than percentages, so `20 / 35 / 45` behaves like 20%, 35%, and 45% when those are the only active pools.

CLI example:

```bash
./plex-curator station-update retro-kids \
  --interstitial-pool "Station IDs|station-id|20" \
  --interstitial-pool "Retro Kids Bumpers|bumper|35" \
  --interstitial-pool "Vintage Commercials|commercial|45" \
  --interstitial-every 3 \
  --interstitial-count 1
```

Existing `interstitial_playlists` configurations remain supported and are treated as `general` pools with weight `1`.


## Media Organizer exclusions

Large media trees often contain disposable sample videos. The Media Organizer can skip these before metadata probing using case-insensitive glob patterns.

Examples:

```text
Sample.avi
sample.*
*/sample/*
```

In the macOS app, **Add Sample Preset** adds the common `sample.*` and `*/sample/*` rules. Excluded files are shown separately in the scan preview and are not analyzed or proposed for organization.

Deletion is separate from exclusion. Enabling **Delete excluded files** permanently deletes only files that matched the explicit exclude patterns, and only after the normal Apply confirmation.

CLI example:

```bash
./plex-curator media-organize "/path/to/Movies" \
  --exclude "sample.*" \
  --exclude "*/sample/*"
```

To apply normal organization and permanently remove the matched sample files:

```bash
./plex-curator media-organize "/path/to/Movies" \
  --exclude "sample.*" \
  --exclude "*/sample/*" \
  --apply \
  --delete-excluded
```
