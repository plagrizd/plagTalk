"""
plagTalk — settings store
JSON-backed settings with deep-merge against defaults.
"""

import json
import os
from copy import deepcopy
from pathlib import Path

# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULTS: dict = {
    "version": 1,

    # Connection
    "ws_token": "",
    "ws_port":  54473,

    # TTS engine selection is now per-voice-ID; keys below enable remote voice lists
    "tts_engine": "sapi",
    "google_api_key": "",
    "elevenlabs_api_key": "",

    # Playback
    "default_voice": "",
    "default_rate":   175,    # words per minute (SAPI scale)
    "default_pitch":  50,     # 0–100 (SAPI)
    "default_volume": 100,    # 0–100

    # Queue
    "max_queue_depth": 20,

    # Word filter — matched words/phrases are removed from spoken text
    "word_filter": [],

    # Platforms hidden from the Events / Advanced UI (platform names, e.g. "tiktok")
    "hidden_platforms": [],

    # Voice pool for randomization (empty = use all voices; list of exact voice names)
    "voice_pool": [],

    # ── Per-event config ──────────────────────────────────────────────────────
    # template tokens: {username} {platform} {Platform} {message}
    #   {amount} {months} {streak} {gift_name} {tier} {streamer}
    "events": {
        "chat":                 {"enabled": True,  "template": "{username} says {message}"},

        "follow_twitch":        {"enabled": False, "template": "{username} just followed!"},
        "sub_twitch":           {"enabled": False, "template": "{username} subscribed for {months} months!"},
        "sub_message_twitch":   {"enabled": False, "template": "{username} subscribed for {months} months and said: {message}"},
        "gift_twitch":          {"enabled": False, "template": "{username} gifted {amount} subs!"},
        "cheer_twitch":         {"enabled": False, "template": "{username} cheered {amount} bits!"},
        "raid_twitch":          {"enabled": False, "template": "Incoming raid! {username} is here with {amount} viewers!"},
        "watch_streak_twitch":  {"enabled": False, "template": "{username} has watched {streak} streams in a row!"},

        "follow_tiktok":        {"enabled": False, "template": "{username} just followed on TikTok!"},
        "gift_tiktok":          {"enabled": False, "template": "{username} sent {amount} {gift_name}!"},
        "sub_tiktok":           {"enabled": False, "template": "{username} subscribed on TikTok!"},
        "superfan_tiktok":      {"enabled": False, "template": "{username} is a Superfan!"},
        "share_tiktok":         {"enabled": False, "template": "{username} shared the stream!"},
        "like_tiktok":          {"enabled": False, "template": "{username} liked the stream!"},

        "superchat_youtube":    {"enabled": False, "template": "{username} Super Chatted {amount} dollars! {message}"},
        "membership_youtube":   {"enabled": False, "template": "{username} became a member! {message}"},

        "follow_kick":          {"enabled": False, "template": "{username} just followed on Kick!"},
        "sub_kick":             {"enabled": False, "template": "{username} subscribed for {months} months on Kick!"},
        "gift_kick":            {"enabled": False, "template": "{username} gifted {amount} subs on Kick!"},
        "raid_kick":            {"enabled": False, "template": "Incoming host! {username} arrived with {amount} viewers!"},
    },

    "thresholds": {
        "min_cheer_bits":        0,
        "min_raid_viewers":      0,
        "min_tiktok_likes":      0,
        "min_tiktok_gift_coins": 0,
    },

    "advanced": {
        "voice_twitch":          "",
        "voice_tiktok":          "",
        "voice_youtube":         "",
        "voice_kick":            "",
        "voice_per_user":        {},   # {"username": "VoiceName"}
        "user_blocklist":        [],
        "max_message_length":    200,
        "chat_cooldown_seconds": 0,
        "chat_command_mode":     False,   # require !tts prefix for chat TTS
        "chat_command":          "!tts",
        "user_whitelist":        [],      # if non-empty, only these users trigger chat TTS
        "read_from_room":        False,
        "include_platform_name": False,
        "read_usernames":        True,
    },
}

DEFAULT_TEMPLATES: dict = {k: v["template"] for k, v in DEFAULTS["events"].items()}


# ── Store ─────────────────────────────────────────────────────────────────────

class Settings:
    def __init__(self) -> None:
        appdata = os.getenv("APPDATA") or str(Path.home())
        self._path = Path(appdata) / "plagTalk" / "settings.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> dict:
        try:
            if self._path.exists():
                saved = json.loads(self._path.read_text("utf-8"))
                return _deep_merge(deepcopy(DEFAULTS), saved)
        except Exception as e:
            print(f"[settings] load failed: {e}")
        return deepcopy(DEFAULTS)

    def save(self) -> None:
        try:
            self._path.write_text(json.dumps(self.data, indent=2), "utf-8")
        except Exception as e:
            print(f"[settings] save failed: {e}")

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value) -> None:
        self.data[key] = value
        self.save()

    def event_cfg(self, key: str) -> dict:
        return self.data.get("events", {}).get(key, {"enabled": False, "template": ""})

    def adv(self, key, default=None):
        return self.data.get("advanced", {}).get(key, default)

    def threshold(self, key, default=0):
        return self.data.get("thresholds", {}).get(key, default)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base
