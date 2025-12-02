#!/usr/bin/env python3
"""
Steam Presence Monitor
"""

import sys
import json
import time
import signal
import logging
import threading
import requests
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m" 
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

@dataclass
class UserState:
    steamid: str
    personaname: str = "Unknown"
    avatar: str = ""
    status: int = 0
    game: Optional[str] = None
    last_change: float = field(default_factory=time.time)

class ConfigurationManager:
    FILE_PATH = "monitor_config.json"

    def __init__(self):
        self.api_key: str = ""
        self.webhook_url: Optional[str] = None
        self.target_users: List[str] = []
        self.interval: int = 30
        self._load()

    def _load(self):
        if Path(self.FILE_PATH).exists():
            try:
                with open(self.FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key", "")
                    self.webhook_url = data.get("webhook_url")
                    self.target_users = data.get("target_users", [])
                    self.interval = data.get("interval", 30)
            except Exception:
                pass

    def save(self):
        data = {
            "api_key": self.api_key,
            "webhook_url": self.webhook_url,
            "target_users": self.target_users,
            "interval": self.interval
        }
        with open(self.FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def validate(self) -> bool:
        return bool(self.api_key and self.target_users)

class NetworkClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def get_summaries(self, steam_ids: List[str]) -> List[Dict]:
        if not steam_ids:
            return []
        
        chunked_ids = [steam_ids[i:i + 100] for i in range(0, len(steam_ids), 100)]
        all_players = []

        for chunk in chunked_ids:
            try:
                response = self.session.get(
                    "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
                    params={"key": self.api_key, "steamids": ",".join(chunk)},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                all_players.extend(data.get("response", {}).get("players", []))
            except Exception as e:
                logging.error(f"Network error during fetch: {e}")
        
        return all_players

    def resolve_id(self, vanity_url: str) -> Optional[str]:
        if vanity_url.isdigit() and len(vanity_url) == 17:
            return vanity_url
        
        try:
            response = self.session.get(
                "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
                params={"key": self.api_key, "vanityurl": vanity_url},
                timeout=5
            )
            data = response.json()
            if data.get("response", {}).get("success") == 1:
                return data["response"]["steamid"]
        except Exception:
            pass
        return None

class NotificationService:
    def __init__(self, webhook_url: Optional[str]):
        self.webhook_url = webhook_url
        self._executor = ThreadPoolExecutor(max_workers=2)

    def dispatch(self, title: str, desc: str, color: int, thumb: str = None, fields: List = None):
        if not self.webhook_url:
            return
        self._executor.submit(self._send, title, desc, color, thumb, fields)

    def _send(self, title, desc, color, thumb, fields):
        payload = {
            "embeds": [{
                "title": title,
                "description": desc,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "thumbnail": {"url": thumb} if thumb else {},
                "footer": {"text": "System Monitor v3.0"}
            }]
        }
        if fields:
            payload["embeds"][0]["fields"] = fields
        
        try:
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            logging.warning(f"Failed to deliver notification: {e}")

class MonitorEngine:
    STATUS_MAP = {
        0: ("Offline", Colors.GRAY),
        1: ("Online", Colors.GREEN),
        2: ("Busy", Colors.RED),
        3: ("Away", Colors.YELLOW),
        4: ("Snooze", Colors.BLUE),
        5: ("Trading", Colors.CYAN),
        6: ("Playing", Colors.MAGENTA)
    }

    def __init__(self):
        self._setup_logging()
        self.config = ConfigurationManager()
        self.client = None
        self.notifier = None
        self.states: Dict[str, UserState] = {}
        self.running = False

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format=f"{Colors.GRAY}%(asctime)s{Colors.RESET} %(message)s",
            datefmt="[%H:%M:%S]",
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    def setup_wizard(self):
        print(f"{Colors.BOLD}{Colors.BLUE}System Configuration Utility{Colors.RESET}")
        if not self.config.api_key:
            self.config.api_key = input("API Key: ").strip()
        
        if not self.config.webhook_url:
            wb = input("Webhook URL (Optional): ").strip()
            self.config.webhook_url = wb if wb else None
        
        if not self.config.target_users:
            while True:
                uid = input("Add User (ID/URL) [Empty to finish]: ").strip()
                if not uid:
                    break
                self.client = NetworkClient(self.config.api_key)
                resolved = self.client.resolve_id(uid.split('/')[-1] if '/' in uid else uid)
                if resolved:
                    self.config.target_users.append(resolved)
                    logging.info(f"Added user ID: {resolved}")
                else:
                    logging.error("Invalid identifier")
        
        self.config.save()
        self.client = NetworkClient(self.config.api_key)
        self.notifier = NotificationService(self.config.webhook_url)

    def _process_changes(self, user_data: Dict):
        sid = user_data["steamid"]
        current_state = self.states.get(sid)
        
        new_status_code = user_data.get("personastate", 0)
        new_game = user_data.get("gameextrainfo")
        
        status_label, status_color = self.STATUS_MAP.get(new_status_code, ("Unknown", Colors.WHITE))

        if not current_state:
            self.states[sid] = UserState(
                steamid=sid,
                personaname=user_data.get("personaname"),
                avatar=user_data.get("avatarfull"),
                status=new_status_code,
                game=new_game
            )
            game_txt = f" | Playing: {new_game}" if new_game else ""
            logging.info(f"{Colors.BOLD}{user_data['personaname']:<20}{Colors.RESET} initialized: {status_color}{status_label}{Colors.RESET}{game_txt}")
            return

        # Status Change
        if new_status_code != current_state.status:
            logging.info(f"{Colors.BOLD}{current_state.personaname}{Colors.RESET} changed status: {status_color}{status_label}{Colors.RESET}")
            self.notifier.dispatch(
                "Status Update",
                f"**{current_state.personaname}** is now **{status_label}**",
                0x3498db,
                current_state.avatar
            )
            current_state.status = new_status_code

        # Game Activity
        if new_game != current_state.game:
            if new_game:
                logging.info(f"{Colors.GREEN}>> {current_state.personaname} started: {new_game}{Colors.RESET}")
                self.notifier.dispatch(
                    "Activity Started",
                    f"**{current_state.personaname}** is playing **{new_game}**",
                    0x2ecc71,
                    current_state.avatar
                )
                current_state.last_change = time.time()
            else:
                duration = int(time.time() - current_state.last_change)
                hours, remainder = divmod(duration, 3600)
                minutes, _ = divmod(remainder, 60)
                time_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
                
                logging.info(f"{Colors.YELLOW}<< {current_state.personaname} closed: {current_state.game} ({time_str}){Colors.RESET}")
                self.notifier.dispatch(
                    "Activity Ended",
                    f"**{current_state.personaname}** finished **{current_state.game}**",
                    0xe74c3c,
                    current_state.avatar,
                    [{"name": "Duration", "value": time_str}]
                )
            
            current_state.game = new_game

    def run(self):
        if not self.config.validate():
            self.setup_wizard()

        self.client = NetworkClient(self.config.api_key)
        self.notifier = NotificationService(self.config.webhook_url)
        self.running = True

        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        logging.info(f"Engine started. Monitoring {len(self.config.target_users)} targets.")
        
        while self.running:
            start_time = time.time()
            try:
                users = self.client.get_summaries(self.config.target_users)
                for user in users:
                    self._process_changes(user)
            except Exception as e:
                logging.error(f"Cycle error: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.config.interval - elapsed)
            time.sleep(sleep_time)

    def _shutdown(self, signum, frame):
        logging.info("Shutdown signal received. Terminating...")
        self.running = False
        sys.exit(0)

if __name__ == "__main__":
    MonitorEngine().run()
