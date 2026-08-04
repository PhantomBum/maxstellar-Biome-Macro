import os
import time
import json
import webbrowser
import psutil
import discord_webhook
import configparser
import customtkinter
import logging
import sys
import ctypes
from PIL import Image

logging.basicConfig(
    filename='crash.log',  # Optional: Specify a file to log to
    level=logging.DEBUG,  # Set the minimum level for logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Customize the log format
)

logger = logging.getLogger('mylogger')


def my_handler(types, value, tb):
    logger.exception("Uncaught exception: {0}".format(str(value)))
    ctypes.windll.user32.MessageBoxW(0, "Check crash.log for information on this crash.", "Crashed!", 0)
    sys.exit()


# exception handler / logger
sys.excepthook = my_handler

# create UI window
customtkinter.set_default_color_theme("dark-blue")
root = customtkinter.CTk()
root.title("maxstellar's Biome Macro")
root.geometry('505x285')
root.resizable(False, False)
dirname = os.path.dirname(__file__)
root.iconbitmap(dirname + '\\icon.ico')
tabview = customtkinter.CTkTabview(root, width=505, height=230)
tabview.grid(row=0, column=0, sticky='nsew', columnspan=75)
tabview.add("Webhook")
tabview.add("Macro")
tabview.add("Credits")
tabview._segmented_button.configure(font=customtkinter.CTkFont(family="Segoe UI", size=16))
tabview._segmented_button.grid(sticky="w", padx=15)

# read configuration file
config_name = 'config.ini'
config = configparser.ConfigParser()
if not os.path.exists(config_name):
    logger.info("Config file not found, creating one...")
    print("Config file not found, creating one...")
    config['Webhook'] = {'webhook_url': "", 'private_server': "", "discord_user_id": "", 'multi_webhook': "0",
                         'multi_webhook_urls': ""}
    config['Macro'] = {'aura_detection': "0", "aura_ping": "0", "min_rarity_to_ping": "", "aura_recording": "0",
                       "record_hotkey": "win+alt+g", "record_delay": "8", "aura_record_minimum": "1000000", "last_roblox_version": "", "roblox_username": "", "seen_notice": "0"}
    config['Biomes'] = {'windy': "Message", 'snowy': "Message", 'rainy': "Message", 'sand_storm': "Message",
                        'hell': "Message", "starfall": "Message",
                        "corruption": "Message", "null": "Message", "blazing_sun": "Message"}
    with open(config_name, 'w') as conffile:
        config.write(conffile)
config.read(config_name)
webhookURL = customtkinter.StringVar(root, config['Webhook']['webhook_url'])
psURL = customtkinter.StringVar(root, config['Webhook']['private_server'])
discID = customtkinter.StringVar(root, config['Webhook']['discord_user_id'])
multi_webhook = customtkinter.StringVar(root, config['Webhook']['multi_webhook'])
if multi_webhook.get() != "1" and webhookURL.get() == "Multi-Webhook On":
    webhookURL.set("")
webhook_urls_string = customtkinter.StringVar(root, config['Webhook']['multi_webhook_urls'])
webhook_urls = webhook_urls_string.get().split()
last_roblox_version = config['Macro']['last_roblox_version']
roblox_username = customtkinter.StringVar(root, config['Macro']['roblox_username'])
try:
    seen_notice = customtkinter.StringVar(root, config['Macro']['seen_notice'])
except:
    seen_notice = customtkinter.StringVar(root, "0")
    config.set('Macro', "seen_notice", "0")
    with open(config_name, 'w+') as configfile:
        config.write(configfile)
if seen_notice.get() == "0":
    seen_notice.set("1")
    config.set('Macro', "seen_notice", "1")
    with open(config_name, 'w+') as configfile:
        config.write(configfile)
    ctypes.windll.user32.MessageBoxW(0,
                                     "Thanks for continuing to use my macro!\n\nPlease check out my fishing macro, fishSol Macro. (discord.gg/fishsol)",
                                     "Notice", 0)

# variables
roblox_open = False
versions_directory = os.path.expandvars(r"%localappdata%\Roblox\Versions")
log_directory = os.path.expandvars(r"%localappdata%\Roblox\logs")
packages_path = os.path.expandvars(r"%localappdata%\Packages")
roblox_folder = None
roblox_log_path = None
roblox_version = None
biome_colors = {"NORMAL": "ffffff", "SAND STORM": "F4C27C",
                "HELL": "5C1219", "STARFALL": "6784E0", "CORRUPTION": "9042FF", "NULL": "000000", "GLITCHED": "65FF65",
                "WINDY": "91F7FF", "SNOWY": "C4F5F6", "RAINY": "4385FF", "DREAMSPACE": "ff7dff",
                "BLAZING SUN": "FFB300", "CYBERSPACE": "2c53a7", "HEAVEN": "e8c49e", "SINGULARITY": "ffa375"}
