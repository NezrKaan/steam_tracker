#!/usr/bin/env python3
"""
Steam Status Monitor - full profile-change tracking
Made by NezrKaan

Behavior:
- Prints/logs when user's status, current game, or profile fields change.
- Detects: nickname, real name, country, profile URL, avatar (profile pic) changes.
- Shows when the user starts/stops playing a specific game, with times and duration.
- Typed keys do NOT echo and do not trigger anything.
- Exit with Ctrl+C.
- Logs events to 'steam_status_log.txt'.
"""

import requests
import time
import sys
import termios
from datetime import datetime

# -------------------------
# Styling (ANSI sequences)
# -------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

# Decorative box characters
HORIZ = "━"
VERT = "┃"
TL = "┏"
TR = "┓"
BL = "┗"
BR = "┛"

# Log file
LOG_FILE = "steam_status_log.txt"

# -------------------------
# Helpers
# -------------------------
def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_time(dt):
    return dt.strftime("%H:%M:%S")

def format_duration(start_dt, end_dt):
    delta = end_dt - start_dt
    secs = int(delta.total_seconds())
    hrs, rem = divmod(secs, 3600)
    mins, sec = divmod(rem, 60)
    parts = []
    if hrs:
        parts.append(f"{hrs}h")
    if mins:
        parts.append(f"{mins}m")
    if sec and not parts:
        parts.append(f"{sec}s")
    return " ".join(parts) if parts else "0s"

def log_plain(line):
    with open(LOG_FILE, "a") as f:
        f.write(f"{line}\n")

def pretty_log(message, color=""):
    ts = now_ts()
    plain = f"{ts} - {message}"
    colored = f"{color}{ts} - {message}{RESET}" if color else plain
    print(colored, flush=True)
    log_plain(plain)

# -------------------------
# Steam API helpers
# -------------------------
def resolve_vanity(api_key, vanity):
    url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
    try:
        r = requests.get(url, params={"key": api_key, "vanityurl": vanity}, timeout=8)
        r.raise_for_status()
        data = r.json()
        if data.get("response", {}).get("success") == 1:
            return data["response"]["steamid"]
    except Exception:
        return None
    return None

def fetch_player(api_key, steamid64):
    """
    Returns a dict of player fields or (None) if not found,
    or ("ERROR", error_message) tuple on API/network error.
    """
    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    try:
        r = requests.get(url, params={"key": api_key, "steamids": steamid64}, timeout=8)
        r.raise_for_status()
        data = r.json()
        players = data.get("response", {}).get("players", [])
        if not players:
            return None
        return players[0]
    except Exception as e:
        return ("ERROR", str(e))

# -------------------------
# Map persona state -> (readable text, color)
# -------------------------
STATE_META = {
    0: ("Offline", RED),
    1: ("Online", GREEN),
    2: ("Busy", YELLOW),
    3: ("Away", CYAN),
    4: ("Snooze", MAGENTA),
    5: ("Looking to trade", BLUE),
    6: ("Looking to play", BLUE),
}

# -------------------------
# Terminal control
# -------------------------
def set_no_echo(fd):
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~(termios.ECHO | termios.ICANON)  # disable ECHO and canonical mode
    termios.tcsetattr(fd, termios.TCSADRAIN, new)
    return old

def restore_terminal(fd, old_settings):
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# -------------------------
# Main program
# -------------------------
def banner():
    title = "STEAM STATUS MONITOR"
    subtitle = "Made by NezrKaan"
    width = max(len(title), len(subtitle)) + 8
    print(f"{TL}{HORIZ * width}{TR}")
    print(f"{VERT}  {BOLD}{CYAN}{title.center(width-4)}{RESET}  {VERT}")
    print(f"{VERT}  {DIM}{WHITE}{subtitle.center(width-4)}{RESET}  {VERT}")
    print(f"{BL}{HORIZ * width}{BR}\n")
    print(f"{DIM}Notes:{RESET} - Tracks status, game, and profile field changes (nickname, avatar, country, profile URL). Press Ctrl+C to quit. Logs -> {LOG_FILE}\n")

