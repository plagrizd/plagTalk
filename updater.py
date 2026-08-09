"""
plagTalk — Update checker + one-click installer
Follows the plagComms self-update pattern.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.request

from PyQt6.QtCore import QObject, pyqtSignal

APP_VERSION = "0.1.0"
VERSION_URL = "https://raw.githubusercontent.com/plagrizd/plagTalk/main/version.json"


def _parse_version(v: str) -> tuple:
    return tuple(int(n) for n in re.findall(r"\d+", v))


def _is_newer(remote: str, local: str) -> bool:
    try:
        return _parse_version(remote) > _parse_version(local)
    except Exception:
        return False


class Updater(QObject):
    """Non-blocking version checker. Fetches version.json on a daemon thread."""
    update_available = pyqtSignal(str, str, str, list)  # version, download_url, asset_url, notes
    no_update        = pyqtSignal()
    check_failed     = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checking = False

    def check(self):
        if self._checking:
            return
        self._checking = True
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            req = urllib.request.Request(
                VERSION_URL,
                headers={"User-Agent": f"plagTalk/{APP_VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())

            remote = data.get("version", "")
            if _is_newer(remote, APP_VERSION):
                notes, asset_url = [], ""
                for entry in data.get("changelog", []):
                    if _is_newer(entry.get("version", ""), APP_VERSION):
                        notes.extend(entry.get("notes", []))
                        asset_url = asset_url or entry.get("asset_url", "")
                self.update_available.emit(remote, data.get("download_url", ""), asset_url, notes)
            else:
                self.no_update.emit()
        except Exception:
            self.check_failed.emit()
        finally:
            self._checking = False


class Installer(QObject):
    """Downloads new exe, writes a helper bat, and exits so the bat can hot-swap."""
    progress = pyqtSignal(int)
    done     = pyqtSignal()
    error    = pyqtSignal(str)

    def __init__(self, asset_url: str, parent=None):
        super().__init__(parent)
        self._asset_url = asset_url

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            tmp_exe     = os.path.join(tempfile.gettempdir(), "plagtalk_update.exe")
            current_exe = os.path.abspath(sys.executable)

            def _prog(count, block_size, total):
                if total > 0:
                    self.progress.emit(min(100, int(count * block_size * 100 / total)))

            urllib.request.urlretrieve(self._asset_url, tmp_exe, _prog)
            self.progress.emit(100)

            with open(tmp_exe, "rb") as f:
                if f.read(2) != b"MZ":
                    self.error.emit("Download isn't a valid exe — AV may have blocked it.")
                    return

            bat = os.path.join(tempfile.gettempdir(), "plagtalk_updater.bat")
            with open(bat, "w") as f:
                f.write("\r\n".join([
                    "@echo off",
                    "ping -n 5 127.0.0.1 >nul",
                    "set tries=0",
                    ":loop",
                    "set /a tries+=1",
                    f'copy /y "{tmp_exe}" "{current_exe}" >nul 2>&1',
                    "if not errorlevel 1 goto ok",
                    "if %tries% geq 12 goto fail",
                    "ping -n 2 127.0.0.1 >nul",
                    "goto loop",
                    ":fail",
                    "echo Update failed. Try running as admin or check antivirus.",
                    "pause",
                    "exit /b 1",
                    ":ok",
                    f'del "{tmp_exe}" 2>nul',
                    f'start "" "{current_exe}"',
                    'del "%~f0"',
                ]))

            # CREATE_NEW_CONSOLE only — do NOT combine with DETACHED_PROCESS (undefined on Windows)
            subprocess.Popen(
                ["cmd.exe", "/c", bat],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                close_fds=True,
            )
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))
