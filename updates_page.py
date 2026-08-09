"""
plagTalk — Updates & Changelog page
Self-contained widget following the plagComms self-update pattern.
"""

import json
import os
import sys

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QProgressBar,
)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from updater import Installer, APP_VERSION


def _asset_path(filename: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def _lbl(text: str, muted=False, heading=False, small=False) -> QLabel:
    l = QLabel(text)
    style = "background: transparent; "
    if heading:
        style += "font-size: 16px; font-weight: 600; color: #ddddf5;"
    elif muted or small:
        style += f"color: #7878a8; font-size: {'10' if small else '11'}px;"
    else:
        style += "color: #ddddf5;"
    l.setStyleSheet(style)
    return l


def _scrollable(widget: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setStyleSheet("QScrollArea { border: none; }")
    return area


# ── Update banner ─────────────────────────────────────────────────────────────

class UpdateBanner(QFrame):
    """Amber 'update available' bar with one-click install."""

    def __init__(self, version: str, download_url: str, asset_url: str,
                 notes: list, parent=None):
        super().__init__(parent)
        self._download_url = download_url
        self._asset_url    = asset_url
        self._installer: Installer | None = None

        self.setStyleSheet(
            "UpdateBanner { background: #2e1f00; border: 1px solid #f0a040; "
            "border-radius: 8px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        hdr = QHBoxLayout()
        hdr_lbl = QLabel(f"🆕  plagTalk {version} is available!")
        hdr_lbl.setStyleSheet(
            "color: #f0c060; font-weight: 600; font-size: 13px; background: transparent;"
        )
        hdr.addWidget(hdr_lbl)
        hdr.addStretch()

        if asset_url:
            self.btn_action = QPushButton("Install Update")
            self.btn_action.setStyleSheet(
                "QPushButton { background: #f0a040; border: none; border-radius: 5px; "
                "color: #1a0f00; font-weight: 700; padding: 5px 14px; }"
                "QPushButton:hover { background: #ffc060; }"
                "QPushButton:disabled { background: #444; color: #888; }"
            )
            self.btn_action.clicked.connect(self._install)
        else:
            self.btn_action = QPushButton("Download")
            self.btn_action.setStyleSheet(
                "QPushButton { background: #f0a040; border: none; border-radius: 5px; "
                "color: #1a0f00; font-weight: 700; padding: 5px 14px; }"
                "QPushButton:hover { background: #ffc060; }"
            )
            self.btn_action.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(download_url))
            )
        hdr.addWidget(self.btn_action)
        layout.addLayout(hdr)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(5)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar { background: #4a2e00; border-radius: 2px; border: none; }"
            "QProgressBar::chunk { background: #f0a040; border-radius: 2px; }"
        )
        self.progress.hide()
        layout.addWidget(self.progress)

        if notes:
            notes_lbl = QLabel("• " + "\n• ".join(notes[:6]))
            notes_lbl.setStyleSheet(
                "color: #c0904a; font-size: 11px; background: transparent;"
            )
            notes_lbl.setWordWrap(True)
            layout.addWidget(notes_lbl)

    def _install(self):
        self.btn_action.setEnabled(False)
        self.btn_action.setText("Downloading…")
        self.progress.show()
        self._installer = Installer(self._asset_url, self)
        self._installer.progress.connect(self.progress.setValue)
        self._installer.done.connect(self._on_done)
        self._installer.error.connect(self._on_error)
        self._installer.start()

    def _on_done(self):
        self.btn_action.setText("Restarting…")
        QTimer.singleShot(600, _exit_for_update)

    def _on_error(self, msg: str):
        self.btn_action.setEnabled(True)
        self.btn_action.setText("Install Update")
        self.progress.hide()
        err = QLabel(f"⚠  {msg}")
        err.setStyleSheet("color: #e05a5a; font-size: 11px; background: transparent;")
        err.setWordWrap(True)
        self.layout().addWidget(err)


# ── Changelog entry ───────────────────────────────────────────────────────────

class ChangelogEntry(QFrame):
    """One version block in the scrollable changelog."""

    def __init__(self, entry: dict, is_current: bool, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "ChangelogEntry { background: #1b1b30; border: 1px solid #25253f; "
            "border-radius: 8px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        hdr = QHBoxLayout()

        ver_lbl = QLabel(f"v{entry.get('version', '')}")
        ver_lbl.setStyleSheet(
            "color: #ddddf5; font-weight: 600; font-size: 13px; background: transparent;"
        )
        hdr.addWidget(ver_lbl)

        if is_current:
            tag = QLabel("current")
            tag.setStyleSheet(
                "background: rgba(76,175,125,0.18); color: #4caf7d; border-radius: 3px; "
                "padding: 1px 6px; font-size: 10px; font-weight: 600;"
            )
            hdr.addWidget(tag)

        date_lbl = QLabel(entry.get("date", ""))
        date_lbl.setStyleSheet("color: #7878a8; font-size: 11px; background: transparent;")
        hdr.addWidget(date_lbl)
        hdr.addStretch()

        gh_tag = entry.get("github_tag", "")
        if gh_tag:
            gh_btn = QPushButton("GitHub ↗")
            gh_btn.setFixedWidth(68)
            gh_btn.setStyleSheet(
                "QPushButton { background: transparent; border: 1px solid #25253f; "
                "border-radius: 4px; color: #7878a8; font-size: 10px; padding: 2px 5px; }"
                "QPushButton:hover { border-color: #7c6ff7; color: #ddddf5; }"
            )
            gh_url = f"https://github.com/plagrizd/plagTalk/releases/tag/{gh_tag}"
            gh_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(gh_url)))
            hdr.addWidget(gh_btn)

        layout.addLayout(hdr)

        for note in entry.get("notes", []):
            n = QLabel(f"• {note}")
            n.setStyleSheet("color: #9090b8; font-size: 11px; background: transparent;")
            n.setWordWrap(True)
            layout.addWidget(n)


