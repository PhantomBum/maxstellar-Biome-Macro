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

To find the exact name a new biome uses, trigger it once and search your latest Roblox log for `SetRichPresence` — the `hoverText` value is the name.

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
- Added **Blazing Sun**
- Removed Pumpkin Moon and Graveyard
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
- New **Settings** tab: appearance, desktop notifications, start/stop messages, biome duration, start-on-launch, open folder, view crash.log, reset
- New **Test Webhook** button
- Removed the dead "Aura Detection [Not Working]" controls

Enjoy!
