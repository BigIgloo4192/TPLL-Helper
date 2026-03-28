"""
TPLL Helper for Minecraft (Version 2.5)
Automates teleporting to real-world coordinates from Google Earth Pro into Minecraft.

Changelog:
  2.2: Bug fixes, coordinate validation, auto-save, GEP activation without focus.
  2.3: Auto-Place mode — jump, look down, place block after teleport.
  2.4: Coordinate CSV logging.
  2.5: System tray icon, success beep, cumulative session time, About tab,
       clear log button, duplicate hotkey warning.
"""

import time
import sys
import os
import re
import csv
import threading
import winsound
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import ctypes
import webbrowser

import keyboard
import pyperclip

try:
    import win32api
    import win32con
    import win32gui
    import pywintypes
except ImportError:
    print("ERROR: PyWin32 library not found. Please install it:\npip install pywin32")
    sys.exit()

# System tray support — optional dependency
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# ==========================================
# --- CONFIGURATION & CONSTANTS ---
# ==========================================

APP_NAME_FOR_DATA_FOLDER = "TPLLHelper"
APP_VERSION = "2.5"
GITHUB_URL = "https://github.com/BigIgloo4192/TPLL-Helper"  
DISCORD_CONTACT = "DM realbigigloo"
EMAIL_CONTACT = "bigigloo4192@gmail.com"

# Setup AppData Settings Directory
try:
    local_app_data_path = os.path.expandvars('%LOCALAPPDATA%')
    APP_SETTINGS_DIR = os.path.join(local_app_data_path, APP_NAME_FOR_DATA_FOLDER)
    os.makedirs(APP_SETTINGS_DIR, exist_ok=True)
    SETTINGS_FILENAME = os.path.join(APP_SETTINGS_DIR, "tpllhelper_settings.json")
    LOG_FILENAME = os.path.join(APP_SETTINGS_DIR, "tpll_coordinate_log.csv")
except Exception as e:
    APP_SETTINGS_DIR = os.getcwd()
    SETTINGS_FILENAME = "tpllhelper_settings.json"
    LOG_FILENAME = "tpll_coordinate_log.csv"

DEFAULT_CONFIG_SETTINGS = {
    "HOTKEY": '`',
    "END_HOTKEY": 'f12',
    "CHAT_KEY": 't',
    "SHOW_WINDOW_ON_STARTUP": True,
    "AUTO_PLACE_ENABLED": False,
    "COORD_LOG_ENABLED": False,
    "SOUND_ENABLED": False,
    "TOTAL_TPLL_COUNT": 0,
    "TOTAL_SESSION_SECONDS": 0
}

# Window Target Titles
MINECRAFT_TITLE_KEYWORD = "Minecraft"
GOOGLE_EARTH_TITLE = "Google Earth Pro"

# Delays (in seconds) to ensure windows and clipboards catch up
GEP_ACTIVATE_WAIT = 0.02
COPY_WAIT = 0.03
MC_ACTIVATE_WAIT = 0.08
ESC_WAIT = 0.05
CHAT_OPEN_WAIT = 0.03
PRE_COPY_WAIT = 0.03
VK_SLEEP = 0.05
PRE_ENTER_WAIT = 0.03

# Auto-Place timing delays
TELEPORT_SETTLE_WAIT = 0.25
JUMP_AIRBORNE_WAIT = 0.12
LOOK_DOWN_SETTLE_WAIT = 0.05

# Large downward mouse delta — Minecraft clamps pitch at 90° so overshooting is fine.
LOOK_DOWN_MOUSE_DELTA = 15000

# Regex to validate coordinate strings from Google Earth Pro.
COORD_PATTERN = re.compile(
    r'^["\s]*-?\d+\.?\d*[°\s]*[NSns]?\s*[,\s]\s*-?\d+\.?\d*[°\s]*[EWew]?["\s]*$'
)

# Auto-save the TPLL count to disk every N successful teleports.
AUTOSAVE_INTERVAL = 10

# CSV column headers for the coordinate log file.
LOG_CSV_HEADERS = ["timestamp", "coordinates", "session_count", "total_count"]

# Success beep parameters (frequency in Hz, duration in ms)
BEEP_FREQUENCY = 800
BEEP_DURATION = 100

# ==========================================
# --- KEYBINDING LISTS ---
# ==========================================

TPLL_SAFE_KEYS = [
    '`', '\\', '[', ']',
    'f1', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f12',
    'b', 'c', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'q', 't', 'v', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'esc', 'insert', 'home', 'end', 'tab'
]

ALL_KEYS = [
    '`', '/', '\\', '-', '=', '[', ']',
    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'enter', 'esc', 'insert', 'delete', 'home', 'end', 'pageup', 'pagedown', 'tab'
]