# ── Updates page ──────────────────────────────────────────────────────────────

class UpdatesPage(QWidget):
    check_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._banner: UpdateBanner | None = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(12)

        root.addWidget(_lbl("Updates", heading=True))

        # Status row
        hdr_row = QHBoxLayout()
        self._status_lbl = QLabel("Checking for updates…")
        self._status_lbl.setStyleSheet("color: #7878a8; font-size: 11px; background: transparent;")
        hdr_row.addWidget(self._status_lbl)
        hdr_row.addStretch()
        self._check_btn = QPushButton("Check Now")
        self._check_btn.setFixedWidth(90)
        self._check_btn.clicked.connect(self.check_requested.emit)
        hdr_row.addWidget(self._check_btn)
        root.addLayout(hdr_row)

        # Banner slot (hidden until an update is found)
        self._banner_slot = QWidget()
        self._banner_slot.setVisible(False)
        self._banner_layout = QVBoxLayout(self._banner_slot)
        self._banner_layout.setContentsMargins(0, 0, 0, 4)
        root.addWidget(self._banner_slot)

        # Changelog
        cur_lbl = _lbl(f"Running: v{APP_VERSION}", muted=True)
        root.addWidget(cur_lbl)

        self._changelog_container = QWidget()
        self._changelog_layout = QVBoxLayout(self._changelog_container)
        self._changelog_layout.setContentsMargins(0, 0, 0, 0)
        self._changelog_layout.setSpacing(8)

        root.addWidget(self._changelog_container)
        root.addStretch()

        outer.addWidget(_scrollable(container))

    # ── Slots called by MainWindow ────────────────────────────────────────────

    def on_update_available(self, version: str, download_url: str,
                            asset_url: str, notes: list):
        self._status_lbl.setText(f"🆕  v{version} is available")
        self._status_lbl.setStyleSheet("color: #f0a040; font-size: 11px; background: transparent;")
        if self._banner is None:
            self._banner = UpdateBanner(version, download_url, asset_url, notes)
            self._banner_layout.addWidget(self._banner)
            self._banner_slot.setVisible(True)

    def on_no_update(self):
        self._status_lbl.setText(f"✓  v{APP_VERSION} is up to date")
        self._status_lbl.setStyleSheet("color: #4caf7d; font-size: 11px; background: transparent;")

    def on_check_failed(self):
        self._status_lbl.setText("Couldn't check for updates")
        self._status_lbl.setStyleSheet("color: #e05a5a; font-size: 11px; background: transparent;")

    def set_changelog(self, changelog: list):
        while self._changelog_layout.count():
            item = self._changelog_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for entry in changelog:
            is_current = entry.get("version") == APP_VERSION
            self._changelog_layout.addWidget(ChangelogEntry(entry, is_current))

    def show_local_changelog(self):
        """Populate changelog from bundled version.json (works offline)."""
        try:
            path = _asset_path("version.json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.set_changelog(data.get("changelog", []))
        except Exception as e:
            print(f"[updates] local changelog load failed: {e}")


# ── Safe exit for swap ────────────────────────────────────────────────────────

def _exit_for_update():
    """os._exit avoids PyInstaller DLL teardown issues during hot-swap."""
    from PyQt6.QtWidgets import QApplication
    for w in QApplication.topLevelWidgets():
        if hasattr(w, "tray"):
            try:
                w.tray.hide()
            except Exception:
                pass
    os._exit(0)