aura_rarities = {
               "MONARCH": 3000000000, "EQUINOX": 2500000000, "EQUINOX youareanidiot": 2500000000,
               "Dream Catcher": 2222222222, "Dream Traveler": 2025812825, "skyfestival": 2000000000,
               "BREAKTHROUGH": 1999999999, "Yolkegg": 1790909090, "ASTRAIOS": 1750000000, "LEVIATHAN": 1730400000,
               "Winter Garden": 1450012025, "Luminosity": 1200000000, "Aegis EGGIS": 1150000000,
               "Pixelation": 1073741824, "NYCTOPHOBIA": 1011111010, "Sovereign Frostveil": 1000000000,
               "LAMENTHYR": 1000000000, "Eostre": 1000000000, "AFoolsExperience": 1000000000,
               "P.U.K.E.K.O.G.O.D.": 1000000000, "Pool Party": 972000000, "ASCENDANT": 935000000,
               "dreamscape": 850000000, "Poseidon Atlantis": 850000000, "Eisveil": 830000000, "Aegis": 825000000,
               "Ruins Withered": 800000000, "Parol": 760000000, "Sovereign": 750000000, "Workshop": 700000000,
               "Eggore": 700000000, "PYTHIOS": 666666666, "PROLOGUE": 666616111, "Workshop System": 650000000,
               "Sloth": 650000000, "REVIVE": 645000000, "Lumenpool Ramenpool": 630000000,
               "Matrix Reality": 601020102, "Surfer Symphony": 600000000, "Sophyra": 570000000, "Elude": 555555555,
               "Sailor Admiral": 540000000, "Gravitational PointZero": 521121900, "Matrix Overdrive": 503000000,
               "Ruins": 500000000, "Kyawthuite Remembrance": 450000000, "Unknown": 444444444,
               "APOSTOLOS": 444000000, "GARGANTUA": 430000000, "EveNight": 424000000, "NORTHERN": 405000000,
               "AbyssalHunter": 400000000, "Doodle AbyssalHunter": 400000000, "Celestial Eclipse": 384000000,
               "CryoFang": 380000000, "CHILLSEAR": 375000000, "Flora Evergreen": 370073730, "Atlas": 360000000,
               "Archangel": 350000000, "Jazz Orchestra": 336870912, "CYTOKINESIS": 330400472,
               "Dreammetric": 320000000, "LOTUSFALL": 320000000, "Perpetual": 315000000, "dreamer": 315000000,
               "Maelstrom": 309999999, "Eggsistance": 307777777, "BLOODLUST": 300000000,
               "Overture History": 300000000, "Exotic Void": 299999999, "Prophecy": 275649430,
               "Astral Legendarium": 267200000, "Astral Zodiac": 267200000, "Impeached IMCRINE": 250000000,
               "Virtual Memory": 232232232, "ENCASE": 230000000, "Hyper-Volt Ever-Storm": 225000000,
               "Oppression": 220000000, "Lumenpool": 220000000, "Impeached": 200000000, "Raven Plague": 200000000,
               "Projection": 197000000, "Felled": 180000000, "Twilight Withering Grace": 180000000,
               "Symphony": 175000000, "BOUNDED AICHMALOTOS": 170000000, "Overture": 150000000,
               "Sharkyn HammerHead": 120000000, "Lily": 112000000, "Starscourge Radiant": 100000000,
               "Spectraflow": 100000000, "Chromatic Genesis": 99999999, "Quartz Rose": 97500000,
               "Atomic Nucleus": 92118000, "Virtual WorldWide": 87500000, "Runic Wilt": 87388744,
               "HARNESSED Elements": 85000000, "Hellbound": 85000000, "Sailor Flying Dutchman": 80000000,
               "Carriage": 80000000, "Virtual FULL CONTROL": 80000000, "Emperor": 80000000, "Aquaria": 80000000,
               "Melodic Serenade": 77000000, "WinterFantasy": 72000000, "Starborn": 72000000, "Dominion": 70000000,
               "bloatedexe": 67676767, "Reaper": 66000000, "Antivirus": 62500000, "Sentinel": 60000000,
               "SkyBurst": 60000000, "Bayview": 60000000, "vacation": 58620000, "Matrix": 50000000,
               "Runic": 50000000, "Goose Rave": 50000000, "Exotic APEX": 49999500, "NorthPole": 45000000,
               "Overseer": 45000000, "Santa Frost": 45000000, "Juxtaposition": 40440400,
               "Virtual Fatal Error": 40413000, "Kromat1k": 40000000, "Hatchwarden": 40000000, "Ethereal": 35000000,
               "Aether Disappointment": 33333330, "Flora Florest": 32800000, "pukeko Jumping": 31980000,
               "Arcane Dark": 30000000, "Blizzard": 27315000, "Centurion": 25000000, "Apotheosis": 24691356,
               "Frostwood": 24500000, "Ruby Brimstone": 24060000, "Aviator": 24000000, "Oculus": 23333340,
               "Plasma": 20600000, "nostalgia": 20270000, "VerySmallSewageRat": 20070629, "Chromatic": 20000000,
               "Lullaby": 17000000, "ICARUS": 15660000, "Arcane Legacy": 15000000, "Sirius": 14000000,
               "Stormal Hurricane": 13500000, "Borealis": 13333333, "Glitch": 12210110, "imaginary": 12200200,
               "Wonderland": 12000000, "Sailor": 12000000, "Graffiti": 12000000, "Melodic": 11300000,
               "Empty": 11111111, "Illusionary": 10000000, "Starscourge": 10000000, "Sharkyn": 10000000,
               "GUARDIAN": 10000000, "LostSoul Wander": 9400000, "Amethyst": 9333700, "Stargazer": 9200000,
               "Jade Purity": 9200000, "Helios": 9000000, "Nihility": 9000000, "HARNESSED": 8500000,
               "Soultorn": 8333333, "Spectre Requiem": 8222000, "OUTLAW": 8000000, "Origin Onion": 8000000,
               "Divinus Guardian": 7777777, "Nautilus Lost": 7700000, "Velocity": 7630000, "Hyper-Volt": 7500000,
               "Faith": 7250000, "Refraction": 7242000, "Anubis": 7200000, "Celestial Divine": 7000000,
               "Hades": 6666666, "Origin": 6500000, "Astronaut": 6117196, "Twilight": 6000000, "Anima": 5730000,
               "Solar Solstice": 5000000, "Galaxy": 5000000, "Lunar Full Moon": 5000000, "Jackfrost": 4700000,
               "Zeus": 4500000, "Wraith": 4100000, "Aquatic Flame": 4000000, "Poseidon": 4000000,
               "Metabytes": 4000000, "Gingerbread": 3750000, "Crystallized Bejeweled": 3600000,
               "Cosmos Alice": 3500000, "Evanescent": 3360000, "Shiftlock": 3325000, "Savior": 3200000,
               "Apatite": 3133133, "Parasite": 3000000, "Orion": 3000000, "Vega": 2580000, "Virtual": 2500000,
               "Defined": 2222000, "Flowed": 2121121, "Gravitational": 2000000, "BOUNDED UNBOUND": 2000000,
               "Flutter Buggify": 2000000, "BOUNDED KIDNAPPED": 2000000, "Player Respawn": 1999999,
               "Beach Ball": 1938000, "Archmage": 1766000, "Obsidian": 1750000, "Cosmos": 1520000,
               "Astral": 1336000, "SYMBIOSIS": 1331201, "Rage Brawler": 1280000, "StarRider yourdidit": 1234567,
               "Undefined": 1111000, "Magnetic Reverse Polarity": 1024000, "Gothic": 1000001, "Arcane": 1000000,
               ":Flushed: Troll": 1000000, "Starlight Kunzite": 1000000, "Kyawthuite": 850000, "Burger": 676767,
               "Undead Devil": 666666, "Warlock": 666000, "Floaty": 600000, "Prowler": 540000, "Raven": 500000,
               "HOPE": 488725, "Terror": 400000, "Vortex": 399999, "Celestial": 350000, "Cryogenic": 250000,
               "BOUNDED": 200000, "Aether": 180000, "Jazz": 160000, "Spectre": 140000, "Jade": 125000,
               "Comet": 120000, "Divinus Angel": 120000, "Diaboli Void": 100400, "Exotic": 99999, "Stormal": 90000,
               "Flow": 87000, "Constella": 86988, "Pulsar": 83345, "Permafrost": 73500, "Hazard Rays": 70000,
               "Nautilus": 70000, "Flushed Lobotomy": 69000, "Pleiades": 65358, "Solar": 50000, "Lunar": 50000,
               "Starlight": 50000, "StarRider": 50000, "Aquatic": 40000, "Lightning": 40000, "WATT": 32768,
               "COPPER": 29000, "Marsh": 25000, "Gilded Crowned": 20000, "Powered": 16384, "L E A K": 14000,
               "Rage Heated": 12800, "Kawaii": 12300, "Undead": 12000, "Corrosive": 12000, "★★★": 10000,
               "Atomic Ribonucleic": 9876, "Lost Soul": 9200, "Honey": 8335, "Quartz": 8192, "Doodle": 7500,
               "Hazard": 7000, ":Flushed:": 6900, "Flutter": 5000, "TARGETED": 5000, "Bleeding": 4444,
               "Sidereum": 4096, "Cola": 3999, "Flora": 3700, "pukeko": 3198, "PLAYER": 3000, "Fault": 3000,
               "Glacier": 2304, "Ash": 2300, "Magnetic": 2048, "Glock": 1700, "Atomic": 1180, "Hydrogen": 1111,
               "Precious": 1024, "Diaboli": 1004, "★★": 1000}
