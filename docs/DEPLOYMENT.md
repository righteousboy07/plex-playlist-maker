# Deployment and Releases

## Normal user installation

Plex Curator now ships as a self-contained macOS installer. The easiest user download is the **Universal Installer DMG**:

- `Plex-Curator-<version>-macOS-Universal-Installer.dmg`

The DMG contains both architecture-specific installers with plain-language names:

- `Install Plex Curator - Intel Mac.pkg`
- `Install Plex Curator - Apple Silicon Mac.pkg`

No Terminal commands are required. Users open the DMG and double-click the installer for their Mac.

The same packages are also published separately:

- **Intel Mac:** `Plex-Curator-<version>-macOS-intel.pkg`
- **Apple Silicon Mac:** `Plex-Curator-<version>-macOS-apple-silicon.pkg`

The release workflow verifies that both packages exist before publishing. If either architecture-specific installer is missing, the release job fails rather than publishing an incomplete user release.

The installer places:

```text
/Applications/Plex Curator.app
/Applications/PlexCurator/plex-curator
/Applications/PlexCurator/plex-curator-api
/Applications/PlexCurator/plex-curator-launchd
/Applications/PlexCurator/examples/
```

No Python runtime or virtual environment is required on the destination Mac.

The branded Installer package presents Welcome, installation-details, Customize, and completion screens. It contains two selectable components, both enabled by default:

- **Plex Curator App** — updates only the native macOS GUI.
- **API Backend & Automation** — updates only the backend/API, CLI engine, examples, and LaunchAgent tooling.

Users can install both, or use **Customize** to install only the component that needs updating.

The backend component's post-install script:

1. finds the currently logged-in macOS user;
2. preserves/initializes `~/.config/plex-curator/`;
3. initializes 30-day log retention;
4. installs and starts the `api-server` LaunchAgent;
5. installs the `log-cleanup` LaunchAgent;
6. waits briefly for the local API to answer;
7. opens Plex Curator.

The distribution requires macOS 12 or later and asks the user to close Plex Curator before replacing an existing app.

On a fresh install, Plex Curator opens a first-run wizard for the Plex URL/token and verifies the connection before handing off to Dashboard. Existing configured users bypass the wizard automatically. Connection settings remain editable under **Settings → Plex Connection**.

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

The build creates a temporary Python build environment, installs PyInstaller, builds and smoke-tests standalone backend/API/LaunchAgent binaries, builds the SwiftUI release app, creates separate App and API Backend component packages, and wraps both with `productbuild` into a branded customizable distribution package using the Installer resources under `scripts/package/resources/`.

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
- clearly labeled Apple Silicon standalone app ZIP for development/testing;
- **Intel installer package**;
- **Apple Silicon installer package**;
- **Universal Installer DMG containing both packages**;
- SHA-256 checksums.

The Universal Installer DMG is the recommended end-user download.

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