def compare_and_log_profile_changes(prev, curr):
    """
    prev and curr are dicts (or None). Check fields:
      - personaname (nickname)
      - realname
      - loccountrycode
      - profileurl
      - avatarfull
    Log descriptive messages for changes.
    Returns updated prev snapshot (dict).
    """
    fields = [
        ("personaname", "Nickname", YELLOW),
        ("realname", "Real name", YELLOW),
        ("loccountrycode", "Country", CYAN),
        ("profileurl", "Profile URL", BLUE),
        ("avatarfull", "Profile picture", MAGENTA),
    ]

    if prev is None:
        # initialize snapshot with available values (no logs)
        snapshot = {}
        for k, _, _ in fields:
            snapshot[k] = curr.get(k) if curr else None
        return snapshot

    snapshot = dict(prev)  # copy
    for key, label, color in fields:
        old = prev.get(key)
        new = curr.get(key) if curr else None
        # treat empty string as None
        old_norm = old if old not in ("", None) else None
        new_norm = new if new not in ("", None) else None

        if old_norm != new_norm:
            # Log specific messages
            if key == "personaname":
                pretty_log(f"Nickname changed: '{old_norm}' -> '{new_norm}'", color)
            elif key == "avatarfull":
                if old_norm is None and new_norm:
                    pretty_log(f"Profile picture set: {new_norm}", color)
                elif old_norm and new_norm is None:
                    pretty_log(f"Profile picture removed (was {old_norm})", color)
                else:
                    pretty_log(f"Profile picture updated: '{old_norm}' -> '{new_norm}'", color)
            else:
                pretty_log(f"{label} changed: '{old_norm}' -> '{new_norm}'", color)
            snapshot[key] = new_norm
    return snapshot

def monitor_loop(api_key, steamid64, interval=10):
    prev_profile_snapshot = None  # dict of tracked fields
    previous_state = None
    current_game = None
    game_start = None
    display_name = None

    while True:
        player = fetch_player(api_key, steamid64)

        # API/network error
        if isinstance(player, tuple) and player[0] == "ERROR":
            pretty_log(f"API error: {player[1]}", RED)
            time.sleep(interval)
            continue

        # player may be None (profile not found / private)
        if player is None:
            # If previously we had a profile snapshot, and now it's gone, log once
            if prev_profile_snapshot is not None:
                pretty_log("Profile became unavailable or is private.", RED)
                prev_profile_snapshot = None
            # also treat as offline state
            if previous_state != 0:
                pretty_log("User is now Offline (profile unavailable).", RED)
                previous_state = 0
            time.sleep(interval)
            continue

        # At this point 'player' is a dict containing all fields
        # set display_name if None
        if display_name is None:
            display_name = player.get("personaname", "Unknown")

        # Compare tracked profile fields and log changes
        prev_profile_snapshot = compare_and_log_profile_changes(prev_profile_snapshot, player)

        # Game handling (gameextrainfo)
        game = player.get("gameextrainfo")
        if game and current_game != game:
            # switching from another game: close previous
            if current_game is not None:
                ended = datetime.now()
                dur = format_duration(game_start, ended) if game_start else "?"
                pretty_log(f"Stopped playing '{current_game}' — played from {format_time(game_start)} to {format_time(ended)} ({dur})", CYAN)
            game_start = datetime.now()
            pretty_log(f"Started playing '{game}' at {format_time(game_start)}", GREEN)
            current_game = game

        if not game and current_game is not None:
            ended = datetime.now()
            dur = format_duration(game_start, ended) if game_start else "?"
            pretty_log(f"Stopped playing '{current_game}' — played from {format_time(game_start)} to {format_time(ended)} ({dur})", CYAN)
            current_game = None
            game_start = None

        # State handling
        state = player.get("personastate", 0)
        if state != previous_state:
            text, color = STATE_META.get(state, ("Unknown", MAGENTA))
            name_to_show = player.get("personaname") or "Unknown"
            pretty_log(f"{name_to_show} is now {text} at {format_time(datetime.now())}", color)
            previous_state = state

        time.sleep(interval)

def main():
    try:
        banner()
        api_key = input("Enter your Steam Web API Key: ").strip()
        usr = input("Enter SteamID64 or custom profile name: ").strip()

        if not usr.isdigit():
            steamid = resolve_vanity(api_key, usr)
            if not steamid:
                print(f"{RED}Could not resolve custom URL '{usr}'. Exiting.{RESET}")
                return
        else:
            steamid = usr

        print(f"\nMonitoring: {BOLD}{steamid}{RESET}  (Checking every 10s)\n")

        # ensure requests is present
        try:
            import requests  # sanity
        except Exception:
            print(f"{RED}Missing dependency: requests. Install: python3 -m pip install requests{RESET}")
            return

        # disable input echo so typed keys won't show
        fd = sys.stdin.fileno()
        old_settings = set_no_echo(fd)

        try:
            monitor_loop(api_key, steamid, interval=10)
        finally:
            restore_terminal(fd, old_settings)

    except KeyboardInterrupt:
        # Restore terminal state if needed
        try:
            restore_terminal(sys.stdin.fileno(), termios.tcgetattr(sys.stdin.fileno()))
        except Exception:
            pass
        print(f"\n{DIM}Exiting. Goodbye!{RESET}")

if __name__ == "__main__":
    main()
