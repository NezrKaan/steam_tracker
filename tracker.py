#!/usr/bin/env python3
"""
Steam Status Monitor - User tracking
Made by NezrKaan

Features:
- User monitoring with comprehensive tracking
- Automatic safe settings (20 second intervals)
- Clean, real-time logging
- Profile change detection
- Game activity tracking with duration
- Optional Discord notifications
"""

import requests
import time
import sys
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path

# -------------------------
# Configuration
# -------------------------
@dataclass
class Config:
    api_key: str
    user_identifier: str
    check_interval: int = 20  # Safe default
    log_file: str = "steam_monitor.log"
    json_log: str = "steam_events.json"
    discord_webhook: Optional[str] = None

@dataclass
class UserProfile:
    steamid: str
    personaname: str
    realname: Optional[str] = None
    country: Optional[str] = None
    avatar: Optional[str] = None
    profile_url: Optional[str] = None
    persona_state: int = 0
    game_name: Optional[str] = None
    game_start_time: Optional[datetime] = None

# -------------------------
# Styling
# -------------------------
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
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    
    STATUS_COLORS = {0: RED, 1: GREEN, 2: YELLOW, 3: CYAN, 4: MAGENTA, 5: BLUE, 6: BLUE}
    STATUS_TEXT = {0: "Offline", 1: "Online", 2: "Busy", 3: "Away", 4: "Snooze", 5: "Looking to trade", 6: "Looking to play"}

# -------------------------
# Steam API Client
# -------------------------
class SteamAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 1.0
        
    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        # Simple rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        try:
            self.last_request_time = time.time()
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                print(f"{Style.YELLOW}[WARNING] Rate limited! Waiting 60s...{Style.RESET}")
                time.sleep(60)
                return None
                
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"{Style.RED}[ERROR] API request failed: {e}{Style.RESET}")
            return None
    
    def resolve_vanity_url(self, vanity: str) -> Optional[str]:
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        params = {"key": self.api_key, "vanityurl": vanity}
        
        data = self._make_request(url, params)
        if data and data.get("response", {}).get("success") == 1:
            return data["response"]["steamid"]
        return None
    
    def get_player_summary(self, steamid: str) -> Optional[Dict]:
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        params = {"key": self.api_key, "steamids": steamid}
        
        data = self._make_request(url, params)
        if data:
            players = data.get("response", {}).get("players", [])
            return players[0] if players else None
        return None

