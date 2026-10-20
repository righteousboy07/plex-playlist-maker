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


## Ordered break sequences

Stations can optionally use an ordered break pattern instead of drawing every clip from the full weighted mix.

An ordered sequence contains interstitial **types**, in playback order. For example:

```text
station-id
commercial
commercial
bumper
```

With a break frequency of one program item, the resulting rhythm is:

```text
Episode → Station ID → Commercial → Commercial → Bumper → Episode
```

Repeat a type when you want more than one clip of that kind. If no unused clip is available for a requested type, Curator skips that step and continues the sequence. Existing recent-history and same-build repeat protection still apply.

Weights remain useful in ordered mode when multiple playlists share the same type: Curator uses the configured weights to choose which matching pool supplies that step.

CLI example:

```bash
./plex-curator station-update retro-kids \
  --interstitial-step station-id \
  --interstitial-step commercial \
  --interstitial-step commercial \
  --interstitial-step bumper \
  --interstitial-every 1
```

Return to the legacy weighted-mix behavior:

```bash
./plex-curator station-update retro-kids --clear-interstitial-sequence
```

The API field is `interstitial_sequence`:

```json
{
  "interstitial_sequence": ["station-id", "commercial", "commercial", "bumper"],
  "interstitial_every": 1
}
```

When `interstitial_sequence` is non-empty it takes precedence over `interstitial_count`. When it is empty, the existing weighted behavior is unchanged.


## Cyclic break patterns

For a more television-like rhythm, a station can vary both the **distance between breaks** and the **contents of each break**.

Each cyclic rule has:

- `after`: number of program items to play before the break.
- `sequence`: ordered interstitial types to insert at that break.

The rules repeat forever while the station lineup is being built.

Example:

```json
{
  "interstitial_break_pattern": [
    {
      "after": 1,
      "sequence": ["station-id", "bumper"]
    },
    {
      "after": 2,
      "sequence": ["station-id", "commercial", "commercial", "bumper"]
    }
  ]
}
```

That produces a rhythm like:

```text
Episode
→ Station ID → Bumper
→ Episode → Episode
→ Station ID → Commercial → Commercial → Bumper
→ repeat
```

Cyclic break patterns take precedence over `interstitial_sequence`, `interstitial_every`, and `interstitial_count`. Existing stations without a cyclic pattern continue to use their current ordered or weighted behavior.

CLI example:

```bash
./plex-curator station-update retro-kids \
  --interstitial-break "1|station-id,bumper" \
  --interstitial-break "2|station-id,commercial,commercial,bumper"
```

Clear the cycle and fall back to the station's other break settings:

```bash
./plex-curator station-update retro-kids --clear-interstitial-break-pattern
```

The macOS station editor includes a **Cyclic pattern** mode and a **Classic Alternating** preset matching the example above.


## Runtime-aware broadcast blocks

Stations can optionally target real broadcast-style time blocks instead of ending after a fixed number of playlist items.

Set:

- `runtime_block_minutes`: target length of each block. `0` disables runtime mode.
- `runtime_block_count`: number of blocks to build.

Curator first assembles the station normally, including ordered or cyclic interstitial breaks. It then counts the Plex runtime of **every program and interstitial clip** and chooses the nearest complete-item boundary to each target. Clips are never cut in half.

For example, a 30-minute block might land at 29.3 minutes if adding the next 4-minute clip would push it to 33.3 minutes. The next item begins the next block.

```json
{
  "runtime_block_minutes": 30,
  "runtime_block_count": 8
}
```

CLI:

```bash
./plex-curator station-update retro-kids \
  --runtime-block-minutes 30 \
  --runtime-block-count 8
```

Disable runtime-aware blocks:

```bash
./plex-curator station-update retro-kids --runtime-block-minutes 0
```

The macOS station editor provides 30-, 60-, and 90-minute shortcuts plus a custom 5-minute-step target. Station previews show each block's actual runtime, item range, and difference from the target.

The existing `total` station length remains a candidate floor while runtime mode is enabled. Curator automatically raises the candidate count when necessary so there is enough material to form the requested blocks.
