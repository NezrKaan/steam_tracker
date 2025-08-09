# Steam Tracker

`tracker.py` is a precise Steam profile monitoring tool designed for OSINT enthusiasts, researchers, and gamers. Using the official Steam Web API, it tracks and logs real-time changes in user status, game activity, and profile details such as nickname, real name, country, avatar, and profile URL. Outputs are color-coded and timestamped, with persistent logs saved to `steam_status_log.txt`. Ideal for digital footprint analysis, user behavior tracking, and investigative research.

## Features

- Tracks Steam user status changes (online, offline, busy, away, etc.)
- Detects game start/stop events with timestamps and play duration
- Monitors profile updates: nickname, real name, country, profile URL, avatar changes
- Color-coded console output for easy reading
- Logs all events to a persistent log file
- Resolves custom Steam vanity URLs to SteamID64
- Runs in terminal, disables input echo for cleaner UX
- Simple setup, runs continuously until interrupted

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/NezrKaan/steam_tracker.git
   cd steam_tracker
Install dependencies:

bash
Copy
Edit
python3 -m pip install requests
Usage
Run the tracker script:

bash
Copy
Edit
python3 tracker.py
Enter your Steam Web API key when prompted.

Provide either a SteamID64 or custom profile name (vanity URL).

The program will start monitoring the user, printing live updates and logging to steam_status_log.txt.

Exit anytime with Ctrl+C.

Getting a Steam Web API Key
Visit Steam API Key registration.

Log in with your Steam account.

Register your domain (or use localhost if testing locally).

Copy your API key and use it with this tool.

Notes
The script requires an active internet connection.

The monitored profile must be public or accessible via the API.

Changes are detected every 10 seconds by default.

Input echo is disabled for cleaner output; no key presses will show in the terminal.

License
MIT License — see LICENSE for details.

Made by NezrKaan
GitHub: NezrKaan/steam_tracker
