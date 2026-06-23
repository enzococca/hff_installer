# HFF Installer

A QGIS plugin to easily install and update the **HFF (Honor Frost Foundation)** plugin directly from GitHub.

Only the **stable master branch** is exposed — development branches are intentionally not selectable.

## Features

- Download and install HFF from GitHub (`enzococca/HFF`, branch `master`)
- Automatic detection of existing installations (`HFF`, `HFF-master`, `HFF-main`, …)
- Clean removal of any prior version before installing
- Forces the installed folder name to **`HFF`** so relative imports work
  (a zipball-extracted `HFF-master/` would break v11.8+ imports)
- Compatible with QGIS 3.x (Qt5) and QGIS 4.x (Qt6)

## Installation

1. Copy the `hff_installer` folder into your QGIS plugins directory:
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows**: `C:\Users\<you>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
2. Restart QGIS.
3. Enable the plugin in **Plugins → Manage and Install Plugins → Installed**.

## Usage

1. Open QGIS.
2. Go to **Plugins → HFF Installer → Install/Update HFF** (or click the toolbar icon).
3. Click **Install / Update**.
4. Wait for the download/extract/copy steps to finish.
5. Restart QGIS to load the newly installed/updated HFF plugin.

## Notes

- The plugin always installs from `https://github.com/enzococca/HFF/archive/refs/heads/master.zip`.
- An existing installation is removed before the new one is copied in.
- The installed folder is renamed to `HFF` regardless of the zipball's top-level folder name.
- An internet connection is required.

## Changelog

### 1.1.0 (2026-06-23)

- Show whether an update is available. The dialog now fetches `metadata.txt` from `enzococca/HFF` master on `raw.githubusercontent.com`, parses the `version=` field, and compares it against the installed version.
- Status line under the installed version shows one of: `Up to date (latest on master: X.Y.Z)`, `Update available: X.Y.Z (installed: A.B.C)`, `Latest available on master: X.Y.Z` (when HFF is not yet installed), or `Could not check for updates (…)` if the request fails.
- Network check is non-blocking — the dialog opens immediately and updates the status line when the response arrives.

### 1.0.0 (2026-06-23)

- Initial release.
- Download the HFF plugin from `enzococca/HFF` (branch `master` only — development branches are intentionally hidden).
- Detect existing installations under any of the common folder names (`HFF`, `HFF-master`, `HFF-main`, `hff`, …) and remove them before installing.
- Always install into a folder named exactly `HFF`, so the relative imports introduced in HFF v11.8 keep working (a GitHub zipball would otherwise produce `HFF-master/` and break them).
- Read installed version from `metadata.txt` and show it in the dialog before and after install.
- Qt5/Qt6 enum compatibility — runs on both QGIS 3.x (Qt5) and QGIS 4.x (Qt6).
- Indeterminate progress bar and inline log of each step (download → extract → remove existing → copy → cleanup).
- Confirmation prompt before overwriting an existing installation.

## License

GPL v2
