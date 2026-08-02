import os
import time
import json
import queue
import threading
import webbrowser
import psutil
import discord_webhook
import configparser
import customtkinter
import logging
import sys
import ctypes
from PIL import Image

APP_VERSION = "2.5"
APP_NAME = "maxstellar's Biome Macro"
THUMB_BASE_URL = "https://maxstellar.github.io/biome_thumb/"
FOOTER_ICON_URL = "https://maxstellar.github.io/maxstellar.png"
UNKNOWN_BIOME_COLOR = "ff69b4"

dirname = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    filename=os.path.join(dirname, 'crash.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mylogger')


def message_box(text, title):
    ctypes.windll.user32.MessageBoxW(0, text, title, 0)


def my_handler(types, value, tb):
    logger.exception("Uncaught exception: {0}".format(str(value)))
    message_box("Check crash.log for information on this crash.", "Crashed!")
    sys.exit()


# exception handler / logger
sys.excepthook = my_handler


# ---------------------------------------------------------------- biome registry

def biome_slug(name):
    return name.replace(" ", "_").lower()


# Fallback registry, used only if biomes.json is missing or unreadable so the macro
# still runs instead of refusing to start.
FALLBACK_BIOMES = [
    {"name": "WINDY", "label": "Windy", "color": "91F7FF", "default": "Message", "everyone": False},
    {"name": "SNOWY", "label": "Snowy", "color": "C4F5F6", "default": "Message", "everyone": False},
    {"name": "RAINY", "label": "Rainy", "color": "4385FF", "default": "Message", "everyone": False},
    {"name": "SAND STORM", "label": "Sand Storm", "color": "F4C27C", "default": "Message", "everyone": False},
    {"name": "HELL", "label": "Hell", "color": "5C1219", "default": "Message", "everyone": False},
    {"name": "STARFALL", "label": "Starfall", "color": "6784E0", "default": "Message", "everyone": False},
    {"name": "CORRUPTION", "label": "Corruption", "color": "9042FF", "default": "Message", "everyone": False},
    {"name": "NULL", "label": "Null", "color": "000000", "default": "Message", "everyone": False},
    {"name": "GLITCHED", "label": "Glitched", "color": "65FF65", "default": "Ping", "everyone": True},
]


def load_biomes():
    path = os.path.join(dirname, 'biomes.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            entries = json.load(f)['biomes']
    except Exception as exc:
        logger.error("Could not read biomes.json (%s), using built-in list.", exc)
        entries = FALLBACK_BIOMES
    registry = {}
    for entry in entries:
        name = entry['name'].upper()
        registry[name] = {
            'name': name,
            'label': entry.get('label', name.title()),
            'color': entry.get('color', UNKNOWN_BIOME_COLOR),
            'thumbnail': entry.get('thumbnail', name.replace(' ', '_') + '.png'),
            'default': entry.get('default', 'Message'),
            'everyone': bool(entry.get('everyone', False)),
            'slug': biome_slug(name),
        }
    return registry


BIOMES = load_biomes()


def thumb_url(info):
    """Empty thumbnail in biomes.json means 'no art for this one yet' -- better than
    pointing Discord at a URL that 404s."""
    return THUMB_BASE_URL + info['thumbnail'] if info['thumbnail'] else None


def biome_info(name):
    """Registry entry for a biome, or a synthetic one if the game added a biome we
    don't know about yet. Unknown biomes still notify -- they just use a fallback colour."""
    if name in BIOMES:
        return BIOMES[name]
    return {
        'name': name,
        'label': name.title(),
        'color': UNKNOWN_BIOME_COLOR,
        'thumbnail': name.replace(' ', '_') + '.png',
        'default': 'Message',
        'everyone': False,
        'slug': biome_slug(name),
        'unknown': True,
    }


# ---------------------------------------------------------------- config

config_name = os.path.join(dirname, 'config.ini')
config = configparser.ConfigParser()

DEFAULTS = {
    'Webhook': {'webhook_url': "", 'private_server': "", 'discord_user_id': "", 'multi_webhook': "0",
                'multi_webhook_urls': ""},
    'Macro': {'aura_detection': "0", 'aura_ping': "0", 'min_rarity_to_ping': "", 'last_roblox_version': "",
              'roblox_username': "", 'seen_notice': "0"},
    'Settings': {'appearance': "Dark", 'desktop_notifications': "1", 'status_messages': "1",
                 'show_duration': "1", 'autostart': "0", 'poll_interval': "0.1"},
    'Biomes': {},
}

if os.path.exists(config_name):
    config.read(config_name)


def save_config():
    with open(config_name, 'w') as configfile:
        config.write(configfile)


def ensure_config():
    """Create any missing section/key without clobbering what the user already set.
    This replaces the old try/except-on-missing-key pattern, which left globals undefined."""
    changed = False
    for section, values in DEFAULTS.items():
        if not config.has_section(section):
            config.add_section(section)
            changed = True
        for key, value in values.items():
            if not config.has_option(section, key):
                config.set(section, key, value)
                changed = True
    for info in BIOMES.values():
        if not config.has_option('Biomes', info['slug']):
            config.set('Biomes', info['slug'], info['default'])
            changed = True
    if changed:
        save_config()


ensure_config()


def cfg(section, key, fallback=""):
    return config.get(section, key, fallback=fallback)


def set_cfg(section, key, value):
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, str(value))
    save_config()


