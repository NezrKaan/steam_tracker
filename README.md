# Steam Tracker

"tracker.py" is a precise Steam profile monitoring tool designed for OSINT enthusiasts, researchers, and gamers. Using the official Steam Web API, it tracks and logs real-time changes in user status, game activity, and profile details such as nickname, real name, country, avatar, and profile URL. Outputs are color-coded and timestamped, with persistent logs saved to steam_status_log.txt. Ideal for digital footprint analysis, user behavior tracking, OSINT, and investigative research.

Why is this important?
Steam automatically runs when a computer is started, making it possible to monitor if and when someone uses their computer by tracking their Steam online status. This tool allows you to see exactly when a user logs in and out, what games they play, and even subtle profile changes, effectively revealing their computer usage patterns and online behavior. For OSINT researchers, cybersecurity analysts, or anyone interested in digital footprint tracking, this means you can gather detailed, time-stamped insights about a user’s activity remotely and continuously without intrusive software.

## Features

* Tracks Steam user status changes (online, offline, busy, away, etc.)
* Detects game start/stop events with timestamps and play duration
* Monitors profile updates: nickname, real name, country, profile URL, avatar changes
* Color-coded console output for easy reading
* Logs all events to a persistent log file
* Resolves custom Steam vanity URLs to SteamID64
* Simple setup, runs continuously until interrupted

## Installation

1. Clone the repository:

   git clone [https://github.com/NezrKaan/steam\_tracker.git](https://github.com/NezrKaan/steam_tracker.git)
   cd steam\_tracker

2. Install dependencies:

   python3 -m pip install requests

## Usage

Run the tracker script:

python3 tracker.py

* Enter your Steam Web API key when prompted.
* Provide either a SteamID64 or custom profile name (vanity URL).
* The program will start monitoring the user, printing live updates and logging to `steam_status_log.txt`.
* Exit anytime with `Ctrl+C`.

## Getting a Steam Web API Key

1. Visit [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. Log in with your Steam account.
3. Register your domain (or use `localhost` if testing locally).
4. Copy your API key and use it with this tool.

## Notes

* The script requires an active internet connection.
* The monitored profile must be public or accessible via the API.
* Changes are detected every 10 seconds by default.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

Made by NezrKaan
GitHub: [https://github.com/NezrKaan/steam\_tracker](https://github.com/NezrKaan/steam_tracker)
