<div align="center" style="text-align: center;">
<h1><img src="icon.ico" height="30px">  maxstellar's Biome Macro</h1>
<p> A small macro that detects biomes in the Roblox game Sol's RNG.<br>This macro started as a small project to detect biomes even when I was using my PC for other things.</p>

![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/purestellenium/maxstellar-Biome-Macro/total)
![GitHub Release](https://img.shields.io/github/v/release/purestellenium/maxstellar-Biome-Macro)
![GitHub License](https://img.shields.io/github/license/purestellenium/maxstellar-Biome-Macro)
</div>

## Features
- Biome detection without OCR — reads Roblox's own log, never touches the game
- Per-biome Discord webhook messages, pings, or silence
- Multi-webhook support
- Desktop notifications
- Biome duration reported when a biome ends
- Survives Roblox restarts and log rotation without needing a macro restart
- Unknown biomes are still reported, so a game update can't silence it

## Installation
Download the [latest release](https://github.com/purestellenium/maxstellar-Biome-Macro/releases/latest) and put it in an empty folder. Run the .exe file and configure to your liking.<br><br>
Alternatively, if you already have Python installed, download the Python file along with the required libraries and images, and run it from command line or with your preferred method.

```
pip install -r requirements.txt
python BiomeMacro.py
```

## Adding a new biome
When Sol's RNG adds a biome you don't need to touch the code — edit **`biomes.json`** and add one entry:

```json
{ "name": "EXAMPLE BIOME", "label": "Example Biome", "color": "AABBCC", "default": "Ping", "everyone": false }
```

- `name` **must match the rich-presence hover text exactly**, in uppercase, as Roblox writes it to the log.
- `color` is the embed colour, hex, no `#`.
- `default` is the starting notification setting (`Message`, `Ping`, or `Nothing`); after that it's remembered in `config.ini`.
- `everyone` sends `@everyone` regardless of the per-biome setting.

The biome then shows up automatically in **Configure Pings**. If a biome appears that isn't in the file yet, the macro still reports it with a fallback colour and notes it in `crash.log`, so you'll never silently miss one.

To find the exact name a new biome uses, trigger it once and search your latest Roblox log for `SetRichPresence` — the `largeImage.hoverText` value is the name. Note it must come from `largeImage`; `smallImage` always reads `Sol's RNG` and is not a biome.

When running the .exe, edit the `biomes.json` that appears next to it — no rebuild needed.

## Common Issues
### Macro doesn't detect biomes
- Make sure your PC time is not offset (early or late)
- Check `crash.log` (Settings → View crash.log) — webhook and parsing failures are recorded there now

### Macro won't launch (shows error message)
- Make sure the zip file downloaded was extracted fully (into a folder)
- Make sure you are running the macro from the extracted folder (and not from the Home page of File Explorer)
- Make sure `biomes.json` is in the same folder as the macro
- Delete and reinstall macro

## Changelog

### v2.5
- Added **Blazing Sun** (confirmed against real Roblox logs)
- Removed Pumpkin Moon and Graveyard

**Critical fix**
- **The macro refused to detect anything if the Discord User ID field was empty.** That field is only needed for pings, but the check ran before detection started, so a default config (which ships with it blank) meant hitting Start did nothing at all. Leaving it empty is now fine — you just don't get pinged.

**Quality of life**
- Sound alert on biomes set to Ping
- Biome history saved to `biome_history.csv` (biome, start/end, duration)
- Session summary posted when you stop: what you caught and how long you ran
- Current biome shown in the window title
- Ping ID can be treated as a **role** instead of a user
- Warns if a second copy is already running, so you don't get every alert twice
- Roblox username is attached to biome embeds
- Test Webhook button
- Failed webhooks now retry, including proper handling of Discord rate limits
- `crash.log` rotates at 2 MB instead of growing forever
- **Fixed:** when built as an .exe, `config.ini` and `crash.log` were written into PyInstaller's temporary extraction folder, so settings reset on every launch. They now sit next to the .exe, and `biomes.json` is seeded beside it so biomes can be added without a rebuild
- Biomes moved to `biomes.json`; adding one no longer needs a code change
- Unknown/new biomes are reported instead of being silently dropped
- **Fixed:** Heaven and Singularity never sent anything (a variable was assigned twice, so Singularity's setting was never created)
- **Fixed:** biomes set to "Nothing" still fired an empty webhook, which Discord rejects
- **Fixed:** Heaven and Singularity had settings but no UI to change them
- **Fixed:** the macro kept tailing a dead log after a Roblox rejoin — this was the real cause of "macro doesn't detect biomes", so closing all Roblox instances is no longer needed
- **Fixed:** the detection loop re-entered itself on every Roblox restart, leaking file handles and eventually overflowing the stack
- **Fixed:** closing any child window could stop the macro (`<Destroy>` fires for child widgets too)
- Detection moved to a background thread — the window no longer freezes
- Errors are logged instead of silently swallowed by bare `except: pass`
- **Fixed:** pausing discarded log lines outright, so resuming could miss the biome you were already in
- Glitched, Dreamspace, Cyberspace and Singularity stay hard-coded and out of Configure Pings, as before — they are still detected and still ping
- New **Settings** tab with six options, no scrolling. The Webhook and Credits tabs are pixel-identical to before, and the window is still 505x285
- Removed the dead "Aura Detection [Not Working]" controls, which had no code behind them

Enjoy!
