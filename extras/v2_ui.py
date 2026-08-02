"""v2 UI -- an alternative interface for maxstellar's Biome Macro.

Dear ImGui (DearPyGui). Native window, no browser, no HTML.

Laid out the way the popular Sol's RNG tools are: a run bar across the top, a
grouped left rail, and content cards with corner brackets. Built from the visual
layout only -- no code from any other macro.

Not bundled. Drop in plugins/ and restart.  Requires: pip install dearpygui
"""

import os
import time
from contextlib import contextmanager

PLUGIN_NAME = "v2 UI"

# --- palette -----------------------------------------------------------------
BG         = (10, 15, 22)
RAIL       = (13, 19, 28)
CARD       = (16, 24, 34)
CARD_HI    = (24, 34, 47)
INPUT      = (11, 17, 25)
BORDER     = (30, 43, 58)
BRACKET    = (58, 92, 122)
TEXT       = (222, 232, 242)
DIM        = (140, 158, 178)
MUTED      = (92, 110, 130)
ACCENT     = (94, 214, 233)
ACCENT_DIM = (36, 96, 112)
GREEN      = (35, 170, 95)
GREEN_HI   = (45, 195, 112)
RED        = (208, 62, 62)
AMBER      = (222, 148, 46)
AMBER_HI   = (240, 168, 62)

SECTIONS = (
    ("GENERAL", (("Notice", "notice", "*"), ("Webhook", "webhook", "~"),
                 ("Stats", "stats", "="), ("Status", "status", "o"))),
    ("BIOMES", (("Biome Config", "biomes", "#"), ("Live Feed", "feed", ">"))),
    ("OTHERS", (("Settings", "settings", "+"), ("Credits", "credits", "@"))),
)
PAGES = [key for _, items in SECTIONS for _, key, _ in items]

_api = None
_dpg = None
_running = False
_feed = []
_session = {}
_started_at = None
_fonts = {}
_themes = {}
_cards = []
_page = "notice"


def _rgb(v, fallback=(150, 150, 150)):
    try:
        v = v.lstrip("#")
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def _load_fonts():
    dpg = _dpg
    root = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    path = next((os.path.join(root, n) for n in
                 ("CascadiaMono.ttf", "CascadiaCode.ttf", "consola.ttf")
                 if os.path.exists(os.path.join(root, n))), None)
    if not path:
        return
    with dpg.font_registry():
        _fonts["body"] = dpg.add_font(path, 15)
        _fonts["tiny"] = dpg.add_font(path, 11)
        _fonts["h1"] = dpg.add_font(path, 24)
        _fonts["h2"] = dpg.add_font(path, 17)
    dpg.bind_font(_fonts["body"])


def _font(item, name):
    if name in _fonts:
        _dpg.bind_item_font(item, _fonts[name])
    return item


def _base_theme():
    dpg = _dpg
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvAll):
            for col, val in ((dpg.mvThemeCol_WindowBg, BG), (dpg.mvThemeCol_ChildBg, BG),
                             (dpg.mvThemeCol_PopupBg, CARD), (dpg.mvThemeCol_FrameBg, INPUT),
                             (dpg.mvThemeCol_FrameBgHovered, CARD_HI),
                             (dpg.mvThemeCol_FrameBgActive, CARD_HI),
                             (dpg.mvThemeCol_Button, CARD_HI),
                             (dpg.mvThemeCol_ButtonHovered, ACCENT_DIM),
                             (dpg.mvThemeCol_ButtonActive, ACCENT_DIM),
                             (dpg.mvThemeCol_Text, TEXT), (dpg.mvThemeCol_Border, BORDER),
                             (dpg.mvThemeCol_Separator, BORDER),
                             (dpg.mvThemeCol_Header, CARD_HI),
                             (dpg.mvThemeCol_HeaderHovered, CARD_HI),
                             (dpg.mvThemeCol_HeaderActive, ACCENT_DIM),
                             (dpg.mvThemeCol_ScrollbarBg, BG),
                             (dpg.mvThemeCol_ScrollbarGrab, BORDER),
                             (dpg.mvThemeCol_CheckMark, ACCENT)):
                dpg.add_theme_color(col, val)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 7)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 7)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 10)
    return t


