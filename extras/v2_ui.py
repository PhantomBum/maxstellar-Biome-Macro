"""v2 UI -- an alternative interface for maxstellar's Biome Macro.

Drawn with Dear ImGui (DearPyGui). Native window, no browser, no HTML.
Layout follows the same conventions as other Sol's RNG tools: a fixed left rail
with the brand, grouped nav, a status pill and the run controls; content on the
right. Written from scratch for this macro -- no code taken from anywhere.

Not bundled with the macro. Drop this file in plugins/ and restart.
Requires: pip install dearpygui
"""

import os
import time

PLUGIN_NAME = "v2 UI"

# --- palette -----------------------------------------------------------------
BG          = (11, 11, 18)
SIDEBAR     = (15, 15, 23)
CARD        = (20, 20, 31)
CARD_HOVER  = (26, 26, 40)
INPUT       = (16, 16, 24)
BORDER      = (35, 35, 51)
TEXT        = (226, 228, 238)
TEXT_DIM    = (150, 154, 172)
TEXT_MUTED  = (104, 108, 128)
ACCENT      = (124, 91, 245)
ACCENT_TEXT = (184, 164, 250)
GREEN       = (26, 173, 82)
RED         = (229, 57, 53)
AMBER       = (224, 159, 62)

NAV = (("Dashboard", "dash"), ("Biomes", "biomes"),
       ("Webhook", "webhook"), ("Settings", "settings"))

_api = None
_dpg = None
_running = False
_feed = []
_session = {}
_started_at = None
_fonts = {}


def _rgb(value, fallback=(150, 150, 150)):
    try:
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def _load_fonts():
    """Monospace throughout, like the other tools in this space."""
    dpg = _dpg
    candidates = ["CascadiaMono.ttf", "CascadiaCode.ttf", "consola.ttf"]
    path = None
    for name in candidates:
        candidate = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
        if os.path.exists(candidate):
            path = candidate
            break
    if not path:
        return
    with dpg.font_registry():
        _fonts["body"] = dpg.add_font(path, 15)
        _fonts["small"] = dpg.add_font(path, 12)
        _fonts["big"] = dpg.add_font(path, 26)
        _fonts["h2"] = dpg.add_font(path, 18)
    dpg.bind_font(_fonts["body"])


def _base_theme():
    dpg = _dpg
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, BG)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, CARD)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, INPUT)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, CARD_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, CARD_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_Button, CARD)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, CARD_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT)
            dpg.add_theme_color(dpg.mvThemeCol_Border, BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_Separator, BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_Header, CARD_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, CARD_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, BG)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, BORDER)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, CARD_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, ACCENT_TEXT)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 11, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 11)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
    return theme


def _flat(bg, hover, text=TEXT, rounding=6):
    dpg = _dpg
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Button, bg)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, hover)
            dpg.add_theme_color(dpg.mvThemeCol_Text, text)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, rounding)
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.0, 0.5)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 9)
    return theme


def _panel_theme(bg=CARD):
    dpg = _dpg
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, bg)
            dpg.add_theme_color(dpg.mvThemeCol_Border, BORDER)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 14)
    return theme


_themes = {}


def _label(text, colour=TEXT_MUTED, font="small"):
    item = _dpg.add_text(text, color=colour)
    if font in _fonts:
        _dpg.bind_item_font(item, _fonts[font])
    return item


def _section(text):
    _dpg.add_spacer(height=9)
    _label("  " + text.upper(), TEXT_MUTED, "small")
    _dpg.add_spacer(height=1)


def _show_page(page):
    for _, key in NAV:
        _dpg.configure_item(f"page_{key}", show=(page == key))
    for _, key in NAV:
        _dpg.bind_item_theme(f"nav_{key}",
                             _themes["nav_on"] if key == page else _themes["nav_off"])


def _stat_card(tag, caption, value, width):
    dpg = _dpg
    with dpg.child_window(width=width, height=82, border=True, no_scrollbar=True):
        dpg.bind_item_theme(dpg.last_item(), _themes["panel"])
        _label(caption, TEXT_MUTED, "small")
        item = dpg.add_text(value, tag=tag, color=ACCENT_TEXT)
        if "h2" in _fonts:
            dpg.bind_item_font(item, _fonts["h2"])