started = False
stopped = False
paused = False
destroyed = False
debug_window = False
tlw_open = False
aura_detection = customtkinter.IntVar(root, int(config['Macro'].get('aura_detection', "0")))
aura_ping = customtkinter.IntVar(root, int(config['Macro'].get('aura_ping', "0")))
aura_recording = customtkinter.IntVar(root, int(config['Macro'].get('aura_recording', "0")))
windy = customtkinter.StringVar(root, config['Biomes']['windy'])
snowy = customtkinter.StringVar(root, config['Biomes']['snowy'])
rainy = customtkinter.StringVar(root, config['Biomes']['rainy'])
sand_storm = customtkinter.StringVar(root, config['Biomes']['sand_storm'])
hell = customtkinter.StringVar(root, config['Biomes']['hell'])
starfall = customtkinter.StringVar(root, config['Biomes']['starfall'])
corruption = customtkinter.StringVar(root, config['Biomes']['corruption'])
null = customtkinter.StringVar(root, config['Biomes']['null'])
glitched = customtkinter.StringVar(root, "Message")
dreamspace = customtkinter.StringVar(root, "Message")
cyberspace = customtkinter.StringVar(root, "Message")


def biome_setting(name):
    if not config.has_option('Biomes', name):
        config.set('Biomes', name, "Message")
        with open(config_name, 'w+') as configfile:
            config.write(configfile)
    return config['Biomes'][name]


heaven = customtkinter.StringVar(root, biome_setting("heaven"))
singularity = customtkinter.StringVar(root, biome_setting("singularity"))
blazing_sun = customtkinter.StringVar(root, biome_setting("blazing_sun"))


def get_aura_rarity(aura):
    if aura in aura_rarities:
        return aura_rarities[aura]
    wanted = aura.replace("_", " ").strip().lower()
    for name in aura_rarities:
        if name.lower() == wanted:
            return aura_rarities[name]
    return 0


press_keys = {"win": 0x5B, "ctrl": 0x11, "alt": 0x12, "shift": 0x10, "tab": 0x09, "space": 0x20,
              "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74, "f6": 0x75, "f7": 0x76,
              "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B, "printscreen": 0x2C,
              "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34, "5": 0x35, "6": 0x36,
              "7": 0x37, "8": 0x38, "9": 0x39}


def press_record_hotkey():
    hotkey = record_field.get().strip() or "win+alt+g"
    codes = []
    for part in hotkey.lower().replace(" ", "").split("+"):
        if part in press_keys:
            codes.append(press_keys[part])
        elif len(part) == 1:
            codes.append(ord(part.upper()))
    if not codes:
        return
    for code in codes:
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)
    time.sleep(0.05)
    for code in reversed(codes):
        ctypes.windll.user32.keybd_event(code, 0, 2, 0)