# ---------------------------------------------------------------- UI window

customtkinter.set_default_color_theme("dark-blue")
customtkinter.set_appearance_mode(cfg('Settings', 'appearance', 'Dark'))
root = customtkinter.CTk()
root.title(APP_NAME)
root.geometry('505x285')
root.resizable(False, False)
root.iconbitmap(os.path.join(dirname, 'icon.ico'))
tabview = customtkinter.CTkTabview(root, width=505, height=230)
tabview.grid(row=0, column=0, sticky='nsew', columnspan=75)
tabview.add("Webhook")
tabview.add("Macro")
tabview.add("Settings")
tabview.add("Credits")
tabview._segmented_button.configure(font=customtkinter.CTkFont(family="Segoe UI", size=15))
tabview._segmented_button.grid(sticky="w", padx=15)

webhookURL = customtkinter.StringVar(root, cfg('Webhook', 'webhook_url'))
psURL = customtkinter.StringVar(root, cfg('Webhook', 'private_server'))
discID = customtkinter.StringVar(root, cfg('Webhook', 'discord_user_id'))
multi_webhook = customtkinter.StringVar(root, cfg('Webhook', 'multi_webhook', '0'))
if multi_webhook.get() != "1" and webhookURL.get() == "Multi-Webhook On":
    webhookURL.set("")
webhook_urls_string = customtkinter.StringVar(root, cfg('Webhook', 'multi_webhook_urls'))
webhook_urls = webhook_urls_string.get().split()
roblox_username = customtkinter.StringVar(root, cfg('Macro', 'roblox_username'))

appearance = customtkinter.StringVar(root, cfg('Settings', 'appearance', 'Dark'))
desktop_notifications = customtkinter.IntVar(root, int(cfg('Settings', 'desktop_notifications', '1')))
status_messages = customtkinter.IntVar(root, int(cfg('Settings', 'status_messages', '1')))
show_duration = customtkinter.IntVar(root, int(cfg('Settings', 'show_duration', '1')))
autostart = customtkinter.IntVar(root, int(cfg('Settings', 'autostart', '0')))

# per-biome action vars, built from the registry instead of one hand-written global each
biome_vars = {}
for _name, _info in BIOMES.items():
    biome_vars[_name] = customtkinter.StringVar(root, cfg('Biomes', _info['slug'], _info['default']))

seen_notice = cfg('Macro', 'seen_notice', '0')
if seen_notice == "0":
    set_cfg('Macro', 'seen_notice', "1")

# Tk variables are not safe to touch from another thread, so the detection worker reads
# this plain snapshot instead. The UI writes it; the worker only ever reads it.
RT = {
    'targets': [],
    'ps_url': "",
    'disc_id': "",
    'notifications': True,
    'status_messages': True,
    'show_duration': True,
    'actions': {name: info['default'] for name, info in BIOMES.items()},
}


