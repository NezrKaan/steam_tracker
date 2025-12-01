#!/usr/bin/env python3
"""
Steam Status Monitor v2.0 - Multi-User Tracking
Made by NezrKaan (Enhanced Version)

Features:
- Tracks MULTIPLE users simultaneously
- Persistent configuration (saves your API key)
- Working Discord Rich Embed notifications
- Network resilience (auto-reconnect)
- Game session duration calculation
"""

import requests
import time
import sys
import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

# -------------------------
# Constants & Styling
# -------------------------
CONFIG_FILE = "monitor_config.json"

class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    
    STATUS_COLORS = {0: RED, 1: GREEN, 2: YELLOW, 3: CYAN, 4: MAGENTA, 5: BLUE, 6: BLUE}
    STATUS_TEXT = {
        0: "Offline", 1: "Online", 2: "Busy", 3: "Away", 
        4: "Snooze", 5: "Looking to trade", 6: "Looking to play"
    }

# -------------------------
# Data Structures
# -------------------------
@dataclass
class UserProfile:
    steamid: str
    personaname: str = "Unknown"
    realname: Optional[str] = None
    avatar: Optional[str] = None
    profile_url: Optional[str] = None
    persona_state: int = 0
    game_name: Optional[str] = None
    game_start_time: Optional[datetime] = None
    last_seen: Optional[datetime] = None

@dataclass
class Config:
    api_key: str
    users: List[str] = field(default_factory=list)
    discord_webhook: Optional[str] = None
    check_interval: int = 30

# -------------------------
# Discord Manager
# -------------------------
class DiscordNotifier:
    def __init__(self, webhook_url: Optional[str]):
        self.webhook_url = webhook_url

    def send_embed(self, title: str, description: str, color: int, fields: List[Dict] = None, thumbnail: str = None):
        if not self.webhook_url:
            return

        payload = {
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "footer": {"text": "Steam Monitor by NezrKaan"},
                "thumbnail": {"url": thumbnail} if thumbnail else {}
            }]
        }
        
        if fields:
            payload["embeds"][0]["fields"] = fields

        try:
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"{Style.RED}[Discord Error] Could not send notification: {e}{Style.RESET}")

# -------------------------
# Steam API Client
# -------------------------
class SteamAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        
    def get_player_summaries(self, steamids: List[str]) -> List[Dict]:
        # Steam API allows multiple IDs separated by commas
        ids_str = ",".join(steamids)
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        params = {"key": self.api_key, "steamids": ids_str}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 429:
                print(f"{Style.YELLOW}[API] Rate limited. Skipping this cycle.{Style.RESET}")
                return []
            response.raise_for_status()
            return response.json().get("response", {}).get("players", [])
        except Exception as e:
            print(f"{Style.RED}[API Error] {e}{Style.RESET}")
            return []

    def resolve_vanity_url(self, vanity: str) -> Optional[str]:
        # If it looks like a steamID64, return it directly
        if vanity.isdigit() and len(vanity) == 17:
            return vanity
            
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        params = {"key": self.api_key, "vanityurl": vanity}
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("response", {}).get("success") == 1:
                return data["response"]["steamid"]
        except:
            pass
        return None