def _btn(bg, hover, text=TEXT, align=0.5, rounding=4):
    dpg = _dpg
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Button, bg)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, hover)
            dpg.add_theme_color(dpg.mvThemeCol_Text, text)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, rounding)
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, align, 0.5)
    return t


def _surface(bg, pad=(18, 16), rounding=4, border=BORDER):
    dpg = _dpg
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, bg)
            dpg.add_theme_color(dpg.mvThemeCol_Border, border)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, rounding)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, pad[0], pad[1])
    return t


def _tiny(text, colour=MUTED):
    return _font(_dpg.add_text(text, color=colour), "tiny")


@contextmanager
def _card(tag, height=None, width=-18):
    """A content card. Corner brackets are drawn over it every frame in _tick."""
    kwargs = {"width": width, "border": True, "tag": tag, "no_scrollbar": True}
    if height:
        kwargs["height"] = height
    with _dpg.child_window(**kwargs) as cw:
        _dpg.bind_item_theme(cw, _themes["card"])
        if tag not in _cards:
            _cards.append(tag)
        yield cw


def _show(page):
    global _page
    _page = page
    for key in PAGES:
        if _dpg.does_item_exist(f"page_{key}"):
            _dpg.configure_item(f"page_{key}", show=(key == page))
        if _dpg.does_item_exist(f"nav_{key}"):
            _dpg.bind_item_theme(f"nav_{key}",
                                 _themes["nav_on"] if key == page else _themes["nav_off"])


def _page_head(title, subtitle):
    _font(_dpg.add_text(title, color=TEXT), "h1")
    _tiny(subtitle, MUTED)
    _dpg.add_spacer(height=8)


