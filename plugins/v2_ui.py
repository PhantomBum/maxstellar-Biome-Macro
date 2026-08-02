"""v2 UI -- a second, nicer interface for the biome macro.

Drawn with Dear ImGui (via DearPyGui). Native window, no browser, no HTML.
The classic window keeps working exactly as before; this opens alongside it.

Delete this file if you don't want it.
"""

import time

PLUGIN_NAME = "v2 UI"
ACCENT = (88, 166, 255)
ACCENT_DIM = (58, 120, 190)
BG = (16, 18, 24)
PANEL = (24, 27, 35)
PANEL_HI = (33, 37, 48)
TEXT = (226, 232, 240)
MUTED = (140, 150, 168)
GOOD = (86, 211, 140)
WARN = (240, 180, 70)

_api = None
_dpg = None
_running = False
_feed = []
_session = {}
_started_at = None
_current = "None"


def _hex_to_rgb(value, fallback=(120, 120, 120)):
    try:
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def _theme():
    dpg = _dpg
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, PANEL_HI)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (44, 50, 64))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_Button, PANEL_HI)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (44, 50, 64))
            dpg.add_theme_color(dpg.mvThemeCol_Header, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, PANEL)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (54, 60, 76))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 7)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 9, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 14)
    return theme


def _accent_button_theme():
    dpg = _dpg
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Button, ACCENT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, ACCENT)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
    return theme


def _show_page(name):
    for page in ("status", "biomes", "webhook", "settings"):
        _dpg.configure_item(f"page_{page}", show=(page == name))


def _set_entry(tk_var, value):
    try:
        tk_var.set(value)
    except Exception:
        pass


def _build():
    dpg = _dpg
    api = _api
    main = api.main  # the macro module's globals

    dpg.create_context()
    dpg.create_viewport(title=f"{api.app_name} — v2 UI", width=940, height=600,
                        min_width=820, min_height=520)
    dpg.setup_dearpygui()
    dpg.bind_theme(_theme())
    accent_theme = _accent_button_theme()

    with dpg.window(tag="root_window"):
        with dpg.group(horizontal=True):
            # ---------------- sidebar ----------------
            with dpg.child_window(width=190, border=False):
                dpg.add_text("BIOME MACRO", color=ACCENT)
                dpg.add_text(f"v{api.version}", color=MUTED)
                dpg.add_spacer(height=14)
                for label, page in (("Status", "status"), ("Biomes", "biomes"),
                                    ("Webhook", "webhook"), ("Settings", "settings")):
                    dpg.add_button(label=label, width=-1, height=36,
                                   callback=lambda s, a, u: _show_page(u), user_data=page)
                dpg.add_spacer(height=18)
                dpg.add_separator()
                dpg.add_spacer(height=10)
                dpg.add_text("DETECTION", color=MUTED)
                dpg.add_text("idle", tag="run_state", color=WARN)
                dpg.add_spacer(height=10)
                b = dpg.add_button(label="Start", width=-1, height=34,
                                   callback=lambda: main["init"]())
                dpg.bind_item_theme(b, accent_theme)
                dpg.add_button(label="Pause", width=-1, height=30,
                               callback=lambda: main["pause"]())

            # ---------------- content ----------------
            with dpg.child_window(border=False):
                # Status
                with dpg.group(tag="page_status"):
                    dpg.add_text("Current biome", color=MUTED)
                    dpg.add_text("None", tag="cur_biome", color=TEXT)
                    dpg.add_spacer(height=6)
                    with dpg.group(horizontal=True):
                        with dpg.child_window(width=210, height=88):
                            dpg.add_text("SESSION", color=MUTED)
                            dpg.add_text("0", tag="stat_total", color=ACCENT)
                            dpg.add_text("biomes seen", color=MUTED)
                        with dpg.child_window(width=210, height=88):
                            dpg.add_text("UPTIME", color=MUTED)
                            dpg.add_text("--", tag="stat_uptime", color=ACCENT)
                            dpg.add_text("since start", color=MUTED)
                        with dpg.child_window(width=210, height=88):
                            dpg.add_text("ROBLOX", color=MUTED)
                            dpg.add_text("checking", tag="stat_roblox", color=MUTED)
                            dpg.add_text("client state", color=MUTED)
                    dpg.add_spacer(height=8)
                    dpg.add_text("Live feed", color=MUTED)
                    with dpg.child_window(height=-1, tag="feed_panel"):
                        dpg.add_text("Waiting for biome activity...", tag="feed_empty", color=MUTED)

                # Biomes
                with dpg.group(tag="page_biomes", show=False):
                    dpg.add_text("Notification per biome", color=MUTED)
                    dpg.add_spacer(height=4)
                    with dpg.child_window(height=-1):
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=False,
                                       borders_innerV=False, borders_outerV=False):
                            dpg.add_table_column(label="Biome")
                            dpg.add_table_column(label="Action", width_fixed=True, init_width_or_weight=150)
                            for name, info in api.biomes.items():
                                if not info["configurable"]:
                                    continue
                                with dpg.table_row():
                                    dpg.add_text(info["label"], color=_hex_to_rgb(info["color"]))
                                    dpg.add_combo(("Message", "Ping", "Nothing"), width=140,
                                                  default_value=api.state["actions"].get(name, info["default"]),
                                                  callback=_on_action_change, user_data=name)

                # Webhook
                with dpg.group(tag="page_webhook", show=False):
                    dpg.add_text("Discord webhook URL", color=MUTED)
                    dpg.add_input_text(tag="in_webhook", width=-1, password=True,
                                       default_value=main["webhookURL"].get(),
                                       callback=lambda s, a: _set_entry(main["webhookURL"], a))
                    dpg.add_spacer(height=6)
                    dpg.add_text("Private server link", color=MUTED)
                    dpg.add_input_text(tag="in_ps", width=-1,
                                       default_value=main["psURL"].get(),
                                       callback=lambda s, a: _set_entry(main["psURL"], a))
                    dpg.add_spacer(height=6)
                    dpg.add_text("Discord user ID (leave empty for no pings)", color=MUTED)
                    dpg.add_input_text(tag="in_discid", width=-1,
                                       default_value=main["discID"].get(),
                                       callback=lambda s, a: _set_entry(main["discID"], a))
                    dpg.add_spacer(height=12)
                    t = dpg.add_button(label="Send test message", height=34,
                                       callback=lambda: main["send_test_webhook"]())
                    dpg.bind_item_theme(t, accent_theme)

                # Settings
                with dpg.group(tag="page_settings", show=False):
                    dpg.add_text("Settings are shared with the classic window", color=MUTED)
                    dpg.add_spacer(height=8)
                    for label, var_name, key in (
                            ("Desktop notifications", "desktop_notifications", "desktop_notifications"),
                            ("Sound on rare biomes", "sound_alerts", "sound_alerts"),
                            ("Start/stop webhook messages", "status_messages", "status_messages"),
                            ("Show biome duration", "show_duration", "show_duration"),
                            ("Ping ID is a role", "ping_role", "ping_role"),
                            ("Start detecting on launch", "autostart", "autostart")):
                        dpg.add_checkbox(label=label, default_value=bool(main[var_name].get()),
                                         callback=_on_toggle, user_data=(var_name, key))
                    dpg.add_spacer(height=14)
                    dpg.add_button(label="Open macro folder", height=32,
                                   callback=lambda: main["open_folder"]())

    dpg.set_primary_window("root_window", True)
    dpg.show_viewport()