def _build():
    dpg = _dpg
    api = _api
    main = api.main

    dpg.create_context()
    dpg.create_viewport(title=f"{api.app_name}  |  v2 UI", width=1000, height=680,
                        min_width=900, min_height=620, clear_color=(11, 11, 18, 255))
    dpg.setup_dearpygui()
    _load_fonts()
    dpg.bind_theme(_base_theme())

    _themes["panel"] = _panel_theme()
    _themes["sidebar"] = _panel_theme(SIDEBAR)
    _themes["nav_off"] = _flat(SIDEBAR, CARD_HOVER, TEXT_DIM)
    _themes["nav_on"] = _flat(CARD_HOVER, CARD_HOVER, ACCENT_TEXT)
    _themes["accent"] = _flat(ACCENT, (140, 112, 250), (255, 255, 255))
    _themes["green"] = _flat(GREEN, (34, 197, 94), (255, 255, 255))
    _themes["red"] = _flat(RED, (239, 68, 68), (255, 255, 255))
    _themes["ghost"] = _flat(CARD_HOVER, (36, 36, 54), TEXT)

    with dpg.window(tag="root_window", no_scrollbar=True):
        with dpg.group(horizontal=True):
            # ------------------------------------------------ left rail
            with dpg.child_window(width=220, border=False, tag="sidebar",
                                  no_scrollbar=True):
                dpg.bind_item_theme("sidebar", _themes["sidebar"])
                dpg.add_spacer(height=14)
                dpg.add_spacer(height=2)
                brand = dpg.add_text("  BIOME MACRO", color=TEXT)
                if "h2" in _fonts:
                    dpg.bind_item_font(brand, _fonts["h2"])
                _label(f"  v{api.version}  ·  maxstellar", TEXT_MUTED, "small")
                dpg.add_spacer(height=8)
                dpg.add_separator()

                _section("Navigation")
                for title, key in NAV:
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=10)
                        dpg.add_button(label="  " + title, width=190, height=36,
                                       tag=f"nav_{key}",
                                       callback=lambda s, a, u: _show_page(u), user_data=key)

                _section("Status")
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text("*", tag="status_dot", color=TEXT_MUTED)
                    dpg.add_text("idle", tag="status_text", color=TEXT_DIM)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_text("roblox", color=TEXT_MUTED)
                    dpg.add_text("--", tag="roblox_text", color=TEXT_DIM)

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_button(label="Start", width=190, height=38, tag="btn_start",
                                   callback=lambda: main["init"]())
                    dpg.bind_item_theme("btn_start", _themes["green"])
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=10)
                    dpg.add_button(label="Pause", width=91, height=32, tag="btn_pause",
                                   callback=_toggle_pause)
                    dpg.bind_item_theme("btn_pause", _themes["ghost"])
                    dpg.add_button(label="Stop", width=91, height=32, tag="btn_stop",
                                   callback=lambda: main["stop"]())
                    dpg.bind_item_theme("btn_stop", _themes["red"])
                dpg.add_spacer(height=12)

            # ------------------------------------------------ content
            with dpg.child_window(border=False):
                dpg.add_spacer(height=14)

                # ---------- dashboard
                with dpg.group(tag="page_dash"):
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=16)
                        with dpg.group():
                            _label("CURRENT BIOME")
                            cur = dpg.add_text("None", tag="cur_biome", color=TEXT_DIM)
                            if "big" in _fonts:
                                dpg.bind_item_font(cur, _fonts["big"])
                            dpg.add_spacer(height=10)
                            with dpg.group(horizontal=True):
                                _stat_card("stat_total", "BIOMES THIS SESSION", "0", 232)
                                _stat_card("stat_uptime", "UPTIME", "--", 232)
                                _stat_card("stat_last", "LAST BIOME", "--", 232)
                            dpg.add_spacer(height=12)
                            _label("LIVE FEED")
                            with dpg.child_window(height=-14, width=-16, tag="feed_panel",
                                                  border=True):
                                dpg.bind_item_theme("feed_panel", _themes["panel"])
                                _label("Nothing yet. Press Start.", TEXT_MUTED, "small")

                # ---------- biomes
                with dpg.group(tag="page_biomes", show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=16)
                        with dpg.group():
                            _label("NOTIFICATION PER BIOME")
                            dpg.add_spacer(height=6)
                            with dpg.child_window(height=-14, width=-16, border=True) as panel:
                                dpg.bind_item_theme(panel, _themes["panel"])
                                for name, info in api.biomes.items():
                                    if not info["configurable"]:
                                        continue
                                    with dpg.group(horizontal=True):
                                        dpg.add_text("#", color=_rgb(info["color"]))
                                        dpg.add_text(info["label"].ljust(14), color=TEXT)
                                        dpg.add_combo(("Message", "Ping", "Nothing"), width=150,
                                                      default_value=api.state["actions"].get(
                                                          name, info["default"]),
                                                      callback=_on_action, user_data=name)
                                dpg.add_spacer(height=6)
                                _label("Glitched, Dreamspace, Cyberspace and Singularity are "
                                       "always on and cannot be changed.", TEXT_MUTED, "small")

                # ---------- webhook
                with dpg.group(tag="page_webhook", show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=16)
                        with dpg.group():
                            _label("DISCORD")
                            dpg.add_spacer(height=6)
                            with dpg.child_window(height=280, width=-16, border=True) as panel:
                                dpg.bind_item_theme(panel, _themes["panel"])
                                _label("WEBHOOK URL")
                                dpg.add_input_text(tag="in_webhook", width=-1, password=True,
                                                   default_value=main["webhookURL"].get(),
                                                   callback=lambda s, a: _set(main["webhookURL"], a))
                                dpg.add_spacer(height=8)
                                _label("PRIVATE SERVER LINK")
                                dpg.add_input_text(tag="in_ps", width=-1,
                                                   default_value=main["psURL"].get(),
                                                   callback=lambda s, a: _set(main["psURL"], a))
                                dpg.add_spacer(height=8)
                                _label("DISCORD USER ID  (leave empty for no pings)")
                                dpg.add_input_text(tag="in_discid", width=-1,
                                                   default_value=main["discID"].get(),
                                                   callback=lambda s, a: _set(main["discID"], a))
                                dpg.add_spacer(height=14)
                                dpg.add_button(label="Send test message", height=34, width=190,
                                               tag="btn_test",
                                               callback=lambda: main["send_test_webhook"]())
                                dpg.bind_item_theme("btn_test", _themes["accent"])

                # ---------- settings
                with dpg.group(tag="page_settings", show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=16)
                        with dpg.group():
                            _label("PREFERENCES")
                            dpg.add_spacer(height=6)
                            with dpg.child_window(height=300, width=-16, border=True) as panel:
                                dpg.bind_item_theme(panel, _themes["panel"])
                                for text, var, key in (
                                        ("Desktop notifications", "desktop_notifications",
                                         "desktop_notifications"),
                                        ("Sound on rare biomes", "sound_alerts", "sound_alerts"),
                                        ("Start/stop webhook messages", "status_messages",
                                         "status_messages"),
                                        ("Show biome duration", "show_duration", "show_duration"),
                                        ("Ping ID is a role", "ping_role", "ping_role"),
                                        ("Start detecting on launch", "autostart", "autostart")):
                                    dpg.add_checkbox(label="  " + text,
                                                     default_value=bool(main[var].get()),
                                                     callback=_on_toggle, user_data=(var, key))
                                dpg.add_spacer(height=14)
                                with dpg.group(horizontal=True):
                                    dpg.add_button(label="Open folder", width=150, height=32,
                                                   tag="btn_folder",
                                                   callback=lambda: main["open_folder"]())
                                    dpg.bind_item_theme("btn_folder", _themes["ghost"])
                                    dpg.add_button(label="View log", width=150, height=32,
                                                   tag="btn_log",
                                                   callback=lambda: main["open_crash_log"]())
                                    dpg.bind_item_theme("btn_log", _themes["ghost"])

    dpg.set_primary_window("root_window", True)
    _show_page("dash")
    dpg.show_viewport()