def refresh_runtime():
    """Copy everything the worker needs out of the Tk vars. Call from the main thread only."""
    if multi_webhook.get() == "1":
        targets = [u for u in webhook_urls if u.startswith("https://") and "discord" in u]
    else:
        url = webhookURL.get().strip()
        targets = [url] if url.startswith("https://") and "discord" in url else []
    RT['targets'] = targets
    RT['ps_url'] = psURL.get().strip()
    RT['disc_id'] = discID.get().strip()
    RT['notifications'] = desktop_notifications.get() == 1
    RT['status_messages'] = status_messages.get() == 1
    RT['show_duration'] = show_duration.get() == 1
    for name, var in biome_vars.items():
        RT['actions'][name] = var.get()

# ---------------------------------------------------------------- state

versions_directory = os.path.expandvars(r"%localappdata%\Roblox\Versions")
log_directory = os.path.expandvars(r"%localappdata%\Roblox\logs")
packages_path = os.path.expandvars(r"%localappdata%\Packages")
roblox_folder = None
roblox_log_path = None
roblox_version = None

started = False
paused = False
stop_event = threading.Event()
ui_queue = queue.Queue()
worker = None

try:
    from win11toast import toast as _toast
except Exception:  # win11toast is optional; the macro works fine without it
    _toast = None


def notify_desktop(title, body):
    if _toast is None or not RT['notifications']:
        return
    try:
        _toast(title, body, duration="short")
    except Exception as exc:
        logger.warning("Desktop notification failed: %s", exc)


def set_title(suffix=None):
    ui_queue.put(("title", APP_NAME + (" - " + suffix if suffix else "")))


def get_action(biome_name):
    return RT['actions'].get(biome_name, biome_info(biome_name)['default'])


# ---------------------------------------------------------------- webhooks

def have_valid_webhook():
    refresh_runtime()
    return len(RT['targets']) > 0


def send(embed=None, content=None):
    """Single send path for both single- and multi-webhook mode.

    The old code duplicated ~90 lines between the two modes and called execute()
    even when there was nothing to send, which Discord rejects with a 400.
    """
    if embed is None and not content:
        return
    targets = RT['targets']
    if not targets:
        logger.warning("Nothing sent: no valid webhook URL configured.")
        return
    for url in targets:
        try:
            # timeout matters: without it a slow Discord response hangs the closing
            # of the window, and stalls the detection thread behind it
            hook = discord_webhook.DiscordWebhook(url=url, timeout=10)
            if embed is not None:
                hook.add_embed(embed)
            if content:
                hook.set_content(content)
            response = hook.execute()
            if response is not None and getattr(response, 'status_code', 200) >= 400:
                logger.error("Webhook rejected (%s): %s", response.status_code, response.text[:300])
        except Exception as exc:
            logger.error("Webhook send failed: %s", exc)


def make_embed(description, color=None, thumbnail=None, include_ps=False):
    embed = discord_webhook.DiscordEmbed(title="[" + time.strftime('%H:%M:%S') + "]", description=description)
    if color:
        embed.set_color(color)
    embed.set_footer(text=f"{APP_NAME} | v{APP_VERSION}", icon_url=FOOTER_ICON_URL)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if include_ps and RT['ps_url']:
        embed.add_embed_field(name="Private Server Link", value=RT['ps_url'])
    return embed


def send_status(text):
    if not RT['status_messages']:
        return
    send(make_embed("[" + time.strftime('%H:%M:%S') + "]: " + text))


def format_duration(seconds):
    seconds = int(seconds)
    if seconds >= 3600:
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m {seconds % 60}s"
    if seconds >= 60:
        return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds}s"


def announce_biome_start(biome):
    info = biome_info(biome)
    action = get_action(biome)
    ui_queue.put(("log", time.strftime('%H:%M:%S') + f": Biome Started - {biome}"))
    if info.get('unknown'):
        logger.warning("Unknown biome '%s' -- add it to biomes.json to give it a colour and thumbnail.", biome)
    notify_desktop("Biome Started", biome)
    if action == "Nothing":
        return
    description = "> ## Biome Started - " + biome
    if info.get('unknown'):
        description += "\n> *(new biome -- not in biomes.json yet)*"
    embed = make_embed(description, color=info['color'],
                       thumbnail=thumb_url(info), include_ps=True)
    content = None
    if info['everyone']:
        content = "@everyone"
    elif action == "Ping" and RT['disc_id'].isnumeric():
        content = f"<@{RT['disc_id']}>"
    send(embed, content)


