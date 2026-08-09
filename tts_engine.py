"""
plagTalk — TTS Engine
QThread speech queue backing SAPI, Google Cloud TTS, and ElevenLabs.

Voice ID scheme:
  sapi:<description or registry ID>  — Windows SAPI (omitting prefix also routes to SAPI)
  google:<voice-name>                — Google Cloud TTS  e.g. google:en-US-Neural2-A
  elevenlabs:<voice-id>              — ElevenLabs API    e.g. elevenlabs:21m00Tcm4TlvDq8ikWAM

The engine for each utterance is determined by the voice_id prefix — not a global setting.
All configured engines are available simultaneously; the voice selection drives routing.
"""

import os
import queue
import struct
import tempfile
import threading

import requests
import base64

from PyQt6.QtCore import QThread, pyqtSignal


# ── Rate helpers ──────────────────────────────────────────────────────────────

def _sapi_rate(wpm: int) -> int:
    """Map words-per-minute (50–400) → SAPI rate (-10 to 10). 175 wpm = 0."""
    return max(-10, min(10, round((wpm - 175) / 17.5)))


def _google_rate(wpm: int) -> float:
    """Map wpm → Google speakingRate (0.25–4.0). 175 wpm = 1.0."""
    return max(0.25, min(4.0, wpm / 175.0))


def _pcm_wav_header(data: bytes, sample_rate: int = 22050, channels: int = 1,
                    bits: int = 16) -> bytes:
    """Build a minimal RIFF/WAV header for raw PCM data."""
    data_size = len(data)
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE", b"fmt ", 16,
        1, channels, sample_rate,
        sample_rate * channels * bits // 8,
        channels * bits // 8, bits,
        b"data", data_size,
    )


def _parse_voice_id(voice_id: str) -> tuple[str, str]:
    """Return (engine, id). IDs with no recognized prefix default to 'sapi'."""
    if voice_id.startswith("google:"):
        return "google", voice_id[7:]
    if voice_id.startswith("elevenlabs:"):
        return "elevenlabs", voice_id[11:]
    return "sapi", voice_id


def _google_lang(voice_name: str) -> str:
    """Extract BCP-47 language code from a Google voice name."""
    parts = voice_name.split("-")
    if len(parts) >= 2 and len(parts[0]) == 2:
        return f"{parts[0]}-{parts[1]}"
    return "en-US"


# ── Engine ────────────────────────────────────────────────────────────────────

