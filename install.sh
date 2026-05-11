#!/usr/bin/env bash
# install.sh – system-wide installation of CONTRA

set -e

# Must be root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)."
    exit 1
fi

echo "[*] Installing required packages..."
apt update
apt install -y nmap traceroute netcat-openbsd openssl dnsutils xterm proxychains

echo "[*] Installing contra to /usr/local/bin/contra..."
install -m 755 contra.py /usr/local/bin/contra

echo "[+] Done. You can now run 'sudo contra' from anywhere."