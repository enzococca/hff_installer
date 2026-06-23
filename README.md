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

## License

GPL v2