def equipped_aura(state):
    if not state.startswith("Equipped"):
        return ""
    aura = state.replace("Equipped", "").strip().strip('"')
    return "" if aura in ("", "_None_") else aura


def aura_rolled(aura):
    rarity = get_aura_rarity(aura)
    minimum = config['Macro'].get('min_rarity_to_ping', "")
    if minimum.isnumeric() and rarity and rarity < int(minimum):
        return
    print(time.strftime('%H:%M:%S') + f": Aura Rolled - {aura}")
    record_minimum = config['Macro'].get('aura_record_minimum', "1000000")
    record_worthy = not record_minimum.isnumeric() or not rarity or rarity >= int(record_minimum)
    if aura_recording.get() == 1 and record_worthy:
        try:
            delay = config['Macro'].get('record_delay', "8")
            root.after(int(float(delay) * 1000) if delay.replace(".", "").isnumeric() else 8000,
                       press_record_hotkey)
        except Exception as exc:
            logger.info("Could not schedule the recording hotkey: " + str(exc))
    if multi_webhook.get() != "1":
        urls = [webhookURL.get()]
    else:
        urls = webhook_urls
    for url in urls:
        if "discord" not in url or "https://" not in url:
            continue
        try:
            embed = discord_webhook.DiscordEmbed(title="[" + time.strftime('%H:%M:%S') + "]",
                                                 color="ffd700",
                                                 description="> ## Aura Rolled - " + aura)
            if rarity:
                embed.add_embed_field(name="Rarity", value="1 in " + format(rarity, ","))
            embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                             icon_url="https://maxstellar.github.io/maxstellar.png")
            webhook = discord_webhook.DiscordWebhook(url=url)
            webhook.add_embed(embed)
            if aura_ping.get() == 1 and discID.get().strip().isnumeric():
                webhook.set_content(f"<@{discID.get().strip()}>")
            webhook.execute()
        except Exception as exc:
            logger.info("Could not send the aura webhook: " + str(exc))


def get_biome_color(biome):
    try:
        return biome_colors[biome]
    except:
        return "ff69b4"


def stop():
    global stopped
    # write config data
    config.set('Webhook', 'webhook_url', webhookURL.get())
    config.set('Webhook', 'private_server', psURL.get())
    config.set('Webhook', 'discord_user_id', discID.get())
    try:
        config.set('Macro', 'min_rarity_to_ping', detectping_field.get() if detectping_field.get().isnumeric() else "")
        config.set('Macro', 'record_hotkey', record_field.get().strip())
    except:
        pass
    with open(config_name, 'w+') as configfile:
        config.write(configfile)

    # end webhook
    if started and not stopped:
        if multi_webhook.get() != "1":
            if "discord" in webhookURL.get() and "https://" in webhookURL.get():
                ending_webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                ending_embed = discord_webhook.DiscordEmbed(
                    description="[" + time.strftime('%H:%M:%S') + "]: Macro stopped.")
                ending_embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                                        icon_url="https://maxstellar.github.io/maxstellar.png")
                ending_webhook.add_embed(ending_embed)
                ending_webhook.execute()
        else:
            ending_embed = discord_webhook.DiscordEmbed(
                description="[" + time.strftime('%H:%M:%S') + "]: Macro stopped.")
            ending_embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                                    icon_url="https://maxstellar.github.io/maxstellar.png")
            for url in webhook_urls:
                ending_webhook = discord_webhook.DiscordWebhook(url=url)
                ending_webhook.add_embed(ending_embed)
                ending_webhook.execute()
    else:
        sys.exit()
    stopped = True


def pause():
    global paused
    paused = not paused
    if paused:
        root.title("maxstellar's Biome Macro - Paused")
    else:
        root.title("maxstellar's Biome Macro - Running")


if multi_webhook.get() == "1":
    if len(webhook_urls) < 2:
        ctypes.windll.user32.MessageBoxW(0, "there's no reason to use multi-webhook... without multiple webhooks??",
                                         "bruh are you serious", 0)
        stop()
    elif len(webhook_urls) > 14:
        if len(webhook_urls) > 49:
            ctypes.windll.user32.MessageBoxW(0,
                                             "you've gotta be doing this on purpose now... you don't need this many webhooks",
                                             "this is ridiculous", 0)
        else:
            ctypes.windll.user32.MessageBoxW(0, "bro you do not need this many webhooks", "okay dude wtf", 0)
        stop()


def x_stop():
    global destroyed
    destroyed = True
    stop()


def detect_roblox_version():
    global roblox_log_path, roblox_version, roblox_folder
    for proc in psutil.process_iter(['name']):
        if 'RobloxPlayerBeta.exe' in proc.info['name']:
            if roblox_version != 'player':
                roblox_version = 'player'
                roblox_log_path = log_directory
            return 'player'
        elif 'Windows10Universal.exe' in proc.info['name']:
            if roblox_version != 'store':
                roblox_version = 'store'
                for folder in os.listdir(packages_path):
                    if folder.startswith("ROBLOXCORPORATION.ROBLOX"):
                        roblox_folder = folder
                        roblox_log_path = os.path.join(packages_path, roblox_folder, "LocalState", "logs")
            return 'store'
    return None


def get_latest_log_file():
    if roblox_log_path:
        files = [f for f in os.listdir(roblox_log_path)
                 if f.endswith(".log") and "Installer" not in f and "Studio" not in f]
        players = [f for f in files if "_Player_" in f]
        if players:
            files = players
        if not files:
            return None
        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(roblox_log_path, f)))
        return os.path.join(roblox_log_path, latest_file)
    return None