SPECIAL_VK_MAP = {
    'F1': win32con.VK_F1, 'F2': win32con.VK_F2, 'F3': win32con.VK_F3,
    'F4': win32con.VK_F4, 'F5': win32con.VK_F5, 'F6': win32con.VK_F6,
    'F7': win32con.VK_F7, 'F8': win32con.VK_F8, 'F9': win32con.VK_F9,
    'F10': win32con.VK_F10, 'F11': win32con.VK_F11, 'F12': win32con.VK_F12,
    'ENTER': win32con.VK_RETURN, 'ESC': win32con.VK_ESCAPE, 'ESCAPE': win32con.VK_ESCAPE,
    'INS': win32con.VK_INSERT, 'INSERT': win32con.VK_INSERT,
    'DEL': win32con.VK_DELETE, 'DELETE': win32con.VK_DELETE,
    'HOME': win32con.VK_HOME, 'END': win32con.VK_END,
    'PGUP': win32con.VK_PRIOR, 'PAGEUP': win32con.VK_PRIOR,
    'PGDN': win32con.VK_NEXT, 'PAGEDOWN': win32con.VK_NEXT,
    'UP': win32con.VK_UP, 'DOWN': win32con.VK_DOWN,
    'LEFT': win32con.VK_LEFT, 'RIGHT': win32con.VK_RIGHT, 'TAB': win32con.VK_TAB,
}

# ==========================================
# --- GLOBAL STATE ---
# ==========================================

tpll_hotkey_listener_thread = None
app_instance = None
_count_lock = threading.Lock()

# ==========================================
# --- DATA & SETTINGS MANAGEMENT ---
# ==========================================

def save_settings_to_file(settings_data):
    """Saves the current configuration dictionary to the JSON file."""
    global TOTAL_TPLL_COUNT
    try:
        settings_to_save = settings_data.copy()
        settings_to_save["TOTAL_TPLL_COUNT"] = TOTAL_TPLL_COUNT
        with open(SETTINGS_FILENAME, 'w') as f:
            json.dump(settings_to_save, f, indent=4)
        return True
    except Exception as e:
        if app_instance:
            app_instance.update_status_async(f"Error saving settings: {e}", is_error=True)
    return False


def load_or_create_settings():
    """Loads settings from JSON, or creates a new one with defaults if none exists."""
    global HOTKEY, END_HOTKEY, CHAT_KEY, SHOW_WINDOW_ON_STARTUP
    global AUTO_PLACE_ENABLED, COORD_LOG_ENABLED, SOUND_ENABLED
    global TOTAL_TPLL_COUNT, TOTAL_SESSION_SECONDS
    effective_settings = DEFAULT_CONFIG_SETTINGS.copy()

    try:
        if os.path.exists(SETTINGS_FILENAME):
            with open(SETTINGS_FILENAME, 'r') as f:
                loaded_from_file = json.load(f)
            for key, default_value in DEFAULT_CONFIG_SETTINGS.items():
                if key in loaded_from_file and isinstance(loaded_from_file[key], type(default_value)):
                    effective_settings[key] = loaded_from_file[key]
        else:
            save_settings_to_file(effective_settings)
    except Exception:
        pass

    HOTKEY = effective_settings["HOTKEY"]
    END_HOTKEY = effective_settings["END_HOTKEY"]
    CHAT_KEY = effective_settings["CHAT_KEY"]
    SHOW_WINDOW_ON_STARTUP = effective_settings["SHOW_WINDOW_ON_STARTUP"]
    AUTO_PLACE_ENABLED = effective_settings["AUTO_PLACE_ENABLED"]
    COORD_LOG_ENABLED = effective_settings["COORD_LOG_ENABLED"]
    SOUND_ENABLED = effective_settings["SOUND_ENABLED"]
    TOTAL_TPLL_COUNT = int(effective_settings.get("TOTAL_TPLL_COUNT", 0))
    TOTAL_SESSION_SECONDS = int(effective_settings.get("TOTAL_SESSION_SECONDS", 0))


load_or_create_settings()

# ==========================================
# --- COORDINATE LOGGING ---
# ==========================================

def log_coordinates(coords, session_count, total_count):
    """Appends a timestamped row to the CSV coordinate log file."""
    try:
        file_is_new = not os.path.exists(LOG_FILENAME) or os.path.getsize(LOG_FILENAME) == 0
        with open(LOG_FILENAME, 'a', newline='') as f:
            writer = csv.writer(f)
            if file_is_new:
                writer.writerow(LOG_CSV_HEADERS)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp, coords, session_count, total_count])
    except Exception as e:
        if app_instance:
            app_instance.update_status_async(f"Error writing to log: {e}", is_error=True)


def clear_log_file():
    """Deletes the coordinate log CSV file."""
    try:
        if os.path.exists(LOG_FILENAME):
            os.remove(LOG_FILENAME)
            return True
    except Exception:
        pass
    return False

# ==========================================
# --- SYSTEM TRAY ---
# ==========================================

