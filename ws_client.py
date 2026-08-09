"""
plagTalk — WebSocket client
Runs in a QThread; emits signals for events and status changes.
Handles exponential-backoff reconnect automatically.
"""

import asyncio
import json
from PyQt6.QtCore import QThread, pyqtSignal

BACKOFF = [1, 2, 4, 8, 15, 30]   # seconds


class WsClient(QThread):
    event_received = pyqtSignal(dict)   # parsed event data dict
    status_changed = pyqtSignal(dict)   # {connected, connecting, retry_in?, error?}

    def __init__(self, settings):
        super().__init__()
        self._settings   = settings
        self._attempt    = 0
        self._loop       = None
        self._ws         = None
        self._running    = True
        self._last_error = ""

    def _url(self) -> str:
        port = self._settings.get("ws_port", 54473)
        return f"ws://localhost:{port}/addons/ws"

    # ── QThread entry ─────────────────────────────────────────────────────────

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        finally:
            self._loop.close()

    # ── Public API (thread-safe) ───────────────────────────────────────────────

    def reconnect(self) -> None:
        """Force an immediate reconnect (e.g. after token/port change)."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._schedule_reconnect_now)

    def stop(self) -> None:
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

    # ── Async internals ───────────────────────────────────────────────────────

    async def _main(self) -> None:
        while self._running:
            self._last_error = ""
            await self._connect_once()
            if not self._running:
                break
            delay = BACKOFF[min(self._attempt, len(BACKOFF) - 1)]
            self._attempt += 1
            self.status_changed.emit({
                "connected": False, "connecting": False,
                "retry_in": delay, "error": self._last_error,
            })
            await asyncio.sleep(delay)

    async def _connect_once(self) -> None:
        import websockets

        url     = self._url()
        token   = self._settings.get("ws_token", "")
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        self.status_changed.emit({"connected": False, "connecting": True, "url": url})

        try:
            async with websockets.connect(url, additional_headers=headers) as ws:
                self._ws      = ws
                self._attempt = 0
                self.status_changed.emit({"connected": True, "connecting": False, "url": url})
                async for raw in ws:
                    if not self._running:
                        break
                    try:
                        frame = json.loads(raw)
                    except Exception:
                        continue
                    if frame.get("type") != "event":
                        continue
                    self.event_received.emit(frame["data"])
        except Exception as exc:
            self._last_error = str(exc)
        finally:
            self._ws = None
            if self._running:
                self.status_changed.emit({"connected": False, "connecting": False})

    def _schedule_reconnect_now(self) -> None:
        self._attempt = 0
        if self._ws:
            asyncio.ensure_future(self._ws.close())