def is_roblox_running():
    return detect_roblox_version() is not None


def check_for_hover_text(file):
    global roblox_version, roblox_username
    last_event = None
    last_aura = None
    try:
        file.seek(0)
        for old_line in file:
            if '"command":"SetRichPresence"' not in old_line:
                continue
            start = old_line.find('{"command":"SetRichPresence"')
            if start == -1:
                continue
            try:
                found = equipped_aura(json.loads(old_line[start:]).get("data", {}).get("state", ""))
            except json.JSONDecodeError:
                continue
            if found:
                last_aura = found
    except Exception:
        pass
    file.seek(0, 2)
    while True:
        if not stopped:
            root.update()
        else:
            if not destroyed:
                root.destroy()
            sys.exit()
        check = is_roblox_running()
        if check:
            line = file.readline()
            if line and not paused:
                if '"command":"SetRichPresence"' in line:
                    try:
                        json_data_start = line.find('{"command":"SetRichPresence"')
                        if json_data_start != -1:
                            json_data = json.loads(line[json_data_start:])
                            state = json_data.get("data", {}).get("state", "")
                            aura = equipped_aura(state)
                            if aura and aura != last_aura:
                                last_aura = aura
                                if aura_detection.get() == 1:
                                    aura_rolled(aura)
                            event = json_data.get("data", {}).get("largeImage", {}).get("hoverText", "")
                            if event and event != last_event:
                                if multi_webhook.get() != "1":
                                    if "discord" not in webhookURL.get() or "https://" not in webhookURL.get():
                                        ctypes.windll.user32.MessageBoxW(0, "Invalid or missing webhook link.", "Error",
                                                                         0)
                                        stop()
                                        return
                                    webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                                    if event == "NORMAL":
                                        if last_event is not None:
                                            print(time.strftime('%H:%M:%S') + f": Biome Ended - " + last_event)
                                            try:
                                                if globals()[last_event.replace(" ", "_").lower()].get() != "Nothing":
                                                    embed = discord_webhook.DiscordEmbed(
                                                        title="[" + time.strftime('%H:%M:%S') + "]",
                                                        color=get_biome_color(last_event),
                                                        description="> ## Biome Ended - " + last_event)
                                                    embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                                                                     icon_url="https://maxstellar.github.io/maxstellar.png")
                                                    embed.set_thumbnail(
                                                        url="https://maxstellar.github.io/biome_thumb/" + last_event.replace(
                                                            " ", "_") + ".png")
                                                    webhook.add_embed(embed)
                                                    webhook.execute()
                                            except:
                                                pass
                                        else:
                                            pass
                                    else:
                                        print(time.strftime('%H:%M:%S') + f": Biome Started - {event}")
                                        try:
                                            if globals()[event.replace(" ", "_").lower()].get() != "Nothing":
                                                embed = discord_webhook.DiscordEmbed(
                                                    title="[" + time.strftime('%H:%M:%S') + "]",
                                                    color=get_biome_color(event),
                                                    description="> ## Biome Started - " + event)
                                                embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                                                                 icon_url="https://maxstellar.github.io/maxstellar.png")
                                                embed.add_embed_field(name="Private Server Link", value=psURL.get())
                                                embed.set_thumbnail(
                                                    url="https://maxstellar.github.io/biome_thumb/" + event.replace(" ", "_") + ".png")
                                                webhook.add_embed(embed)
                                                ping_id = discID.get().strip()
                                                if globals()[event.replace(" ", "_").lower()].get() == "Ping" and ping_id.isnumeric():
                                                    webhook.set_content(f"<@{ping_id}>")
                                                if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                                    webhook.set_content("@everyone")
                                                webhook.execute()
                                        except:
                                            pass
                                else:
                                    if event == "NORMAL":
                                        if last_event is not None:
                                            print(time.strftime('%H:%M:%S') + f": Biome Ended - " + last_event)
                                            try:
                                                if globals()[last_event.replace(" ", "_").lower()].get() != "Nothing":
                                                    for url in webhook_urls:
                                                        webhook = discord_webhook.DiscordWebhook(url=url)
                                                        embed = discord_webhook.DiscordEmbed(
                                                            title="[" + time.strftime('%H:%M:%S') + "]",
                                                            color=get_biome_color(last_event),
                                                            description="> ## Biome Ended - " + last_event)
                                                        embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                                                                         icon_url="https://maxstellar.github.io/maxstellar.png")
                                                        embed.set_thumbnail(
                                                            url="https://maxstellar.github.io/biome_thumb/" + last_event.replace(
                                                                " ", "_") + ".png")
                                                        webhook.add_embed(embed)
                                                        webhook.execute()
                                            except:
                                                pass
                                        else:
                                            pass
                                    else:
                                        print(time.strftime('%H:%M:%S') + f": Biome Started - {event}")
                                        try:
                                            if globals()[event.replace(" ", "_").lower()].get() != "Nothing":
                                                for url in webhook_urls:
                                                    embed = discord_webhook.DiscordEmbed(
                                                        title="[" + time.strftime('%H:%M:%S') + "]",
                                                        color=get_biome_color(event),
                                                        description="> ## Biome Started - " + event)
                                                    embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                                                                     icon_url="https://maxstellar.github.io/maxstellar.png")
                                                    embed.add_embed_field(name="Private Server Link", value=psURL.get())
                                                    embed.set_thumbnail(
                                                        url="https://maxstellar.github.io/biome_thumb/" + event.replace(" ", "_") + ".png")
                                                    webhook = discord_webhook.DiscordWebhook(url=url)
                                                    webhook.add_embed(embed)
                                                    ping_id = discID.get().strip()
                                                    if globals()[event.replace(" ", "_").lower()].get() == "Ping" and ping_id.isnumeric():
                                                        webhook.set_content(f"<@{ping_id}>")
                                                    if event == "GLITCHED" or event == "DREAMSPACE" or event == "CYBERSPACE":
                                                        webhook.set_content("@everyone")
                                                    webhook.execute()
                                        except:
                                            pass
                                last_event = event
                    except json.JSONDecodeError:
                        print("Error decoding JSON")
            else:
                time.sleep(0.1)
        else:
            print("Roblox is closed, waiting for Roblox to start...")
            if multi_webhook.get() != "1":
                if "discord" not in webhookURL.get() or "https://" not in webhookURL.get():
                    ctypes.windll.user32.MessageBoxW(0, "Invalid or missing webhook link.", "Error", 0)
                    stop()
                    return
                close_webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
                close_embed = discord_webhook.DiscordEmbed(
                    description="[" + time.strftime('%H:%M:%S') + "]: Roblox was closed/crashed.")
                close_embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                                       icon_url="https://maxstellar.github.io/maxstellar.png")
                close_webhook.add_embed(close_embed)
                close_webhook.execute()
            else:
                for url in webhook_urls:
                    close_webhook = discord_webhook.DiscordWebhook(url=url)
                    close_embed = discord_webhook.DiscordEmbed(
                        description="[" + time.strftime('%H:%M:%S') + "]: Roblox was closed/crashed.")
                    close_embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                                           icon_url="https://maxstellar.github.io/maxstellar.png")
                    close_webhook.add_embed(close_embed)
                    close_webhook.execute()
            root.title("maxstellar's Biome Macro - No Roblox Detected")
            while True:
                if not stopped:
                    root.update()
                else:
                    if not destroyed:
                        root.destroy()
                    sys.exit()
                check = is_roblox_running()
                if check:
                    break
                time.sleep(0.1)
            if roblox_version == "player":
                logger.info("Detected Roblox Player.")
                print("Detected Roblox Player.")
                time.sleep(5)
            else:
                logger.info("Detected Roblox Microsoft Store.")
                print("Detected Roblox Microsoft Store.")
                time.sleep(5)
            latest_log = get_latest_log_file()
            if not latest_log:
                logger.info("No log files found.")
                print("No log files found.")
                return
            with open(latest_log, 'r', encoding='utf-8', errors='ignore') as file:
                print(f"Using log file: {latest_log}")
                print()
                logger.info(f"Using log file: {latest_log}")
                root.title("maxstellar's Biome Macro - Running")
                check_for_hover_text(file)


