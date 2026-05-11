# CONTRA – Remote Connection Reconnaissance & Counter Action Suite

**CONTRA** is an advanced, modular network exploitation and post‑exploitation framework. It scans active connections on the local machine, assesses their threat level, and can autonomously deploy reverse shells, persistence mechanisms, and comprehensive network reconnaissance against selected targets.

> ⚠️ **DISCLAIMER**
> This tool is intended **only** for authorised security assessments on networks and systems you own or have explicit permission to test. Unauthorised use is illegal and unethical. The author assumes no liability for misuse.

## Features

- **Real‑time connection monitoring**
  Uses `ss` and `ps` to list active ESTABLISHED connections, identify the remote address, process name, and TTY.
- **Threat scoring engine**
  Classifies connections based on:
  - Remote port (known malicious ports)
  - Process (e.g., `sshd`, `redis`, `mongod`)
  - IP type (private vs. public)
  Generates a score and a visual classification (`UNAUTHORIZED ACCESS`, `SUSPICIOUS ACTIVITY`, `NORMAL INTERNET`).
- **Polymorphic payload generator**
  Creates hundreds of obfuscated reverse‑shell payloads:
  - Bash, Python, OpenSSL pipelines
  - PowerShell for Windows targets
  - Random comments, whitespace, and case changes to evade signature‑based detection
- **Autonomous exploitation**
  - Automatically select a high‑threat target from the connection list.
  - Spawn a listener on a random high port.
  - Test all generated payloads against the target.
  - On success, deploy persistence mechanisms.
- **Persistence deployment**
  Installs hidden, periodic callback scripts on Linux and Windows targets (via `nc`).
- **Multi‑route traceroute**
  Runs six parallel traceroutes using:
  - Standard traceroute
  - System DNS
  - ProxyChains
  - VPN endpoint traceroutes
  - Tor network
  - Full DNS resolution with `dig +trace`
- **Comprehensive scanning**
  Launches parallel Nmap scans: full TCP, UDP, vulnerability scripts, OS detection, and service versioning.
- **Beautiful terminal UI**
  Colour‑coded output, live connection table, and step‑by‑step feedback.

## Requirements

- **Operating System**: Linux (tested on Kali, Ubuntu, Debian)
- **Python**: 3.6+
- **Root privileges** (required by `ss` and deployment commands)
- **External tools** (must be installed):
  - `netcat` (traditional or nmap‑ncat)
  - `nmap`
  - `traceroute`
  - `openssl`
  - `proxychains` (optional, for Tor/VPN routes)
  - `dig`
  - `xterm` (for automated windows; can be replaced with `gnome-terminal` or removed)
- **Python modules**: all are standard library (`os`, `re`, `sys`, `time`, `socket`, `random`, `subprocess`, `ipaddress`, `threading`, `configparser`, `datetime`, `collections`).

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/contra.git
cd contra

# Install system dependencies (Debian/Ubuntu)
sudo apt update
sudo apt install -y nmap traceroute netcat-openbsd openssl dnsutils xterm proxychains

# Give execution permission
chmod +x contra.py
```

Note: If you don’t have proxychains configured, the Tor/VPN traceroute steps will fail gracefully.

Usage

Run as root:

```bash
sudo ./contra.py
```

Main Menu

```
----====<[ C O N T R A ]>====----
Remote connection reconnaissance tracehound and counter action.
Contact: Using force to take the situation under control.
============================================================
1. Scan active connections
2. Autonomous exploitation
3. Deploy persistence
4. Advanced traceroute
5. Comprehensive network scan
6. Exit
Select option:
```

Typical Workflow

1. Scan active connections (option 1)
   · Displays a table of all remote ESTABLISHED sockets.
   · Automatically highlights high‑threat targets (score ≥ 40).
2. Autonomous exploitation (option 2)
   · Choose a connection from the list.
   · The tool will:
     · Launch a full traceroute and Nmap scan in the background.
     · Generate hundreds of polymorphic payloads.
     · Open a listener on a random port.
     · Send each payload to the target and check for a return shell.
     · On success, deploy persistence.
3. Manual persistence (option 3)
   · Re‑deploy persistence to the last selected target, or manually specify one.
4. Advanced traceroute (option 4)
   · Execute the six‑route traceroute against the current target.
5. Comprehensive scan (option 5)
   · Run full TCP, UDP, vulnerability, OS, and service scans.

File Structure

```
contra/
├── contra.py          # Main script
└── README.md          # This file
```

No external configuration is required; the listener port is randomised at startup. You may modify PROXY_CHAINS_CONF and VPN_PROVIDERS inside the script.

How It Works (Technical Breakdown)

· Connection Gathering
    ss -ntup lists all TCP/UDP sockets in numeric form. The output is parsed to extract PID, process name, and remote IP:port.
· Threat Assessment
    assess_threat() checks the remote port against a hardcoded list of common attack surfaces (SQL, SSH, RDP, etc.), the process name against known remote services, and whether the IP is private or public. A score is accumulated, and a global THREAT_SCORE dictionary tracks all seen IPs.
· Polymorphism
    generate_polymorphic_payloads() starts with a base set of reverse‑shell one‑liners and applies transformations:
  · Prepends or interleaves random comments and whitespace.
  · Randomises capitalisation of letters (helpful against case‑sensitive filtering).
  · Combines multiple encodings (e.g., OpenSSL‑encrypted pipes).
· Autonomous Exploitation
    autonomous_shell_test() runs the traceroute and scan in background threads. It then iterates over the shuffled payload list, sending each with echo '...' | nc <target> <port>. After each attempt, it checks whether the local listener (nc -lnvp) has an established connection. If it does, it calls deploy_persistence() to install the callback scripts.
· Persistence
    For Linux, a loop script is written to /tmp/.systemd-cache that re‑connects every 10 minutes (with a random delay). For Windows, a VBScript is created and added to the Run registry key. Both are sent via nc to the target’s port (assuming a shell is already present or the target is vulnerable to command injection).
· Traceroute & Scanning
    Each step opens a new xterm window to display the ongoing operation. This allows the user to watch multiple scans concurrently and keeps the main menu responsive.

Known Limitations

· Root requirement: The tool must run as root for raw socket access and to bind listening ports.
· X11 dependency: Uses xterm -display :0; on headless servers, either set DISPLAY appropriately or replace those calls with background processes.
· Detection: Payloads are transmitted in plain text and will likely trigger network and endpoint detection systems. This is a test tool, not a stealth framework.
· No session handling: The reverse shell listener is a single nc instance; multiple simultaneous connections may be unpredictable.
· Hardcoded payloads: Windows persistence expects a command‑execution vector (e.g., a web shell that runs cmd commands via nc).

Contributing

Pull requests for additional payload obfuscation, better session management, or multi‑platform support are welcome. Please ensure you only contribute features that adhere to ethical use.

License

This project is provided for educational and authorised testing purposes only. The author retains all copyrights. Usage of this tool for malicious activities is strictly prohibited.