class TTSEngine(QThread):
    voices_ready     = pyqtSignal(list)   # [(display_name, voice_id), ...]
    queue_updated    = pyqtSignal(list)   # [text, ...] of pending items
    speaking_started = pyqtSignal(str)    # text now being spoken

    def __init__(self, settings):
        super().__init__()
        self._settings = settings
        self._queue    = queue.Queue()
        self._pending  = []
        self._lock     = threading.Lock()
        self._muted    = False
        self._running  = True

        self._speaker  = None    # win32com SAPI.SpVoice (set in run())
        self._sapi_voices: list[tuple[str, str]] = []
        self._google_voices: list[tuple[str, str]] = []
        self._el_voices: list[tuple[str, str]] = []

    # ── QThread entry ─────────────────────────────────────────────────────────

    def run(self) -> None:
        try:
            import pythoncom
            pythoncom.CoInitialize()
            _com = True
        except Exception:
            _com = False

        try:
            self._init_speaker()
            while self._running:
                try:
                    item = self._queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if item is None:
                    break
                self._speak_item(item)
        finally:
            if _com:
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _init_speaker(self) -> None:
        """Init SAPI (synchronous) then kick off remote voice fetches in background."""
        try:
            from win32com.client import Dispatch
            self._speaker = Dispatch("SAPI.SpVoice")
            col = self._speaker.GetVoices()
            self._sapi_voices = [
                (col.Item(i).GetDescription(), col.Item(i).Id)
                for i in range(col.Count)
            ]
        except Exception as e:
            print(f"[TTS] win32com init failed: {e} — trying pyttsx3")
            try:
                import pyttsx3
                self._pyttsx3_engine = pyttsx3.init()
                raw = self._pyttsx3_engine.getProperty("voices") or []
                self._sapi_voices = [(v.name, v.id) for v in raw]
            except Exception as e2:
                print(f"[TTS] pyttsx3 also failed: {e2}")
                self._sapi_voices = []

        # Emit SAPI voices immediately so the UI isn't waiting
        self._emit_all_voices()

        # Fetch remote voices in background (non-blocking)
        gkey = self._settings.get("google_api_key", "")
        ekey = self._settings.get("elevenlabs_api_key", "")
        if gkey or ekey:
            threading.Thread(
                target=self._fetch_remote_voices,
                args=(gkey, ekey),
                daemon=True
            ).start()

    # ── Voice emission ────────────────────────────────────────────────────────

    def _emit_all_voices(self) -> None:
        combined: list[tuple[str, str]] = []
        for name, vid in self._sapi_voices:
            combined.append((name, vid))
        combined.extend(self._google_voices)
        combined.extend(self._el_voices)
        self.voices_ready.emit(combined)

    def refresh_voices(self, google_key: str = "", elevenlabs_key: str = "") -> None:
        """Fetch remote voices and re-emit the combined list. Call from any thread."""
        threading.Thread(
            target=self._fetch_remote_voices,
            args=(google_key, elevenlabs_key),
            daemon=True
        ).start()

    def _fetch_remote_voices(self, google_key: str, elevenlabs_key: str) -> None:
        if google_key:
            self._google_voices = _fetch_google_voice_list(google_key)
        if elevenlabs_key:
            self._el_voices = _fetch_el_voice_list(elevenlabs_key)
        self._emit_all_voices()

    # ── Speak dispatch ────────────────────────────────────────────────────────

    def _speak_item(self, item: dict) -> None:
        s = self._settings
        raw_voice = item.get("voice", "") or s.get("default_voice", "")
        engine, vid = _parse_voice_id(raw_voice)

        if engine == "google":
            api_key = s.get("google_api_key", "")
            if api_key:
                ok = self._speak_google(item, vid, api_key)
                if not ok:
                    self._speak_sapi(item, "")
            else:
                self._speak_sapi(item, "")
        elif engine == "elevenlabs":
            api_key = s.get("elevenlabs_api_key", "")
            if api_key:
                ok = self._speak_elevenlabs(item, vid, api_key)
                if not ok:
                    self._speak_sapi(item, "")
            else:
                self._speak_sapi(item, "")
        else:
            self._speak_sapi(item, vid)

        with self._lock:
            if self._pending:
                self._pending.pop(0)
        self.queue_updated.emit(list(self._pending))

    # ── SAPI ──────────────────────────────────────────────────────────────────

    def _speak_sapi(self, item: dict, voice_id: str) -> None:
        s        = self._settings
        rate_wpm = s.get("default_rate",   175)
        vol_pct  = s.get("default_volume", 100)
        text     = item["text"]

        try:
            if self._speaker is not None:
                sp = self._speaker
                if voice_id:
                    col = sp.GetVoices()
                    for i in range(col.Count):
                        tok = col.Item(i)
                        if tok.GetDescription() == voice_id or tok.Id == voice_id:
                            sp.Voice = tok
                            break
                sp.Rate   = _sapi_rate(rate_wpm)
                sp.Volume = max(0, min(100, vol_pct))
                self.speaking_started.emit(text)
                sp.Speak(text)
            else:
                self._speak_pyttsx3(item)
        except Exception as e:
            print(f"[TTS] SAPI speak error: {e}")

    def _speak_pyttsx3(self, item: dict) -> None:
        eng = getattr(self, "_pyttsx3_engine", None)
        if eng is None:
            return
        s = self._settings
        eng.setProperty("rate",   s.get("default_rate",   175))
        eng.setProperty("volume", s.get("default_volume", 100) / 100.0)
        self.speaking_started.emit(item["text"])
        eng.say(item["text"])
        eng.runAndWait()

    # ── Google Cloud TTS ──────────────────────────────────────────────────────

    def _speak_google(self, item: dict, voice_name: str, api_key: str) -> bool:
        """Synthesize via Google REST API. Returns True on success."""
        s        = self._settings
        rate_wpm = s.get("default_rate",   175)
        vol_pct  = s.get("default_volume", 100)

        voice_cfg: dict = {"languageCode": _google_lang(voice_name)}
        if voice_name:
            voice_cfg["name"] = voice_name

        payload = {
            "input":       {"text": item["text"]},
            "voice":       voice_cfg,
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "sampleRateHertz": 22050,
                "speakingRate":    _google_rate(rate_wpm),
                "volumeGainDb":    max(-6.0, min(6.0, (vol_pct - 100) * 0.06)),
            },
        }
        try:
            resp = requests.post(
                f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
                json=payload, timeout=10
            )
            resp.raise_for_status()
            pcm = base64.b64decode(resp.json()["audioContent"])
            self._play_pcm(pcm, 22050, item["text"])
            return True
        except Exception as e:
            print(f"[TTS] Google Cloud error: {e}")
            return False

    # ── ElevenLabs ────────────────────────────────────────────────────────────

    def _speak_elevenlabs(self, item: dict, voice_id: str, api_key: str) -> bool:
        """Synthesize via ElevenLabs API (pcm_22050 output). Returns True on success."""
        s        = self._settings
        rate_wpm = s.get("default_rate",   175)

        # ElevenLabs uses stability + similarity_boost; speed is in voice_settings
        speed = max(0.7, min(1.2, rate_wpm / 175.0))
        try:
            resp = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": item["text"],
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "speed": speed,
                    },
                    "output_format": "pcm_22050",
                },
                timeout=20,
            )
            resp.raise_for_status()
            self._play_pcm(resp.content, 22050, item["text"])
            return True
        except Exception as e:
            print(f"[TTS] ElevenLabs error: {e}")
            return False

    # ── PCM playback ──────────────────────────────────────────────────────────

    def _play_pcm(self, pcm: bytes, sample_rate: int, text: str) -> None:
        """Wrap raw PCM in a WAV header and play via winsound."""
        import winsound
        wav = _pcm_wav_header(pcm, sample_rate) + pcm
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(wav)
        tmp.close()
        self.speaking_started.emit(text)
        winsound.PlaySound(tmp.name, winsound.SND_FILENAME)
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────────────────────

    def enqueue(self, text: str, voice: str = "") -> None:
        if self._muted or not text:
            return
        max_depth = self._settings.get("max_queue_depth", 20)
        with self._lock:
            if len(self._pending) >= max_depth:
                self._pending.pop(0)
            self._pending.append(text)
        self._queue.put({"text": text, "voice": voice})
        self.queue_updated.emit(list(self._pending))

    def skip(self) -> None:
        self.clear_queue()

    def clear_queue(self) -> None:
        with self._lock:
            self._pending.clear()
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self.queue_updated.emit([])

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        if muted:
            self.clear_queue()

    def is_muted(self) -> bool:
        return self._muted

    def shutdown(self) -> None:
        self._running = False
        self._queue.put(None)

    # ── Static key testers ────────────────────────────────────────────────────

    @staticmethod
    def test_google_key(api_key: str) -> tuple[bool, str]:
        try:
            r = requests.get(
                f"https://texttospeech.googleapis.com/v1/voices?key={api_key}",
                timeout=8
            )
            if r.status_code == 200:
                count = len(r.json().get("voices", []))
                return True, f"API key valid ✓  ({count} voices available)"
            return False, f"Invalid key ({r.status_code})"
        except Exception as e:
            return False, f"Network error: {e}"

    @staticmethod
    def test_elevenlabs_key(api_key: str) -> tuple[bool, str]:
        try:
            r = requests.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": api_key},
                timeout=8
            )
            if r.status_code == 200:
                count = len(r.json().get("voices", []))
                return True, f"API key valid ✓  ({count} voices available)"
            return False, f"Invalid key ({r.status_code})"
        except Exception as e:
            return False, f"Network error: {e}"