def announce_biome_end(biome, started_at):
    info = biome_info(biome)
    ui_queue.put(("log", time.strftime('%H:%M:%S') + f": Biome Ended - {biome}"))
    if get_action(biome) == "Nothing":
        return
    description = "> ## Biome Ended - " + biome
    if RT['show_duration'] and started_at:
        description += "\n> Lasted " + format_duration(time.time() - started_at)
    send(make_embed(description, color=info['color'], thumbnail=thumb_url(info)))


# ---------------------------------------------------------------- roblox / log discovery

def detect_roblox_version():
    global roblox_log_path, roblox_version, roblox_folder
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'] or ""
        except Exception:
            continue
        if 'RobloxPlayerBeta.exe' in name:
            if roblox_version != 'player':
                roblox_version = 'player'
                roblox_log_path = log_directory
            return 'player'
        elif 'Windows10Universal.exe' in name:
            if roblox_version != 'store':
                roblox_version = 'store'
                for folder in os.listdir(packages_path):
                    if folder.startswith("ROBLOXCORPORATION.ROBLOX"):
                        roblox_folder = folder
                        roblox_log_path = os.path.join(packages_path, roblox_folder, "LocalState", "logs")
            return 'store'
    return None


def is_roblox_running():
    return detect_roblox_version() is not None


def get_latest_log_file():
    if not roblox_log_path or not os.path.isdir(roblox_log_path):
        return None
    try:
        files = [f for f in os.listdir(roblox_log_path) if f.endswith(".log") and "Installer" not in f]
    except OSError as exc:
        logger.error("Could not list log directory: %s", exc)
        return None
    if not files:
        return None
    latest = max(files, key=lambda f: os.path.getctime(os.path.join(roblox_log_path, f)))
    return os.path.join(roblox_log_path, latest)


def wait_for_log_file(timeout=30):
    """Roblox writes its log a moment after the process appears, so poll instead of
    the old fixed sleep, which sometimes returned 'No log files found'."""
    deadline = time.time() + timeout
    while time.time() < deadline and not stop_event.is_set():
        path = get_latest_log_file()
        if path:
            return path
        time.sleep(0.5)
    return None


# ---------------------------------------------------------------- detection worker

def parse_hover_text(line):
    marker = '{"command":"SetRichPresence"'
    start = line.find(marker)
    if start == -1:
        return None
    try:
        data = json.loads(line[start:])
    except json.JSONDecodeError:
        # Roblox occasionally flushes a partial line; skipping it is correct.
        return None
    hover = data.get("data", {}).get("largeImage", {}).get("hoverText", "")
    return hover.strip().upper() if hover else None


def watch_loop():
    """Runs on a worker thread. Never touches widgets directly -- UI updates go
    through ui_queue so Tk only ever runs on the main thread."""
    last_event = None
    biome_started_at = None
    current_path = None
    handle = None
    roblox_was_running = False
    last_rotation_check = 0.0
    poll = float(cfg('Settings', 'poll_interval', '0.1') or 0.1)

    try:
        while not stop_event.is_set():
            if not is_roblox_running():
                if roblox_was_running:
                    ui_queue.put(("log", "Roblox was closed/crashed, waiting for it to start..."))
                    send_status("Roblox was closed/crashed.")
                    if handle:
                        handle.close()
                        handle = None
                    current_path = None
                    last_event = None
                    roblox_was_running = False
                set_title("No Roblox Detected")
                stop_event.wait(0.5)
                continue

            if not roblox_was_running:
                roblox_was_running = True
                ui_queue.put(("log", "Detected Roblox " + ("Player." if roblox_version == "player" else "Microsoft Store.")))

            # (re)open the log, and re-check periodically so a mid-session rotation
            # doesn't leave us tailing a dead file forever
            if handle is None or time.time() - last_rotation_check > 5:
                last_rotation_check = time.time()
                latest = get_latest_log_file() if handle is not None else wait_for_log_file()
                if latest and latest != current_path:
                    if handle:
                        ui_queue.put(("log", "Log file rotated, switching over."))
                        handle.close()
                    try:
                        handle = open(latest, 'r', encoding='utf-8', errors='ignore')
                    except OSError as exc:
                        logger.error("Could not open log file %s: %s", latest, exc)
                        handle = None
                        stop_event.wait(1)
                        continue
                    current_path = latest
                    # A log created in the last minute belongs to a session that just
                    # started, so read it from the top to catch the biome we joined into.
                    # Anything older gets tailed from the end so we don't replay history.
                    try:
                        brand_new = time.time() - os.path.getctime(latest) < 60
                    except OSError:
                        brand_new = False
                    if not brand_new:
                        handle.seek(0, 2)
                    ui_queue.put(("log", f"Using log file: {current_path}"))
                    set_title("Running")
                elif handle is None:
                    ui_queue.put(("log", "No log files found."))
                    stop_event.wait(2)
                    continue

            # detect truncation (same path, file replaced under us)
            try:
                if os.path.getsize(current_path) < handle.tell():
                    handle.seek(0)
            except OSError:
                pass

            line = handle.readline()
            if not line:
                stop_event.wait(poll)
                continue
            if paused:
                continue

            if '"command":"SetRichPresence"' not in line:
                continue
            event = parse_hover_text(line)
            if not event or event == last_event:
                continue

            if event == "NORMAL":
                if last_event is not None:
                    announce_biome_end(last_event, biome_started_at)
                biome_started_at = None
            else:
                biome_started_at = time.time()
                announce_biome_start(event)
            last_event = event
    except Exception as exc:
        logger.exception("Detection thread crashed: %s", exc)
        ui_queue.put(("log", "Detection stopped -- see crash.log"))
        set_title("Error")
    finally:
        if handle:
            handle.close()