def open_url(url):
    webbrowser.open(url, new=2, autoraise=True)


def auradetection_toggle_update():
    config.set('Macro', 'aura_detection', str(aura_detection.get()))
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def auraping_toggle_update():
    config.set('Macro', 'aura_ping', str(aura_ping.get()))
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def aurarecording_toggle_update():
    config.set('Macro', 'aura_recording', str(aura_recording.get()))
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_windy(new_val):
    config.set('Biomes', "windy", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_snowy(new_val):
    config.set('Biomes', "snowy", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_rainy(new_val):
    config.set('Biomes', "rainy", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_sand_storm(new_val):
    config.set('Biomes', "sand_storm", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_hell(new_val):
    config.set('Biomes', "hell", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_starfall(new_val):
    config.set('Biomes', "starfall", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_corruption(new_val):
    config.set('Biomes', "corruption", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_null(new_val):
    config.set('Biomes', "null", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def set_blazing_sun(new_val):
    config.set('Biomes', "blazing_sun", new_val)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)


def manage_tlw():
    global tlw_open, dirname
    if not tlw_open:
        # create tlw
        tlw_open = True
        tlw = customtkinter.CTkToplevel()
        tlw.bind("<Destroy>", lambda e: globals().__setitem__('tlw_open', False))
        tlw.title("Configure Pings")
        tlw_label = customtkinter.CTkLabel(tlw, text="Choose what you get notified for!",
                                           font=customtkinter.CTkFont(family="Segoe UI", size=20))
        tlw_label.grid(row=0, column=0, columnspan=2, pady=10, padx=10)
        windy_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                   font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                                   variable=windy,
                                                   command=set_windy)
        windy_toggle.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        snowy_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                   font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                                   variable=snowy,
                                                   command=set_snowy)
        snowy_toggle.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        rainy_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                   font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                                   variable=rainy,
                                                   command=set_rainy)
        rainy_toggle.grid(row=3, column=1, sticky="w", padx=10, pady=10)
        sand_storm_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                        font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                                        variable=sand_storm,
                                                        command=set_sand_storm)
        sand_storm_toggle.grid(row=4, column=1, sticky="w", padx=10, pady=10)
        hell_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                  font=customtkinter.CTkFont(family="Segoe UI", size=20), variable=hell,
                                                  command=set_hell)
        hell_toggle.grid(row=1, column=3, sticky="w", padx=10, pady=10)
        starfall_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                      font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                                      variable=starfall, command=set_starfall)
        starfall_toggle.grid(row=2, column=3, sticky="w", padx=10, pady=10)
        corruption_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                        font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                                        variable=corruption, command=set_corruption)
        corruption_toggle.grid(row=3, column=3, sticky="w", padx=10, pady=10)
        null_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                  font=customtkinter.CTkFont(family="Segoe UI", size=20), variable=null,
                                                  command=set_null)
        null_toggle.grid(row=4, column=3, sticky="w", padx=10, pady=10)
        blazing_sun_toggle = customtkinter.CTkOptionMenu(tlw, values=["Message", "Ping", "Nothing"],
                                                         font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                                         variable=blazing_sun, command=set_blazing_sun)
        blazing_sun_toggle.grid(row=5, column=1, sticky="w", padx=10, pady=10)
        windy_label = customtkinter.CTkLabel(tlw, text="Windy",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20))
        windy_label.grid(column=0, row=1, padx=(10, 0), pady=10, sticky="w")
        snowy_label = customtkinter.CTkLabel(tlw, text="Snowy",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20))
        snowy_label.grid(column=0, row=2, padx=(10, 0), pady=10, sticky="w")
        rainy_label = customtkinter.CTkLabel(tlw, text="Rainy",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20))
        rainy_label.grid(column=0, row=3, padx=(10, 0), pady=10, sticky="w")
        sand_storm_label = customtkinter.CTkLabel(tlw, text="Sand Storm",
                                                  font=customtkinter.CTkFont(family="Segoe UI", size=20))
        sand_storm_label.grid(column=0, row=4, padx=(10, 0), pady=10, sticky="w")
        hell_label = customtkinter.CTkLabel(tlw, text="Hell",
                                            font=customtkinter.CTkFont(family="Segoe UI", size=20))
        hell_label.grid(column=2, row=1, padx=(10, 0), pady=10, sticky="w")
        starfall_label = customtkinter.CTkLabel(tlw, text="Starfall",
                                                font=customtkinter.CTkFont(family="Segoe UI", size=20))
        starfall_label.grid(column=2, row=2, padx=(10, 0), pady=10, sticky="w")
        corruption_label = customtkinter.CTkLabel(tlw, text="Corruption",
                                                  font=customtkinter.CTkFont(family="Segoe UI", size=20))
        corruption_label.grid(column=2, row=3, padx=(10, 0), pady=10, sticky="w")
        null_label = customtkinter.CTkLabel(tlw, text="Null",
                                            font=customtkinter.CTkFont(family="Segoe UI", size=20))
        null_label.grid(column=2, row=4, padx=(10, 0), pady=10, sticky="w")
        blazing_sun_label = customtkinter.CTkLabel(tlw, text="Blazing Sun",
                                                   font=customtkinter.CTkFont(family="Segoe UI", size=20))
        blazing_sun_label.grid(column=0, row=5, padx=(10, 0), pady=10, sticky="w")
        tlw.after(0, tlw.focus)
        tlw.after(100, lambda: tlw.resizable(False, False))
        tlw.after(250, lambda: tlw.iconbitmap(dirname + '\\icon.ico'))