def _on_action_change(sender, value, biome):
    try:
        main = _api.main
        main["set_cfg"]("Biomes", _api.biomes[biome]["slug"], value)
        _api.state["actions"][biome] = value
        main["biome_vars"][biome].set(value)
    except Exception as exc:
        _api.log(f"could not change {biome}: {exc}")


def _on_toggle(sender, value, payload):
    var_name, key = payload
    try:
        main = _api.main
        main[var_name].set(1 if value else 0)
        main["toggle_setting"](key, main[var_name])
    except Exception as exc:
        _api.log(f"could not toggle {key}: {exc}")


def _push_feed(text, color):
    _feed.insert(0, (time.strftime("%H:%M:%S"), text, color))
    del _feed[40:]
    if _dpg.does_item_exist("feed_empty"):
        _dpg.delete_item("feed_empty")
    for child in _dpg.get_item_children("feed_panel", 1) or []:
        _dpg.delete_item(child)
    for stamp, line, colour in _feed:
        with _dpg.group(horizontal=True, parent="feed_panel"):
            _dpg.add_text(stamp, color=MUTED)
            _dpg.add_text(line, color=colour)


def _on_biome_start(biome):
    global _current
    _current = biome
    _session[biome] = _session.get(biome, 0) + 1
    colour = _hex_to_rgb(_api.biome_info(biome)["color"])
    if _dpg.does_item_exist("cur_biome"):
        _dpg.set_value("cur_biome", biome)
        _dpg.configure_item("cur_biome", color=colour)
        _dpg.set_value("stat_total", str(sum(_session.values())))
    _push_feed(f"  {biome} started", colour)


def _on_biome_end(biome, seconds):
    global _current
    _current = "None"
    if _dpg.does_item_exist("cur_biome"):
        _dpg.set_value("cur_biome", "None")
        _dpg.configure_item("cur_biome", color=TEXT)
    _push_feed(f"  {biome} ended after {seconds}s", MUTED)


def _on_macro_start():
    global _started_at
    _started_at = time.time()
    if _dpg.does_item_exist("run_state"):
        _dpg.set_value("run_state", "running")
        _dpg.configure_item("run_state", color=GOOD)


def _on_macro_stop():
    if _dpg.does_item_exist("run_state"):
        _dpg.set_value("run_state", "stopped")
        _dpg.configure_item("run_state", color=WARN)


def _tick():
    """Pumped from the Tk event loop so both UIs share one thread."""
    if not _running:
        return
    try:
        if not _dpg.is_dearpygui_running():
            _shutdown()
            return
        if _started_at and _dpg.does_item_exist("stat_uptime"):
            secs = int(time.time() - _started_at)
            _dpg.set_value("stat_uptime", f"{secs // 3600}h {secs % 3600 // 60}m" if secs >= 3600
                           else f"{secs // 60}m {secs % 60}s")
        if _dpg.does_item_exist("stat_roblox"):
            main = _api.main
            up = main["_proc_cache"]["running"]
            _dpg.set_value("stat_roblox", "open" if up else "closed")
            _dpg.configure_item("stat_roblox", color=GOOD if up else WARN)
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
        api.log("dearpygui is not installed, v2 UI disabled. pip install dearpygui")
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