# ---------------------------------------------------------------- controls

def init():
    global started, paused, worker

    if started:
        if paused:
            paused = False
            root.title(APP_NAME + " - Running")
        return

    if not have_valid_webhook():
        message_box("Invalid or missing webhook link.", "Error")
        return
    if not discID.get().strip().isnumeric():
        message_box("Discord User ID should only be a number.\n"
                    "If it is something else, such as @everyone, or your username, "
                    "that is not your Discord User ID.", "Error")
        return

    set_cfg('Webhook', 'webhook_url', webhookURL.get())
    set_cfg('Webhook', 'private_server', psURL.get())
    set_cfg('Webhook', 'discord_user_id', discID.get())
    set_cfg('Macro', 'roblox_username', roblox_username.get())

    for field in (webhook_field, ps_field, discid_field, username_field):
        field.configure(state="disabled", text_color="gray")
    start_button.configure(state="disabled")

    started = True
    paused = False
    stop_event.clear()
    refresh_runtime()
    threading.Thread(target=send_status, args=("Macro started!",), daemon=True).start()
    worker = threading.Thread(target=watch_loop, daemon=True)
    worker.start()
    root.title(APP_NAME + " - Running")


def pause():
    global paused
    if not started:
        return
    paused = not paused
    root.title(APP_NAME + (" - Paused" if paused else " - Running"))


def stop():
    set_cfg('Webhook', 'webhook_url', webhookURL.get())
    set_cfg('Webhook', 'private_server', psURL.get())
    set_cfg('Webhook', 'discord_user_id', discID.get())
    set_cfg('Macro', 'roblox_username', roblox_username.get())
    if started:
        stop_event.set()
        send_status("Macro stopped.")
    root.destroy()


def on_close():
    stop()


def pump_ui():
    """Drains worker messages on the main thread."""
    try:
        while True:
            kind, payload = ui_queue.get_nowait()
            if kind == "title":
                root.title(payload)
            elif kind == "log":
                print(payload)
                logger.info(payload)
    except queue.Empty:
        pass
    root.after(100, pump_ui)


def open_url(url):
    webbrowser.open(url, new=2, autoraise=True)


# ---------------------------------------------------------------- settings callbacks

def set_appearance(value):
    customtkinter.set_appearance_mode(value)
    set_cfg('Settings', 'appearance', value)


def toggle_setting(key, var):
    set_cfg('Settings', key, str(var.get()))
    refresh_runtime()


def open_folder():
    os.startfile(dirname)


def open_crash_log():
    path = os.path.join(dirname, 'crash.log')
    if os.path.exists(path):
        os.startfile(path)
    else:
        message_box("No crash.log yet -- nothing has gone wrong.", "Nothing to show")


