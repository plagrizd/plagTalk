"""
plagTalk — main application
PyQt6 TTS addon for plagComms.
"""

import sys
import os
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QSlider, QSpinBox, QScrollArea,
    QFrame, QGroupBox, QSystemTrayIcon, QMenu, QMessageBox,
    QTextEdit, QDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QUrl, QEvent, QObject
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QAction, QDesktopServices

from settings import Settings, DEFAULT_TEMPLATES
from ws_client import WsClient
from tts_engine import TTSEngine
from event_handler import EventHandler
from updater import APP_VERSION, Updater
from updates_page import UpdatesPage


# ── Event definitions ─────────────────────────────────────────────────────────

EVENT_DEFS = [
    ("chat",               "twitch",  "Chat Messages",          "All platforms"),
    ("follow_twitch",      "twitch",  "New Follower",           ""),
    ("sub_twitch",         "twitch",  "Subscription",           "Shared, no message"),
    ("sub_message_twitch", "twitch",  "Subscription + Message", "Shared, with message"),
    ("gift_twitch",        "twitch",  "Gift Subs",              ""),
    ("cheer_twitch",       "twitch",  "Bits Cheer",             "Threshold in Advanced"),
    ("raid_twitch",        "twitch",  "Incoming Raid",          "Threshold in Advanced"),
    ("watch_streak_twitch","twitch",  "Watch Streak",           "Power-Up share"),

    ("chat",               "tiktok",  "Chat Messages",          "All platforms (shared setting)"),
    ("follow_tiktok",      "tiktok",  "New Follower",           ""),
    ("gift_tiktok",        "tiktok",  "Gift",                   "Threshold in Advanced"),
    ("sub_tiktok",         "tiktok",  "Subscription",           ""),
    ("superfan_tiktok",    "tiktok",  "Superfan",               ""),
    ("share_tiktok",       "tiktok",  "Stream Share",           ""),
    ("like_tiktok",        "tiktok",  "Likes",                  "Often noisy — threshold recommended"),

    ("chat",               "youtube", "Chat Messages",          "All platforms (shared setting)"),
    ("superchat_youtube",  "youtube", "Super Chat",             ""),
    ("membership_youtube", "youtube", "Membership",             ""),

    ("chat",               "kick",    "Chat Messages",          "All platforms (shared setting)"),
    ("follow_kick",        "kick",    "New Follower",           "Anonymous — polled from follower count"),
    ("sub_kick",           "kick",    "Subscription",           ""),
    ("gift_kick",          "kick",    "Gift Subs",              ""),
    ("raid_kick",          "kick",    "Incoming Host",          ""),
]

PLATFORM_COLOR = {"twitch": "#9146ff", "tiktok": "#ee1d52", "youtube": "#ff4040", "kick": "#53FC18"}

# ── Inline SVG assets ─────────────────────────────────────────────────────────

_CHECK_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'>"
              "<polyline points='1.5,6 4.5,9.5 10.5,2.5' stroke='white' "
              "stroke-width='2.2' fill='none' stroke-linecap='round' "
              "stroke-linejoin='round'/></svg>")

_ARROW_SVG = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'>"
              "<polyline points='1,3.5 5,7 9,3.5' stroke='#7878a8' "
              "stroke-width='1.5' fill='none' stroke-linecap='round' "
              "stroke-linejoin='round'/></svg>")


def _svg_url(name: str, svg: str) -> str:
    path = os.path.join(tempfile.gettempdir(), f"plagtalk_{name}")
    try:
        with open(path, "w") as fh:
            fh.write(svg)
    except Exception:
        return ""
    return path.replace("\\", "/")


STYLESHEET_BASE = """
QWidget {
    background: #12121f;
    color: #ddddf5;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}
QMainWindow, QDialog { background: #12121f; }

QLabel    { background: transparent; }
QCheckBox { background: transparent; }

/* Sidebar */
QListWidget {
    background: #0f0f1e;
    border: none;
    border-right: 1px solid #25253f;
    outline: 0;
    padding: 6px 4px;
}
QListWidget::item { border-radius: 6px; padding: 9px 12px; color: #7878a8; margin: 1px 0; }
QListWidget::item:hover    { background: #23233d; color: #ddddf5; }
QListWidget::item:selected { background: rgba(124,111,247,0.18); color: #7c6ff7; }

/* Scroll areas */
QScrollArea { border: none; }
QScrollBar:vertical { background: transparent; width: 5px; }
QScrollBar::handle:vertical { background: #25253f; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* Group boxes — title rendered as a QLabel child, no CSS title trick needed */
QGroupBox {
    background: #1b1b30;
    border: 1px solid #25253f;
    border-radius: 10px;
    margin-top: 0;
    padding: 14px 16px 12px 16px;
}

/* Inputs */
QLineEdit, QTextEdit, QComboBox, QSpinBox {
    background: #0e0e1d;
    border: 1px solid #25253f;
    border-radius: 6px;
    padding: 6px 9px;
    color: #ddddf5;
    selection-background-color: #3e3880;
    outline: 0;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #5a50d0; }
QComboBox::drop-down { border: none; border-left: 1px solid #1e1e35; width: 26px; }
QComboBox::down-arrow { image: url(__ARROW_URL__); width: 10px; height: 10px; }
QComboBox QAbstractItemView {
    background: #1b1b30; border: 1px solid #25253f;
    selection-background-color: #3e3880; outline: 0;
}

/* Sliders */
QSlider::groove:horizontal { height: 4px; background: #25253f; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #7c6ff7; border: none;
    width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #7c6ff7; border-radius: 2px; }

/* Checkboxes */
QCheckBox { color: #ddddf5; spacing: 7px; }
QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid #35355a; border-radius: 4px; background: #0e0e1d; }
QCheckBox::indicator:hover { border-color: #7c6ff7; }
QCheckBox::indicator:checked { background: #7c6ff7; border-color: #7c6ff7; image: url(__CHECK_URL__); }

/* Buttons */
QPushButton {
    background: #1b1b30; border: 1px solid #25253f;
    border-radius: 6px; padding: 6px 14px;
    color: #ddddf5; font-weight: 500;
}
QPushButton:hover   { background: #23233d; border-color: #3e3880; }
QPushButton:pressed { background: #2a2a48; }

QPushButton[primary="true"] { background: #7c6ff7; border-color: #7c6ff7; color: white; }
QPushButton[primary="true"]:hover   { background: #6a5ee0; border-color: #6a5ee0; }
QPushButton[primary="true"]:pressed { background: #5a4fd0; }

QPushButton[danger="true"]  { color: #e05a5a; border-color: #e05a5a; }
QPushButton[danger="true"]:hover { background: rgba(224,90,90,0.12); }

/* Label variants */
QLabel[heading="true"] { font-size: 16px; font-weight: 600; color: #ddddf5; }
QLabel[muted="true"]   { color: #7878a8; font-size: 11px; }
QLabel[mono="true"]    { font-family: Consolas, monospace; font-size: 11px; color: #b8aff9; }

QFrame[separator="true"] { background: #25253f; max-height: 1px; min-height: 1px; }
"""