def init():
    global roblox_open, started, paused, roblox_username

    if paused:
        paused = False
        root.title("maxstellar's Biome Macro - Running")

    if started:
        return

    config.set('Macro', 'min_rarity_to_ping', detectping_field.get() if detectping_field.get().isnumeric() else "")
    config.set('Macro', 'record_hotkey', record_field.get().strip())
    detectping_field.configure(state="disabled", text_color="gray")
    record_field.configure(state="disabled", text_color="gray")
    webhook_field.configure(state="disabled", text_color="gray")
    ps_field.configure(state="disabled", text_color="gray")
    discid_field.configure(state="disabled", text_color="gray")
    username_field.configure(state="disabled", text_color="gray")
    # write new settings to config
    config.set('Webhook', 'webhook_url', webhookURL.get())
    config.set('Webhook', 'private_server', psURL.get())
    config.set('Webhook', 'discord_user_id', discID.get())

    # Writing configuration file to 'config.ini'
    with open(config_name, 'w+') as configfile:
        config.write(configfile)

    # start webhook
    starting_embed = discord_webhook.DiscordEmbed(
        description="[" + time.strftime('%H:%M:%S') + "]: Macro started!")
    starting_embed.set_footer(text="maxstellar's Biome Macro | v2.5",
                              icon_url="https://maxstellar.github.io/maxstellar.png")
    if multi_webhook.get() != "1":
        if "discord" not in webhookURL.get() or "https://" not in webhookURL.get():
            ctypes.windll.user32.MessageBoxW(0, "Invalid or missing webhook link.", "Error", 0)
            stop()
            return
        starting_webhook = discord_webhook.DiscordWebhook(url=webhookURL.get())
        starting_webhook.add_embed(starting_embed)
        starting_webhook.execute()
    else:
        for url in webhook_urls:
            starting_webhook = discord_webhook.DiscordWebhook(url=url)
            starting_webhook.add_embed(starting_embed)
            starting_webhook.execute()

    if discID.get().strip() and not discID.get().strip().isnumeric():
        ctypes.windll.user32.MessageBoxW(0,
                                         "Discord User ID should only be a number.\nIf it is something else, such as @everyone, or your username, that is not your Discord User ID.",
                                         "Error", 0)
        stop()
        return

    started = True

    # start detection
    if is_roblox_running():
        roblox_open = True
        logger.info("Roblox is open.")
        print("Roblox is open.")
        root.title("maxstellar's Biome Macro - Running")
    else:
        logger.info("Roblox is closed, waiting for Roblox to start...")
        print("Roblox is closed, waiting for Roblox to start...")
        root.title("maxstellar's Biome Macro - No Roblox Detected")
        while True:
            if not stopped:
                root.update()
            else:
                if not destroyed:
                    root.destroy()
                sys.exit()
            check = is_roblox_running()
            if check:
                break
            time.sleep(0.1)
    if not roblox_open:
        if roblox_version == "player":
            logger.info("Detected Roblox Player.")
            print("Detected Roblox Player.")
            time.sleep(1.5)
        else:
            logger.info("Detected Roblox Microsoft Store.")
            print("Detected Roblox Microsoft Store.")
            time.sleep(3.5)
    latest_log = get_latest_log_file()
    if not latest_log:
        logger.info(print("No log files found."))
        print("No log files found.")
        return
    with open(latest_log, 'r', encoding='utf-8') as file:
        print(f"Using log file: {latest_log}")
        print()
        logger.info(f"Using log file: {latest_log}")
        root.title("maxstellar's Biome Macro - Running")
        check_for_hover_text(file)


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

