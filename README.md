Steam Tracker
"tracker.py" is a precise Steam profile monitoring tool designed for OSINT enthusiasts, researchers, and gamers. Using the official Steam Web API, it tracks and logs real-time changes in user status, game activity, and profile details such as nickname, real name, country, avatar, and profile URL. Outputs are color-coded and timestamped, with persistent logs saved to steam_status_log.txt. Ideal for digital footprint analysis, user behavior tracking, OSINT, and investigative research.
Why is this important?
Steam automatically runs when a computer is started, making it possible to monitor if and when someone uses their computer by tracking their Steam online status. This tool allows you to see exactly when a user logs in and out, what games they play, and even subtle profile changes, effectively revealing their computer usage patterns and online behavior. For OSINT researchers, cybersecurity analysts, or anyone interested in digital footprint tracking, this means you can gather detailed, time-stamped insights about a user's activity remotely and continuously without intrusive software.
Features

Real-time Status Tracking - Monitors Steam user status changes (online, offline, busy, away, etc.)
Game Activity Detection - Detects game start/stop events with timestamps and play duration calculation
Profile Change Monitoring - Tracks profile updates including nickname, real name, country, profile URL, and avatar changes
Color-coded Output - Easy-to-read console output with color coding for different event types
Persistent Logging - All events logged to steam_status_log.txt with timestamps
JSON Event Log - Machine-readable event history in steam_events.json
Vanity URL Support - Resolves custom Steam vanity URLs to SteamID64 automatically
Safe Rate Limiting - Built-in API rate limiting with 20-second intervals for optimal performance
Comprehensive Error Handling - Robust error handling for network issues and API limitations

Installation

Clone the repository:
bashgit clone https://github.com/NezrKaan/steam_tracker.git
cd steam_tracker

Install dependencies:
bashpython3 -m pip install requests


Usage

Run the tracker script:
bashpython3 tracker.py

Enter your Steam Web API key when prompted
Provide target user identification:

SteamID64 (e.g., 76561198123456789)
Custom profile name/vanity URL (e.g., gaben)


Optional: Enter Discord webhook URL for notifications
The program will start monitoring, displaying live updates and logging to files
Exit anytime with Ctrl+C

Getting a Steam Web API Key

Visit https://steamcommunity.com/dev/apikey
Log in with your Steam account
Register your domain (you can use localhost for personal use)
Copy your API key and use it with this tool

Output Examples
Console Output
[14:23:15] john_doe is now Online (was Offline)
[14:25:32] john_doe started playing 'Counter-Strike 2'
[16:42:18] john_doe stopped playing 'Counter-Strike 2' (played for 2h 16m)
[16:42:25] john_doe changed nickname: 'john_doe' -> 'JohnTheGamer'
[16:45:03] john_doe is now Away (was Online)
Log Files

steam_status_log.txt - Human-readable log with timestamps
steam_events.json - Machine-readable JSON format for data analysis

Technical Details
Monitoring Capabilities

Status Changes: Online/Offline transitions, Away/Busy states
Game Activity: Start/stop times, duration calculations, game switching
Profile Modifications: Name changes, country updates, avatar changes, profile URL modifications
Timing Analysis: Precise timestamps for all events, activity pattern recognition

API Specifications

Request Interval: 20 seconds (optimized for single-user tracking)
Rate Limiting: Built-in protection against API rate limits
Timeout Handling: 10-second request timeouts with retry logic
Error Recovery: Automatic recovery from temporary network issues

Important Notes & Warnings
Legal & Ethical Considerations
⚠️ IMPORTANT: This tool is intended for legitimate research, security analysis, and personal use only. Users must comply with:

Steam's Terms of Service and API Terms of Use
Local privacy laws and regulations
Ethical guidelines for data collection and monitoring
Obtaining appropriate permissions when monitoring others

Technical Limitations

Public Profiles Only: Can only monitor users with public Steam profiles
API Dependency: Requires active internet connection and Steam API availability
Rate Limits: Steam API has rate limits; tool includes safe defaults
Privacy Settings: Some profile information may be hidden based on user privacy settings

Privacy & Security

Data Storage: All logs are stored locally on your machine
No Data Transmission: Tool does not send data to external servers (except Steam API)
Sensitive Information: API keys and logs may contain sensitive information - handle appropriately
Responsible Use: Always respect user privacy and applicable laws

System Requirements

Python: 3.6 or higher
Dependencies: requests library
Storage: Minimal disk space for log files
Network: Stable internet connection for API requests

Troubleshooting
Common Issues

"Could not resolve custom URL": Verify the vanity URL is correct and public
"API request failed": Check your API key and internet connection
"Rate limited": Tool will automatically wait and retry
Empty profile data: Target profile may be private or have restricted visibility

Debug Tips

Verify API key is valid at Steam's developer portal
Ensure target profile is set to public
Check firewall settings if connection issues persist
Monitor console output for specific error messages

Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues for:

Bug fixes and improvements
Feature suggestions
Documentation updates
Code optimization

Changelog
Current Version Features

20-second monitoring intervals (optimized from 30s)
Enhanced profile change detection
Improved error handling and recovery
Color-coded console output
Dual logging system (text + JSON)
Comprehensive game activity tracking

License
MIT License — see LICENSE for details.
Disclaimer
This tool is provided for educational and research purposes. Users are responsible for ensuring their use complies with applicable laws, terms of service, and ethical guidelines. The authors assume no responsibility for misuse or any consequences arising from the use of this software.

Made by NezrKaan
GitHub: https://github.com/NezrKaan/steam_tracker
For OSINT researchers, cybersecurity analysts, and digital footprint investigation
