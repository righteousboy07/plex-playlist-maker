# Deployment and Releases

## Normal user installation

Plex Curator now ships as a self-contained macOS installer. Users should download the architecture-specific `.pkg` from the GitHub Release:

- Intel: `Plex-Curator-<version>-macOS-intel.pkg`
- Apple Silicon: `Plex-Curator-<version>-macOS-apple-silicon.pkg`

The installer places:

```text
/Applications/Plex Curator.app
/Applications/PlexCurator/plex-curator
/Applications/PlexCurator/plex-curator-api
/Applications/PlexCurator/plex-curator-launchd
/Applications/PlexCurator/examples/
```

No Python runtime or virtual environment is required on the destination Mac.

The post-install script:

1. finds the currently logged-in macOS user;
2. preserves/initializes `~/.config/plex-curator/`;
3. initializes 30-day log retention;
4. installs and starts the `api-server` LaunchAgent;
5. installs the `log-cleanup` LaunchAgent;
6. opens Plex Curator.

First-time Plex URL/token setup is completed in **Plex Curator → Settings → Plex Connection**.

## Persistent state

Installer payloads do not replace the user's configuration directory:

```text
~/.config/plex-curator/
```

Important files include:

```text
.env
api.key
stations.json
schedules.json
state.sqlite3
media-organizer-presets.json
backups/
deployment-backups/
exports/
```

## Building the installer

On macOS:

```bash
bash scripts/build-installer.sh
```

The build creates a temporary Python build environment, installs PyInstaller, builds standalone backend/API/LaunchAgent binaries, builds the SwiftUI release app, assembles the package payload, and emits one architecture-specific `.pkg`.

Output:

```text
dist/installer/Plex-Curator-<version>-macOS-<architecture>.pkg
```

## Signing and notarization

Unsigned development packages can be built without credentials.

For distribution:

```bash
APP_SIGN_IDENTITY="Developer ID Application: ..." \
PKG_SIGN_IDENTITY="Developer ID Installer: ..." \
bash scripts/build-installer.sh
```

If `APPLE_NOTARY_PROFILE` is set to a configured `notarytool` keychain profile, the package is submitted for notarization and stapled.

## GitHub Releases

Tagged releases (`v*`) build:

- backend source archive;
- compiled macOS app ZIP;
- Intel installer package;
- Apple Silicon installer package;
- SHA-256 checksums.

## Legacy source deployment

The old source-deployment path remains useful for development:

```bash
bash scripts/install-all.sh --dry-run
bash scripts/install-all.sh
bash scripts/update-from-git.sh
```

The live source backend target remains `/Applications/PlexCurator`, and runtime configuration remains under `~/.config/plex-curator/`.

## Rollback

Persistent config/state backups remain under:

```text
~/.config/plex-curator/backups/
```

The package pre-install script also asks an existing Plex Curator installation to create a safety backup when possible before files are replaced.