def _build():
    dpg, api, main = _dpg, _api, _api.main

    dpg.create_context()
    dpg.create_viewport(title=f"{api.app_name}  |  v2 UI", width=1180, height=720,
                        min_width=980, min_height=620, clear_color=(10, 15, 22, 255))
    dpg.setup_dearpygui()
    _load_fonts()
    dpg.bind_theme(_base_theme())

    _themes["card"] = _surface(CARD, border=BRACKET)
    _themes["rail"] = _surface(RAIL, pad=(0, 0))
    _themes["topbar"] = _surface(RAIL, pad=(12, 10))
    _themes["nav_off"] = _btn(RAIL, CARD_HI, DIM, align=0.0)
    _themes["nav_on"] = _btn(CARD_HI, CARD_HI, ACCENT, align=0.0)
    _themes["green"] = _btn(GREEN, GREEN_HI, (255, 255, 255))
    _themes["amber"] = _btn(AMBER, AMBER_HI, (20, 20, 20))
    _themes["red"] = _btn(RED, (232, 82, 82), (255, 255, 255))
    _themes["ghost"] = _btn(CARD_HI, ACCENT_DIM, DIM)

    with dpg.window(tag="root_window", no_scrollbar=True):
        with dpg.group(horizontal=True):
            # ============================================ left rail
            with dpg.child_window(width=200, border=False, tag="rail", no_scrollbar=True):
                dpg.bind_item_theme("rail", _themes["rail"])
                dpg.add_spacer(height=16)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=14)
                    _font(dpg.add_text("Biome Macro", color=ACCENT), "h2")
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=14)
                    _tiny(f"v{api.version}")
                dpg.add_spacer(height=10)

                for label, items in SECTIONS:
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=14)
                        _tiny(label)
                    dpg.add_spacer(height=2)
                    for title, key, icon in items:
                        with dpg.group(horizontal=True):
                            dpg.add_spacer(width=8)
                            dpg.add_button(label=f" {icon}  {title}", width=184, height=32,
                                           tag=f"nav_{key}", user_data=key,
                                           callback=lambda s, a, u: _show(u))
                    dpg.add_spacer(height=8)

                dpg.add_spacer(height=8)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=14)
                    _tiny("maxstellar's Biome Macro")
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=14)
                    _tiny("v2 UI plugin")

            # ============================================ right side
            with dpg.child_window(border=False, no_scrollbar=True):
                with dpg.child_window(height=56, border=False, tag="topbar",
                                      no_scrollbar=True):
                    dpg.bind_item_theme("topbar", _themes["topbar"])
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="  Start", width=110, height=32,
                                       tag="btn_start", callback=lambda: main["init"]())
                        dpg.bind_item_theme("btn_start", _themes["green"])
                        dpg.add_button(label="Pause", width=84, height=32, tag="btn_pause",
                                       callback=_toggle_pause)
                        dpg.bind_item_theme("btn_pause", _themes["ghost"])
                        dpg.add_button(label="Stop", width=76, height=32, tag="btn_stop",
                                       callback=lambda: main["stop"]())
                        dpg.bind_item_theme("btn_stop", _themes["red"])
                        dpg.add_spacer(width=12)
                        dpg.add_text("*", tag="status_dot", color=MUTED)
                        dpg.add_text("Idle", tag="status_text", color=DIM)
                        dpg.add_spacer(width=22)
                        dpg.add_text("roblox", color=MUTED)
                        dpg.add_text("--", tag="roblox_text", color=MUTED)

                dpg.add_spacer(height=10)
                with dpg.child_window(border=False):
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=18)
                        with dpg.group():
                            _build_pages(dpg, api, main)

    dpg.set_primary_window("root_window", True)
    _show("notice")
    dpg.show_viewport()