# --- callbacks ---------------------------------------------------------------

def _set(var, value):
    try:
        var.set(value)
    except Exception as exc:
        _api.log(f"could not set field: {exc}")


def _toggle_pause():
    _api.main["pause"]()
    paused = _api.main.get("paused", False)
    _dpg.configure_item("btn_pause", label="Resume" if paused else "Pause")


def _on_action(sender, value, biome):
    try:
        main = _api.main
        main["set_cfg"]("Biomes", _api.biomes[biome]["slug"], value)
        _api.state["actions"][biome] = value
        main["biome_vars"][biome].set(value)
    except Exception as exc:
        _api.log(f"could not change {biome}: {exc}")


def _on_toggle(sender, value, payload):
    var, key = payload
    try:
        main = _api.main
        main[var].set(1 if value else 0)
        main["toggle_setting"](key, main[var])
    except Exception as exc:
        _api.log(f"could not toggle {key}: {exc}")


# --- events ------------------------------------------------------------------

def _feed_line(stamp, text, colour):
    with _dpg.group(horizontal=True, parent="feed_panel"):
        item = _dpg.add_text(stamp, color=TEXT_MUTED)
        if "small" in _fonts:
            _dpg.bind_item_font(item, _fonts["small"])
        _dpg.add_text(text, color=colour)


