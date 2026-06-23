# -*- coding: utf-8 -*-
"""
HFF Installer - Dialog UI
"""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QProgressBar, QFrame, QMessageBox
)
from qgis.PyQt.QtGui import QFont

# Qt5/Qt6 enum compatibility
ALIGN_CENTER = getattr(Qt, 'AlignCenter', None) or Qt.AlignmentFlag.AlignCenter
FRAME_HLINE = getattr(QFrame, 'HLine', None) or QFrame.Shape.HLine
FRAME_SUNKEN = getattr(QFrame, 'Sunken', None) or QFrame.Shadow.Sunken
MSG_YES = getattr(QMessageBox, 'Yes', None) or QMessageBox.StandardButton.Yes
MSG_NO = getattr(QMessageBox, 'No', None) or QMessageBox.StandardButton.No


class InstallerDialog(QDialog):
    """Dialog for HFF Installer."""

    def __init__(self, installer, parent=None):
        """Constructor.

        :param installer: The HFFInstaller instance
        :param parent: Parent widget
        """
        super().__init__(parent)
        self.installer = installer
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("HFF Installer")
        self.setMinimumWidth(500)
        self.setMinimumHeight(380)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title_label = QLabel("HFF Installer")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(ALIGN_CENTER)
        layout.addWidget(title_label)

        # Subtitle
        subtitle = QLabel("Install or update the HFF plugin from GitHub")
        subtitle.setAlignment(ALIGN_CENTER)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)

        # Separator
        line = QFrame()
        line.setFrameShape(FRAME_HLINE)
        line.setFrameShadow(FRAME_SUNKEN)
        layout.addWidget(line)

        # Current installation status
        status_group = QGroupBox("Current Installation")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Checking...")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        self.version_label = QLabel("")
        self.version_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.version_label)

        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: gray; font-size: 10px;")
        status_layout.addWidget(self.path_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Version-to-install info (master only — no dev branches)
        source_group = QGroupBox("Source")
        source_layout = QVBoxLayout()

        source_label = QLabel(
            f"Branch: <b>master</b> (stable) — "
            f"{self.installer.REPO_OWNER}/{self.installer.REPO_NAME}"
        )
        source_label.setTextFormat(Qt.RichText)
        source_layout.addWidget(source_label)

        source_desc = QLabel(
            "Only the stable master branch is installed — development branches are not exposed."
        )
        source_desc.setWordWrap(True)
        source_desc.setStyleSheet("color: gray; font-size: 10px;")
        source_layout.addWidget(source_desc)

        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # Progress section
        progress_group = QGroupBox("Installation Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setPlaceholderText("Installation log will appear here...")
        progress_layout.addWidget(self.log_text)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.install_button = QPushButton("Install / Update")
        self.install_button.setMinimumHeight(40)
        self.install_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
            }
        """)
        self.install_button.clicked.connect(self.on_install_clicked)
        button_layout.addWidget(self.install_button)

        self.close_button = QPushButton("Close")
        self.close_button.setMinimumHeight(40)
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        # Warning label
        warning_label = QLabel(
            "Note: After installation, you need to restart QGIS to load the plugin."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #ff9800; font-size: 10px;")
        warning_label.setAlignment(ALIGN_CENTER)
        layout.addWidget(warning_label)

        self.setLayout(layout)

    def update_current_status(self, info):
        """Update the current installation status display.

        :param info: Dict with exists, path, version, folder_name
        """
        if info['exists']:
            self.status_label.setText("HFF is currently installed")
            self.status_label.setStyleSheet("color: #2e7d32;")
            self.version_label.setText(f"Version: {info['version'] or 'Unknown'}")
            self.path_label.setText(f"Location: {info['path']}")

            if info['folder_name'] != self.installer.TARGET_FOLDER:
                self.log_message(
                    f"Note: Plugin folder is named '{info['folder_name']}' "
                    f"instead of '{self.installer.TARGET_FOLDER}'. It will be "
                    f"renamed on the next install."
                )
        else:
            self.status_label.setText("HFF is not installed")
            self.status_label.setStyleSheet("color: #f44336;")
            self.version_label.setText("")
            self.path_label.setText(f"Plugins path: {self.installer.get_plugins_path()}")

    def log_message(self, message):
        """Add a message to the log."""
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_install_clicked(self):
        """Handle install button click."""
        existing = self.installer.get_existing_hff_info()
        if existing['exists']:
            reply = QMessageBox.question(
                self,
                'Confirm Installation',
                f"This will replace the existing HFF installation.\n\n"
                f"Current version: {existing['version'] or 'Unknown'}\n"
                f"Current folder: {existing['folder_name']}\n\n"
                f"Install master branch from "
                f"{self.installer.REPO_OWNER}/{self.installer.REPO_NAME}?",
                MSG_YES | MSG_NO,
                MSG_NO
            )
            if reply != MSG_YES:
                return

        self.install_button.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.log_text.clear()
        self.log_message("Starting installation of master branch...")

        self.installer.install_plugin(
            progress_callback=self.on_progress,
            finished_callback=self.on_finished
        )

    def on_progress(self, message):
        """Handle progress updates."""
        self.log_message(message)

    def on_finished(self, success, message):
        """Handle installation completion."""
        self.progress_bar.setVisible(False)
        self.install_button.setEnabled(True)

        if success:
            self.log_message("Installation completed successfully!")
            QMessageBox.information(self, "Installation Complete", message)
            existing = self.installer.get_existing_hff_info()
            self.update_current_status(existing)
        else:
            self.log_message(f"Installation failed: {message}")
            QMessageBox.critical(self, "Installation Failed", message)