def _build_pages(dpg, api, main):
    # ---------------------------------------------------------------- notice
    with dpg.group(tag="page_notice"):
        _page_head("Notice", "Latest updates and patch notes")
        with _card("card_notice"):
            _font(dpg.add_text("v2.5  (What's new?)", color=AMBER), "h2")
            dpg.add_spacer(height=4)
            for line in (
                    "Fixed: the macro watched the Roblox Studio log and never saw a biome",
                    "Fixed: an empty Discord User ID stopped detection entirely",
                    "Fixed: the webhook could replay a log and spam hundreds of messages",
                    "Added: a biome already running is detected the moment you press Start",
                    "Added: plugins, with a template and full docs",
                    "Added: per-biome ping targets, sound alerts, history, session summary",
                    "Changed: exe 30 MB -> 18 MB, ~95% less CPU while idle"):
                dpg.add_text("  -  " + line, color=DIM)
        dpg.add_spacer(height=10)
        with _card("card_notice2", height=96):
            _tiny("BIOMES LOADED")
            dpg.add_text(f"{len(api.biomes)} from biomes.json", color=DIM)
            _tiny("edit biomes.json next to the exe to add one -- no rebuild needed")

    # ---------------------------------------------------------------- webhook
    with dpg.group(tag="page_webhook", show=False):
        _page_head("Webhook", "Configure Discord webhook URLs for notifications")
        with _card("card_user", height=126):
            _font(dpg.add_text("Your Roblox username", color=TEXT), "h2")
            _tiny("Attached to biome alerts so your server knows whose they are")
            dpg.add_input_text(tag="in_user", width=-1, hint="Enter your Roblox username",
                               default_value=main["roblox_username"].get(),
                               callback=lambda s, a: _set(main["roblox_username"], a))
        dpg.add_spacer(height=10)
        with _card("card_hook", height=186):
            _font(dpg.add_text("Discord Webhook URL", color=TEXT), "h2")
            _tiny("Where biome alerts get posted")
            dpg.add_input_text(tag="in_webhook", width=-1, password=True,
                               hint="https://discord.com/api/webhooks/...",
                               default_value=main["webhookURL"].get(),
                               callback=lambda s, a: _set(main["webhookURL"], a))
            dpg.add_spacer(height=6)
            dpg.add_button(label="Test Webhook", width=150, height=30, tag="btn_test",
                           callback=lambda: main["send_test_webhook"]())
            dpg.bind_item_theme("btn_test", _themes["amber"])
        dpg.add_spacer(height=10)
        with _card("card_ps", height=126):
            _font(dpg.add_text("Private Server Link", color=TEXT), "h2")
            _tiny("Your Roblox private server link, sent when a biome starts")
            dpg.add_input_text(tag="in_ps", width=-1, hint="https://www.roblox.com/games/...",
                               default_value=main["psURL"].get(),
                               callback=lambda s, a: _set(main["psURL"], a))
        dpg.add_spacer(height=10)
        with _card("card_id", height=126):
            _font(dpg.add_text("Default ping target", color=TEXT), "h2")
            _tiny("Used for any biome without its own ID. Leave empty for no pings.")
            dpg.add_input_text(tag="in_discid", width=-1, hint="Discord User ID",
                               default_value=main["discID"].get(),
                               callback=lambda s, a: _set(main["discID"], a))

    # ---------------------------------------------------------------- biomes
    with dpg.group(tag="page_biomes", show=False):
        _page_head("Biome Configuration", "Notifications and individual pings per biome")
        with _card("card_biomes"):
            dpg.add_text("GLITCHED, DREAMSPACE, CYBERSPACE and SINGULARITY are always on "
                         "and force @everyone.", color=(206, 96, 96))
            dpg.add_spacer(height=8)
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=False,
                           borders_innerV=False, borders_outerV=False,
                           policy=dpg.mvTable_SizingFixedFit):
                dpg.add_table_column(label="Biome", init_width_or_weight=180)
                dpg.add_table_column(label="Action", init_width_or_weight=140)
                dpg.add_table_column(label="User / Role ID", init_width_or_weight=310)
                dpg.add_table_column(label="Type", init_width_or_weight=120)
                for name, info in api.biomes.items():
                    if not info["configurable"]:
                        continue
                    slug = info["slug"]
                    with dpg.table_row():
                        with dpg.group(horizontal=True):
                            dpg.add_text("*", color=_rgb(info["color"]))
                            dpg.add_text(info["name"], color=_rgb(info["color"]))
                        dpg.add_combo(("Message", "Ping", "Nothing"), width=128,
                                      default_value=api.state["actions"].get(
                                          name, info["default"]),
                                      callback=_on_action, user_data=name)
                        dpg.add_input_text(width=300, hint="User/Role ID",
                                           default_value=api.config.get(
                                               "BiomePings", slug, fallback=""),
                                           callback=_on_ping_id, user_data=slug)
                        dpg.add_combo(("User ID", "Role ID"), width=110,
                                      default_value=("Role ID" if api.config.get(
                                          "BiomePings", slug + "_type", fallback="user")
                                          == "role" else "User ID"),
                                      callback=_on_ping_type, user_data=slug)

    # ---------------------------------------------------------------- feed
    with dpg.group(tag="page_feed", show=False):
        _page_head("Live Feed", "Biome activity this session")
        with _card("card_feed"):
            _tiny("Nothing yet. Press Start.")
            dpg.add_group(tag="feed_panel")

    # ---------------------------------------------------------------- stats
    with dpg.group(tag="page_stats", show=False):
        _page_head("Stats", "This session")
        with dpg.group(horizontal=True):
            for tag, cap in (("stat_total", "BIOMES SEEN"), ("stat_uptime", "UPTIME"),
                             ("stat_last", "LAST BIOME")):
                with _card("card_" + tag, height=96, width=250):
                    _tiny(cap)
                    _font(dpg.add_text("0" if tag == "stat_total" else "--", tag=tag,
                                       color=ACCENT), "h2")
        dpg.add_spacer(height=10)
        with _card("card_breakdown"):
            _tiny("BREAKDOWN")
            dpg.add_text("nothing yet", tag="breakdown_empty", color=MUTED)
            dpg.add_group(tag="breakdown_panel")

    # ---------------------------------------------------------------- status
    with dpg.group(tag="page_status", show=False):
        _page_head("Status", "What the macro is doing right now")
        with _card("card_status", height=196):
            for cap, tag in (("DETECTION", "st_detect"), ("LOG FILE", "st_log"),
                             ("CURRENT BIOME", "st_biome"), ("QUEUED MESSAGES", "st_queue")):
                _tiny(cap)
                dpg.add_text("--", tag=tag, color=DIM)
                dpg.add_spacer(height=4)

    # ---------------------------------------------------------------- settings
    with dpg.group(tag="page_settings", show=False):
        _page_head("Settings", "Shared with the classic window")
        with _card("card_settings", height=262):
            for text, var, key in (
                    ("Desktop notifications", "desktop_notifications", "desktop_notifications"),
                    ("Sound on rare biomes", "sound_alerts", "sound_alerts"),
                    ("Start/stop webhook messages", "status_messages", "status_messages"),
                    ("Show biome duration when it ends", "show_duration", "show_duration"),
                    ("Default ping ID is a role", "ping_role", "ping_role"),
                    ("Start detecting on launch", "autostart", "autostart")):
                dpg.add_checkbox(label="  " + text, default_value=bool(main[var].get()),
                                 callback=_on_toggle, user_data=(var, key))
            dpg.add_spacer(height=12)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Open folder", width=150, height=30, tag="btn_folder",
                               callback=lambda: main["open_folder"]())
                dpg.bind_item_theme("btn_folder", _themes["ghost"])
                dpg.add_button(label="View log", width=150, height=30, tag="btn_log",
                               callback=lambda: main["open_crash_log"]())
                dpg.bind_item_theme("btn_log", _themes["ghost"])

    # ---------------------------------------------------------------- credits
    with dpg.group(tag="page_credits", show=False):
        _page_head("Credits", "Who built this")
        with _card("card_credits", height=164):
            dpg.add_text("maxstellar", color=ACCENT)
            _tiny("original creator  -  youtube.com/@maxstellar_")
            dpg.add_spacer(height=10)
            dpg.add_text("v2 UI", color=ACCENT)
            _tiny("an optional plugin -- delete plugins/v2_ui.py for the classic window")