def _push(text, colour):
    _feed.insert(0, (time.strftime("%H:%M:%S"), text, colour))
    del _feed[60:]
    for child in _dpg.get_item_children("feed_panel", 1) or []:
        _dpg.delete_item(child)
    for stamp, line, col in _feed:
        _feed_line(stamp, line, col)


def _on_biome_start(biome):
    colour = _rgb(_api.biome_info(biome)["color"])
    _session[biome] = _session.get(biome, 0) + 1
    if _dpg.does_item_exist("cur_biome"):
        _dpg.set_value("cur_biome", biome)
        _dpg.configure_item("cur_biome", color=colour)
        _dpg.set_value("stat_total", str(sum(_session.values())))
        _dpg.set_value("stat_last", biome[:14])
    _push(f"{biome} started", colour)


def _on_biome_end(biome, seconds):
    if _dpg.does_item_exist("cur_biome"):
        _dpg.set_value("cur_biome", "None")
        _dpg.configure_item("cur_biome", color=TEXT_DIM)
    _push(f"{biome} ended  ({seconds}s)", TEXT_DIM)


def _on_macro_start():
    global _started_at
    _started_at = time.time()
    if _dpg.does_item_exist("status_text"):
        _dpg.set_value("status_text", "running")
        _dpg.configure_item("status_text", color=GREEN)
        _dpg.configure_item("status_dot", color=GREEN)
    _push("detection started", GREEN)


def _on_macro_stop():
    if _dpg.does_item_exist("status_text"):
        _dpg.set_value("status_text", "stopped")
        _dpg.configure_item("status_text", color=AMBER)
        _dpg.configure_item("status_dot", color=AMBER)


# --- loop --------------------------------------------------------------------

def _tick():
    if not _running:
        return
    try:
        if not _dpg.is_dearpygui_running():
            _shutdown()
            return
        if _dpg.does_item_exist("stat_uptime") and _started_at:
            secs = int(time.time() - _started_at)
            _dpg.set_value("stat_uptime",
                           f"{secs // 3600}h {secs % 3600 // 60}m" if secs >= 3600
                           else f"{secs // 60}m {secs % 60}s")
        if _dpg.does_item_exist("roblox_text"):
            up = _api.main["_proc_cache"]["running"]
            _dpg.set_value("roblox_text", "open" if up else "closed")
            _dpg.configure_item("roblox_text", color=GREEN if up else TEXT_MUTED)
        _dpg.render_dearpygui_frame()
    except Exception as exc:
        _api.log(f"render stopped: {exc}")
        _shutdown()
        return
    _api.root.after(16, _tick)


def _shutdown():
    global _running
    if not _running:
        return
    _running = False
    try:
        _dpg.destroy_context()
    except Exception:
        pass


def register(api):
    global _api, _dpg, _running
    _api = api
    try:
        import dearpygui.dearpygui as dpg
    except ImportError:
        api.log("dearpygui not installed -- v2 UI disabled. Run: pip install dearpygui")
        return
    _dpg = dpg
    _build()
    _running = True
    api.on("biome_start", _on_biome_start)
    api.on("biome_end", _on_biome_end)
    api.on("macro_start", _on_macro_start)
    api.on("macro_stop", _on_macro_stop)
    api.root.after(16, _tick)
    api.log("v2 UI open")