# -------------------------
# Main Logic
# -------------------------
class SteamMonitor:
    def __init__(self):
        self.config = self._load_config()
        self.api = SteamAPIClient(self.config.api_key)
        self.discord = DiscordNotifier(self.config.discord_webhook)
        self.profiles: Dict[str, UserProfile] = {}
        self.running = False

    def _load_config(self) -> Config:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    return Config(**data)
            except Exception as e:
                print(f"{Style.RED}Config file corrupted: {e}{Style.RESET}")
        
        # Setup Wizard
        print(f"{Style.CYAN}--- First Time Setup ---{Style.RESET}")
        key = input("Enter Steam API Key: ").strip()
        webhook = input("Discord Webhook (Optional, press Enter to skip): ").strip()
        
        cfg = Config(api_key=key, discord_webhook=webhook if webhook else None)
        self._save_config(cfg)
        return cfg

    def _save_config(self, config: Config):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(asdict(config), f, indent=4)

    def add_user(self):
        user_input = input(f"{Style.GREEN}Enter Steam Profile URL or Custom ID to track: {Style.RESET}").strip()
        if not user_input: return
        
        # Extract ID from URL if full URL is pasted
        if "steamcommunity.com/id/" in user_input:
            user_input = user_input.split("/id/")[-1].strip("/")
        elif "steamcommunity.com/profiles/" in user_input:
            user_input = user_input.split("/profiles/")[-1].strip("/")

        steamid = self.api.resolve_vanity_url(user_input)
        if steamid:
            if steamid not in self.config.users:
                self.config.users.append(steamid)
                self._save_config(self.config)
                print(f"{Style.GREEN}User added! Restarting monitor loop...{Style.RESET}")
            else:
                print(f"{Style.YELLOW}User already in list.{Style.RESET}")
        else:
            print(f"{Style.RED}Could not resolve user.{Style.RESET}")

    def initialize_profiles(self):
        print(f"{Style.DIM}Fetching initial data for {len(self.config.users)} users...{Style.RESET}")
        data = self.api.get_player_summaries(self.config.users)
        for p_data in data:
            sid = p_data['steamid']
            self.profiles[sid] = UserProfile(
                steamid=sid,
                personaname=p_data.get('personaname'),
                avatar=p_data.get('avatarfull'),
                persona_state=p_data.get('personastate', 0),
                game_name=p_data.get('gameextrainfo')
            )
            if self.profiles[sid].game_name:
                self.profiles[sid].game_start_time = datetime.now()
                
            print(f"Tracking: {Style.BOLD}{self.profiles[sid].personaname}{Style.RESET}")

    def _format_duration(self, start_time: datetime) -> str:
        delta = datetime.now() - start_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def check_updates(self):
        if not self.config.users:
            print(f"{Style.YELLOW}No users to track. Use 'Add User' option.{Style.RESET}")
            return

        current_data_list = self.api.get_player_summaries(self.config.users)
        
        for data in current_data_list:
            sid = data['steamid']
            if sid not in self.profiles: continue
            
            profile = self.profiles[sid]
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # 1. Check Status Change
            new_state = data.get('personastate', 0)
            if new_state != profile.persona_state:
                old_text = Style.STATUS_TEXT.get(profile.persona_state, "Unknown")
                new_text = Style.STATUS_TEXT.get(new_state, "Unknown")
                color = Style.STATUS_COLORS.get(new_state, Style.WHITE)
                
                print(f"[{current_time}] {color}{profile.personaname} is now {new_text}{Style.RESET} (was {old_text})")
                
                # Discord Notification for Status
                discord_color = 0x00FF00 if new_state == 1 else 0x95a5a6
                self.discord.send_embed(
                    title=f"Status Update: {profile.personaname}",
                    description=f"User is now **{new_text}**",
                    color=discord_color,
                    thumbnail=profile.avatar
                )
                
                profile.persona_state = new_state

            # 2. Check Game Activity
            new_game = data.get('gameextrainfo')
            
            # Game Started
            if new_game and new_game != profile.game_name:
                print(f"[{current_time}] {Style.GREEN}{profile.personaname} started playing {Style.BOLD}{new_game}{Style.RESET}")
                profile.game_start_time = datetime.now()
                profile.game_name = new_game
                
                self.discord.send_embed(
                    title=f"Game Started: {profile.personaname}",
                    description=f"Started playing **{new_game}**",
                    color=0x2ecc71, # Green
                    thumbnail=profile.avatar
                )

            # Game Stopped
            elif not new_game and profile.game_name:
                duration = "Unknown"
                if profile.game_start_time:
                    duration = self._format_duration(profile.game_start_time)
                
                print(f"[{current_time}] {Style.YELLOW}{profile.personaname} stopped playing {profile.game_name}{Style.RESET} (Time: {duration})")
                
                self.discord.send_embed(
                    title=f"Game Session Ended",
                    description=f"**{profile.personaname}** finished playing **{profile.game_name}**",
                    color=0xe74c3c, # Red
                    fields=[{"name": "Duration", "value": duration, "inline": True}],
                    thumbnail=profile.avatar
                )
                
                profile.game_name = None
                profile.game_start_time = None

    def start(self):
        self.initialize_profiles()
        self.running = True
        
        print(f"\n{Style.CYAN}Monitor is running... Press Ctrl+C to stop.{Style.RESET}")
        
        try:
            while self.running:
                self.check_updates()
                time.sleep(self.config.check_interval)
        except KeyboardInterrupt:
            print(f"\n{Style.RED}Stopping monitor...{Style.RESET}")

# -------------------------
# Entry Point
# -------------------------
def main():
    print(f"""{Style.BOLD}{Style.BLUE}
    ╔══════════════════════════════════╗
    ║       STEAM MONITOR v2.0         ║
    ╚══════════════════════════════════╝
    {Style.RESET}""")
    
    monitor = SteamMonitor()
    
    while True:
        if not monitor.config.users:
            print("\nUser list is empty!")
            monitor.add_user()
        else:
            print(f"\nTracking {len(monitor.config.users)} users.")
            print("1. Start Monitoring")
            print("2. Add Another User")
            print("3. Reset Config")
            print("4. Exit")
            
            choice = input("Select: ").strip()
            
            if choice == "1":
                monitor.start()
                break
            elif choice == "2":
                monitor.add_user()
            elif choice == "3":
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
                    print("Config deleted. Please restart.")
                    return
            elif choice == "4":
                sys.exit()
            else:
                print("Invalid choice")

if __name__ == "__main__":
    main()