# --- callbacks ---------------------------------------------------------------

def _set(var, value):
    try:
        var.set(value)
    except Exception as exc:
        _api.log(f"could not set field: {exc}")


def _toggle_pause():
    _api.main["pause"]()
    _dpg.configure_item("btn_pause",
                        label="Resume" if _api.main.get("paused") else "Pause")


def _on_action(sender, value, biome):
    try:
        main = _api.main
        main["set_cfg"]("Biomes", _api.biomes[biome]["slug"], value)
        _api.state["actions"][biome] = value
        main["biome_vars"][biome].set(value)
    except Exception as exc:
        _api.log(f"could not change {biome}: {exc}")


def _on_ping_id(sender, value, slug):
    try:
        _api.main["set_cfg"]("BiomePings", slug, value.strip())
        _api.main["refresh_runtime"]()
    except Exception as exc:
        _api.log(f"could not set ping id for {slug}: {exc}")


def _on_ping_type(sender, value, slug):
    try:
        _api.main["set_cfg"]("BiomePings", slug + "_type",
                             "role" if value == "Role ID" else "user")
        _api.main["refresh_runtime"]()
    except Exception as exc:
        _api.log(f"could not set ping type for {slug}: {exc}")


def _on_toggle(sender, value, payload):
    var, key = payload
    try:
        main = _api.main
        main[var].set(1 if value else 0)
        main["toggle_setting"](key, main[var])
    except Exception as exc:
        _api.log(f"could not toggle {key}: {exc}")


