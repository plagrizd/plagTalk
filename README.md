# plagTalk

> **Text-to-Speech addon for plagComms — have your stream talk back to you.**

plagTalk is a free, local text-to-speech addon for [plagComms](https://plagrizr.com/plagcomms) that reads your stream events aloud in real time. Chat messages, follows, subscriptions, bits, raids, gifts, superchats, and more — spoken out loud through your speakers or headset while you stream, so you never have to glance away from your game or camera.

It runs silently in your Windows system tray, connects to plagComms automatically, and starts reading chat the moment your stream goes live. No subscription. No cloud account. No configuration required to get started.

> **Status:** Active development  
> **Platform:** Windows  
> **Requires:** [plagComms](https://plagrizr.com/plagcomms) (free)  
> **GitHub:** [github.com/plagrizd/plagTalk](https://github.com/plagrizd/plagTalk)  
> **plagComms on GitHub:** [github.com/plagrizr/plagcomms](https://github.com/plagrizr/plagcomms)

---

## Table of Contents

- [What It Does](#what-it-does)
- [Why plagTalk](#why-plagtalk)
- [Supported Events](#supported-events)
- [Features](#features)
- [Settings](#settings)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Audio Output & Streaming](#audio-output--streaming)
- [TTS Engines](#tts-engines)
- [Google Cloud TTS — Do I Need It?](#google-cloud-tts--do-i-need-it)
- [Template System](#template-system)
- [Word Filter](#word-filter)
- [Advanced Options](#advanced-options)
- [Roadmap](#roadmap)
- [Part of the plagComms Ecosystem](#part-of-the-plagcomms-ecosystem)

---

## What It Does

plagTalk sits between your stream and your ears. It connects to plagComms over a local WebSocket and receives every stream event — chat messages, follows, subs, raids, gifts, bits, and more — as they happen across Twitch, TikTok, YouTube, and Kick simultaneously. Each event is run through your configured rules and then read aloud using text-to-speech.

You decide exactly what gets read and how. Every event type has its own toggle and its own message template, so you can craft spoken alerts that sound exactly the way you want them to. Most streamers leave chat reading on and turn on event alerts one by one as they decide they want them.

The speech queue ensures events never pile on top of each other — one at a time, in order, no overlapping audio. If the queue fills up during a raid, the oldest pending items are dropped automatically to keep things current.

---

## Why plagTalk

- **Keep your eyes on your stream.** You hear chat and events without having to read a screen.
- **Works for all platforms at once.** Twitch, TikTok, YouTube, and Kick events all come through the same voice.
- **Zero setup to get started.** Windows voices are built in — open it and it works.
- **Fully customisable.** Every event has its own message template. Write exactly what you want spoken.
- **Route audio separately.** Send TTS to a virtual audio device so OBS captures it independently from game audio.
- **Private and local.** Everything runs on your machine. No data leaves your PC.
- **Free.** No subscription, no usage limits on the default engine, no paywall.

---

## Supported Events

### Twitch

| Event | Spoken by Default | Notes |
|---|---|---|
| Chat messages | ✅ Yes | Includes `/me` actions and announcements |
| Channel Points redemption | Off | Per-title voice rules — assign different voices to specific rewards |
| New follower | Off | |
| Subscription | Off | Only fires for viewer-shared subs — the silent payment event is automatically ignored |
| Subscription with message | Off | Separate template for subs that include a personal message |
| Gift subs | Off | |
| Bits / Cheer | Off | Configurable minimum bits threshold |
| Incoming raid | Off | Configurable minimum viewer count threshold |
| Watch streak (Power-Up) | Off | Fires when a viewer shares their stream watch streak |

### TikTok

| Event | Spoken by Default | Notes |
|---|---|---|
| Chat messages | ✅ Yes | Independent toggle and template from other platforms |
| New follower | Off | |
| Gift | Off | Configurable minimum coin value threshold |
| Subscription | Off | |
| Superfan | Off | |
| Stream share | Off | |
| Likes | Off | Batched per user — configurable minimum like count threshold |

### YouTube

| Event | Spoken by Default | Notes |
|---|---|---|
| Chat messages | ✅ Yes | Independent toggle and template from other platforms |
| Super Chat | Off | Reads the amount and message |
| Membership | Off | New memberships, milestones, and gifted memberships |

### Kick

| Event | Spoken by Default | Notes |
|---|---|---|
| Chat messages | ✅ Yes | Independent toggle and template from other platforms |
| New follower | Off | |
| Subscription | Off | |
| Gift subs | Off | |
| Incoming raid | Off | |

---

## Features

### 🔊 Works Immediately, No Setup Required
plagTalk uses Windows built-in SAPI5 voices right out of the box. Open it, make sure plagComms is running, and it starts reading chat. No accounts, no API keys, nothing to configure before your first use.

### 🗣️ Three TTS Engines
- **Windows SAPI5** — built-in, free, no setup, works offline
- **Google Cloud TTS** — natural-sounding WaveNet and Neural2 voices via your own API key; free tier covers most streamers
- **ElevenLabs** — ultra-realistic AI voices via your own API key

### 🎙️ Audio Output Routing
Route TTS to any output device on your system — including virtual audio cables like VB-Audio Virtual Cable. This lets OBS or your streaming software capture TTS audio as a separate source, completely isolated from your game audio and headset. No more everything doubling on stream.

### 📢 Channel Points Voice Rules (Twitch)
Assign specific voices to specific Channel Points redemptions by title. When a viewer redeems "Robot Mode", you can make TTS switch to a robotic voice for that message. Each rule is a keyword match — configurable per title, with enable/disable toggle per rule.

### 🔊 Per-Event Voice Override
Every event type has its own voice button — assign a specific TTS voice to follows, raids, subs, or any event independently of the global default.

### 📝 Customisable Message Templates
Every event has its own message template that you write yourself. Use plain text with tokens like `{username}`, `{amount}`, `{message}`, and more to build exactly the phrasing you want spoken. Templates are live — change them any time and they take effect immediately.

```
{username} says {message}
{username} just gifted {amount} subs!
{username} cheered {amount} bits!
Incoming raid! {username} is here with {amount} viewers — let's go!
{username} subscribed for {months} months and said: {message}
```

### 🔇 Word Filter
Add words or phrases to the filter list and they will be silently removed from spoken text before anything is sent to TTS. Useful for blocking specific phrases, usernames in messages, or words you just don't want read aloud on stream. The rest of the message still plays — only the filtered words are stripped out.

### 🗂️ Speech Queue
Events are queued and played one at a time. No overlapping audio, no chaos during a raid. The queue depth is configurable — when it fills, the oldest pending items drop automatically to keep readings current. You can skip the current speech, clear the entire queue, or mute everything with one click.

### 🎙️ Voice Overrides at Every Level
- **Default voice** — one voice for everything
- **Per-platform voice** — a different voice for Twitch vs. TikTok vs. YouTube vs. Kick
- **Per-event voice** — a specific voice just for raids, or just for subs
- **Per-username voice** — specific viewers always get read in the same voice
- **Channel Points rules** — per-redemption-title voice matching
All levels stack in priority order: per-user > per-event > redemption rule > per-platform > default.

### 💬 TTS Command Mode
Restrict chat TTS to messages that start with a specific prefix (e.g. `!tts`). Only messages using that prefix are spoken — everything else is ignored.

### 🛡️ Blocklist & Whitelist
**Blocklist**: specific usernames are completely silenced — no messages, no events.  
**Whitelist**: when non-empty, only listed usernames' chat messages are spoken. Useful for reading only mods/VIPs or a specific set of trusted viewers.

### ⚙️ Thresholds
Set minimums before an event is spoken. Don't want to read every 1-bit cheer? Set the minimum to 100 bits. Only want big raids announced? Set a minimum viewer count. Available for bits, raid size, TikTok gift coins, and TikTok like batches.

### 💬 Chat Behaviour Controls
- Truncate long messages at a configurable character limit
- Per-user cooldown — don't read the same viewer more than once every N seconds
- Toggle whether usernames are included in chat reads
- Toggle whether the platform name is appended to reads ("on Twitch", "on YouTube")
- Toggle whether multi-stream room relay events are read
- Bot command filter — ignore messages that start with `!` (on by default)

### 💾 Auto-Save
All settings save automatically after a brief pause — no Save button required. A confirmation toast confirms every save.

### 📊 Dashboard
Live dashboard shows the connection status, current speech queue, and a rolling log of recent events — including which events were spoken and which were skipped, with reasons.

---

## Settings

### Settings Tab
| Setting | Description |
|---|---|
| TTS Engine | Windows SAPI (free, no setup), Google Cloud TTS, or ElevenLabs |
| Google API Key | Paste your key — a Test button validates it immediately |
| ElevenLabs API Key | Paste your key — a Test button validates it immediately |
| Default Voice | Choose from all voices available (SAPI, Google, and ElevenLabs if configured) |
| Speed | Reading speed in words per minute |
| Volume | TTS volume, independent of system audio |
| Audio Output | Send TTS to a specific output device (e.g. VB-Audio CABLE Input for OBS capture) |
| Word Filter | Words and phrases to silently remove from spoken text, one per line |
| Bearer Token | Optional authentication token if one is set in plagComms → Settings → Add-ons |

### Events Tab (per platform)
Every supported event type has:
- **Toggle** — on/off
- **Voice** — optional per-event voice override (🔊 button)
- **Message template** — fully editable, with token reference
- **Reset to default** — one click restores the original template
- **Channel Points rules** — per-title voice matching (Twitch redemptions only)

### Advanced Tab

**Voice per Platform**
Assign a separate default voice for Twitch, TikTok, YouTube, and Kick independently. Per-row randomize (🎲) and reset (↺) buttons. Leave any platform blank to fall back to the default voice.

**Thresholds**
- Minimum cheer bits before announcing
- Minimum raid viewers before announcing
- Minimum TikTok like batch count before announcing
- Minimum TikTok gift coin value before announcing

**Chat Behaviour**
- Max message length in characters (0 = no limit)
- Per-user cooldown in seconds (0 = off)
- Toggle: read usernames in chat messages
- Toggle: include platform name in event reads
- Toggle: read room relay events from multi-stream sessions
- Toggle: ignore bot commands (messages starting with `!`)
- Toggle: TTS command mode with configurable prefix

**User Blocklist**
Usernames listed here are completely silenced.

**User Whitelist**
When non-empty, only listed usernames' chat is spoken. Leave empty to read everyone (subject to blocklist).

**Voice per Username**
Map specific usernames to specific voices. That viewer always gets read in that voice.

---

## How It Works

plagTalk connects to plagComms at `ws://localhost:54473/addons/ws` and receives every stream event as a JSON frame. The event handler processes each one in sequence:

1. **Room relay check** — drop if from a multi-stream relay and that setting is off
2. **Blocklist check** — drop if the sender is on the blocklist
3. **Whitelist check** — drop if whitelist is active and sender is not on it (chat only)
4. **Event type routing** — match the event to its configured key (e.g. `cheer_twitch`, `gift_tiktok`)
5. **Enabled check** — drop if that event type is toggled off
6. **Threshold check** — drop if the event doesn't meet the configured minimum value
7. **Text processing** — command mode gate, bot command filter, truncate, word filter, cooldown
8. **Template rendering** — substitute tokens into the configured template string
9. **Voice resolution** — per-user > per-event > redemption rule > per-platform > default
10. **Enqueue** — add the final spoken string to the TTS queue

The TTS queue plays items one at a time using the selected engine. plagTalk reconnects to plagComms automatically using exponential backoff if the connection drops — you never need to restart it.

---

## Getting Started

### 1. Download plagTalk
Download the latest `plagTalk.exe` from the [Releases page](https://github.com/plagrizd/plagTalk/releases/latest). No installation required — just run the exe.

### 2. Make sure plagComms is running
plagTalk requires plagComms to be open and the add-on WebSocket endpoint to be enabled.

In plagComms: **Settings → Add-ons → Enable add-on WebSocket endpoint**

### 3. Run plagTalk
Double-click `plagTalk.exe`. It opens its main window and immediately attempts to connect to plagComms. When the status indicator in the sidebar turns green, it is connected and listening.

### 4. Configure (optional)
Out of the box, only chat messages are read aloud. Go to the **Twitch / TikTok / YouTube / Kick** tabs to enable and customise additional event types. Go to **Settings** to choose a voice, adjust playback, or add an API key for Google or ElevenLabs voices.

### 5. Stream
plagTalk stays in your system tray. Close the window and it keeps running. Right-click the tray icon to show the window or quit.

---

## Audio Output & Streaming

By default plagTalk plays through your Windows default output device. If you want your stream to hear TTS separately from your game audio, use a virtual audio cable:

**Recommended: [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)** (free)

1. Install VB-Audio Virtual Cable
2. In plagTalk → **Settings → Audio Output**, select **CABLE Input (VB-Audio Virtual Cable)**
3. In OBS/Streamlabs/Meld, add an **Audio Input Capture** source and select **CABLE Output (VB-Audio Virtual Cable)**
4. Set that source to **Monitor and Output** so you also hear it through your headset

This completely isolates TTS audio from your game and other sources — no doubling, no bleeding.

---

## TTS Engines

### Windows SAPI5 (Default)
Uses the voices built into Windows. Available immediately, no setup, no internet required, no cost. Additional voices can be downloaded through Windows Settings → Time & Language → Speech.

**Pros:** Zero setup, works offline, completely free  
**Cons:** Voices sound robotic compared to neural TTS options

### Google Cloud TTS
Uses Google's Text-to-Speech API to generate high-quality speech including WaveNet and Neural2 voices. Requires your own Google Cloud API key.

**Pros:** Significantly better voice quality, large selection of voices and languages  
**Cons:** Requires a Google Cloud project setup (~5 minutes), internet required

### ElevenLabs
Uses ElevenLabs' AI voice synthesis API for ultra-realistic voices. Requires your own ElevenLabs API key.

**Pros:** Best voice quality available, highly customisable voice characters  
**Cons:** Requires an ElevenLabs account, paid tiers for higher usage, internet required

---

## Google Cloud TTS — Do I Need It?

No. Windows SAPI is fully functional and works for most streamers.

If voice quality matters to your stream presentation — for example if you read a lot of chat on camera, or you want TTS to feel more like a character than a robot — Google Cloud TTS is worth considering.

**Free tier:** 4 million standard characters/month, 1 million WaveNet/Neural2 characters/month. A typical 4-hour stream with active chat TTS uses roughly 30,000–80,000 characters. Most streamers will never reach the free tier limit.

**How to get a key (approx. 5 minutes):**
1. Go to [console.cloud.google.com](https://console.cloud.google.com) and sign in with your Google account
2. Create a new project (give it any name)
3. Navigate to **APIs & Services → Library** and search for "Text-to-Speech"
4. Click **Enable**
5. Navigate to **APIs & Services → Credentials → Create Credentials → API Key**
6. Copy the key and paste it into plagTalk → Settings → Google API Key
7. Click **Test** to confirm it works

You are using your own Google Cloud account and your own quota. plagTalk never handles billing or credentials on your behalf.

---

## Template System

Every event type has a message template you write yourself using curly-brace tokens. The template is what plagTalk actually speaks — customise it to match your stream's tone and language.

### Available Tokens

| Token | Value |
|---|---|
| `{username}` | Viewer's display name |
| `{platform}` | `twitch` · `tiktok` · `youtube` · `kick` |
| `{Platform}` | `Twitch` · `TikTok` · `YouTube` · `Kick` (capitalised) |
| `{message}` | Chat message text, sub message, or event text |
| `{amount}` | Numeric quantity — bits, viewers, gifts, likes |
| `{months}` | Total subscription months |
| `{streak}` | Watch streak count (Twitch Power-Up) |
| `{gift_name}` | TikTok gift name (e.g. "Rose", "Galaxy", "Lion") |
| `{tier}` | Subscription tier ("Tier 1", "Tier 2", "Tier 3", "Prime") |
| `{streamer}` | The channel name the event came from |

### Examples

```
# Chat
{username} says {message}
{username} from {Platform} says {message}

# Follows
{username} just followed! Welcome in!

# Twitch sub with message
{username} re-subbed for {months} months on {tier} and said: {message}

# Bits
{username} dropped {amount} bits! Thank you!

# Raid
{username} is raiding in with {amount} viewers! Welcome everyone!

# TikTok gift
{username} just sent {amount} {gift_name}!

# YouTube Super Chat
{username} Super Chatted {amount} dollars! They said: {message}
```

Any token that has no value for a particular event is simply removed from the spoken string. You will never hear "undefined" or empty token placeholders.

---

## Word Filter

The word filter removes specific words or phrases from spoken text before TTS. It works on any user-generated content — chat messages, sub messages, Super Chat text — but not on the surrounding template text you wrote.

**How it works:**
- Words are matched case-insensitively at word boundaries (so filtering "bad" doesn't strip "badge")
- Matched words are silently removed — surrounding text is still spoken
- If removing all filtered words leaves an empty or blank message, the message is skipped entirely
- The rest of the event template (username, amount, etc.) is not affected

Configure in **Settings → Word Filter**, one word or phrase per line.

---

## Advanced Options

### Per-User Cooldown
Limit how often any single viewer's chat is read. If set to 30 seconds, a viewer who sends 10 messages in quick succession will only have their first message spoken — then nothing for 30 seconds, then the next one. Useful for high-volume chats where a single active viewer would otherwise dominate the queue.

### Max Message Length
Chat messages longer than this limit are truncated with an ellipsis before being spoken. Set to 0 for no limit. Default is 200 characters.

### Bot Command Filter
When enabled (default), messages starting with `!` are ignored by chat TTS. This prevents bot commands and chat game responses from being spoken. Automatically disabled when TTS command mode is active.

### TTS Command Mode
When enabled, only messages starting with the configured prefix (default `!tts`) are spoken. The prefix is stripped before speech. Useful for streams where you only want intentional TTS messages.

### Room Relay Events
plagComms supports multi-streamer rooms. When room relay is off (default), plagTalk only reads events from your own channel.

### Include Platform Name
When enabled, plagTalk appends "on Twitch", "on TikTok", etc. to event reads that don't already include a platform token.

---

## Roadmap

### Near Term
- **Queue visualisation** — see pending items, skip individual items from the list
- **Global mute / skip keyboard shortcuts** — configurable hotkeys that work even when the window is hidden

### Medium Term
- **OBS scene change integration** — automatically mute or reduce TTS when switching to a brb/ending scene
- **Streamer mode** — automatically suppress TTS when events arrive faster than a configurable rate (large raids, bot floods)
- **Chat filtering by badge** — only read chat from subs, followers, or mods
- **Sound effects** — play a short audio clip before or after specific event types

### Future
- **Auto-translation** — translate messages to a selected language before TTS
- **plagComms chatbot integration** — trigger TTS commands and responses through chat

---

## Part of the plagComms Ecosystem

plagTalk is an official addon for [plagComms](https://plagrizr.com/plagcomms) — a free, multi-platform live chat aggregator and OBS overlay tool for streamers on Windows.

plagComms connects to Twitch, TikTok Live, YouTube Live, and Kick simultaneously, merging all chat, events, and alerts into a single OBS browser-source overlay. It also includes a native pop-out chat window, multi-streamer room system, live channel stats overlay, chat history logging, and a bidirectional chat input with Twitch moderation tools.

plagTalk is built on plagComms' public add-on WebSocket API — the same API any developer can use to build their own tools.

**Links:**
- plagComms website: [plagrizr.com/plagcomms](https://plagrizr.com/plagcomms)
- plagComms on GitHub: [github.com/plagrizr/plagcomms](https://github.com/plagrizr/plagcomms)
- plagTalk on GitHub: [github.com/plagrizd/plagTalk](https://github.com/plagrizd/plagTalk)
- Streamer: [twitch.tv/plagrizr](https://twitch.tv/plagrizr)

---

## Keywords

_For search and discovery purposes:_

stream text to speech, TTS for streamers, Twitch TTS addon, TikTok stream TTS, YouTube live TTS, Kick TTS, read chat aloud, stream event reader, plagComms addon, OBS text to speech, streamer accessibility tool, multi-platform stream TTS, Windows TTS streamer, Google Cloud TTS stream, ElevenLabs stream TTS, SAPI streamer tool, stream chat reader, follow alert TTS, sub alert TTS, raid alert TTS, bits alert voice, gift alert voice, channel points TTS, virtual audio cable stream, plagrizr, plagTalk, plagComms

---

> Built by [@plagrizr](https://twitch.tv/plagrizr)