detection_toggle = customtkinter.CTkCheckBox(tabview.tab("Macro"), text="Aura Detection",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                             variable=aura_detection, command=auradetection_toggle_update)
detection_toggle.grid(row=1, column=0, columnspan=2, padx=(10, 0), pady=(10, 0), sticky="w")

detectping_toggle = customtkinter.CTkCheckBox(tabview.tab("Macro"), text="Aura Pings",
                                              font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                              variable=aura_ping, command=auraping_toggle_update)
detectping_toggle.grid(row=2, column=0, columnspan=2, padx=(10, 0), pady=(12, 0), sticky="w")
detectping_field = customtkinter.CTkEntry(tabview.tab("Macro"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                          width=155, textvariable=None, placeholder_text="Minimum Rarity")
detectping_field.grid(row=2, column=1, padx=(140, 0), pady=(10, 0), sticky="w")

recording_toggle = customtkinter.CTkCheckBox(tabview.tab("Macro"), text="Aura Recording",
                                             font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                             variable=aura_recording, command=aurarecording_toggle_update)
recording_toggle.grid(row=3, column=0, columnspan=2, padx=(10, 0), pady=(12, 0), sticky="w")
record_field = customtkinter.CTkEntry(tabview.tab("Macro"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                      width=150, textvariable=None, placeholder_text="Record Keybind")
record_field.grid(row=3, column=1, padx=(185, 0), pady=(10, 0), sticky="w")
record_field.insert(0, config['Macro'].get('record_hotkey', "win+alt+g"))

min_rarity_to_ping = config['Macro'].get('min_rarity_to_ping', "")
if min_rarity_to_ping != "":
    detectping_field.insert(0, min_rarity_to_ping)

keysym_names = {"shift_l": "shift", "shift_r": "shift", "control_l": "ctrl", "control_r": "ctrl",
                "alt_l": "alt", "alt_r": "alt", "super_l": "win", "super_r": "win", "win_l": "win",
                "win_r": "win", "print": "printscreen", "prior": "pageup", "next": "pagedown"}
capturing = [False]
held = []


def key_name(event):
    name = event.keysym.lower()
    return keysym_names.get(name, name)


def start_capture(event=None):
    if capturing[0]:
        return
    capturing[0] = True
    held.clear()
    record_field.configure(state="normal")
    record_field.delete(0, "end")
    record_field.insert(0, "press keys...")
    record_field.focus_set()


def finish_capture(combo):
    capturing[0] = False
    record_field.delete(0, "end")
    record_field.insert(0, combo)
    config.set('Macro', 'record_hotkey', combo)
    with open(config_name, 'w+') as configfile:
        config.write(configfile)
    root.focus_set()


def capture_key(event):
    if not capturing[0]:
        return
    name = key_name(event)
    if name == "escape":
        finish_capture(config['Macro'].get('record_hotkey', "win+alt+g"))
        return "break"
    if name in ("shift", "ctrl", "alt", "win"):
        if name not in held:
            held.append(name)
        return "break"
    if name in press_keys or len(name) == 1:
        finish_capture("+".join(held + [name]))
    return "break"


def cancel_capture(event=None):
    if capturing[0]:
        capturing[0] = False
        record_field.delete(0, "end")
        record_field.insert(0, config['Macro'].get('record_hotkey', "win+alt+g"))


def release_key(event):
    if capturing[0] and key_name(event) in held:
        held.remove(key_name(event))
    return "break" if capturing[0] else None


record_field.bind("<Button-1>", start_capture)
record_field.bind("<FocusIn>", start_capture)
record_field.bind("<KeyPress>", capture_key)
record_field.bind("<KeyRelease>", release_key)
record_field.bind("<FocusOut>", cancel_capture)

biome_button = customtkinter.CTkButton(tabview.tab("Macro"), text="Configure Pings",
                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
                                       command=manage_tlw)
biome_button.grid(row=2, column=1, padx=(310, 0), pady=(10, 0), sticky="w")

# patch_button = customtkinter.CTkButton(tabview.tab("Macro"), text="Patch Roblox",
#                                       font=customtkinter.CTkFont(family="Segoe UI", size=20, weight="bold"), width=75,
#                                       command=patch_roblox)
# patch_button.grid(row=3, column=1, padx=(10, 0), columnspan=2, pady=(12, 0), sticky="w")

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

max_pfp = customtkinter.CTkImage(dark_image=Image.open(dirname + "\\maxstellar.png"), size=(70, 70))
max_pfp_label = customtkinter.CTkLabel(tabview.tab("Credits"), image=max_pfp, text="")
max_pfp_label.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

sols_sniper = customtkinter.CTkImage(dark_image=Image.open(dirname + "\\sols_sniper.png"), size=(70, 70))
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

discid_label = customtkinter.CTkLabel(tabview.tab("Macro"), text="Roblox Username:",
                                      font=customtkinter.CTkFont(family="Segoe UI", size=20))
discid_label.grid(column=0, row=0, padx=(10, 0), pady=(5, 0), columnspan=2, sticky="w")

username_field = customtkinter.CTkEntry(tabview.tab("Macro"), font=customtkinter.CTkFont(family="Segoe UI", size=20),
                                      width=307, textvariable=roblox_username)
username_field.grid(row=0, column=1, padx=(172, 0), pady=(10, 0), sticky="w")

root.bind("<Destroy>", lambda event: x_stop())
root.bind("<Button-1>", lambda e: e.widget.focus_set())

root.mainloop()