# --- events ------------------------------------------------------------------

def _push(text, colour):
    _feed.insert(0, (time.strftime("%H:%M:%S"), text, colour))
    del _feed[80:]
    if not _dpg.does_item_exist("feed_panel"):
        return
    for child in _dpg.get_item_children("feed_panel", 1) or []:
        _dpg.delete_item(child)
    for stamp, line, col in _feed:
        with _dpg.group(horizontal=True, parent="feed_panel"):
            _font(_dpg.add_text(stamp, color=MUTED), "tiny")
            _dpg.add_text(line, color=col)


def _refresh_breakdown():
    if not _dpg.does_item_exist("breakdown_panel"):
        return
    if _session and _dpg.does_item_exist("breakdown_empty"):
        _dpg.delete_item("breakdown_empty")
    for child in _dpg.get_item_children("breakdown_panel", 1) or []:
        _dpg.delete_item(child)
    for name, count in sorted(_session.items(), key=lambda kv: -kv[1]):
        with _dpg.group(horizontal=True, parent="breakdown_panel"):
            _dpg.add_text(f"{count:>3}x", color=ACCENT)
            _dpg.add_text(name, color=_rgb(_api.biome_info(name)["color"]))


def _on_biome_start(biome):
    colour = _rgb(_api.biome_info(biome)["color"])
    _session[biome] = _session.get(biome, 0) + 1
    if _dpg.does_item_exist("stat_total"):
        _dpg.set_value("stat_total", str(sum(_session.values())))
        _dpg.set_value("stat_last", biome[:14])
    if _dpg.does_item_exist("st_biome"):
        _dpg.set_value("st_biome", biome)
        _dpg.configure_item("st_biome", color=colour)
    _push(f"{biome} started", colour)
    _refresh_breakdown()


def _on_biome_end(biome, seconds):
    if _dpg.does_item_exist("st_biome"):
        _dpg.set_value("st_biome", "None")
        _dpg.configure_item("st_biome", color=DIM)
    _push(f"{biome} ended  ({seconds}s)", DIM)


def _on_macro_start():
    global _started_at
    _started_at = time.time()
    if _dpg.does_item_exist("status_text"):
        _dpg.set_value("status_text", "Running")
        _dpg.configure_item("status_text", color=GREEN_HI)
        _dpg.configure_item("status_dot", color=GREEN_HI)
    _push("detection started", GREEN_HI)


def _on_macro_stop():
    if _dpg.does_item_exist("status_text"):
        _dpg.set_value("status_text", "Stopped")
        _dpg.configure_item("status_text", color=AMBER)
        _dpg.configure_item("status_dot", color=AMBER)


# --- frame -------------------------------------------------------------------



def _tick():
    if not _running:
        return
    try:
        if not _dpg.is_dearpygui_running():
            _shutdown()
            return
        main = _api.main
        if _dpg.does_item_exist("stat_uptime") and _started_at:
            secs = int(time.time() - _started_at)
            _dpg.set_value("stat_uptime", f"{secs // 3600}h {secs % 3600 // 60}m"
                           if secs >= 3600 else f"{secs // 60}m {secs % 60}s")
        if _dpg.does_item_exist("roblox_text"):
            up = main["_proc_cache"]["running"]
            _dpg.set_value("roblox_text", "open" if up else "closed")
            _dpg.configure_item("roblox_text", color=GREEN_HI if up else MUTED)
        if _page == "status" and _dpg.does_item_exist("st_detect"):
            _dpg.set_value("st_detect", "running" if main.get("started") else "idle")
            _dpg.set_value("st_queue", str(main["webhook_queue"].qsize()))
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