def send_test_webhook():
    if not have_valid_webhook():
        message_box("Invalid or missing webhook link.", "Error")
        return

    def _run():
        send(make_embed("> ## Test message\n> If you can read this, your webhook works.",
                        color="6784E0", include_ps=True))
    threading.Thread(target=_run, daemon=True).start()
    notify_desktop("Test sent", "Check your Discord channel.")


def reset_settings():
    for key, value in DEFAULTS['Settings'].items():
        config.set('Settings', key, value)
    save_config()
    appearance.set(DEFAULTS['Settings']['appearance'])
    customtkinter.set_appearance_mode(DEFAULTS['Settings']['appearance'])
    desktop_notifications.set(int(DEFAULTS['Settings']['desktop_notifications']))
    status_messages.set(int(DEFAULTS['Settings']['status_messages']))
    show_duration.set(int(DEFAULTS['Settings']['show_duration']))
    autostart.set(int(DEFAULTS['Settings']['autostart']))
    refresh_runtime()
    message_box("Settings reset to defaults.", "Done")


# ---------------------------------------------------------------- configure pings window

tlw_open = False


def manage_tlw():
    global tlw_open
    if tlw_open:
        return
    tlw_open = True
    tlw = customtkinter.CTkToplevel()
    tlw.title("Configure Pings")

    def _closed():
        global tlw_open
        tlw_open = False
        tlw.destroy()

    tlw.protocol("WM_DELETE_WINDOW", _closed)

    tlw_label = customtkinter.CTkLabel(tlw, text="Choose what you get notified for!",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20))
    tlw_label.grid(row=0, column=0, columnspan=4, pady=10, padx=10)

    scroll = customtkinter.CTkScrollableFrame(tlw, width=560, height=340)
    scroll.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 10))

    def make_setter(name, info):
        def _set(new_val):
            set_cfg('Biomes', info['slug'], new_val)
            RT['actions'][name] = new_val
        return _set

    # built from the registry, so every biome gets a row -- Pumpkin Moon, Graveyard,
    # Heaven and Singularity previously had config entries but no way to change them
    names = list(BIOMES.keys())
    half = (len(names) + 1) // 2
    for index, name in enumerate(names):
        info = BIOMES[name]
        column = 0 if index < half else 2
        row = (index if index < half else index - half) + 1
        label = customtkinter.CTkLabel(scroll, text=info['label'],
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20))
        label.grid(column=column, row=row, padx=(10, 0), pady=10, sticky="w")
        menu = customtkinter.CTkOptionMenu(scroll, values=["Message", "Ping", "Nothing"],
                                           font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                           variable=biome_vars[name], command=make_setter(name, info))
        menu.grid(row=row, column=column + 1, sticky="w", padx=10, pady=10)

    tlw.after(0, tlw.focus)
    tlw.after(100, lambda: tlw.resizable(False, False))
    tlw.after(250, lambda: tlw.iconbitmap(os.path.join(dirname, 'icon.ico')))


# ---------------------------------------------------------------- webhook tab

tabview.set("Webhook")

webhook_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Webhook URL:",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20))
webhook_label.grid(column=0, row=0, columnspan=2, padx=(10, 0), pady=(5, 0), sticky="w")

webhook_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                       width=335, textvariable=webhookURL)
webhook_field.grid(row=0, column=1, padx=(144, 0), pady=(10, 0), sticky="w")
if multi_webhook.get() == "1":
    webhook_field.configure(state="disabled", text_color="gray")
    webhookURL.set("Multi-Webhook On")

ps_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Private Server URL:",
                                  font=customtkinter.CTkFont(family="Segoe UI", size=20))
ps_label.grid(column=0, row=1, padx=(10, 0), pady=(20, 0), columnspan=2, sticky="w")

ps_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                  width=300, textvariable=psURL)
ps_field.grid(row=1, column=1, padx=(179, 0), pady=(23, 0), sticky="w")

discid_label = customtkinter.CTkLabel(tabview.tab("Webhook"), text="Discord User ID:",
                                      font=customtkinter.CTkFont(family="Segoe UI", size=20))
discid_label.grid(column=0, row=2, padx=(10, 0), pady=(20, 0), columnspan=2, sticky="w")