# ── Remote voice list fetchers (module-level, usable without an engine instance)

def _fetch_google_voice_list(api_key: str) -> list[tuple[str, str]]:
    """Fetch Google TTS voice list. Returns [(display_name, voice_id), ...]."""
    try:
        r = requests.get(
            f"https://texttospeech.googleapis.com/v1/voices?key={api_key}",
            timeout=10
        )
        r.raise_for_status()
        voices = []
        for v in r.json().get("voices", []):
            name   = v.get("name", "")
            gender = v.get("ssmlGender", "").title()
            display = f"{name} — {gender}  [Google]"
            voices.append((display, f"google:{name}"))
        voices.sort(key=lambda x: x[0])
        return voices
    except Exception as e:
        print(f"[TTS] Google voice list fetch failed: {e}")
        return []


def _fetch_el_voice_list(api_key: str) -> list[tuple[str, str]]:
    """Fetch ElevenLabs voice list. Returns [(display_name, voice_id), ...]."""
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": api_key},
            timeout=10
        )
        r.raise_for_status()
        voices = []
        for v in r.json().get("voices", []):
            display = f"{v.get('name', '')}  [ElevenLabs]"
            voices.append((display, f"elevenlabs:{v.get('voice_id', '')}"))
        voices.sort(key=lambda x: x[0])
        return voices
    except Exception as e:
        print(f"[TTS] ElevenLabs voice list fetch failed: {e}")
        return []
