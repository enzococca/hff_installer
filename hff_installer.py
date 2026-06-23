# -*- coding: utf-8 -*-
"""
HFF Installer - Main Plugin Class
"""

import os
import shutil
import tempfile
import zipfile
import configparser

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from qgis.core import QgsApplication

from .installer_dialog import InstallerDialog

# Qt5/Qt6 enum compatibility
NETWORK_NO_ERROR = getattr(QNetworkReply, 'NoError', None) or QNetworkReply.NetworkError.NoError


class HFFInstaller:
    """QGIS Plugin Implementation."""

    # GitHub repository info
    REPO_OWNER = "enzococca"
    REPO_NAME = "HFF"
    MASTER_BRANCH = "master"

    GITHUB_ZIP_URL = "https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    GITHUB_RAW_METADATA_URL = (
        "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/metadata.txt"
    )

    # Target folder name. The HFF plugin uses relative imports from v11.8 onwards,
    # but historical builds (and any code that resolves the package by name) expect
    # the directory to be literally 'HFF'.
    TARGET_FOLDER = "HFF"

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Initialize locale
        locale = QSettings().value('locale/userLocale')
        if locale:
            locale = locale[0:2]
            locale_path = os.path.join(
                self.plugin_dir,
                'i18n',
                'hff_installer_{}.qm'.format(locale))

            if os.path.exists(locale_path):
                self.translator = QTranslator()
                self.translator.load(locale_path)
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr('&HFF Installer')

        # Network manager for downloads
        self.network_manager = QNetworkAccessManager()
        self.current_reply = None
        self.dialog = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('HFFInstaller', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar."""

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.join(self.plugin_dir, 'icon.png')

        self.add_action(
            icon_path,
            text=self.tr('Install/Update HFF'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr('&HFF Installer'), action)
            self.iface.removeToolBarIcon(action)

    def get_plugins_path(self):
        """Get the QGIS plugins directory path."""
        return os.path.join(
            QgsApplication.qgisSettingsDirPath(),
            'python', 'plugins'
        )

    def get_existing_hff_info(self):
        """Check for existing HFF installation and get its info.

        Returns a dict with:
        - exists: bool
        - path: str (path to the plugin folder)
        - version: str (version from metadata.txt if available)
        - folder_name: str (actual folder name)
        """
        plugins_path = self.get_plugins_path()
        result = {
            'exists': False,
            'path': None,
            'version': None,
            'folder_name': None
        }

        # Folders to exclude (this installer plugin)
        exclude_folders = [
            'hff_installer',
            'hff-installer'
        ]

        # Known HFF folder names produced by either git clone or GitHub zipball
        possible_names = [
            'HFF',
            'HFF-master',
            'HFF-main',
            'hff',
            'hff-master',
            'hff-main',
        ]

        # Also pick up any folder starting with 'HFF' / 'hff' that isn't the installer
        if os.path.exists(plugins_path):
            for item in os.listdir(plugins_path):
                item_path = os.path.join(plugins_path, item)
                if item.lower() in [x.lower() for x in exclude_folders]:
                    continue
                if os.path.isdir(item_path) and item.lower().startswith('hff'):
                    if item not in possible_names:
                        possible_names.append(item)

        for name in possible_names:
            if name.lower() in [x.lower() for x in exclude_folders]:
                continue

            plugin_path = os.path.join(plugins_path, name)
            if os.path.exists(plugin_path) and os.path.isdir(plugin_path):
                # Verify it's actually HFF by reading metadata.txt
                metadata_path = os.path.join(plugin_path, 'metadata.txt')
                if os.path.exists(metadata_path):
                    try:
                        config = configparser.ConfigParser()
                        config.read(metadata_path)
                        plugin_name = config.get('general', 'name', fallback='').lower()
                        # Skip if this is the installer itself
                        if 'installer' in plugin_name:
                            continue
                        result['exists'] = True
                        result['path'] = plugin_path
                        result['folder_name'] = name
                        result['version'] = config.get('general', 'version', fallback='Unknown')
                    except Exception:
                        result['exists'] = True
                        result['path'] = plugin_path
                        result['folder_name'] = name
                        result['version'] = 'Unknown'
                else:
                    result['exists'] = True
                    result['path'] = plugin_path
                    result['folder_name'] = name
                    result['version'] = 'Unknown'

                if result['exists']:
                    break

        return result

    def download_branch(self, branch, callback):
        """Download a branch from GitHub as a zip file.

        :param branch: Branch name to download
        :param callback: Function to call when download completes
        """
        url = self.GITHUB_ZIP_URL.format(
            owner=self.REPO_OWNER,
            repo=self.REPO_NAME,
            branch=branch
        )

        request = QNetworkRequest(QUrl(url))
        # Qt5: use FollowRedirectsAttribute; Qt6: redirects are followed by default
        if hasattr(QNetworkRequest, 'FollowRedirectsAttribute'):
            request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        elif hasattr(QNetworkRequest, 'RedirectPolicyAttribute'):
            request.setAttribute(
                QNetworkRequest.RedirectPolicyAttribute,
                QNetworkRequest.NoLessSafeRedirectPolicy
            )

        self.current_reply = self.network_manager.get(request)
        self.current_reply.finished.connect(lambda: callback(self.current_reply))

        return self.current_reply

    def check_latest_version(self, callback):
        """Fetch the latest HFF version from the master branch's metadata.txt
        on raw.githubusercontent.com.

        :param callback: function(latest_version_str_or_None, error_message_or_None)
        """
        url = self.GITHUB_RAW_METADATA_URL.format(
            owner=self.REPO_OWNER,
            repo=self.REPO_NAME,
            branch=self.MASTER_BRANCH,
        )
        request = QNetworkRequest(QUrl(url))
        if hasattr(QNetworkRequest, 'FollowRedirectsAttribute'):
            request.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
        elif hasattr(QNetworkRequest, 'RedirectPolicyAttribute'):
            request.setAttribute(
                QNetworkRequest.RedirectPolicyAttribute,
                QNetworkRequest.NoLessSafeRedirectPolicy,
            )

        reply = self.network_manager.get(request)

        def on_finished():
            try:
                if reply.error() != NETWORK_NO_ERROR:
                    callback(None, reply.errorString())
                    return
                raw = bytes(reply.readAll()).decode('utf-8', errors='replace')
                version = None
                for line in raw.splitlines():
                    s = line.strip()
                    if s.lower().startswith('version'):
                        # 'version=11.12' or 'version = 11.12'
                        eq = s.find('=')
                        if eq != -1:
                            version = s[eq + 1:].strip()
                            break
                if not version:
                    callback(None, "version field not found in metadata.txt")
                    return
                callback(version, None)
            finally:
                reply.deleteLater()

        reply.finished.connect(on_finished)
        return reply

    @staticmethod
    def parse_version(v):
        """Turn a 'X.Y.Z' string into a tuple of ints for comparison.

        Non-numeric segments are dropped. Returns () if nothing parseable —
        which compares 'less than' every real version, matching the intuition
        that an unknown installed version should trigger an update prompt.
        """
        if not v:
            return ()
        parts = []
        for chunk in str(v).strip().split('.'):
            digits = ''
            for ch in chunk:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            if digits == '':
                break
            parts.append(int(digits))
        return tuple(parts)

    @classmethod
    def compare_versions(cls, installed, latest):
        """Return -1 / 0 / +1 where -1 means an update is available."""
        a = cls.parse_version(installed)
        b = cls.parse_version(latest)
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    def install_plugin(self, progress_callback=None, finished_callback=None):
        """Download and install the plugin from the master branch.

        :param progress_callback: Function to call with progress updates
        :param finished_callback: Function to call when finished (success, message)
        """
        if progress_callback:
            progress_callback(f"Downloading {self.MASTER_BRANCH} branch...")

        def on_download_complete(reply):
            if reply.error() != NETWORK_NO_ERROR:
                if finished_callback:
                    finished_callback(False, f"Download error: {reply.errorString()}")
                return

            temp_dir = None
            try:
                if progress_callback:
                    progress_callback("Download complete. Installing...")

                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, 'hff.zip')

                with open(zip_path, 'wb') as f:
                    f.write(reply.readAll().data())

                if progress_callback:
                    progress_callback("Extracting files...")

                extract_dir = os.path.join(temp_dir, 'extracted')
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                extracted_folders = [
                    f for f in os.listdir(extract_dir)
                    if os.path.isdir(os.path.join(extract_dir, f))
                ]
                if not extracted_folders:
                    if finished_callback:
                        finished_callback(False, "No files found in downloaded archive")
                    return

                source_folder = os.path.join(extract_dir, extracted_folders[0])

                if progress_callback:
                    progress_callback("Checking existing installation...")

                plugins_path = self.get_plugins_path()
                target_path = os.path.join(plugins_path, self.TARGET_FOLDER)

                existing = self.get_existing_hff_info()
                if existing['exists']:
                    if progress_callback:
                        progress_callback(f"Removing existing installation: {existing['folder_name']}...")
                    try:
                        shutil.rmtree(existing['path'])
                    except Exception as e:
                        if finished_callback:
                            finished_callback(False, f"Failed to remove existing installation: {str(e)}")
                        return

                # Also remove the target folder if it still exists under a different case / leftover
                if os.path.exists(target_path):
                    if progress_callback:
                        progress_callback(f"Removing old {self.TARGET_FOLDER} folder...")
                    shutil.rmtree(target_path)

                if progress_callback:
                    progress_callback("Copying new plugin files...")

                shutil.copytree(source_folder, target_path)

                if progress_callback:
                    progress_callback("Cleaning up...")

                new_info = self.get_existing_hff_info()
                version = new_info.get('version', 'Unknown')

                if finished_callback:
                    finished_callback(
                        True,
                        f"HFF (v{version}) installed successfully!\n\n"
                        f"Please restart QGIS to load the plugin."
                    )

            except Exception as e:
                if finished_callback:
                    finished_callback(False, f"Installation error: {str(e)}")
            finally:
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass

        self.download_branch(self.MASTER_BRANCH, on_download_complete)

    def run(self):
        """Run method that performs all the real work."""
        self.dialog = InstallerDialog(self)
        existing = self.get_existing_hff_info()
        self.dialog.update_current_status(existing)
        self.dialog.show()