discid_field = customtkinter.CTkEntry(tabview.tab("Webhook"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                      width=324, textvariable=discID)
discid_field.grid(row=2, column=1, padx=(155, 0), pady=(23, 0), sticky="w")

# ---------------------------------------------------------------- macro tab

username_label = customtkinter.CTkLabel(tabview.tab("Macro"), text="Roblox Username:",
                                        font=customtkinter.CTkFont(family="Segoe UI", size=20))
username_label.grid(column=0, row=0, padx=(10, 0), pady=(5, 0), columnspan=2, sticky="w")

username_field = customtkinter.CTkEntry(tabview.tab("Macro"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                        width=307, textvariable=roblox_username)
username_field.grid(row=0, column=1, padx=(172, 0), pady=(10, 0), sticky="w")

biome_button = customtkinter.CTkButton(tabview.tab("Macro"), text="Configure Pings",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                       command=manage_tlw)
biome_button.grid(row=1, column=0, padx=(10, 0), columnspan=2, pady=(15, 0), sticky="w")

test_button = customtkinter.CTkButton(tabview.tab("Macro"), text="Test Webhook",
                                      font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                      command=send_test_webhook)
test_button.grid(row=1, column=1, padx=(172, 0), pady=(15, 0), sticky="w")

biome_count_label = customtkinter.CTkLabel(tabview.tab("Macro"),
                                           text=f"{len(BIOMES)} biomes loaded from biomes.json",
                                           font=customtkinter.CTkFont(family="Segoe UI", size=15))
biome_count_label.grid(row=2, column=0, columnspan=2, padx=(10, 0), pady=(15, 0), sticky="w")

# ---------------------------------------------------------------- settings tab

appearance_label = customtkinter.CTkLabel(tabview.tab("Settings"), text="Appearance:",
                                          font=customtkinter.CTkFont(family="Segoe UI", size=20))
appearance_label.grid(column=0, row=0, padx=(10, 0), pady=(5, 0), sticky="w")

appearance_menu = customtkinter.CTkOptionMenu(tabview.tab("Settings"), values=["Dark", "Light", "System"],
                                              font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                              width=130, variable=appearance, command=set_appearance)
appearance_menu.grid(row=0, column=1, padx=(10, 0), pady=(8, 0), sticky="w")

notif_toggle = customtkinter.CTkCheckBox(tabview.tab("Settings"), text="Desktop notifications",
                                         font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                         variable=desktop_notifications,
                                         command=lambda: toggle_setting('desktop_notifications', desktop_notifications))
notif_toggle.grid(row=1, column=0, columnspan=2, padx=(10, 0), pady=(12, 0), sticky="w")

status_toggle = customtkinter.CTkCheckBox(tabview.tab("Settings"), text="Start/stop webhook messages",
                                          font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                          variable=status_messages,
                                          command=lambda: toggle_setting('status_messages', status_messages))
status_toggle.grid(row=2, column=0, columnspan=2, padx=(10, 0), pady=(10, 0), sticky="w")

duration_toggle = customtkinter.CTkCheckBox(tabview.tab("Settings"), text="Show biome duration when it ends",
                                            font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                            variable=show_duration,
                                            command=lambda: toggle_setting('show_duration', show_duration))
duration_toggle.grid(row=3, column=0, columnspan=2, padx=(10, 0), pady=(10, 0), sticky="w")

autostart_toggle = customtkinter.CTkCheckBox(tabview.tab("Settings"), text="Start detecting on launch",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                             variable=autostart,
                                             command=lambda: toggle_setting('autostart', autostart))
autostart_toggle.grid(row=4, column=0, columnspan=2, padx=(10, 0), pady=(10, 0), sticky="w")

folder_button = customtkinter.CTkButton(tabview.tab("Settings"), text="Open Folder",
                                        font=customtkinter.CTkFont(family="Segoe UI", size=15, weight="bold"),
                                        width=110, command=open_folder)
folder_button.grid(row=5, column=0, padx=(10, 0), pady=(14, 0), sticky="w")

log_button = customtkinter.CTkButton(tabview.tab("Settings"), text="View crash.log",
                                     font=customtkinter.CTkFont(family="Segoe UI", size=15, weight="bold"),
                                     width=110, command=open_crash_log)
log_button.grid(row=5, column=1, padx=(10, 0), pady=(14, 0), sticky="w")

reset_button = customtkinter.CTkButton(tabview.tab("Settings"), text="Reset Settings",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=15, weight="bold"),
                                       width=110, fg_color="#8B2E2E", hover_color="#A33A3A", command=reset_settings)
reset_button.grid(row=5, column=2, padx=(10, 0), pady=(14, 0), sticky="w")

# ---------------------------------------------------------------- credits tab

max_pfp = customtkinter.CTkImage(dark_image=Image.open(os.path.join(dirname, "maxstellar.png")), size=(70, 70))
max_pfp_label = customtkinter.CTkLabel(tabview.tab("Credits"), image=max_pfp, text="")
max_pfp_label.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

sols_sniper = customtkinter.CTkImage(dark_image=Image.open(os.path.join(dirname, "sols_sniper.png")), size=(70, 70))
sols_sniper_label = customtkinter.CTkLabel(tabview.tab("Credits"), image=sols_sniper, text="")
sols_sniper_label.grid(row=1, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

credits_frame = customtkinter.CTkFrame(tabview.tab("Credits"))
credits_frame.grid(row=0, column=1, padx=(7, 0), pady=(10, 0), sticky="w")

credits_frame_2 = customtkinter.CTkFrame(tabview.tab("Credits"))
credits_frame_2.grid(row=1, column=1, padx=(7, 0), pady=(10, 0), sticky="w")

max_label = customtkinter.CTkLabel(credits_frame, text="maxstellar - Creator",
                                   font=customtkinter.CTkFont(family="Segoe UI", size=15, weight="bold"))
max_label.grid(row=0, column=0, padx=(5, 0), sticky="nw")

youtube_link = customtkinter.CTkLabel(credits_frame, text="YouTube", font=("Segoe UI", 14, "underline"),
                                      text_color="dodgerblue", cursor="hand2")
youtube_link.grid(row=1, column=0, padx=(5, 0), sticky="nw")
youtube_link.bind("<Button-1>", lambda e: open_url("https://youtube.com/@maxstellar_"))

sniper_label = customtkinter.CTkLabel(credits_frame_2, text="dannw & yeswe - Developers",
                                      font=customtkinter.CTkFont(family="Segoe UI", size=15, weight="bold"))
sniper_label.grid(row=2, column=0, padx=(5, 0), pady=(5, 0), sticky="nw")

support_link = customtkinter.CTkLabel(credits_frame_2, text="Discord", font=("Segoe UI", 14, "underline"),
                                      text_color="dodgerblue", cursor="hand2")
support_link.grid(row=3, column=0, padx=(5, 0), sticky="nw")
support_link.bind("<Button-1>", lambda e: open_url("https://discord.gg/solsniper"))

version_label = customtkinter.CTkLabel(tabview.tab("Credits"), text=f"v{APP_VERSION}",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=13))
version_label.grid(row=2, column=1, padx=(12, 0), pady=(6, 0), sticky="w")

# ---------------------------------------------------------------- bottom buttons

start_button = customtkinter.CTkButton(root, text="Start",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                       command=init)
start_button.grid(row=1, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

pause_button = customtkinter.CTkButton(root, text="Pause",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                       command=pause)
pause_button.grid(row=1, column=1, padx=(5, 0), pady=(10, 0), sticky="w")

stop_button = customtkinter.CTkButton(root, text="Stop",
                                      font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                      command=stop)
stop_button.grid(row=1, column=2, padx=(5, 0), pady=(10, 0), sticky="w")

# multi-webhook sanity check, kept from the original (including the attitude)
if multi_webhook.get() == "1":
    if len(webhook_urls) < 2:
        message_box("there's no reason to use multi-webhook... without multiple webhooks??", "bruh are you serious")
    elif len(webhook_urls) > 49:
        message_box("you've gotta be doing this on purpose now... you don't need this many webhooks",
                    "this is ridiculous")
    elif len(webhook_urls) > 14:
        message_box("bro you do not need this many webhooks", "okay dude wtf")

root.protocol("WM_DELETE_WINDOW", on_close)
root.bind("<Button-1>", lambda e: e.widget.focus_set())
root.after(100, pump_ui)
if autostart.get() == 1:
    root.after(400, init)

root.mainloop()