# -------------------------
# Logger
# -------------------------
class Logger:
    def __init__(self, config: Config):
        self.config = config
        Path(self.config.log_file).touch(exist_ok=True)
        
    def log(self, message: str, color: str = Style.WHITE):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Console output
        print(f"{Style.GRAY}[{timestamp}]{Style.RESET} {color}{message}{Style.RESET}")
        
        # File output
        file_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.config.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{file_timestamp}] {message}\n")
        
        # JSON output
        self._write_json({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
    
    def _write_json(self, event: Dict):
        events = []
        if Path(self.config.json_log).exists():
            try:
                with open(self.config.json_log, "r", encoding="utf-8") as f:
                    events = json.load(f)
            except:
                events = []
        
        events.append(event)
        
        # Keep last 500 events
        if len(events) > 500:
            events = events[-500:]
        
        with open(self.config.json_log, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)

# -------------------------
# Steam Monitor
# -------------------------
class SteamMonitor:
    def __init__(self, config: Config):
        self.config = config
        self.api_client = SteamAPIClient(config.api_key)
        self.logger = Logger(config)
        self.profile: Optional[UserProfile] = None
        self.running = False
        
    def setup_user(self) -> bool:
        """Setup the user to monitor"""
        print(f"Setting up user: {self.config.user_identifier}...")
        
        # Resolve user ID
        if not self.config.user_identifier.isdigit():
            print(f"  Resolving custom URL...")
            steamid = self.api_client.resolve_vanity_url(self.config.user_identifier)
            if not steamid:
                print(f"{Style.RED}Could not resolve custom URL: {self.config.user_identifier}{Style.RESET}")
                return False
        else:
            steamid = self.config.user_identifier
        
        # Get initial profile
        print(f"  Fetching profile data...")
        player_data = self.api_client.get_player_summary(steamid)
        if not player_data:
            print(f"{Style.RED}Could not fetch profile for: {steamid}{Style.RESET}")
            return False
        
        # Create profile
        self.profile = UserProfile(
            steamid=steamid,
            personaname=player_data.get('personaname', 'Unknown'),
            realname=player_data.get('realname'),
            country=player_data.get('loccountrycode'),
            avatar=player_data.get('avatarfull'),
            profile_url=player_data.get('profileurl'),
            persona_state=player_data.get('personastate', 0),
            game_name=player_data.get('gameextrainfo')
        )
        
        if self.profile.game_name:
            self.profile.game_start_time = datetime.now()
        
        # Show initial status
        status_text = Style.STATUS_TEXT.get(self.profile.persona_state, 'Unknown')
        status_color = Style.STATUS_COLORS.get(self.profile.persona_state, Style.WHITE)
        game_text = f" | Playing: {self.profile.game_name}" if self.profile.game_name else ""
        
        print(f"{Style.GREEN}Successfully set up monitoring for:{Style.RESET}")
        print(f"  Name: {Style.BOLD}{self.profile.personaname}{Style.RESET}")
        print(f"  Status: {status_color}{status_text}{Style.RESET}{game_text}")
        print(f"  SteamID: {steamid}")
        
        return True
    
    def start_monitoring(self):
        """Start the monitoring loop"""
        if not self.profile:
            print(f"{Style.RED}No user profile set up!{Style.RESET}")
            return
        
        self.running = True
        
        print(f"\n{Style.BOLD}{Style.GREEN}Steam Monitor Started{Style.RESET}")
        print(f"Monitoring: {Style.CYAN}{self.profile.personaname}{Style.RESET}")
        print(f"Check interval: {self.config.check_interval} seconds")
        print(f"Log file: {Style.DIM}{self.config.log_file}{Style.RESET}")
        print(f"Press {Style.BOLD}Ctrl+C{Style.RESET} to stop")
        print(f"\n{Style.DIM}--- Live Updates ---{Style.RESET}")
        
        self.logger.log(f"Monitor started for {self.profile.personaname}")
        
        try:
            while self.running:
                self._check_for_changes()
                time.sleep(self.config.check_interval)
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        self.logger.log("Monitor stopped")
        print(f"\n{Style.CYAN}Monitor stopped. Check {self.config.log_file} for full log.{Style.RESET}")
    
    def _check_for_changes(self):
        """Check for any changes in the user's profile/status"""
        current_data = self.api_client.get_player_summary(self.profile.steamid)
        if not current_data:
            return
        
        current_time = datetime.now()
        
        # Check status changes
        new_status = current_data.get('personastate', 0)
        if new_status != self.profile.persona_state:
            old_status = Style.STATUS_TEXT.get(self.profile.persona_state, 'Unknown')
            new_status_text = Style.STATUS_TEXT.get(new_status, 'Unknown')
            status_color = Style.STATUS_COLORS.get(new_status, Style.WHITE)
            
            message = f"{self.profile.personaname} is now {new_status_text} (was {old_status})"
            self.logger.log(message, status_color)
            
            self.profile.persona_state = new_status
        
        # Check game changes
        new_game = current_data.get('gameextrainfo')
        if new_game != self.profile.game_name:
            if self.profile.game_name and not new_game:
                # Game stopped
                duration = "Unknown"
                if self.profile.game_start_time:
                    delta = current_time - self.profile.game_start_time
                    duration = self._format_duration(delta)
                
                message = f"{self.profile.personaname} stopped playing '{self.profile.game_name}' (played for {duration})"
                self.logger.log(message, Style.YELLOW)
                
            elif new_game:
                # Game started
                message = f"{self.profile.personaname} started playing '{new_game}'"
                self.logger.log(message, Style.GREEN)
                self.profile.game_start_time = current_time
            
            self.profile.game_name = new_game
        
        # Check profile changes
        self._check_profile_changes(current_data, current_time)
    
    def _check_profile_changes(self, current_data: Dict, timestamp: datetime):
        """Check for profile field changes"""
        changes = [
            ('personaname', 'nickname', self.profile.personaname),
            ('realname', 'real name', self.profile.realname),
            ('loccountrycode', 'country', self.profile.country),
            ('profileurl', 'profile URL', self.profile.profile_url),
            ('avatarfull', 'avatar', self.profile.avatar)
        ]
        
        for api_field, display_name, old_value in changes:
            new_value = current_data.get(api_field)
            
            # Normalize empty values
            old_norm = old_value if old_value not in ("", None) else None
            new_norm = new_value if new_value not in ("", None) else None
            
            if old_norm != new_norm:
                message = f"{self.profile.personaname} changed {display_name}: '{old_norm}' -> '{new_norm}'"
                self.logger.log(message, Style.MAGENTA)
                
                # Update stored value
                if api_field == 'personaname':
                    self.profile.personaname = new_norm
                elif api_field == 'realname':
                    self.profile.realname = new_norm
                elif api_field == 'loccountrycode':
                    self.profile.country = new_norm
                elif api_field == 'profileurl':
                    self.profile.profile_url = new_norm
                elif api_field == 'avatarfull':
                    self.profile.avatar = new_norm
    
    def _format_duration(self, delta: timedelta) -> str:
        """Format duration in readable format"""
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds and not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts) if parts else "0s"

# -------------------------
# Main Application
# -------------------------
def create_banner():
    print(f"""
{Style.CYAN}{Style.BOLD}
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃       STEAM STATUS MONITOR        ┃
┃         Made by NezrKaan          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
{Style.RESET}
{Style.DIM}Real-time Steam user monitoring with safe settings{Style.RESET}
""")

def main():
    create_banner()
    
    # Get API key
    print(f"{Style.BOLD}Setup:{Style.RESET}")
    api_key = input(f"Steam API Key: ").strip()
    if not api_key:
        print(f"{Style.RED}API key is required!{Style.RESET}")
        return
    
    # Get user to monitor
    user_id = input(f"Steam user (ID or custom URL): ").strip()
    if not user_id:
        print(f"{Style.RED}User identifier is required!{Style.RESET}")
        return
    
    # Optional Discord webhook
    discord_webhook = input(f"Discord webhook URL (optional): ").strip() or None
    
    # Create config with safe defaults
    config = Config(
        api_key=api_key,
        user_identifier=user_id,
        discord_webhook=discord_webhook
    )
    
    print(f"\n{Style.DIM}Using safe monitoring settings (20 second intervals){Style.RESET}")
    
    # Setup and start monitor
    monitor = SteamMonitor(config)
    
    if not monitor.setup_user():
        return
    
    input(f"\n{Style.GREEN}Press Enter to start monitoring...{Style.RESET}")
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