def _asset_path(filename: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def _make_stylesheet() -> str:
    check = _svg_url("check.svg", _CHECK_SVG)
    arrow = _svg_url("arrow.svg", _ARROW_SVG)
    return (STYLESHEET_BASE
            .replace("__CHECK_URL__", check)
            .replace("__ARROW_URL__", arrow))


# ═════════════════════════════════════════════════════════════════════════════
# Helpers / mini-widgets
# ═════════════════════════════════════════════════════════════════════════════

def hline():
    f = QFrame()
    f.setProperty("separator", True)
    return f


def label(text, muted=False, heading=False, mono=False):
    l = QLabel(text)
    if muted:   l.setProperty("muted",   True)
    if heading: l.setProperty("heading", True)
    if mono:    l.setProperty("mono",    True)
    return l


def section_title(text: str) -> QLabel:
    """Bold section header rendered inside a QGroupBox (replaces the title trick)."""
    l = QLabel(text)
    l.setStyleSheet(
        "color: #ddddf5; font-weight: 600; font-size: 12px; "
        "background: transparent; margin-bottom: 2px;"
    )
    return l


def primary_btn(text):
    b = QPushButton(text)
    b.setProperty("primary", True)
    return b


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"{r},{g},{b}"


def scrollable(widget):
    area = QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    return area


def _populate_voice_combo(combo: QComboBox, voices: list, current: str = ""):
    """Fill a QComboBox with grouped voices; section headers are disabled items."""
    combo.clear()
    combo.setMaxVisibleItems(15)
    combo.addItem("— Default —", "")

    sapi_v   = [(n, v) for n, v in voices if not v.startswith("google:") and not v.startswith("elevenlabs:")]
    google_v = [(n, v) for n, v in voices if v.startswith("google:")]
    el_v     = [(n, v) for n, v in voices if v.startswith("elevenlabs:")]

    def _sep(text):
        combo.addItem(text)
        item = combo.model().item(combo.count() - 1)
        item.setEnabled(False)
        item.setForeground(QColor("#7878a8"))

    if sapi_v:
        _sep("── Windows SAPI ──")
        for name, vid in sapi_v:
            combo.addItem(name, vid)
    if google_v:
        _sep("── Google Cloud TTS ──")
        for name, vid in google_v:
            combo.addItem(name, vid)
    if el_v:
        _sep("── ElevenLabs ──")
        for name, vid in el_v:
            combo.addItem(name, vid)

    idx = combo.findData(current)
    if idx >= 0:
        combo.setCurrentIndex(idx)


# ── Wheel guard ───────────────────────────────────────────────────────────────

class WheelBlocker(QObject):
    """Block accidental spinbox / combobox changes via scroll when not focused."""
    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.Wheel:
            if isinstance(obj, (QSpinBox, QComboBox)) and not obj.hasFocus():
                return True
        return False


# ── Voice picker dialog ───────────────────────────────────────────────────────

class VoicePickerDialog(QDialog):
    def __init__(self, voices: list, current_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Voice")
        self.setMinimumSize(430, 480)
        self.setWindowIcon(QIcon(_asset_path("icon.png")))
        self._voices     = voices
        self._current_id = current_id
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search voices…")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = primary_btn("Select")
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

        self._populate("")

        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == self._current_id:
                self._list.setCurrentItem(item)
                self._list.scrollToItem(item)
                break

    def _populate(self, search: str):
        self._list.clear()
        s = search.lower()

        sapi_v   = [(n, v) for n, v in self._voices
                    if not v.startswith("google:") and not v.startswith("elevenlabs:")]
        google_v = [(n, v) for n, v in self._voices if v.startswith("google:")]
        el_v     = [(n, v) for n, v in self._voices if v.startswith("elevenlabs:")]

        def _group(section, items):
            filtered = [(n, v) for n, v in items if not s or s in n.lower()]
            if not filtered:
                return
            hdr = QListWidgetItem(f"  {section}")
            hdr.setFlags(Qt.ItemFlag.NoItemFlags)
            hdr.setForeground(QColor("#7878a8"))
            hdr.setBackground(QColor("#0f0f1e"))
            self._list.addItem(hdr)
            for name, vid in filtered:
                item = QListWidgetItem(f"  {name}")
                item.setData(Qt.ItemDataRole.UserRole, vid)
                self._list.addItem(item)

        _group("Windows SAPI", sapi_v)
        _group("Google Cloud TTS", google_v)
        _group("ElevenLabs", el_v)

    def _filter(self, text: str):
        self._populate(text)

    def selected_id(self) -> str:
        item = self._list.currentItem()
        if item and bool(item.flags() & Qt.ItemFlag.ItemIsEnabled):
            vid = item.data(Qt.ItemDataRole.UserRole)
            if vid is not None:
                return vid
        return self._current_id


class VoicePicker(QWidget):
    """Read-only display field + 'Choose…' button that opens VoicePickerDialog."""
    voice_changed = pyqtSignal(str)

    def __init__(self, voices: list, current_id: str, parent=None):
        super().__init__(parent)
        self._voices   = voices
        self._voice_id = current_id
        self._build()

    def _build(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        self._display = QLineEdit()
        self._display.setReadOnly(True)
        self._display.setPlaceholderText("— Default / System —")
        row.addWidget(self._display, 1)

        self._btn = QPushButton("Choose…")
        self._btn.setFixedWidth(72)
        self._btn.clicked.connect(self._open_picker)
        row.addWidget(self._btn)

        self._update_display()

    def _update_display(self):
        if not self._voice_id:
            self._display.setText("")
            return
        for name, vid in self._voices:
            if vid == self._voice_id:
                self._display.setText(name)
                return
        self._display.setText(self._voice_id)

    def _open_picker(self):
        dlg = VoicePickerDialog(self._voices, self._voice_id, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_id = dlg.selected_id()
            self._voice_id = new_id
            self._update_display()
            self.voice_changed.emit(new_id)

    def voice_id(self) -> str:
        return self._voice_id

    def set_voice_id(self, vid: str):
        self._voice_id = vid
        self._update_display()

    def set_voices(self, voices: list):
        self._voices = voices
        self._update_display()


# ── About dialog ──────────────────────────────────────────────────────────────

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About plagTalk")
        self.setFixedSize(440, 300)
        self.setWindowIcon(QIcon(_asset_path("icon.png")))
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(12)

        hdr = QHBoxLayout()
        logo = QLabel()
        pix = QPixmap(_asset_path("icon.png")).scaled(
            52, 52, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logo.setPixmap(pix)
        logo.setStyleSheet("background: transparent;")
        hdr.addWidget(logo)
        hdr.addSpacing(12)

        info = QVBoxLayout()
        name_lbl = QLabel("plagTalk")
        name_lbl.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #ddddf5; background: transparent;"
        )
        info.addWidget(name_lbl)
        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet("color: #7878a8; font-size: 12px; background: transparent;")
        info.addWidget(ver_lbl)
        hdr.addLayout(info)
        hdr.addStretch()
        root.addLayout(hdr)

        desc = QLabel(
            "A Windows TTS add-on for plagComms.\n"
            "Reads chat events aloud via SAPI, Google Cloud TTS, or ElevenLabs."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #9090b8; font-size: 12px; background: transparent;")
        root.addWidget(desc)

        root.addWidget(hline())

        link_row = QHBoxLayout()
        btn_site = QPushButton("plagrizr.com/plagTalk")
        btn_site.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://www.plagrizr.com/plagTalk"))
        )
        btn_gh = QPushButton("GitHub ↗")
        btn_gh.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/plagrizd/plagTalk"))
        )
        link_row.addWidget(btn_site)
        link_row.addWidget(btn_gh)
        link_row.addStretch()
        root.addLayout(link_row)

        copy_lbl = QLabel("© 2026 plagrizr. All rights reserved.")
        copy_lbl.setStyleSheet("color: #55556a; font-size: 10px; background: transparent;")
        root.addWidget(copy_lbl)

        root.addStretch()

        close_row = QHBoxLayout()
        close_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(80)
        btn_close.clicked.connect(self.accept)
        close_row.addWidget(btn_close)
        root.addLayout(close_row)


# ═════════════════════════════════════════════════════════════════════════════
# Sidebar navigation
# ═════════════════════════════════════════════════════════════════════════════

class SidebarNav(QWidget):
    """Accordion sidebar.
    Top section: Dashboard + Events platforms.
    Bottom section: Settings / Advanced / Updates.
    About opens as a dialog via about_requested signal.
    """
    page_changed    = pyqtSignal(int)
    about_requested = pyqtSignal()

    _BTN_SS = """
        QPushButton {
            background: transparent; border: none;
            border-radius: 6px; padding: 9px 12px;
            color: #7878a8; text-align: left; font-size: 12px;
        }
        QPushButton:hover { background: #23233d; color: #ddddf5; }
        QPushButton[active=true] { background: rgba(124,111,247,0.18); color: #7c6ff7; }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(148)
        self.setStyleSheet("background: #0f0f1e; border-right: 1px solid #25253f;")
        self._active_btn: QPushButton | None = None
        self._events_open = True
        self._plat_btns: dict[str, QPushButton] = {}
        self._build()

    def _build(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(6, 10, 6, 10)
        vbox.setSpacing(1)

        # Logo
        logo_row = QHBoxLayout()
        logo_lbl = QLabel()
        pix = QPixmap(_asset_path("icon.png")).scaled(
            28, 28, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logo_lbl.setPixmap(pix)
        logo_lbl.setStyleSheet("background: transparent;")
        logo_row.addWidget(logo_lbl)
        title_lbl = QLabel("plagTalk")
        title_lbl.setStyleSheet("background: transparent; color: #ddddf5; font-weight: 600;")
        logo_row.addWidget(title_lbl)
        logo_row.addStretch()
        vbox.addLayout(logo_row)
        vbox.addSpacing(6)

        # ── Top nav: Dashboard + Events ────────────────────────────────────────
        self.btn_dashboard = self._nav_btn("Dashboard")
        self.btn_dashboard.clicked.connect(lambda: self._activate(self.btn_dashboard, 0))
        vbox.addWidget(self.btn_dashboard)

        self.btn_events_hdr = QPushButton("▾  Events")
        self.btn_events_hdr.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_events_hdr.setFixedHeight(36)
        self.btn_events_hdr.setStyleSheet("""
            QPushButton {
                background: transparent; border: none; border-radius: 6px;
                padding: 9px 12px; color: #9898c8;
                text-align: left; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: #23233d; }
        """)
        self.btn_events_hdr.clicked.connect(self._toggle_events)
        vbox.addWidget(self.btn_events_hdr)

        self._plat_frame = QWidget()
        self._plat_frame.setStyleSheet("background: transparent;")
        pf = QVBoxLayout(self._plat_frame)
        pf.setContentsMargins(0, 0, 0, 0)
        pf.setSpacing(1)
        for plat_name, page_idx in [("Twitch", 1), ("TikTok", 2), ("YouTube", 3), ("Kick", 4)]:
            plat_key = plat_name.lower()
            btn = self._plat_btn(plat_name, page_idx, PLATFORM_COLOR.get(plat_key, "#7c6ff7"))
            self._plat_btns[plat_key] = btn
            pf.addWidget(btn)
        vbox.addWidget(self._plat_frame)

        # ── Push bottom nav to the bottom ─────────────────────────────────────
        vbox.addStretch()

        # Subtle separator before bottom nav group
        sep = QFrame()
        sep.setStyleSheet("background: #25253f; max-height: 1px; min-height: 1px;")
        vbox.addWidget(sep)
        vbox.addSpacing(2)

        # ── Bottom nav: Settings / Advanced / Updates ──────────────────────────
        self.btn_settings = self._nav_btn("Settings")
        self.btn_settings.clicked.connect(lambda: self._activate(self.btn_settings, 5))
        vbox.addWidget(self.btn_settings)

        self.btn_advanced = self._nav_btn("Advanced")
        self.btn_advanced.clicked.connect(lambda: self._activate(self.btn_advanced, 6))
        vbox.addWidget(self.btn_advanced)

        self.btn_updates = self._nav_btn("Updates")
        self.btn_updates.clicked.connect(lambda: self._activate(self.btn_updates, 7))
        vbox.addWidget(self.btn_updates)

        vbox.addSpacing(4)

        # ── Status / About / Version ──────────────────────────────────────────
        self.status_label = QLabel("● Connecting…")
        self.status_label.setStyleSheet("color: #f0a040; font-size: 11px; background: transparent;")
        self.status_label.setContentsMargins(6, 0, 0, 0)
        vbox.addWidget(self.status_label)

        self._about_btn = QPushButton("ⓘ About")
        self._about_btn.setFixedHeight(22)
        self._about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._about_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #45455a; "
            "font-size: 10px; text-align: left; padding: 0 6px; }"
            "QPushButton:hover { color: #7878a8; }"
        )
        self._about_btn.clicked.connect(self.about_requested.emit)
        vbox.addWidget(self._about_btn)

        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet("color: #35355a; font-size: 10px; background: transparent;")
        ver_lbl.setContentsMargins(6, 0, 0, 2)
        vbox.addWidget(ver_lbl)

        self._activate(self.btn_dashboard, 0)

    def _nav_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._BTN_SS)
        return btn

    def _plat_btn(self, text: str, page_idx: int, color: str) -> QPushButton:
        r, g, b = (int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        btn = QPushButton(f"  {text}")
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; border-radius: 5px;"
            f" padding: 6px 12px 6px 20px; color: rgba({r},{g},{b},0.65);"
            f" text-align: left; font-size: 11px; }}"
            f"QPushButton:hover {{ background: rgba({r},{g},{b},0.12); color: rgb({r},{g},{b}); }}"
            f"QPushButton[active=true] {{ background: rgba({r},{g},{b},0.15);"
            f" color: rgb({r},{g},{b}); font-weight: 600; }}"
        )
        btn.clicked.connect(lambda _, idx=page_idx: self._activate(btn, idx))
        return btn

    def _activate(self, btn: QPushButton, page_idx: int):
        if self._active_btn is not None and self._active_btn is not btn:
            self._active_btn.setProperty("active", False)
            self._active_btn.style().unpolish(self._active_btn)
            self._active_btn.style().polish(self._active_btn)
        btn.setProperty("active", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        self._active_btn = btn
        self.page_changed.emit(page_idx)

    def _toggle_events(self):
        self._events_open = not self._events_open
        self._plat_frame.setVisible(self._events_open)
        self.btn_events_hdr.setText("▾  Events" if self._events_open else "▸  Events")

    def set_platform_visible(self, platform: str, visible: bool):
        btn = self._plat_btns.get(platform.lower())
        if btn:
            btn.setVisible(visible)

    def set_update_badge(self, show: bool):
        self.btn_updates.setText("Updates  🆕" if show else "Updates")


# ═════════════════════════════════════════════════════════════════════════════
# Pages
# ═════════════════════════════════════════════════════════════════════════════

class DashboardPage(QWidget):
    def __init__(self, tts: TTSEngine, parent=None):
        super().__init__(parent)
        self._tts = tts
        self._build()
        tts.queue_updated.connect(self._on_queue)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(16)
        root.addWidget(label("Dashboard", heading=True))

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        self.btn_mute = QPushButton("🔊  Mute")
        self.btn_mute.setFixedHeight(34)
        self.btn_mute.setStyleSheet(
            "QPushButton { color: #4caf7d; border-color: #4caf7d; }"
            "QPushButton:hover { background: rgba(76,175,125,0.12); }"
        )
        self.btn_mute.clicked.connect(self._toggle_mute)

        self.btn_skip = QPushButton("⏭  Skip")
        self.btn_skip.setFixedHeight(34)
        self.btn_skip.setStyleSheet("color: #f0a040; border-color: #f0a040;")
        self.btn_skip.clicked.connect(self._tts.skip)

        self.btn_clear = QPushButton("🗑  Clear Queue")
        self.btn_clear.setFixedHeight(34)
        self.btn_clear.clicked.connect(self._tts.clear_queue)

        self.btn_reconnect = QPushButton("⟳  Reconnect")
        self.btn_reconnect.setFixedHeight(34)
        self.btn_reconnect.setStyleSheet("color: #7c6ff7; border-color: #3e3880;")

        ctrl.addWidget(self.btn_mute)
        ctrl.addWidget(self.btn_skip)
        ctrl.addWidget(self.btn_clear)
        ctrl.addStretch()
        ctrl.addWidget(self.btn_reconnect)
        root.addLayout(ctrl)

        q_header = QHBoxLayout()
        q_header.addWidget(label("Queue"))
        self.queue_badge = QLabel("0")
        self.queue_badge.setStyleSheet(
            "background: #23233d; color: #7878a8; border-radius: 8px; padding: 0 8px; font-size: 11px;"
        )
        q_header.addWidget(self.queue_badge)
        q_header.addStretch()
        root.addLayout(q_header)

        self.queue_list = QTextEdit()
        self.queue_list.setReadOnly(True)
        self.queue_list.setFixedHeight(110)
        self.queue_list.setPlaceholderText("Queue is empty")
        self.queue_list.setStyleSheet(
            "background: #1b1b30; border: 1px solid #25253f; border-radius: 8px;"
        )
        root.addWidget(self.queue_list)

        root.addWidget(label("Recent Events"))
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setPlaceholderText("Waiting for plagComms…")
        self.event_log.setStyleSheet(
            "background: #1b1b30; border: 1px solid #25253f; border-radius: 8px;"
        )
        root.addWidget(self.event_log)

    def _toggle_mute(self):
        muted = not self._tts.is_muted()
        self._tts.set_muted(muted)
        if muted:
            self.btn_mute.setText("🔇  Unmute")
            self.btn_mute.setStyleSheet(
                "color: #e05a5a; border-color: #e05a5a;"
                "QPushButton:hover { background: rgba(224,90,90,0.12); }"
            )
        else:
            self.btn_mute.setText("🔊  Mute")
            self.btn_mute.setStyleSheet(
                "QPushButton { color: #4caf7d; border-color: #4caf7d; }"
                "QPushButton:hover { background: rgba(76,175,125,0.12); }"
            )

    def _on_queue(self, items: list):
        self.queue_badge.setText(str(len(items)))
        if not items:
            self.queue_list.setPlainText("")
            return
        self.queue_list.setPlainText("\n".join(f"{i+1:2}. {t}" for i, t in enumerate(items)))

    def log_system(self, msg: str):
        from PyQt6.QtGui import QTextCursor
        now  = datetime.now().strftime("%H:%M:%S")
        cursor = self.event_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.event_log.setTextCursor(cursor)
        self.event_log.insertPlainText(f"[{now}] [system] {msg}\n")

    def log_event(self, evt: dict, spoken: bool, text: str):
        from PyQt6.QtGui import QTextCursor
        now   = datetime.now().strftime("%H:%M:%S")
        plat  = evt.get("platform", "?")
        user  = evt.get("username", "?")
        etype = evt.get("type", "?")
        msg   = evt.get("text", "")[:60]
        skip  = "" if spoken else " [skip]"
        line  = f"[{now}] [{plat}] {etype} — {user}{': ' + msg if msg else ''}{skip}\n"

        cursor = self.event_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.event_log.setTextCursor(cursor)
        self.event_log.insertPlainText(line)

        doc = self.event_log.document()
        while doc.blockCount() > 200:
            cursor = self.event_log.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()


# ── Events page ───────────────────────────────────────────────────────────────

class EventRow(QWidget):
    changed = pyqtSignal()

    def __init__(self, key: str, label_text: str, hint: str, cfg: dict, parent=None):
        super().__init__(parent)
        self.key = key
        self._build(key, label_text, hint, cfg)

    def _build(self, key, label_text, hint, cfg):
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(10)

        self.toggle = QCheckBox()
        self.toggle.setChecked(cfg.get("enabled", False))
        self.toggle.stateChanged.connect(self._on_change)
        row.addWidget(self.toggle)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_col.addWidget(label(label_text))
        if hint:
            name_col.addWidget(label(hint, muted=True))
        row.addLayout(name_col, 1)

        self.template_input = QLineEdit(cfg.get("template", DEFAULT_TEMPLATES.get(key, "")))
        self.template_input.setPlaceholderText("TTS template…")
        self.template_input.setFont(QFont("Consolas", 10))
        self.template_input.setEnabled(cfg.get("enabled", False))
        self.template_input.textChanged.connect(self._on_change)
        row.addWidget(self.template_input, 2)

        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(52)
        reset_btn.setStyleSheet("font-size: 10px; padding: 4px 6px;")
        reset_btn.clicked.connect(self._reset)
        row.addWidget(reset_btn)

        self.toggle.stateChanged.connect(
            lambda _: self.template_input.setEnabled(self.toggle.isChecked())
        )

    def _reset(self):
        self.template_input.setText(DEFAULT_TEMPLATES.get(self.key, ""))

    def _on_change(self):
        self.changed.emit()

    def get_cfg(self):
        return {"enabled": self.toggle.isChecked(), "template": self.template_input.text()}


class PlatformEventsPage(QWidget):
    def __init__(self, platform: str, settings: Settings, parent=None):
        super().__init__(parent)
        self._s = settings
        self._platform = platform
        self._rows: list[EventRow] = []
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        color = PLATFORM_COLOR.get(self._platform, "#7c6ff7")
        hdr = label(self._platform.title() + " Events", heading=True)
        hdr.setStyleSheet(f"color: {color}; background: transparent;")
        root.addWidget(hdr)

        token_hint = label(
            "Tokens: {username}  {platform}  {Platform}  {message}  "
            "{amount}  {months}  {streak}  {gift_name}  {tier}  {streamer}",
            muted=True, mono=True
        )
        token_hint.setWordWrap(True)
        root.addWidget(token_hint)

        grp = QGroupBox()
        grp.setStyleSheet(f"QGroupBox {{ border-top: 2px solid {color}; }}")
        glayout = QVBoxLayout(grp)
        glayout.setSpacing(0)
        glayout.setContentsMargins(0, 8, 0, 0)

        seen: set[str] = set()
        for key, section, lbl_text, hint in EVENT_DEFS:
            if section != self._platform or key in seen:
                continue
            seen.add(key)
            cfg = self._s.event_cfg(key)
            row = EventRow(key, lbl_text, hint, cfg)
            row.changed.connect(self._autosave)
            self._rows.append(row)
            if glayout.count():
                glayout.addWidget(hline())
            glayout.addWidget(row)

        root.addWidget(grp)
        root.addStretch()
        outer.addWidget(scrollable(container))

    def _autosave(self):
        seen: set[str] = set()
        for row in self._rows:
            if row.key not in seen:
                self._s.data["events"][row.key] = row.get_cfg()
                seen.add(row.key)
        self._s.save()


# ── Settings page ─────────────────────────────────────────────────────────────

class SettingsPage(QWidget):
    token_changed     = pyqtSignal()
    engine_changed    = pyqtSignal()
    platforms_changed = pyqtSignal()

    def __init__(self, settings: Settings, voices: list, parent=None):
        super().__init__(parent)
        self._s      = settings
        self._voices = voices
        self._build()

    def set_voices(self, voices: list):
        self._voices = voices
        self.voice_picker.set_voices(voices)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        root.addWidget(label("Settings", heading=True))

        # ── TTS Engines ───────────────────────────────────────────────────────
        grp_engine = QGroupBox()
        eg = QVBoxLayout(grp_engine)
        eg.setSpacing(8)
        eg.addWidget(section_title("TTS Engines"))

        sapi_hdr = QHBoxLayout()
        sapi_hdr.addWidget(QLabel("Windows SAPI"))
        sapi_hdr.addWidget(label("Always active — no setup required.", muted=True))
        sapi_hdr.addStretch()
        eg.addLayout(sapi_hdr)

        eg.addWidget(hline())

        eg.addWidget(QLabel("Google Cloud TTS"))
        g_row = QHBoxLayout()
        g_row.addWidget(QLabel("API Key:"))
        self.google_key = QLineEdit(self._s.get("google_api_key", ""))
        self.google_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_key.setPlaceholderText("AIza…")
        g_row.addWidget(self.google_key, 1)
        self.btn_test_key = QPushButton("Test")
        self.btn_test_key.setFixedWidth(52)
        self.btn_test_key.clicked.connect(self._test_google_key)
        g_row.addWidget(self.btn_test_key)
        eg.addLayout(g_row)
        eg.addWidget(label(
            "console.cloud.google.com → enable Text-to-Speech API → Credentials → API key.  "
            "Free tier: 4M standard chars/month.", muted=True
        ))

        eg.addWidget(hline())

        eg.addWidget(QLabel("ElevenLabs"))
        el_row = QHBoxLayout()
        el_row.addWidget(QLabel("API Key:"))
        self.elevenlabs_key = QLineEdit(self._s.get("elevenlabs_api_key", ""))
        self.elevenlabs_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.elevenlabs_key.setPlaceholderText("sk_…")
        el_row.addWidget(self.elevenlabs_key, 1)
        self.btn_test_el = QPushButton("Test")
        self.btn_test_el.setFixedWidth(52)
        self.btn_test_el.clicked.connect(self._test_elevenlabs_key)
        el_row.addWidget(self.btn_test_el)
        eg.addLayout(el_row)
        eg.addWidget(label("elevenlabs.io — free tier: 10 000 characters/month.", muted=True))

        eg.addWidget(hline())

        ref_row = QHBoxLayout()
        self.btn_refresh_voices = QPushButton("⟳  Refresh All Voices")
        self.btn_refresh_voices.clicked.connect(self._refresh_all_voices)
        ref_row.addWidget(self.btn_refresh_voices)
        ref_row.addWidget(label("Reload voice lists from all configured engines.", muted=True))
        ref_row.addStretch()
        eg.addLayout(ref_row)

        root.addWidget(grp_engine)

        # ── Voice & Playback ──────────────────────────────────────────────────
        grp_voice = QGroupBox()
        vg = QVBoxLayout(grp_voice)
        vg.addWidget(section_title("Voice & Playback"))

        voice_row = QHBoxLayout()
        voice_row.addWidget(QLabel("Default Voice:"))
        self.voice_picker = VoicePicker(self._voices, self._s.get("default_voice", ""))
        voice_row.addWidget(self.voice_picker, 1)
        self.btn_rand_voice = QPushButton("🎲 Rand.")
        self.btn_rand_voice.setFixedWidth(72)
        self.btn_rand_voice.setToolTip("Pick a random voice from the Voice Randomization Pool")
        self.btn_rand_voice.clicked.connect(self._randomize_default_voice)
        btn_test_voice = QPushButton("Test")
        btn_test_voice.setFixedWidth(52)
        btn_test_voice.clicked.connect(self._test_voice)
        voice_row.addWidget(self.btn_rand_voice)
        voice_row.addWidget(btn_test_voice)
        vg.addLayout(voice_row)

        def make_slider_row(text, attr, lo, hi, val, fmt_fn):
            row = QHBoxLayout()
            row.addWidget(QLabel(text))
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(lo, hi)
            sl.setValue(val)
            lbl = QLabel(fmt_fn(val))
            lbl.setFixedWidth(44)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sl.valueChanged.connect(lambda v: lbl.setText(fmt_fn(v)))
            row.addWidget(sl)
            row.addWidget(lbl)
            setattr(self, attr, sl)
            return row

        vg.addLayout(make_slider_row("Speed (wpm):", "slider_rate",   80, 350,
                                     self._s.get("default_rate",   175), lambda v: f"{v}"))
        vg.addLayout(make_slider_row("Volume:",       "slider_volume", 0,  100,
                                     self._s.get("default_volume", 100), lambda v: f"{v}%"))
        root.addWidget(grp_voice)

        # ── Platform Visibility ───────────────────────────────────────────────
        grp_vis = QGroupBox()
        pv = QVBoxLayout(grp_vis)
        pv.addWidget(section_title("Platform Visibility"))
        pv.addWidget(label(
            "Uncheck platforms you don't use to hide their sections "
            "from the Events and Advanced tabs.", muted=True
        ))
        hidden_now = set(self._s.get("hidden_platforms", []))
        self.plat_checks: dict[str, QCheckBox] = {}
        for plat, plat_name in [("twitch","Twitch"),("tiktok","TikTok"),
                                 ("youtube","YouTube"),("kick","Kick")]:
            cb = QCheckBox(f"Show {plat_name}")
            cb.setChecked(plat not in hidden_now)
            self.plat_checks[plat] = cb
            pv.addWidget(cb)
        root.addWidget(grp_vis)

        # ── Voice Pool ────────────────────────────────────────────────────────
        grp_pool = QGroupBox()
        vpool = QVBoxLayout(grp_pool)
        vpool.addWidget(section_title("Voice Randomization Pool"))
        vpool.addWidget(label(
            "Limit 🎲 Rand. to specific voices. One exact voice name per line. "
            "Leave blank to use all voices.", muted=True
        ))
        self.voice_pool_edit = QTextEdit()
        self.voice_pool_edit.setFixedHeight(80)
        self.voice_pool_edit.setPlainText("\n".join(self._s.get("voice_pool", [])))
        self.voice_pool_edit.setPlaceholderText(
            "Microsoft Jenny Online (Natural) - English (United States)"
        )
        vpool.addWidget(self.voice_pool_edit)
        root.addWidget(grp_pool)

        # ── Word Filter ───────────────────────────────────────────────────────
        grp_filter = QGroupBox()
        fg = QVBoxLayout(grp_filter)
        fg.addWidget(section_title("Word Filter"))
        fg.addWidget(label(
            "Words or phrases listed here are silently removed from spoken text. "
            "One per line.", muted=True
        ))
        self.word_filter_edit = QTextEdit()
        self.word_filter_edit.setFixedHeight(90)
        self.word_filter_edit.setPlainText("\n".join(self._s.get("word_filter", [])))
        self.word_filter_edit.setPlaceholderText("badword\nanother phrase")
        fg.addWidget(self.word_filter_edit)
        root.addWidget(grp_filter)

        # ── Connection ────────────────────────────────────────────────────────
        grp_conn = QGroupBox()
        cg = QVBoxLayout(grp_conn)
        cg.addWidget(section_title("Connection"))

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("plagComms Port:"))
        self.ws_port = QSpinBox()
        self.ws_port.setRange(1024, 65535)
        self.ws_port.setValue(self._s.get("ws_port", 54473))
        self.ws_port.setFixedWidth(90)
        port_row.addWidget(self.ws_port)
        port_row.addWidget(label("default 54473", muted=True))
        port_row.addStretch()
        cg.addLayout(port_row)

        cg.addWidget(label("Bearer Token (leave blank if not required in plagComms):", muted=True))
        self.ws_token = QLineEdit(self._s.get("ws_token", ""))
        self.ws_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.ws_token.setPlaceholderText("plagComms → Settings → Add-ons → Token")
        cg.addWidget(self.ws_token)
        root.addWidget(grp_conn)

        # Save
        save_row = QHBoxLayout()
        btn_save = primary_btn("Save Settings")
        btn_save.clicked.connect(self._save)
        self.save_lbl = QLabel("")
        self.save_lbl.setStyleSheet("color: #4caf7d;")
        save_row.addWidget(btn_save)
        save_row.addWidget(self.save_lbl)
        save_row.addStretch()
        root.addLayout(save_row)
        root.addStretch()

        outer.addWidget(scrollable(container))

    def _randomize_default_voice(self):
        import random
        pool_names = [l.strip() for l in self.voice_pool_edit.toPlainText().splitlines() if l.strip()]
        candidates = ([vid for name, vid in self._voices if name in pool_names]
                      if pool_names else [vid for _, vid in self._voices])
        if not candidates:
            return
        self.voice_picker.set_voice_id(random.choice(candidates))

    def _test_voice(self):
        vid = self.voice_picker.voice_id()
        win = self.window()
        if hasattr(win, "tts"):
            win.tts.enqueue("This is plagTalk. Voice check!", vid)

    def _test_google_key(self):
        ok, msg = TTSEngine.test_google_key(self.google_key.text().strip())
        QMessageBox.information(self, "Google TTS Key", msg)

    def _test_elevenlabs_key(self):
        ok, msg = TTSEngine.test_elevenlabs_key(self.elevenlabs_key.text().strip())
        QMessageBox.information(self, "ElevenLabs Key", msg)

    def _refresh_all_voices(self):
        win = self.window()
        if hasattr(win, "tts"):
            win.tts.refresh_voices(
                self.google_key.text().strip(),
                self.elevenlabs_key.text().strip()
            )

    def _save(self):
        prev_token  = self._s.get("ws_token", "")
        prev_port   = self._s.get("ws_port", 54473)
        prev_hidden = set(self._s.get("hidden_platforms", []))

        self._s.set("google_api_key",     self.google_key.text().strip())
        self._s.set("elevenlabs_api_key", self.elevenlabs_key.text().strip())
        self._s.set("default_voice",      self.voice_picker.voice_id())
        self._s.set("default_rate",       self.slider_rate.value())
        self._s.set("default_volume",     self.slider_volume.value())
        self._s.set("voice_pool",         [l.strip() for l in self.voice_pool_edit.toPlainText().splitlines() if l.strip()])
        self._s.set("word_filter",        [w.strip() for w in self.word_filter_edit.toPlainText().splitlines() if w.strip()])

        new_token = self.ws_token.text().strip()
        new_port  = self.ws_port.value()
        self._s.set("ws_token", new_token)
        self._s.set("ws_port",  new_port)

        new_hidden = [p for p, cb in self.plat_checks.items() if not cb.isChecked()]
        self._s.set("hidden_platforms", new_hidden)

        self.save_lbl.setText("✓ Saved")
        QTimer.singleShot(2500, lambda: self.save_lbl.setText(""))

        if new_token != prev_token or new_port != prev_port:
            self.token_changed.emit()
        self.engine_changed.emit()
        self._refresh_all_voices()
        if set(new_hidden) != prev_hidden:
            self.platforms_changed.emit()


# ── Advanced page ─────────────────────────────────────────────────────────────

class AdvancedPage(QWidget):
    def __init__(self, settings: Settings, voices: list, parent=None):
        super().__init__(parent)
        self._s      = settings
        self._voices = voices
        self._plat_voice_rows: dict[str, QWidget] = {}
        self._build()

    def set_voices(self, voices: list):
        self._voices = voices
        self._repopulate_voices()

    def _repopulate_voices(self):
        for picker in [self.voice_twitch, self.voice_tiktok, self.voice_youtube, self.voice_kick]:
            picker.set_voices(self._voices)
        # per_user_voice is a plain QComboBox — repopulate preserving selection
        cur = self.per_user_voice.currentData() or ""
        _populate_voice_combo(self.per_user_voice, self._voices, cur)

    def apply_visibility(self):
        hidden = set(self._s.get("hidden_platforms", []))
        for platform, widget in self._plat_voice_rows.items():
            widget.setVisible(platform not in hidden)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        root.addWidget(label("Advanced", heading=True))
        adv = self._s.data.get("advanced", {})
        thr = self._s.data.get("thresholds", {})

        # ── Voice per platform ────────────────────────────────────────────────
        grp_plat = QGroupBox()
        pg = QVBoxLayout(grp_plat)
        pg.addWidget(section_title("Voice per Platform"))
        pg.addWidget(label("Override the default voice for events from a specific platform.", muted=True))

        def plat_row(text, attr, key, platform_name=""):
            row_widget = QWidget()
            row_widget.setContentsMargins(0, 0, 0, 0)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.addWidget(QLabel(text))
            vp = VoicePicker(self._voices, adv.get(key, ""))
            setattr(self, attr, vp)
            row.addWidget(vp, 1)
            pg.addWidget(row_widget)
            if platform_name:
                self._plat_voice_rows[platform_name] = row_widget

        plat_row("Twitch:",  "voice_twitch",  "voice_twitch",  "twitch")
        plat_row("TikTok:",  "voice_tiktok",  "voice_tiktok",  "tiktok")
        plat_row("YouTube:", "voice_youtube", "voice_youtube", "youtube")
        plat_row("Kick:",    "voice_kick",    "voice_kick",    "kick")

        rand_all_row = QHBoxLayout()
        self.btn_rand_all = QPushButton("🎲  Randomize All Platform Voices")
        self.btn_rand_all.clicked.connect(self._randomize_all_voices)
        rand_all_row.addWidget(self.btn_rand_all)
        rand_all_row.addStretch()
        pg.addLayout(rand_all_row)
        root.addWidget(grp_plat)
        self.apply_visibility()

        # ── Thresholds ────────────────────────────────────────────────────────
        grp_thr = QGroupBox()
        tg = QVBoxLayout(grp_thr)
        tg.addWidget(section_title("Thresholds"))
        tg.addWidget(label("Minimum values required before an event is spoken. 0 = read everything.", muted=True))

        def thr_row(text, attr, key):
            row = QHBoxLayout()
            row.addWidget(QLabel(text))
            sb = QSpinBox()
            sb.setRange(0, 999999)
            sb.setValue(thr.get(key, 0))
            sb.setFixedWidth(90)
            setattr(self, attr, sb)
            row.addWidget(sb)
            row.addStretch()
            tg.addLayout(row)

        thr_row("Min Cheer Bits:",        "thr_cheer",      "min_cheer_bits")
        thr_row("Min Raid Viewers:",      "thr_raid",       "min_raid_viewers")
        thr_row("Min TikTok Likes:",      "thr_likes",      "min_tiktok_likes")
        thr_row("Min TikTok Gift Coins:", "thr_gift_coins", "min_tiktok_gift_coins")
        root.addWidget(grp_thr)

        # ── Chat behaviour ────────────────────────────────────────────────────
        grp_chat = QGroupBox()
        cg = QVBoxLayout(grp_chat)
        cg.addWidget(section_title("Chat Behaviour"))

        def spin_row(text, attr, key, suffix="", lo=0, hi=9999):
            row = QHBoxLayout()
            row.addWidget(QLabel(text))
            sb = QSpinBox()
            sb.setRange(lo, hi)
            sb.setValue(adv.get(key, 0))
            sb.setFixedWidth(80)
            setattr(self, attr, sb)
            row.addWidget(sb)
            if suffix: row.addWidget(QLabel(suffix))
            row.addStretch()
            cg.addLayout(row)

        spin_row("Max message length:", "spin_maxlen",   "max_message_length",    "chars (0=off)", 0, 2000)
        spin_row("User cooldown:",      "spin_cooldown", "chat_cooldown_seconds", "seconds (0=off)", 0, 3600)

        def chk(text, attr, key, default=False):
            cb = QCheckBox(text)
            cb.setChecked(adv.get(key, default))
            setattr(self, attr, cb)
            cg.addWidget(cb)

        chk("Read usernames in chat",               "chk_usernames",    "read_usernames",        True)
        chk("Include platform name in reads",       "chk_platform_name","include_platform_name", False)
        chk("Read room relay events (multi-stream)","chk_room",         "read_from_room",        False)

        cg.addWidget(hline())
        self.chk_cmd_mode = QCheckBox("Require command prefix for chat TTS  (e.g. !tts message)")
        self.chk_cmd_mode.setChecked(adv.get("chat_command_mode", False))
        cg.addWidget(self.chk_cmd_mode)

        cmd_row = QHBoxLayout()
        cmd_row.addWidget(QLabel("Command:"))
        self.cmd_input = QLineEdit(adv.get("chat_command", "!tts"))
        self.cmd_input.setPlaceholderText("!tts")
        self.cmd_input.setFixedWidth(100)
        self.cmd_input.setEnabled(self.chk_cmd_mode.isChecked())
        self.chk_cmd_mode.stateChanged.connect(
            lambda: self.cmd_input.setEnabled(self.chk_cmd_mode.isChecked())
        )
        cmd_row.addWidget(self.cmd_input)
        cmd_row.addWidget(label("Only chat messages starting with this prefix will be spoken.", muted=True))
        cmd_row.addStretch()
        cg.addLayout(cmd_row)
        root.addWidget(grp_chat)

        # ── User blocklist ────────────────────────────────────────────────────
        grp_block = QGroupBox()
        bg = QVBoxLayout(grp_block)
        bg.addWidget(section_title("User Blocklist"))
        bg.addWidget(label("One username per line. Events from these users are never spoken.", muted=True))
        self.blocklist_edit = QTextEdit()
        self.blocklist_edit.setFixedHeight(80)
        self.blocklist_edit.setPlainText("\n".join(adv.get("user_blocklist", [])))
        bg.addWidget(self.blocklist_edit)
        root.addWidget(grp_block)

        # ── User whitelist ────────────────────────────────────────────────────
        grp_white = QGroupBox()
        wg = QVBoxLayout(grp_white)
        wg.addWidget(section_title("User Whitelist (Chat Only)"))
        wg.addWidget(label(
            "When non-empty, ONLY these users can trigger chat TTS. "
            "One username per line. Follows / subs / raids are unaffected.", muted=True
        ))
        self.whitelist_edit = QTextEdit()
        self.whitelist_edit.setFixedHeight(80)
        self.whitelist_edit.setPlainText("\n".join(adv.get("user_whitelist", [])))
        self.whitelist_edit.setPlaceholderText("Leave blank to allow everyone")
        wg.addWidget(self.whitelist_edit)
        root.addWidget(grp_white)

        # ── Voice per user ────────────────────────────────────────────────────
        grp_user = QGroupBox()
        ug = QVBoxLayout(grp_user)
        ug.addWidget(section_title("Voice per Username"))
        ug.addWidget(label("Assign a specific voice when a viewer speaks. Click a row to select it.", muted=True))

        self.per_user_list = QListWidget()
        self.per_user_list.setFixedHeight(110)
        self.per_user_list.setStyleSheet(
            "QListWidget { background: #0e0e1d; border: 1px solid #25253f; border-radius: 6px; }"
            "QListWidget::item { padding: 4px 8px; color: #ddddf5; }"
            "QListWidget::item:selected { background: #3e3880; color: #ddddf5; }"
        )
        self.per_user_list.itemClicked.connect(self._on_per_user_select)
        self._refresh_per_user_list()
        ug.addWidget(self.per_user_list)

        add_row = QHBoxLayout()
        self.per_user_name = QLineEdit()
        self.per_user_name.setPlaceholderText("Username")
        self.per_user_voice = QComboBox()
        _populate_voice_combo(self.per_user_voice, self._voices, "")
        btn_add = primary_btn("Add")
        btn_add.clicked.connect(self._add_per_user)
        btn_rem = QPushButton("Remove")
        btn_rem.setProperty("danger", True)
        btn_rem.clicked.connect(self._remove_per_user)
        add_row.addWidget(self.per_user_name, 1)
        add_row.addWidget(self.per_user_voice, 2)
        add_row.addWidget(btn_add)
        add_row.addWidget(btn_rem)
        ug.addLayout(add_row)
        root.addWidget(grp_user)

        # Save
        save_row = QHBoxLayout()
        btn_save = primary_btn("Save Advanced")
        btn_save.clicked.connect(self._save)
        self.save_lbl = QLabel("")
        self.save_lbl.setStyleSheet("color: #4caf7d;")
        save_row.addWidget(btn_save)
        save_row.addWidget(self.save_lbl)
        save_row.addStretch()
        root.addLayout(save_row)
        root.addStretch()

        outer.addWidget(scrollable(container))

    def _refresh_per_user_list(self):
        pu = self._s.data.get("advanced", {}).get("voice_per_user", {})
        self.per_user_list.clear()
        for u, v in pu.items():
            self.per_user_list.addItem(f"{u}  →  {v}")

    def _on_per_user_select(self, item: QListWidgetItem):
        text = item.text()
        if "  →  " in text:
            self.per_user_name.setText(text.split("  →  ")[0].strip())

    def _add_per_user(self):
        uname = self.per_user_name.text().strip()
        voice = self.per_user_voice.currentText()
        if not uname or voice.startswith("—") or voice.startswith("──"):
            return
        adv = self._s.data.setdefault("advanced", {})
        adv.setdefault("voice_per_user", {})[uname] = voice
        self._s.save()
        self._refresh_per_user_list()
        self.per_user_name.clear()

    def _remove_per_user(self):
        uname = self.per_user_name.text().strip()
        if not uname:
            sel = self.per_user_list.currentItem()
            if sel and "  →  " in sel.text():
                uname = sel.text().split("  →  ")[0].strip()
        if not uname:
            return
        pu = self._s.data.get("advanced", {}).get("voice_per_user", {})
        if uname in pu:
            del pu[uname]
            self._s.save()
            self._refresh_per_user_list()
            self.per_user_name.clear()

    def _randomize_all_voices(self):
        import random
        pool_names = [l.strip() for l in self._s.get("voice_pool", [])]
        candidates = ([vid for name, vid in self._voices if name in pool_names]
                      if pool_names else [vid for _, vid in self._voices])
        if not candidates:
            return
        for picker in [self.voice_twitch, self.voice_tiktok, self.voice_youtube, self.voice_kick]:
            if picker.isVisible():
                picker.set_voice_id(random.choice(candidates))

    def _save(self):
        adv = self._s.data.setdefault("advanced", {})
        thr = self._s.data.setdefault("thresholds", {})

        adv["voice_twitch"]           = self.voice_twitch.voice_id()
        adv["voice_tiktok"]           = self.voice_tiktok.voice_id()
        adv["voice_youtube"]          = self.voice_youtube.voice_id()
        adv["voice_kick"]             = self.voice_kick.voice_id()
        thr["min_cheer_bits"]         = self.thr_cheer.value()
        thr["min_raid_viewers"]       = self.thr_raid.value()
        thr["min_tiktok_likes"]       = self.thr_likes.value()
        thr["min_tiktok_gift_coins"]  = self.thr_gift_coins.value()
        adv["max_message_length"]     = self.spin_maxlen.value()
        adv["chat_cooldown_seconds"]  = self.spin_cooldown.value()
        adv["read_usernames"]         = self.chk_usernames.isChecked()
        adv["include_platform_name"]  = self.chk_platform_name.isChecked()
        adv["read_from_room"]         = self.chk_room.isChecked()
        adv["chat_command_mode"]      = self.chk_cmd_mode.isChecked()
        adv["chat_command"]           = self.cmd_input.text().strip() or "!tts"
        adv["user_blocklist"]         = [l.strip() for l in self.blocklist_edit.toPlainText().splitlines() if l.strip()]
        adv["user_whitelist"]         = [l.strip() for l in self.whitelist_edit.toPlainText().splitlines() if l.strip()]

        self._s.save()
        self.save_lbl.setText("✓ Saved")
        QTimer.singleShot(2500, lambda: self.save_lbl.setText(""))


# ═════════════════════════════════════════════════════════════════════════════
# Main Window
# ═════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.voices   = []

        self._build_tts()
        self._build_ui()
        self._build_ws()
        self._build_tray()
        self._build_updater()

        self.setWindowTitle(f"plagTalk v{APP_VERSION}")
        self.setWindowIcon(QIcon(_asset_path("icon.png")))
        self.resize(960, 680)
        self.setMinimumSize(820, 560)

    # ── TTS ───────────────────────────────────────────────────────────────────

    def _build_tts(self):
        self.tts = TTSEngine(self.settings)
        self.tts.voices_ready.connect(self._on_voices_ready)
        self.tts.start()

    def _on_voices_ready(self, voice_list: list):
        self.voices = voice_list
        if hasattr(self, "page_settings"):
            self.page_settings.set_voices(voice_list)
        if hasattr(self, "page_advanced"):
            self.page_advanced.set_voices(voice_list)

    # ── WebSocket ─────────────────────────────────────────────────────────────

    def _build_ws(self):
        self.ws = WsClient(self.settings)
        self.ws.event_received.connect(self._on_event)
        self.ws.status_changed.connect(self._on_ws_status)
        self.ws.start()

        self.event_handler = EventHandler(
            self.settings, self.tts,
            on_log=self.page_dashboard.log_event
        )
        self.page_dashboard.btn_reconnect.clicked.connect(self.ws.reconnect)

    def _on_event(self, evt: dict):
        self.event_handler.handle(evt)

    @staticmethod
    def _short_ws_error(err: str) -> str:
        if not err:
            return ""
        low = err.lower()
        if "10061" in err or "refused" in low:     return "plagComms not running or wrong port"
        if "10060" in err or "timed out" in low:   return "Connection timed out"
        if "401" in err:                            return "Auth failed — check bearer token"
        if "403" in err:                            return "Auth rejected (403)"
        return err[:80]

    def _on_ws_status(self, status: dict):
        connected  = status.get("connected", False)
        connecting = status.get("connecting", False)
        retry_in   = status.get("retry_in")
        error      = status.get("error", "")
        url        = status.get("url", "")

        _ss = lambda c: f"color: {c}; font-size: 11px; background: transparent;"
        if connected:
            self.status_label.setText("● Connected")
            self.status_label.setStyleSheet(_ss("#4caf7d"))
            self.page_dashboard.log_system(f"Connected to plagComms ({url})")
        elif connecting:
            self.status_label.setText("● Connecting…")
            self.status_label.setStyleSheet(_ss("#f0a040"))
            if url:
                self.page_dashboard.log_system(f"Connecting to {url}…")
        elif retry_in:
            self.status_label.setText(f"● Retry in {retry_in}s")
            self.status_label.setStyleSheet(_ss("#e05a5a"))
            err_msg = self._short_ws_error(error)
            self.page_dashboard.log_system(
                f"Connection failed{': ' + err_msg if err_msg else ''} — retry in {retry_in}s"
            )
        else:
            self.status_label.setText("● Disconnected")
            self.status_label.setStyleSheet(_ss("#e05a5a"))

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_row = QHBoxLayout(central)
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(0)

        self.sidebar = SidebarNav()
        self.sidebar.page_changed.connect(self._on_nav)
        self.sidebar.about_requested.connect(lambda: AboutDialog(self).exec())
        self.status_label = self.sidebar.status_label
        main_row.addWidget(self.sidebar)

        # Stack: 0=Dashboard 1-4=Platforms 5=Settings 6=Advanced 7=Updates
        self.stack = QStackedWidget()

        self.page_dashboard = DashboardPage(self.tts)
        self.page_twitch    = PlatformEventsPage("twitch",  self.settings)
        self.page_tiktok    = PlatformEventsPage("tiktok",  self.settings)
        self.page_youtube   = PlatformEventsPage("youtube", self.settings)
        self.page_kick      = PlatformEventsPage("kick",    self.settings)
        self.page_settings  = SettingsPage(self.settings, self.voices)
        self.page_advanced  = AdvancedPage(self.settings, self.voices)
        self.page_updates   = UpdatesPage()

        for page in [self.page_dashboard,
                     self.page_twitch, self.page_tiktok,
                     self.page_youtube, self.page_kick,
                     self.page_settings, self.page_advanced,
                     self.page_updates]:
            self.stack.addWidget(page)

        self.page_settings.token_changed.connect(lambda: self.ws.reconnect())
        self.page_settings.engine_changed.connect(lambda: None)
        self.page_settings.platforms_changed.connect(self._apply_platform_visibility)

        main_row.addWidget(self.stack, 1)
        self._apply_platform_visibility()

    def _apply_platform_visibility(self):
        hidden = set(self.settings.get("hidden_platforms", []))
        for plat in ["twitch", "tiktok", "youtube", "kick"]:
            self.sidebar.set_platform_visible(plat, plat not in hidden)
        self.page_advanced.apply_visibility()

    def _on_nav(self, idx: int):
        self.stack.setCurrentIndex(idx)

    # ── Updater ───────────────────────────────────────────────────────────────

    def _build_updater(self):
        self.page_updates.show_local_changelog()
        self._update_found = False

        self._updater = Updater(self)
        self._updater.update_available.connect(self._on_update_available)
        self._updater.no_update.connect(self.page_updates.on_no_update)
        self._updater.check_failed.connect(self.page_updates.on_check_failed)
        self.page_updates.check_requested.connect(self._updater.check)

        QTimer.singleShot(3000, self._updater.check)
        self._poll = QTimer(self)
        self._poll.setInterval(60_000)
        self._poll.timeout.connect(lambda: not self._update_found and self._updater.check())
        self._poll.start()

    def _on_update_available(self, version: str, download_url: str, asset_url: str, notes: list):
        self._update_found = True
        self._poll.stop()
        self.page_updates.on_update_available(version, download_url, asset_url, notes)
        self.sidebar.set_update_badge(True)
        self.tray.showMessage(
            "plagTalk Update Available",
            f"v{version} is ready to install — click Updates in the sidebar.",
            QSystemTrayIcon.MessageIcon.Information, 5000
        )

    # ── Tray ──────────────────────────────────────────────────────────────────

    def _build_tray(self):
        self.tray = QSystemTrayIcon(QIcon(_asset_path("icon.png")), self)
        self.tray.setToolTip(f"plagTalk v{APP_VERSION} — click to open")
        menu = QMenu()
        menu.addAction(QAction("Open plagTalk", self, triggered=self.show))
        menu.addSeparator()
        menu.addAction(QAction("Quit", self, triggered=self._quit))
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.show()
            if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()

    def _quit(self):
        self.tts.shutdown()
        self.ws.stop()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "plagTalk is still running",
            "Minimized to the system tray. Right-click the tray icon to quit.",
            QSystemTrayIcon.MessageIcon.Information, 3000
        )


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("plagTalk")
    app.setStyle("Fusion")
    app.setStyleSheet(_make_stylesheet())

    # Block accidental scroll-wheel changes on unfocused spinboxes / combos
    app._wheel_guard = WheelBlocker(app)
    app.installEventFilter(app._wheel_guard)

    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window,     QColor("#12121f"))
    pal.setColor(QPalette.ColorRole.WindowText, QColor("#ddddf5"))
    pal.setColor(QPalette.ColorRole.Base,       QColor("#0e0e1d"))
    pal.setColor(QPalette.ColorRole.Text,       QColor("#ddddf5"))
    pal.setColor(QPalette.ColorRole.Button,     QColor("#1b1b30"))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor("#ddddf5"))
    pal.setColor(QPalette.ColorRole.Highlight,  QColor("#7c6ff7"))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
