Steam Tracker
Steam Tracker is an advanced OSINT (Open Source Intelligence) monitoring tool designed for digital footprint analysis, behavioral research, and real-time user tracking. Leveraging the official Steam Web API, it provides granular visibility into user activity, session duration, and profile modifications.

This tool is engineered for security researchers, data analysts, and OSINT professionals requiring precise, timestamped logs of target activity without deploying intrusive client-side software.

Intelligence Value
Steam clients often launch automatically upon system startup, making Steam activity a high-fidelity indicator of a target's physical presence and computer usage. Steam Tracker capitalizes on this by monitoring:

System Activity Patterns: Correlate online/offline transitions with physical activity.

Behavioral Analysis: Track gaming habits, session lengths, and time-of-day usage patterns.

Profile Integrity: Detect subtle changes in identity (avatar, aliases, location data) often used to obfuscate user identity.

This data enables the construction of detailed behavioral profiles and activity timelines remotely and passively.

Key Features
Multi-Target Monitoring: Support for tracking multiple subjects simultaneously (Enterprise Edition).

Real-time State Detection: Instant logging of status transitions (Online, Offline, Away, Busy, Snooze).

Session Telemetry: Precise calculation of game session durations and application switching.

Profile Reconnaissance: Automatic detection of changes to:

Display Name (Aliases)

Real Name

Geo-location (Country Code)

Avatar/Profile Images

Custom URL (Vanity ID)

Discord Integration: Real-time rich embed notifications sent to a configured Discord Webhook.

Resilient Architecture: Built-in network error handling, auto-reconnection logic, and thread-safe execution.

Dual-Format Logging:

monitor.log: Human-readable chronological events.

steam_events.json: Structured data for programmatic analysis.

Installation
Prerequisites
Python 3.8 or higher

Valid Steam Web API Key

Internet connectivity

Setup
Clone the Repository

Bash

git clone https://github.com/NezrKaan/steam_tracker.git
cd steam_tracker
Install Dependencies

Bash

pip3 install -r requirements.txt
# Or manually:
pip3 install requests
Configuration
The tool utilizes a monitor_config.json file for persistent configuration. This is generated automatically upon the first run, or can be created manually:

JSON

{
  "api_key": "YOUR_STEAM_API_KEY",
  "webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
  "target_users": [
    "76561198000000000",
    "76561198000000001"
  ],
  "interval": 30
}
api_key: Obtain from Steam Developer Portal.

webhook_url: (Optional) For Discord notifications.

target_users: List of SteamID64s to monitor.

interval: Polling frequency in seconds (Default: 30).

Usage
Execute the tracker using Python:

Bash

python3 tracker.py
Operational Workflow
Initialization: Validates API credentials and resolves target vanity URLs.

Baseline Acquisition: Fetches initial state for all targets.

Polling Loop: Queries the Steam API at defined intervals.

Delta Analysis: Compares current state against cached state to identify changes.

Reporting: Logs events to console/disk and dispatches webhook alerts.

Output Samples
Console Stream
Plaintext

[14:23:15] [INFO] Target_A is now Online (was Offline)
[14:25:32] [INFO] Target_A started playing 'Counter-Strike 2'
[16:42:18] [INFO] Target_A stopped playing 'Counter-Strike 2' (Duration: 2h 16m)
[16:42:25] [WARN] Target_A changed nickname: 'Target_A' -> 'GhostUser'
Discord Alerts
Rich embeds provide visual indicators:

Green: Online / Game Started

Red: Offline / Game Stopped

Yellow: Status Change (Away/Busy)

Blue: Profile Metadata Change

Legal & Ethical Disclaimer
Steam Tracker is strictly intended for educational purposes, authorized security research, and personal use.

Compliance: Users are responsible for complying with Steam's Terms of Service, the Steam Web API Terms of Use, and all applicable local, state, and federal privacy laws.

Privacy: This tool accesses only publicly available profile data. It cannot bypass privacy settings or access private profiles.

Liability: The developer (NezrKaan) assumes no liability for misuse of this software or for any consequences resulting from its use.

Author
NezrKaan Full Stack Developer & Security Researcher

Website: nezrkaan.com GitHub: github.com/NezrKaan
