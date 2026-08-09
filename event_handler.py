"""
plagTalk — Event handler
Routes plagComms WebSocket events → TTS queue.

Template tokens (curly-brace style):
  {username}  {platform}  {Platform}  {message}
  {amount}    {months}    {streak}    {gift_name}
  {tier}      {streamer}
"""

import re
import time
from settings import DEFAULT_TEMPLATES


# ── Tier label map ────────────────────────────────────────────────────────────

_TIER_LABELS = {"1000": "Tier 1", "2000": "Tier 2", "3000": "Tier 3", "Prime": "Prime"}
_PLATFORM_LABELS = {"twitch": "Twitch", "tiktok": "TikTok", "youtube": "YouTube", "kick": "Kick"}


# ── EventHandler ──────────────────────────────────────────────────────────────

class EventHandler:
    def __init__(self, settings, tts_engine, on_log=None):
        """
        settings    — Settings instance
        tts_engine  — TTSEngine instance
        on_log      — optional callable(evt: dict, spoken: bool, text: str)
                      called for every event (for dashboard log)
        """
        self._s       = settings
        self._tts     = tts_engine
        self._on_log  = on_log
        self._cooldowns: dict[str, float] = {}   # username → last_spoken_ts

    def handle(self, evt: dict) -> None:
        """Entry point — called for every event from the WebSocket."""
        platform = evt.get("platform", "")
        username = evt.get("username", "")

        # Room relay gate
        if evt.get("from_room") and not self._s.adv("read_from_room", False):
            self._log(evt, False, "")
            return

        # Blocklist
        blocklist = [b.lower() for b in self._s.adv("user_blocklist", [])]
        if username.lower() in blocklist:
            self._log(evt, False, "")
            return

        # Whitelist (chat only — follows / subs / raids are never restricted)
        if evt.get("type") in ("chat", "emote_chat"):
            whitelist = [u.lower() for u in self._s.adv("user_whitelist", [])]
            if whitelist and username.lower() not in whitelist:
                self._log(evt, False, "")
                return

        spoken_text = self._route(evt)
        self._log(evt, bool(spoken_text), spoken_text or "")

    # ── Routing ───────────────────────────────────────────────────────────────

    def _route(self, evt: dict) -> str | None:
        """Resolve event key, check enabled, apply filters, enqueue. Returns spoken text or None."""
        platform = evt.get("platform", "")
        etype    = evt.get("type", "")
        username = evt.get("username", "")
        text     = evt.get("text", "") or ""

        key = self._resolve_key(evt)
        if key is None:
            return None

        cfg = self._s.event_cfg(key)
        if not cfg.get("enabled"):
            return None

        # Thresholds
        if not self._check_thresholds(evt, key):
            return None

        # Chat-specific processing
        if key == "chat":
            text = self._process_chat_text(text, username)
            if text is None:
                return None   # filtered out / cooldown

        # Word filter on any user-generated text
        text = apply_word_filter(text, self._s.get("word_filter", []))

        # Build spoken string from template
        template = cfg.get("template") or DEFAULT_TEMPLATES.get(key, "")
        spoken   = apply_template(template, {
            "username":  username if self._s.adv("read_usernames", True) or key != "chat" else "",
            "platform":  platform,
            "Platform":  _PLATFORM_LABELS.get(platform, platform.title()),
            "message":   text,
            "amount":    evt.get("amount", ""),
            "months":    evt.get("months", ""),
            "streak":    evt.get("streak", ""),
            "gift_name": evt.get("gift_name", ""),
            "tier":      _TIER_LABELS.get(evt.get("sub_tier", ""), evt.get("sub_tier", "")),
            "streamer":  evt.get("streamer", ""),
        })

        if self._s.adv("include_platform_name") and "{platform}" not in template and "{Platform}" not in template:
            spoken = spoken + f" on {_PLATFORM_LABELS.get(platform, platform)}"

        spoken = spoken.strip()
        if not spoken:
            return None

        # Resolve voice override
        voice = self._resolve_voice(platform, username)

        self._tts.enqueue(spoken, voice)
        return spoken

    # ── Key resolution ────────────────────────────────────────────────────────

    def _resolve_key(self, evt: dict) -> str | None:
        platform = evt.get("platform", "")
        etype    = evt.get("type", "")
        text     = evt.get("text", "") or ""

        if etype in ("chat", "emote_chat"):
            return "chat"
        if etype == "follow":
            return f"follow_{platform}"
        if etype == "sub":
            if platform == "twitch":
                if not evt.get("sub_is_shared"):
                    return None   # silent payment — never speak
                return "sub_message_twitch" if text.strip() else "sub_twitch"
            return f"sub_{platform}"
        if etype == "gift":
            return f"gift_{platform}"
        if etype == "cheer":
            return "cheer_twitch"
        if etype == "raid":
            return f"raid_{platform}"
        if etype == "watch_streak":
            return "watch_streak_twitch"
        if etype == "superfan":
            return "superfan_tiktok"
        if etype == "share":
            return "share_tiktok"
        if etype == "like":
            return "like_tiktok"
        if etype == "superchat":
            return "superchat_youtube"
        if etype == "membership":
            return "membership_youtube"
        return None

    # ── Threshold check ───────────────────────────────────────────────────────

    def _check_thresholds(self, evt: dict, key: str) -> bool:
        etype    = evt.get("type", "")
        platform = evt.get("platform", "")
        amount   = evt.get("amount", 0) or 0
        coins    = evt.get("coins",  0) or 0

        if etype == "cheer" and amount < self._s.threshold("min_cheer_bits"):
            return False
        if etype == "raid"  and amount < self._s.threshold("min_raid_viewers"):
            return False
        if etype == "like"  and amount < self._s.threshold("min_tiktok_likes"):
            return False
        if etype == "gift" and platform == "tiktok" and coins < self._s.threshold("min_tiktok_gift_coins"):
            return False
        return True

    # ── Chat processing ───────────────────────────────────────────────────────

    def _process_chat_text(self, text: str, username: str) -> str | None:
        """Check command gate, truncate, check cooldown. Returns None to suppress."""
        # TTS command gate — only speak if message starts with the command prefix
        if self._s.adv("chat_command_mode", False):
            cmd = (self._s.adv("chat_command", "!tts") or "!tts").strip().lower()
            stripped = text.strip()
            if not stripped.lower().startswith(cmd):
                return None
            text = stripped[len(cmd):].strip()
            if not text:
                return None

        max_len = self._s.adv("max_message_length", 200)
        if max_len and len(text) > max_len:
            text = text[:max_len] + "…"

        cooldown = self._s.adv("chat_cooldown_seconds", 0)
        if cooldown:
            last = self._cooldowns.get(username.lower(), 0)
            if time.time() - last < cooldown:
                return None
            self._cooldowns[username.lower()] = time.time()

        return text

    # ── Voice resolution ──────────────────────────────────────────────────────

    def _resolve_voice(self, platform: str, username: str) -> str:
        adv = self._s.data.get("advanced", {})
        per_user = adv.get("voice_per_user", {})

        # Per-user override (case-insensitive)
        for u, v in per_user.items():
            if u.lower() == username.lower():
                return v

        # Per-platform override
        if platform == "twitch"  and adv.get("voice_twitch"):  return adv["voice_twitch"]
        if platform == "tiktok"  and adv.get("voice_tiktok"):  return adv["voice_tiktok"]
        if platform == "youtube" and adv.get("voice_youtube"): return adv["voice_youtube"]
        if platform == "kick"    and adv.get("voice_kick"):    return adv["voice_kick"]

        return self._s.get("default_voice", "")

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, evt: dict, spoken: bool, text: str) -> None:
        if self._on_log:
            try:
                self._on_log(evt, spoken, text)
            except Exception:
                pass


# ── Template engine ───────────────────────────────────────────────────────────

def apply_template(template: str, vars: dict) -> str:
    result = template
    for key, val in vars.items():
        result = result.replace(f"{{{key}}}", str(val) if val is not None else "")
    # Remove any leftover {token} placeholders so TTS doesn't read them
    result = re.sub(r"\{[^}]+\}", "", result)
    result = re.sub(r"\s{2,}", " ", result).strip()
    return result


def apply_word_filter(text: str, word_filter: list[str]) -> str:
    if not word_filter or not text:
        return text
    result = text
    for word in word_filter:
        if not word.strip():
            continue
        pattern = re.compile(r"(?<!\w)" + re.escape(word) + r"(?!\w)", re.IGNORECASE)
        result  = pattern.sub("", result)
    result = re.sub(r"\s{2,}", " ", result).strip()
    return result