def create_tray_icon_image():
    """Loads the app icon for the system tray. Falls back to a generated icon if not found."""
    try:
        icon_path = "tpllicon.ico"
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, icon_path)
        elif getattr(sys, 'frozen', False):
            icon_path = os.path.join(os.path.dirname(sys.executable), icon_path)
        else:
            icon_path = os.path.join(os.path.dirname(__file__), icon_path)
        if os.path.exists(icon_path):
            return Image.open(icon_path)
    except Exception:
        pass
    # Fallback: generate a simple "T" icon
    img = Image.new('RGB', (64, 64), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    draw.rectangle([18, 10, 46, 18], fill=(0, 180, 80))
    draw.rectangle([27, 18, 37, 54], fill=(0, 180, 80))
    return img

# ==========================================
# --- CORE LOGIC & MACROS ---
# ==========================================

def simulate_key(key_str):
    """Uses Win32 API to simulate a precise hardware-level keypress."""
    vk_code = 0
    shift_needed = False

    if key_str.upper() in SPECIAL_VK_MAP:
        vk_code = SPECIAL_VK_MAP[key_str.upper()]
    elif len(key_str) == 1:
        scan_result = win32api.VkKeyScan(key_str)
        if scan_result != -1:
            vk_code = scan_result & 0xFF
            modifiers = scan_result >> 8
            shift_needed = (modifiers & 1) != 0
        else:
            try:
                vk_code = win32api.VkKeyScan(key_str.lower()) & 0xFF
                if vk_code == 0:
                    vk_code = ord(key_str.upper())
            except Exception:
                return False

    if vk_code == 0:
        return False

    try:
        if shift_needed:
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            time.sleep(VK_SLEEP / 2)
        win32api.keybd_event(vk_code, 0, 0, 0)
        time.sleep(VK_SLEEP)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        if shift_needed:
            time.sleep(VK_SLEEP / 2)
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False


def simulate_mouse_move(dx, dy):
    """Sends a relative mouse movement using ctypes SendInput."""
    try:
        INPUT_MOUSE = 0
        MOUSEEVENTF_MOVE = 0x0001

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT_UNION(ctypes.Union):
                _fields_ = [("mi", MOUSEINPUT)]
            _fields_ = [("type", ctypes.c_ulong), ("union", _INPUT_UNION)]

        mi = MOUSEINPUT(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(ctypes.c_ulong(0)))
        inp = INPUT(type=INPUT_MOUSE)
        inp.union.mi = mi
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        return True
    except Exception:
        return False


def simulate_right_click():
    """Simulates a right mouse button press and release."""
    try:
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        return True
    except Exception:
        return False


def play_success_beep():
    """Plays a short beep in a separate thread so it doesn't block the macro."""
    try:
        threading.Thread(
            target=winsound.Beep, args=(BEEP_FREQUENCY, BEEP_DURATION), daemon=True
        ).start()
    except Exception:
        pass


def perform_auto_place():
    """
    After a teleport, jumps, looks straight down, and right-clicks to place
    the block in the player's hand. Works in both fly mode and normal mode.
    """
    time.sleep(TELEPORT_SETTLE_WAIT)

    # Hold spacebar — must span at least 2 Minecraft game ticks (50ms each).
    # 100ms guarantees 2-tick overlap for reliable height gain.
    win32api.keybd_event(win32con.VK_SPACE, 0, 0, 0)
    time.sleep(0.10)
    win32api.keybd_event(win32con.VK_SPACE, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(JUMP_AIRBORNE_WAIT)

    # Snap camera straight down in smaller chunks across frames
    for _ in range(10):
        simulate_mouse_move(0, LOOK_DOWN_MOUSE_DELTA // 10)
        time.sleep(0.01)
    time.sleep(LOOK_DOWN_SETTLE_WAIT)

    simulate_right_click()


def validate_coordinates(text):
    """Returns True if the text looks like valid Google Earth Pro coordinates."""
    return bool(COORD_PATTERN.match(text.strip()))


def perform_tpll_action():
    """
    The main macro function. Captures coordinates from Google Earth
    (activating it if needed), forces Minecraft to the foreground,
    executes the /tpll command, and optionally auto-places a block.
    """
    global TOTAL_TPLL_COUNT
    start_time = time.time()
    if app_instance:
        app_instance.update_status_async("TPLL Action started...")

    try:
        user32 = ctypes.windll.user32

        # 1. VERIFY GOOGLE EARTH IS UNDER THE CURSOR
        cursor_pos = win32gui.GetCursorPos()
        hwnd_under_cursor = win32gui.WindowFromPoint(cursor_pos)
        if not hwnd_under_cursor:
            return

        hwnd_main_app = win32gui.GetAncestor(hwnd_under_cursor, win32con.GA_ROOTOWNER)
        if not hwnd_main_app:
            hwnd_main_app = hwnd_under_cursor

        window_title_under_mouse = win32gui.GetWindowText(hwnd_main_app)
        if GOOGLE_EARTH_TITLE not in window_title_under_mouse:
            return

        # 2. ACTIVATE GEP IF NEEDED
        current_foreground = user32.GetForegroundWindow()
        if hwnd_main_app != current_foreground:
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            user32.SetForegroundWindow(hwnd_main_app)
            time.sleep(GEP_ACTIVATE_WAIT)

        # 3. COPY COORDINATES
        pyperclip.copy("")
        time.sleep(PRE_COPY_WAIT)
        keyboard.press_and_release('ctrl+shift+c')
        time.sleep(COPY_WAIT)
        coords = pyperclip.paste().strip()

        if not coords:
            if app_instance:
                app_instance.update_status_async("Error: Clipboard empty after copy.", is_error=True)
            return

        # 4. VALIDATE COORDINATES
        if not validate_coordinates(coords):
            if app_instance:
                app_instance.update_status_async(
                    f"Error: Invalid coordinates copied: '{coords[:50]}'", is_error=True
                )
            return

        final_command = f"/tpll {coords}"

        # 5. FIND MINECRAFT WINDOW
        mc_hwnd = 0

        def enum_windows_callback(hwnd, _):
            nonlocal mc_hwnd
            if win32gui.IsWindowVisible(hwnd) and MINECRAFT_TITLE_KEYWORD in win32gui.GetWindowText(hwnd):
                mc_hwnd = hwnd

        win32gui.EnumWindows(enum_windows_callback, None)

        if mc_hwnd == 0:
            if app_instance:
                app_instance.update_status_async("Error: No Minecraft window found.", is_error=True)
            return

        # 6. FORCE MINECRAFT TO FOREGROUND
        try:
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            if user32.IsIconic(mc_hwnd):
                user32.ShowWindow(mc_hwnd, 9)
            user32.SetForegroundWindow(mc_hwnd)
            time.sleep(MC_ACTIVATE_WAIT)
        except Exception as e:
            if app_instance:
                app_instance.update_status_async(f"Error activating Minecraft: {e}", is_error=True)
            return

        # 7. EXECUTE MINECRAFT COMMAND
        keyboard.press_and_release('esc')
        time.sleep(ESC_WAIT)
        if not simulate_key(CHAT_KEY):
            if app_instance:
                app_instance.update_status_async("Error simulating chat key.", is_error=True)
            return

        time.sleep(CHAT_OPEN_WAIT)
        keyboard.write(final_command)
        time.sleep(PRE_ENTER_WAIT)
        keyboard.press_and_release('enter')

        # 8. UPDATE STATISTICS
        with _count_lock:
            TOTAL_TPLL_COUNT += 1
            current_total = TOTAL_TPLL_COUNT

        if app_instance:
            app_instance.session_tpll_count += 1
            session_count = app_instance.session_tpll_count
            app_instance.session_tpll_count_var.set(session_count)
            app_instance.total_tpll_count_var.set(current_total)
            app_instance.last_coords_var.set(coords)

            if current_total % AUTOSAVE_INTERVAL == 0:
                save_settings_to_file(app_instance.build_settings_dict())

            # 9. LOG COORDINATES
            if app_instance.coord_log_enabled_var.get():
                log_coordinates(coords, session_count, current_total)

        # 10. AUTO-PLACE BLOCK
        if app_instance and app_instance.auto_place_enabled_var.get():
            perform_auto_place()

        # 11. SUCCESS FEEDBACK
        if app_instance and app_instance.sound_enabled_var.get():
            play_success_beep()

        end_time = time.time()
        if app_instance:
            app_instance.update_status_async(f"Action complete. ({end_time - start_time:.3f}s)")

    except Exception as e:
        if app_instance:
            app_instance.update_status_async(f"Error in tpll action: {e}", is_error=True)


def tpll_hotkey_loop():
    """Background thread function that listens for the TPLL hotkey."""
    global app_instance, HOTKEY
    current_hotkey = HOTKEY
    try:
        keyboard.add_hotkey(current_hotkey, perform_tpll_action, trigger_on_release=False)
        if app_instance:
            app_instance.update_status_async(f"TPLL Hotkey '{current_hotkey}' is now ACTIVE.")

        while app_instance and app_instance.tpll_hotkey_should_run:
            time.sleep(0.1)
    except Exception as e:
        if app_instance:
            app_instance.after(0, lambda: app_instance.handle_listener_thread_stop(
                f"Hotkey error: {e}", is_error=True))
    finally:
        try:
            keyboard.remove_hotkey(current_hotkey)
        except Exception:
            pass
        if app_instance:
            app_instance.after(0, app_instance.handle_listener_thread_stop, "TPLL Hotkey INACTIVE.")


# ==========================================
# --- GRAPHICAL USER INTERFACE ---
# ==========================================

class TPLLHelperApp(tk.Tk):
    """Main Application Window Class using Tkinter."""

    def __init__(self):
        super().__init__()
        global app_instance, SHOW_WINDOW_ON_STARTUP, AUTO_PLACE_ENABLED
        global COORD_LOG_ENABLED, SOUND_ENABLED, TOTAL_TPLL_COUNT, TOTAL_SESSION_SECONDS
        app_instance = self

        self.title(f"TPLL Helper v{APP_VERSION}")

        # Load custom application icon
        try:
            icon_path = "tpllicon.ico"
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, icon_path)
            elif getattr(sys, 'frozen', False):
                icon_path = os.path.join(os.path.dirname(sys.executable), icon_path)
            else:
                icon_path = os.path.join(os.path.dirname(__file__), icon_path)
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self.initial_width = 480
        self.initial_height = 450
        self.geometry(f"{self.initial_width}x{self.initial_height}")
        self.resizable(False, False)

        # State Variables
        self.tpll_hotkey_should_run = False
        self.exit_hotkey_registered_token = None
        self.app_start_time = time.monotonic()
        self.tray_icon = None

        # UI Tracking Variables
        self.session_tpll_count = 0
        self.session_tpll_count_var = tk.IntVar(value=0)
        self.total_tpll_count_var = tk.IntVar(value=TOTAL_TPLL_COUNT)
        self.hotkey_var = tk.StringVar(value=HOTKEY)
        self.end_hotkey_var = tk.StringVar(value=END_HOTKEY)
        self.chat_key_var = tk.StringVar(value=CHAT_KEY)
        self.show_window_on_startup_var = tk.BooleanVar(value=SHOW_WINDOW_ON_STARTUP)
        self.auto_place_enabled_var = tk.BooleanVar(value=AUTO_PLACE_ENABLED)
        self.coord_log_enabled_var = tk.BooleanVar(value=COORD_LOG_ENABLED)
        self.sound_enabled_var = tk.BooleanVar(value=SOUND_ENABLED)
        self.uptime_var = tk.StringVar(value="00:00:00")
        self.total_time_var = tk.StringVar(value="00:00:00")
        self.status_var = tk.StringVar(value="Initializing...")
        self.last_coords_var = tk.StringVar(value="None yet")

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing_via_x_button)
        self.setup_global_exit_hotkey()

        if not SHOW_WINDOW_ON_STARTUP:
            self.after_idle(self.minimize_to_tray)

        self.after(200, self.start_tpll_hotkey_listener_ui)
        self.update_uptime_label()

    # --- System Tray ---

    def minimize_to_tray(self):
        """Hides the window and shows a system tray icon.
        If pystray is not available, falls back to taskbar minimize."""
        if not TRAY_AVAILABLE:
            self.iconify()
            self.update_status_async("Minimized to taskbar. Use exit hotkey to quit.")
            return

        self.withdraw()  # Hide from taskbar entirely

        if self.tray_icon is None:
            try:
                icon_image = create_tray_icon_image()
                menu = pystray.Menu(
                    pystray.MenuItem("Show Window", self._tray_show_window, default=True),
                    pystray.MenuItem("Exit", self._tray_exit)
                )
                self.tray_icon = pystray.Icon("TPLLHelper", icon_image, "TPLL Helper", menu)
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
            except Exception as e:
                self.deiconify()  # Show window again if tray fails

    def _tray_show_window(self, icon=None, item=None):
        """Restores the main window from the system tray."""
        self.after(0, self._restore_from_tray)

    def _restore_from_tray(self):
        """Called on the main thread to deiconify and bring window to front."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _tray_exit(self, icon=None, item=None):
        """Exit the app from the tray menu."""
        self.after(0, self.on_closing_via_x_button, True)

    def _stop_tray_icon(self):
        """Stops the system tray icon if it's running."""
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

    # --- Widget Construction ---

    def create_widgets(self):
        """Constructs the tabs, text, and buttons for the user interface."""
        container = ttk.Frame(self, padding="5")
        container.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(container)

        main_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_tab_frame, text='Main')
        self.populate_main_tab(main_tab_frame)

        settings_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_tab_frame, text='Settings')
        self.populate_settings_tab(settings_tab_frame)

        about_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(about_tab_frame, text='About')
        self.populate_about_tab(about_tab_frame)

        self.notebook.grid(row=0, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            container, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W, wraplength=450, padding=5
        )
        self.status_label.grid(row=1, column=0, sticky="ew", pady=(5, 0), padx=0)
        self._update_button_states()

    def populate_main_tab(self, parent_frame):
        """Builds the content of the Main tab."""
        parent_frame.columnconfigure(0, weight=1)

        instr_text = (
            "Instructions:\n"
            "1. Hover mouse over Google Earth Pro window.\n"
            "2. Press the TPLL Hotkey (see Settings tab).\n"
            "3. Coordinates are copied and sent to Minecraft.\n"
            "4. Press Exit Program Hotkey (see Settings) to close this app."
        )
        ttk.Label(parent_frame, text=instr_text, justify=tk.LEFT).grid(
            row=0, column=0, columnspan=2, pady=5, sticky="w"
        )

        stats_frame = ttk.LabelFrame(parent_frame, text="Statistics", padding="5")
        stats_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        stats_frame.columnconfigure(1, weight=1)

        ttk.Label(stats_frame, text="TPLLs this session:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.session_tpll_count_var).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(stats_frame, text="Total TPLLs (all time):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.total_tpll_count_var).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(stats_frame, text="Last coordinates:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.last_coords_var).grid(row=2, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(stats_frame, text="Session Uptime:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.uptime_var).grid(row=3, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(stats_frame, text="Total Time (all sessions):").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.total_time_var).grid(row=4, column=1, sticky="w", padx=5, pady=2)

        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        self.start_button = ttk.Button(button_frame, text="Start TPLL Hotkey", command=self.start_tpll_hotkey_listener_ui)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(button_frame, text="Stop TPLL Hotkey", command=self.stop_tpll_hotkey_listener_ui)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.auto_place_toggle_button = ttk.Button(
            button_frame, text="Auto-Place: OFF",
            command=self.toggle_auto_place_from_main
        )
        self.auto_place_toggle_button.pack(side=tk.LEFT, padx=5)
        self._update_auto_place_button_text()

    def populate_settings_tab(self, parent_frame):
        """Builds the content of the Settings tab."""
        parent_frame.columnconfigure(1, weight=1)

        help_text = "Select valid keys from the dropdown menus below."
        ttk.Label(parent_frame, text=help_text, font=("", 9, "italic")).grid(
            column=0, row=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )

        # Dropdowns
        ttk.Label(parent_frame, text="TPLL Hotkey (GEP Safe):").grid(column=0, row=1, sticky=tk.W, pady=5, padx=5)
        self.hotkey_entry = ttk.Combobox(
            parent_frame, textvariable=self.hotkey_var,
            values=TPLL_SAFE_KEYS, state="readonly", width=18
        )
        self.hotkey_entry.grid(column=1, row=1, sticky="ew", pady=5, padx=5)

        ttk.Label(parent_frame, text="Exit Program Hotkey:").grid(column=0, row=2, sticky=tk.W, pady=5, padx=5)
        self.end_hotkey_entry = ttk.Combobox(
            parent_frame, textvariable=self.end_hotkey_var,
            values=ALL_KEYS, state="readonly", width=18
        )
        self.end_hotkey_entry.grid(column=1, row=2, sticky="ew", pady=5, padx=5)

        ttk.Label(parent_frame, text="Minecraft Chat Key:").grid(column=0, row=3, sticky=tk.W, pady=5, padx=5)
        self.chat_key_entry = ttk.Combobox(
            parent_frame, textvariable=self.chat_key_var,
            values=ALL_KEYS, state="readonly", width=18
        )
        self.chat_key_entry.grid(column=1, row=3, sticky="ew", pady=5, padx=5)

        # Checkboxes
        self.show_window_check = ttk.Checkbutton(
            parent_frame, text="Show window on startup",
            variable=self.show_window_on_startup_var
        )
        self.show_window_check.grid(column=0, row=4, columnspan=2, sticky=tk.W, pady=(10, 2), padx=5)

        self.auto_place_check = ttk.Checkbutton(
            parent_frame, text="Enable Auto-Place by default",
            variable=self.auto_place_enabled_var
        )
        self.auto_place_check.grid(column=0, row=5, columnspan=2, sticky=tk.W, pady=2, padx=5)

        self.coord_log_check = ttk.Checkbutton(
            parent_frame, text="Log coordinates to CSV file",
            variable=self.coord_log_enabled_var
        )
        self.coord_log_check.grid(column=0, row=6, columnspan=2, sticky=tk.W, pady=2, padx=5)

        self.sound_check = ttk.Checkbutton(
            parent_frame, text="Play sound on successful TPLL",
            variable=self.sound_enabled_var
        )
        self.sound_check.grid(column=0, row=7, columnspan=2, sticky=tk.W, pady=(2, 10), padx=5)

        # Action Buttons
        btn_frame = ttk.Frame(parent_frame)
        btn_frame.grid(column=0, row=8, columnspan=2, pady=10)

        self.save_button = ttk.Button(btn_frame, text="Save All Settings", command=self.save_gui_settings)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.open_folder_button = ttk.Button(btn_frame, text="Open Settings Folder", command=self.open_settings_folder)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)

        self.clear_log_button = ttk.Button(btn_frame, text="Clear Log", command=self.clear_log_file_ui)
        self.clear_log_button.pack(side=tk.LEFT, padx=5)

    def populate_about_tab(self, parent_frame):
        """Builds the content of the About tab with selectable text and a clickable link."""
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.rowconfigure(0, weight=1)

        # Use a Text widget so all content is selectable/copyable
        about_box = tk.Text(
            parent_frame, wrap=tk.WORD, relief=tk.FLAT,
            background=self.cget('background'), borderwidth=0,
            font=("TkDefaultFont", 9), cursor="arrow",
            height=16, width=50
        )
        about_box.grid(row=0, column=0, pady=20, sticky="n")

        # Insert the text content
        about_box.insert(tk.END, f"TPLL Helper v{APP_VERSION}\n\n")
        about_box.insert(tk.END, "A tool for Build The Earth builders.\n")
        about_box.insert(tk.END, "Automates /tpll teleportation from Google Earth Pro\n")
        about_box.insert(tk.END, "coordinates directly into Minecraft.\n\n")

        about_box.insert(tk.END, "Note: Closing this window (X button) will minimize\n")
        about_box.insert(tk.END, "the app to your system tray \u2014 it will keep running\n")
        about_box.insert(tk.END, "in the background. To fully exit, use the Exit\n")
        about_box.insert(tk.END, "Program Hotkey or right-click the tray icon and\n")
        about_box.insert(tk.END, "select Exit.\n\n")

        # Insert GitHub link with a clickable tag
        about_box.insert(tk.END, "GitHub: ")
        link_start = about_box.index(tk.INSERT)
        about_box.insert(tk.END, GITHUB_URL)
        link_end = about_box.index(tk.INSERT)
        about_box.tag_add("link", link_start, link_end)
        about_box.insert(tk.END, "\n")

        about_box.insert(tk.END, f"Discord: {DISCORD_CONTACT}\n")
        about_box.insert(tk.END, f"Email: {EMAIL_CONTACT}\n")

        # Style the link: blue and underlined, hand cursor on hover
        about_box.tag_config("link", foreground="blue", underline=True)
        about_box.tag_bind("link", "<Button-1>", lambda e: webbrowser.open(GITHUB_URL))
        about_box.tag_bind("link", "<Enter>", lambda e: about_box.config(cursor="hand2"))
        about_box.tag_bind("link", "<Leave>", lambda e: about_box.config(cursor="arrow"))

        # Make read-only but still selectable
        about_box.config(state=tk.DISABLED)

    # --- UI Helpers ---

    def toggle_auto_place_from_main(self):
        """Quick toggle for Auto-Place from the Main tab button."""
        new_state = not self.auto_place_enabled_var.get()
        self.auto_place_enabled_var.set(new_state)
        self._update_auto_place_button_text()
        if new_state:
            self.update_status_async("Auto-Place ON \u2014 hold a block in your hand for it to work.")
        else:
            self.update_status_async("Auto-Place OFF.")

    def _update_auto_place_button_text(self):
        """Keeps the Main tab toggle button label in sync."""
        if self.auto_place_enabled_var.get():
            self.auto_place_toggle_button.config(text="Auto-Place: ON")
        else:
            self.auto_place_toggle_button.config(text="Auto-Place: OFF")

    def open_settings_folder(self):
        """Opens the AppData folder where the JSON and log are stored."""
        try:
            if os.path.exists(APP_SETTINGS_DIR):
                os.startfile(APP_SETTINGS_DIR)
                self.update_status_async("Opened settings folder.")
            else:
                self.update_status_async("Settings directory not found.", is_error=True)
        except Exception as e:
            self.update_status_async(f"Error opening folder: {e}", is_error=True)

    def clear_log_file_ui(self):
        """Clears the coordinate log CSV after confirmation."""
        if not os.path.exists(LOG_FILENAME):
            self.update_status_async("No log file to clear.")
            return
        if messagebox.askyesno("Clear Log", "Delete the coordinate log file? This cannot be undone."):
            if clear_log_file():
                self.update_status_async("Coordinate log cleared.")
            else:
                self.update_status_async("Error clearing log file.", is_error=True)

    def _update_button_states(self):
        """Enables/disables Start and Stop buttons."""
        if self.tpll_hotkey_should_run:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def update_status_async(self, message, is_error=False):
        """Thread-safe method to update the status bar text."""
        self.after(0, lambda: self.status_var.set(message))

    def build_settings_dict(self):
        """Builds the current settings dictionary from GUI state."""
        return {
            "HOTKEY": HOTKEY, "END_HOTKEY": END_HOTKEY, "CHAT_KEY": CHAT_KEY,
            "SHOW_WINDOW_ON_STARTUP": self.show_window_on_startup_var.get(),
            "AUTO_PLACE_ENABLED": self.auto_place_enabled_var.get(),
            "COORD_LOG_ENABLED": self.coord_log_enabled_var.get(),
            "SOUND_ENABLED": self.sound_enabled_var.get(),
            "TOTAL_TPLL_COUNT": TOTAL_TPLL_COUNT,
            "TOTAL_SESSION_SECONDS": TOTAL_SESSION_SECONDS + int(time.monotonic() - self.app_start_time)
        }

    # --- Settings Save ---

    def save_gui_settings(self):
        """Saves current GUI selections to variables and writes to the JSON file."""
        global HOTKEY, END_HOTKEY, CHAT_KEY, SHOW_WINDOW_ON_STARTUP
        global AUTO_PLACE_ENABLED, COORD_LOG_ENABLED, SOUND_ENABLED, TOTAL_TPLL_COUNT
        new_tpll_hotkey = self.hotkey_var.get().strip()
        new_exit_hotkey = self.end_hotkey_var.get().strip()
        new_chat_key = self.chat_key_var.get().strip()

        if not all([new_tpll_hotkey, new_exit_hotkey, new_chat_key]):
            messagebox.showerror("Input Error", "All hotkey fields must be filled.")
            return

        # Duplicate hotkey check
        hotkeys = [new_tpll_hotkey, new_exit_hotkey, new_chat_key]
        if len(hotkeys) != len(set(hotkeys)):
            messagebox.showwarning(
                "Duplicate Hotkey",
                "Two or more hotkeys are set to the same key. This will cause conflicts.\n"
                "Please choose unique keys for each setting."
            )
            return

        tpll_hotkey_changed = (new_tpll_hotkey != HOTKEY)
        exit_hotkey_changed = (new_exit_hotkey != END_HOTKEY)

        HOTKEY = new_tpll_hotkey
        END_HOTKEY = new_exit_hotkey
        CHAT_KEY = new_chat_key
        SHOW_WINDOW_ON_STARTUP = self.show_window_on_startup_var.get()
        AUTO_PLACE_ENABLED = self.auto_place_enabled_var.get()
        COORD_LOG_ENABLED = self.coord_log_enabled_var.get()
        SOUND_ENABLED = self.sound_enabled_var.get()

        if save_settings_to_file(self.build_settings_dict()):
            self.update_status_async("Settings saved.")
            if self.tpll_hotkey_should_run and tpll_hotkey_changed:
                self.update_status_async("TPLL Hotkey changed. Stop/Start for changes to apply.", is_error=True)
            if exit_hotkey_changed:
                self.update_status_async("Exit Hotkey changed. Re-registering...", is_error=True)
                self.setup_global_exit_hotkey()
        else:
            self.update_status_async("Error saving settings.", is_error=True)

    # --- Hotkey Listener ---

    def start_tpll_hotkey_listener_ui(self):
        """Spawns the background thread to listen for the TPLL hotkey."""
        global tpll_hotkey_listener_thread, HOTKEY
        if self.tpll_hotkey_should_run or (tpll_hotkey_listener_thread and tpll_hotkey_listener_thread.is_alive()):
            return

        HOTKEY = self.hotkey_var.get().strip()
        try:
            self.tpll_hotkey_should_run = True
            self._update_button_states()
            tpll_hotkey_listener_thread = threading.Thread(target=tpll_hotkey_loop, daemon=True)
            tpll_hotkey_listener_thread.start()
        except Exception as e:
            self.tpll_hotkey_should_run = False
            self._update_button_states()
            self.update_status_async(f"Error starting TPLL hotkey: {e}", is_error=True)

    def stop_tpll_hotkey_listener_ui(self):
        """Signals the background listener thread to stop."""
        global tpll_hotkey_listener_thread
        if not self.tpll_hotkey_should_run:
            return

        self.update_status_async("Stopping TPLL Hotkey...")
        self.tpll_hotkey_should_run = False

        if tpll_hotkey_listener_thread and tpll_hotkey_listener_thread.is_alive():
            tpll_hotkey_listener_thread.join(timeout=1.0)
            if tpll_hotkey_listener_thread.is_alive():
                try:
                    keyboard.remove_hotkey(HOTKEY)
                except Exception:
                    pass
            tpll_hotkey_listener_thread = None

        self.handle_listener_thread_stop("TPLL Hotkey stopped via UI button.")

    def handle_listener_thread_stop(self, status_message, is_error=False):
        """Called when the listener thread stops."""
        global tpll_hotkey_listener_thread
        self.tpll_hotkey_should_run = False
        if tpll_hotkey_listener_thread and not tpll_hotkey_listener_thread.is_alive():
            tpll_hotkey_listener_thread = None
        self.update_status_async(status_message, is_error=is_error)
        self._update_button_states()
        if is_error and "Invalid hotkey string" not in status_message:
            messagebox.showerror("TPLL Hotkey Listener Error", status_message)

    def setup_global_exit_hotkey(self):
        """Registers the 'Kill Switch' exit hotkey."""
        global END_HOTKEY
        try:
            if hasattr(self, 'exit_hotkey_registered_token') and self.exit_hotkey_registered_token:
                try:
                    keyboard.remove_hotkey(self.exit_hotkey_registered_token)
                except Exception:
                    pass
            self.exit_hotkey_registered_token = keyboard.add_hotkey(
                END_HOTKEY, self.program_exit_handler,
                trigger_on_release=False, suppress=True
            )
        except Exception as e:
            self.update_status_async(f"Error registering Exit Hotkey: {e}", is_error=True)

    def program_exit_handler(self):
        """Called from the exit hotkey."""
        self.after(0, self.on_closing_via_x_button, True)

    def on_closing_via_x_button(self, force_quit_by_hotkey=False):
        """Handles window close (X button) or exit hotkey press.
        X button minimizes to tray so the hotkey keeps running.
        Exit hotkey or tray menu 'Exit' actually closes the app."""
        if force_quit_by_hotkey:
            self._final_app_destroy()
        else:
            # X button minimizes to tray instead of quitting
            self.minimize_to_tray()

    def _final_app_destroy(self):
        """Cleans up threads, saves final state, and safely closes the application."""
        global tpll_hotkey_listener_thread, TOTAL_TPLL_COUNT, TOTAL_SESSION_SECONDS
        # Accumulate this session's runtime into the total
        TOTAL_SESSION_SECONDS += int(time.monotonic() - self.app_start_time)
        save_settings_to_file(self.build_settings_dict())
        self.tpll_hotkey_should_run = False
        if tpll_hotkey_listener_thread and tpll_hotkey_listener_thread.is_alive():
            tpll_hotkey_listener_thread.join(timeout=0.3)
        if hasattr(self, 'exit_hotkey_registered_token') and self.exit_hotkey_registered_token:
            try:
                keyboard.remove_hotkey(self.exit_hotkey_registered_token)
            except Exception:
                pass
        self._stop_tray_icon()
        self.destroy()

    def update_uptime_label(self):
        """Runs every second to update uptime and total time displays."""
        # Session uptime
        session_seconds = int(time.monotonic() - self.app_start_time)
        hours, remainder = divmod(session_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.uptime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Total cumulative time (previous sessions + current session)
        total_seconds = TOTAL_SESSION_SECONDS + session_seconds
        t_hours, t_remainder = divmod(total_seconds, 3600)
        t_minutes, t_seconds = divmod(t_remainder, 60)
        self.total_time_var.set(f"{t_hours:02d}:{t_minutes:02d}:{t_seconds:02d}")

        self.after(1000, self.update_uptime_label)


if __name__ == "__main__":
    main_app = TPLLHelperApp()
    try:
        main_app.mainloop()
    except KeyboardInterrupt:
        if app_instance:
            app_instance.on_closing_via_x_button(force_quit_by_hotkey=True)
    finally:
        keyboard.unhook_all()
