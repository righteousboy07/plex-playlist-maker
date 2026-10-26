# Mac App Store Edition

Plex Curator is maintained as **one product with two macOS distribution channels**.

## Distribution channels

### Direct Download

The direct edition remains the full-power build and ships as the signed/notarized `.pkg`.

It may use:

- `/Applications/PlexCurator/` for the self-contained backend
- `~/.config/plex-curator/` for persistent configuration/state
- `~/Library/Logs/PlexCurator/` for external logs
- LaunchAgents installed and managed by Plex Curator
- the Developer ID signing + notarization distribution path

The direct edition continues to support Intel and Apple Silicon.

### Mac App Store

The App Store edition shares the same SwiftUI screens, API models, station engine behavior, and Plex programming logic, but must use an App Store-safe runtime architecture.

The App Store flavor is compiled with:

```text
-DAPP_STORE
```

and uses:

```text
macos/PlexCuratorAppStore.entitlements
```

Current App Store bundle identifier scaffold:

```text
com.ry.plexcurator.appstore
```

Register/finalize that identifier in the Apple Developer portal before submission.

## Shared code policy

Do not fork the application into separate source trees.

Channel differences belong behind:

```swift
BuildFlavor.current
```

The direct build is the default. The App Store build is selected at compile time with `APP_STORE`.

Current capabilities:

| Capability | Direct | App Store |
| --- | --- | --- |
| Station programming | Yes | Shared |
| Schedules | Yes | Shared |
| Playlist browser | Yes | Shared |
| Movie Curator | Yes | Shared |
| History | Yes | Shared |
| Plex connection UI | Yes | Shared |
| External `.pkg` installer | Yes | No |
| External LaunchAgent management | Yes | No |
| External log-file browser | Yes | No |
| App Sandbox | No | Required |
| User-selected media folders | Direct path access | Security-scoped access required |
| Updates | Direct package/release | Mac App Store |

## App Sandbox entitlements

The current App Store scaffold requests:

- App Sandbox
- outgoing network client access
- local network server access
- user-selected read/write file access
- app-scoped security bookmarks

The server entitlement is retained because the current architecture uses a localhost API. Re-evaluate whether it remains necessary after the bundled-helper migration.

## Build the App Store flavor

For a local sandbox compile:

```bash
bash macos/scripts/build-app-store.sh
```

Output:

```text
macos/dist/app-store/Plex Curator.app
```

Without `APP_STORE_SIGN_IDENTITY`, the build uses ad-hoc signing so CI can validate the App Sandbox entitlements.

For a future App Store submission, provide the appropriate Apple distribution signing identity/provisioning profile through the Xcode/App Store submission workflow.

## Submission-readiness roadmap

The App Store flavor now validates the **UI/build/sandbox split plus a self-contained bundled backend runtime**. It is still intentionally not labeled submission-ready until Media Organizer folder authorization and Store-safe background automation are complete.

### Phase 1 — Complete

- shared Direct/App Store build flavor
- App Sandbox entitlement file
- App Store-specific bundle identifier
- direct-only UI feature gating
- sandbox build CI
- explicit dual-distribution documentation

### Phase 2 — Bundled backend/helper — Complete

The Store build now embeds a signed `PlexCuratorBackend.app` helper inside `Plex Curator.app`.

Implemented:

- no dependency on `/Applications/PlexCurator/`
- no external installer for the Store edition
- no runtime download of executable code
- PyInstaller directory runtime packaged as a proper nested helper app
- helper startup is smoke-tested during CI
- nested helper and outer app signatures/entitlements are verified in CI
- helper lifecycle is owned by the foreground Plex Curator app
- Store API uses localhost port `8766`, while Direct remains on `8765`

Persistent/background operation is intentionally not enabled yet. For macOS 13+, future background automation will use Apple's ServiceManagement APIs such as `SMAppService` rather than writing plist files into `~/Library/LaunchAgents`.

### Phase 3 — Sandbox storage — Core complete

The backend now accepts distribution-specific runtime paths. The Store app launches the bundled API with container-scoped Application Support and Logs directories, while Direct retains the existing `~/.config/plex-curator/` and `~/Library/Logs/PlexCurator/` locations.

Implemented:

- sandbox Application Support path for config, database, stations, schedules, presets, backups and API key
- sandbox Logs path
- bundled examples/resource path override
- Store-specific Doctor behavior with LaunchAgent checks disabled
- independent Direct and Store API ports

Still pending:

- optional one-time import from a Direct-edition installation into the Store sandbox
- security-scoped authorization for user media folders

### Phase 4 — Media Organizer folder authorization

The Store edition cannot crawl arbitrary folders by path alone.

Use:

1. `NSOpenPanel` to let the user select a media root;
2. security-scoped bookmarks for persistent permission;
3. `startAccessingSecurityScopedResource()` only while the folder is being used;
4. matching stop-access calls afterward.

Media Organizer presets should refer to authorized bookmark identities rather than unrestricted filesystem roots.

### Phase 5 — Store automation

Replace direct LaunchAgent management with an App Store-safe model.

Potential design:

- explicit **Enable Background Automation** user control
- bundled helper registered through ServiceManagement
- automation definitions stored in the sandbox
- no root escalation
- no external plist installation
- no helper continuing after the user disables the feature

The Direct edition keeps its current LaunchAgent manager.

### Phase 6 — App Store Connect submission

Before submission:

- finalize App ID and bundle identifier
- configure App Sandbox and signing capabilities in Xcode
- create the App Store Connect app record
- add privacy disclosures and support/privacy-policy URLs
- add screenshots and product metadata
- provide App Review instructions for connecting to a Plex server
- build/upload through Apple's supported Xcode/App Store pipeline
- test the receipt-signed Store build on a clean Mac account

## App Review notes

The review build should explain that Plex Curator is a local companion/control application for a user's own Plex Media Server.

If App Review cannot access a normal Plex server, prepare either:

- clear reviewer setup instructions and a reachable review Plex environment, or
- a review/demo mode that exercises the UI without modifying a real media library.

Do not submit the App Store flavor until the bundled-helper, sandbox-storage, and security-scoped-folder phases are complete.

## Release discipline

Every feature should answer two questions:

1. Is this logic shared between Direct and App Store?
2. If it touches installation, background execution, filesystem access, credentials, logs, or updates, does it require channel-specific behavior?

Prefer a capability switch in `BuildFlavor` over copied screens or copied business logic.
