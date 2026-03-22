"""
TPLL Helper for Minecraft (Version 2.1)
Automates teleporting to real-world coordinates from Google Earth Pro into Minecraft.
"""

import time
import sys
import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import ctypes

import keyboard
import pyperclip
import pygetwindow as gw

try:
    import win32api
    import win32con
    import win32gui
    import pywintypes
except ImportError:
    print("ERROR: PyWin32 library not found. Please install it:\npip install pywin32")
    sys.exit()

# ==========================================
# --- CONFIGURATION & CONSTANTS ---
# ==========================================

APP_NAME_FOR_DATA_FOLDER = "TPLLHelper" 

# Setup AppData Settings Directory
try:
    local_app_data_path = os.path.expandvars('%LOCALAPPDATA%')
    APP_SETTINGS_DIR = os.path.join(local_app_data_path, APP_NAME_FOR_DATA_FOLDER)
    os.makedirs(APP_SETTINGS_DIR, exist_ok=True) 
    SETTINGS_FILENAME = os.path.join(APP_SETTINGS_DIR, "tpllhelper_settings.json")
except Exception as e:
    APP_SETTINGS_DIR = os.getcwd() # Fallback to current directory
    SETTINGS_FILENAME = "tpllhelper_settings.json" 

DEFAULT_CONFIG_SETTINGS = {
    "HOTKEY": '`',
    "END_HOTKEY": 'f12',
    "CHAT_KEY": '/',
    "SHOW_WINDOW_ON_STARTUP": True,
    "TOTAL_TPLL_COUNT": 0
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

# ==========================================
# --- KEYBINDING LISTS ---
# ==========================================

# Keys safe to use in Google Earth Pro without triggering default actions
TPLL_SAFE_KEYS = [
    '`', '\\', '[', ']', 
    'f1', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f12',
    'b', 'c', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'q', 't', 'v', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'esc', 'insert', 'home', 'end', 'tab'
]

# All available keys for standard bindings (Minecraft Chat and Exit hotkeys)
ALL_KEYS = [
    '`', '/', '\\', '-', '=', '[', ']', 
    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'enter', 'esc', 'insert', 'delete', 'home', 'end', 'pageup', 'pagedown', 'tab'
]

SPECIAL_VK_MAP = {
    'F1': win32con.VK_F1, 'F2': win32con.VK_F2, 'F3': win32con.VK_F3,
    'F10': win32con.VK_F10, 'F11': win32con.VK_F11, 'F12': win32con.VK_F12,
    'ENTER': win32con.VK_RETURN, 'ESC': win32con.VK_ESCAPE,
    'INS': win32con.VK_INSERT, 'DEL': win32con.VK_DELETE,
    'HOME': win32con.VK_HOME, 'END': win32con.VK_END,
    'PGUP': win32con.VK_PRIOR, 'PGDN': win32con.VK_NEXT,
    'UP': win32con.VK_UP, 'DOWN': win32con.VK_DOWN,
    'LEFT': win32con.VK_LEFT, 'RIGHT': win32con.VK_RIGHT, 'TAB': win32con.VK_TAB,
}

# Global Variables
tpll_hotkey_listener_thread = None
app_instance = None 

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
        if app_instance: app_instance.update_status_async(f"Error saving settings: {e}", is_error=True)
    return False

def load_or_create_settings():
    """Loads settings from JSON, or creates a new one with defaults if none exists."""
    global HOTKEY, END_HOTKEY, CHAT_KEY, SHOW_WINDOW_ON_STARTUP, TOTAL_TPLL_COUNT
    effective_settings = DEFAULT_CONFIG_SETTINGS.copy()
    
    try:
        if os.path.exists(SETTINGS_FILENAME):
            with open(SETTINGS_FILENAME, 'r') as f:
                loaded_from_file = json.load(f)
            # Validate loaded keys
            for key, default_value in DEFAULT_CONFIG_SETTINGS.items():
                if key in loaded_from_file and isinstance(loaded_from_file[key], type(default_value)):
                    effective_settings[key] = loaded_from_file[key]
        else:
            save_settings_to_file(effective_settings)
    except Exception:
        pass # Fallback to defaults on any catastrophic read error
    
    HOTKEY = effective_settings["HOTKEY"]
    END_HOTKEY = effective_settings["END_HOTKEY"]
    CHAT_KEY = effective_settings["CHAT_KEY"]
    SHOW_WINDOW_ON_STARTUP = effective_settings["SHOW_WINDOW_ON_STARTUP"]
    TOTAL_TPLL_COUNT = int(effective_settings.get("TOTAL_TPLL_COUNT", 0))

load_or_create_settings() 

# ==========================================
# --- CORE LOGIC & MACROS ---
# ==========================================

def simulate_key(key_str):
    """Uses Win32 API to simulate a precise hardware-level keypress."""
    vk_code = 0
    if key_str.upper() in SPECIAL_VK_MAP: 
        vk_code = SPECIAL_VK_MAP[key_str.upper()]
    elif len(key_str) == 1:
        scan_result = win32api.VkKeyScan(key_str)
        if scan_result != -1: vk_code = scan_result & 0xFF

    if vk_code == 0: return False

    try:
        win32api.keybd_event(vk_code, 0, 0, 0)
        time.sleep(VK_SLEEP)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False

def perform_tpll_action():
    """
    The main macro function. Captures coordinates from Google Earth, 
    forces Minecraft to the foreground, and executes the /tpll command.
    """
    global TOTAL_TPLL_COUNT
    start_time = time.time()
    
    if app_instance: app_instance.update_status_async("TPLL Action started...")
    
    try:
        user32 = ctypes.windll.user32 

        # 1. VERIFY GOOGLE EARTH IS ACTIVE
        cursor_pos = win32gui.GetCursorPos()
        hwnd_under_cursor = win32gui.WindowFromPoint(cursor_pos)
        if not hwnd_under_cursor: return
        
        hwnd_main_app = win32gui.GetAncestor(hwnd_under_cursor, win32con.GA_ROOTOWNER)
        if not hwnd_main_app: hwnd_main_app = hwnd_under_cursor
        
        window_title_under_mouse = win32gui.GetWindowText(hwnd_main_app)
        if GOOGLE_EARTH_TITLE not in window_title_under_mouse: return
        
        # 2. COPY COORDINATES
        pyperclip.copy("") 
        time.sleep(PRE_COPY_WAIT)
        keyboard.press_and_release('ctrl+shift+c')
        time.sleep(COPY_WAIT)
        coords = pyperclip.paste().strip()
        
        if not coords:
            if app_instance: app_instance.update_status_async("Error: Clipboard empty.", is_error=True)
            return
            
        final_command = f"/tpll {coords}"
        
        # 3. FIND MINECRAFT WINDOW NATIVELY
        mc_hwnd = 0
        def enum_windows_callback(hwnd, _):
            nonlocal mc_hwnd
            if win32gui.IsWindowVisible(hwnd) and MINECRAFT_TITLE_KEYWORD in win32gui.GetWindowText(hwnd):
                mc_hwnd = hwnd
                
        win32gui.EnumWindows(enum_windows_callback, None)
        
        if mc_hwnd == 0:
            if app_instance: app_instance.update_status_async(f"Error: No Minecraft window found.", is_error=True)
            return
            
        # 4. FORCE MINECRAFT TO FOREGROUND
        try:
            # Tap ALT to bypass the strict Windows 10/11 focus-stealing block
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0) 
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0) 
            
            # SW_RESTORE (9) brings the window out of minimization
            if user32.IsIconic(mc_hwnd):
                user32.ShowWindow(mc_hwnd, 9)
                
            user32.SetForegroundWindow(mc_hwnd)
            time.sleep(MC_ACTIVATE_WAIT)
        except Exception as e: 
            if app_instance: app_instance.update_status_async(f"Error activating Minecraft: {e}", is_error=True)
            return
            
        # 5. EXECUTE MINECRAFT COMMAND
        keyboard.press_and_release('esc') # Clear active menus
        time.sleep(ESC_WAIT)
        if not simulate_key(CHAT_KEY):
            if app_instance: app_instance.update_status_async(f"Error simulating chat key.", is_error=True)
            return
            
        time.sleep(CHAT_OPEN_WAIT)
        keyboard.write(final_command)
        time.sleep(PRE_ENTER_WAIT)
        keyboard.press_and_release('enter')
        
        # 6. UPDATE STATISTICS
        if app_instance:
            app_instance.session_tpll_count += 1
            app_instance.session_tpll_count_var.set(app_instance.session_tpll_count)
            TOTAL_TPLL_COUNT += 1
            app_instance.total_tpll_count_var.set(TOTAL_TPLL_COUNT)
            
        end_time = time.time()
        if app_instance: app_instance.update_status_async(f"Action complete. (Total: {end_time - start_time:.3f}s)")
        
    except Exception as e:
        if app_instance: app_instance.update_status_async(f"Error in tpll action: {e}", is_error=True)

def tpll_hotkey_loop():
    """Background thread function that listens for the TPLL hotkey."""
    global app_instance, HOTKEY
    try:
        keyboard.add_hotkey(HOTKEY, perform_tpll_action, trigger_on_release=False)
        if app_instance: app_instance.update_status_async(f"TPLL Hotkey '{HOTKEY}' is now ACTIVE.")
        
        while app_instance and app_instance.tpll_hotkey_should_run:
            time.sleep(0.1)
    except Exception as e: 
        if app_instance: app_instance.after(0, lambda: app_instance.handle_listener_thread_stop(f"Hotkey error: {e}", is_error=True))
    finally:
        try:
            keyboard.remove_hotkey(HOTKEY) 
        except: pass
        if app_instance:
            app_instance.after(0, app_instance.handle_listener_thread_stop, "TPLL Hotkey INACTIVE.")

# ==========================================
# --- GRAPHICAL USER INTERFACE ---
# ==========================================

class TPLLHelperApp(tk.Tk):
    """Main Application Window Class using Tkinter."""
    def __init__(self):
        super().__init__()
        global app_instance, SHOW_WINDOW_ON_STARTUP, TOTAL_TPLL_COUNT
        app_instance = self 
        
        self.title("TPLL Helper")
        
        # Load custom application icon
        try:
            icon_path = "tpll_helper_icon.ico" 
            if hasattr(sys, '_MEIPASS'): icon_path = os.path.join(sys._MEIPASS, icon_path)
            elif getattr(sys, 'frozen', False): icon_path = os.path.join(os.path.dirname(sys.executable), icon_path)
            else: icon_path = os.path.join(os.path.dirname(__file__), icon_path)
            if os.path.exists(icon_path): self.iconbitmap(icon_path)
        except: pass
            
        self.initial_width = 480
        self.initial_height = 360  
        self.geometry(f"{self.initial_width}x{self.initial_height}") 
        self.resizable(False, False) 

        # State Variables
        self.tpll_hotkey_should_run = False 
        self.exit_hotkey_registered_token = None 
        self.app_start_time = time.monotonic()
        
        # UI Tracking Variables
        self.session_tpll_count = 0
        self.session_tpll_count_var = tk.IntVar(value=0)
        self.total_tpll_count_var = tk.IntVar(value=TOTAL_TPLL_COUNT)
        self.hotkey_var = tk.StringVar(value=HOTKEY)
        self.end_hotkey_var = tk.StringVar(value=END_HOTKEY) 
        self.chat_key_var = tk.StringVar(value=CHAT_KEY)
        self.show_window_on_startup_var = tk.BooleanVar(value=SHOW_WINDOW_ON_STARTUP)
        self.uptime_var = tk.StringVar(value="00:00:00")
        self.status_var = tk.StringVar(value="Initializing...")
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing_via_x_button)
        self.setup_global_exit_hotkey() 
        
        if not SHOW_WINDOW_ON_STARTUP:
            self.after_idle(self.iconify_window) 
            
        self.after(200, self.start_tpll_hotkey_listener_ui)
        self.update_uptime_label() 

    def iconify_window(self):
        """Minimizes the window to the taskbar."""
        self.iconify()

    def create_widgets(self):
        """Constructs the tabs, text, and buttons for the user interface."""
        container = ttk.Frame(self, padding="5")
        container.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1); self.rowconfigure(0, weight=1)
        self.notebook = ttk.Notebook(container)
        
        # Build Main Tab
        main_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_tab_frame, text='Main')
        self.populate_main_tab(main_tab_frame)
        
        # Build Settings Tab
        settings_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_tab_frame, text='Settings')
        self.populate_settings_tab(settings_tab_frame)
        
        self.notebook.grid(row=0, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1); container.columnconfigure(0, weight=1)
        
        # Status Bar
        self.status_label = ttk.Label(container, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, wraplength=450, padding=5)
        self.status_label.grid(row=1, column=0, sticky="ew", pady=(5,0), padx=0)
        self._update_button_states()

    def populate_main_tab(self, parent_frame):
        parent_frame.columnconfigure(0, weight=1) 
        instr_text = ("Instructions:\n"
                      "1. Hover mouse over Google Earth Pro window.\n"
                      "2. Press the TPLL Hotkey (see Settings tab).\n"
                      "3. Coordinates are copied and sent to Minecraft.\n"
                      f"4. Press Exit Program Hotkey (see Settings) to close this app.")
        ttk.Label(parent_frame, text=instr_text, justify=tk.LEFT).grid(row=0, column=0, columnspan=2, pady=5, sticky="w")
        
        # Statistics Box
        stats_frame = ttk.LabelFrame(parent_frame, text="Statistics", padding="5")
        stats_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        stats_frame.columnconfigure(1, weight=1)
        ttk.Label(stats_frame, text="TPLLs this session:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.session_tpll_count_var).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, text="Total TPLLs (all time):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.total_tpll_count_var).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, text="Program Uptime:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.uptime_var).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Start/Stop Buttons
        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10) 
        self.start_button = ttk.Button(button_frame, text="Start TPLL Hotkey", command=self.start_tpll_hotkey_listener_ui)
        self.start_button.pack(side=tk.LEFT, padx=5) 
        self.stop_button = ttk.Button(button_frame, text="Stop TPLL Hotkey", command=self.stop_tpll_hotkey_listener_ui)
        self.stop_button.pack(side=tk.LEFT, padx=5) 

    def populate_settings_tab(self, parent_frame):
        parent_frame.columnconfigure(1, weight=1)
        
        help_text = "Select valid keys from the dropdown menus below."
        ttk.Label(parent_frame, text=help_text, font=("", 9, "italic")).grid(column=0, row=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # Dropdowns
        ttk.Label(parent_frame, text="TPLL Hotkey (GEP Safe):").grid(column=0, row=1, sticky=tk.W, pady=5, padx=5)
        self.hotkey_entry = ttk.Combobox(parent_frame, textvariable=self.hotkey_var, values=TPLL_SAFE_KEYS, state="readonly", width=18)
        self.hotkey_entry.grid(column=1, row=1, sticky="ew", pady=5, padx=5)
        
        ttk.Label(parent_frame, text="Exit Program Hotkey:").grid(column=0, row=2, sticky=tk.W, pady=5, padx=5)
        self.end_hotkey_entry = ttk.Combobox(parent_frame, textvariable=self.end_hotkey_var, values=ALL_KEYS, state="readonly", width=18)
        self.end_hotkey_entry.grid(column=1, row=2, sticky="ew", pady=5, padx=5)
        
        ttk.Label(parent_frame, text="Minecraft Chat Key:").grid(column=0, row=3, sticky=tk.W, pady=5, padx=5)
        self.chat_key_entry = ttk.Combobox(parent_frame, textvariable=self.chat_key_var, values=ALL_KEYS, state="readonly", width=18)
        self.chat_key_entry.grid(column=1, row=3, sticky="ew", pady=5, padx=5)
        
        self.show_window_check = ttk.Checkbutton(parent_frame, text="Show window on startup", variable=self.show_window_on_startup_var)
        self.show_window_check.grid(column=0, row=4, columnspan=2, sticky=tk.W, pady=10, padx=5)
        
        # Action Buttons
        btn_frame = ttk.Frame(parent_frame)
        btn_frame.grid(column=0, row=5, columnspan=2, pady=10)
        
        self.save_button = ttk.Button(btn_frame, text="Save All Settings", command=self.save_gui_settings)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.open_folder_button = ttk.Button(btn_frame, text="Open Settings Folder", command=self.open_settings_folder)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
    def open_settings_folder(self):
        """Opens the hidden Windows AppData folder where the JSON is stored."""
        try:
            if os.path.exists(APP_SETTINGS_DIR):
                os.startfile(APP_SETTINGS_DIR)
                self.update_status_async("Opened settings folder.")
            else:
                self.update_status_async("Settings directory not found.", is_error=True)
        except Exception as e:
             self.update_status_async(f"Error opening folder: {e}", is_error=True)

    def _update_button_states(self):
        if self.tpll_hotkey_should_run:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def update_status_async(self, message, is_error=False):
        self.after(0, lambda: self.status_var.set(message))

    def save_gui_settings(self):
        """Saves current GUI selections to variables and writes to the JSON file."""
        global HOTKEY, END_HOTKEY, CHAT_KEY, SHOW_WINDOW_ON_STARTUP, TOTAL_TPLL_COUNT
        new_tpll_hotkey = self.hotkey_var.get().strip()
        new_exit_hotkey = self.end_hotkey_var.get().strip()
        new_chat_key = self.chat_key_var.get().strip()
        new_show_window = self.show_window_on_startup_var.get()
        
        if not all([new_tpll_hotkey, new_exit_hotkey, new_chat_key]):
            messagebox.showerror("Input Error", "All hotkey fields must be filled.")
            return
            
        tpll_hotkey_changed = (new_tpll_hotkey != HOTKEY)
        exit_hotkey_changed = (new_exit_hotkey != END_HOTKEY)
        
        HOTKEY = new_tpll_hotkey 
        END_HOTKEY = new_exit_hotkey 
        CHAT_KEY = new_chat_key 
        SHOW_WINDOW_ON_STARTUP = new_show_window
        
        settings_data = {
            "HOTKEY": HOTKEY, "END_HOTKEY": END_HOTKEY, "CHAT_KEY": CHAT_KEY,
            "SHOW_WINDOW_ON_STARTUP": SHOW_WINDOW_ON_STARTUP,
            "TOTAL_TPLL_COUNT": TOTAL_TPLL_COUNT 
        }
        
        if save_settings_to_file(settings_data):
            self.update_status_async("Settings saved.")
            if self.tpll_hotkey_should_run and tpll_hotkey_changed:
                 self.update_status_async("TPLL Hotkey changed. Stop/Start for changes to apply.", is_error=True)
            if exit_hotkey_changed:
                self.update_status_async("Exit Hotkey changed. Re-registering...", is_error=True)
                self.setup_global_exit_hotkey() 
        else: 
            self.update_status_async("Error saving settings.", is_error=True)

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
        if not self.tpll_hotkey_should_run: return
        
        self.update_status_async("Stopping TPLL Hotkey...")
        self.tpll_hotkey_should_run = False 
        
        if tpll_hotkey_listener_thread and tpll_hotkey_listener_thread.is_alive():
            tpll_hotkey_listener_thread.join(timeout=1.0) 
            if tpll_hotkey_listener_thread.is_alive():
                try: keyboard.remove_hotkey(HOTKEY) 
                except: pass
            tpll_hotkey_listener_thread = None
            
        self.handle_listener_thread_stop("TPLL Hotkey stopped via UI button.")

    def handle_listener_thread_stop(self, status_message, is_error=False):
        global tpll_hotkey_listener_thread 
        self.tpll_hotkey_should_run = False 
        if tpll_hotkey_listener_thread and not tpll_hotkey_listener_thread.is_alive():
            tpll_hotkey_listener_thread = None 
        self.update_status_async(status_message, is_error=is_error)
        self._update_button_states() 
        if is_error and not ("Invalid hotkey string" in status_message):
             messagebox.showerror("TPLL Hotkey Listener Error", status_message)

    def setup_global_exit_hotkey(self):
        """Registers the 'Kill Switch' exit hotkey."""
        global END_HOTKEY 
        try:
            if hasattr(self, 'exit_hotkey_registered_token') and self.exit_hotkey_registered_token:
                try: keyboard.remove_hotkey(self.exit_hotkey_registered_token)
                except Exception: pass
            self.exit_hotkey_registered_token = keyboard.add_hotkey(END_HOTKEY, self.program_exit_handler, trigger_on_release=False, suppress=True)
        except Exception as e:
            self.update_status_async(f"Error registering Exit Hotkey: {e}", is_error=True)
            
    def program_exit_handler(self): 
        self.after(0, self.on_closing_via_x_button, True)

    def on_closing_via_x_button(self, force_quit_by_hotkey=False): 
        if self.tpll_hotkey_should_run and not force_quit_by_hotkey:
            if messagebox.askyesno("Exit Confirmation", "TPLL Hotkey is active. Stop it and exit?"):
                self.update_status_async("Exit requested. Stopping TPLL Hotkey...")
                self.stop_tpll_hotkey_listener_ui() 
                self.after(300, self._final_app_destroy) 
        else: 
            self._final_app_destroy()

    def _final_app_destroy(self):
        """Cleans up threads and safely closes the application."""
        global tpll_hotkey_listener_thread, TOTAL_TPLL_COUNT
        save_settings_to_file({
            "HOTKEY": HOTKEY, "END_HOTKEY": END_HOTKEY, "CHAT_KEY": CHAT_KEY,
            "SHOW_WINDOW_ON_STARTUP": SHOW_WINDOW_ON_STARTUP, "TOTAL_TPLL_COUNT": TOTAL_TPLL_COUNT
        })
        self.tpll_hotkey_should_run = False
        if tpll_hotkey_listener_thread and tpll_hotkey_listener_thread.is_alive():
            tpll_hotkey_listener_thread.join(timeout=0.3) 
        if hasattr(self, 'exit_hotkey_registered_token') and self.exit_hotkey_registered_token:
            try: keyboard.remove_hotkey(self.exit_hotkey_registered_token)
            except Exception: pass
        self.destroy()

    def update_uptime_label(self):
        """Runs every second to update the uptime clock on the UI."""
        diff_seconds = int(time.monotonic() - self.app_start_time)
        hours, remainder = divmod(diff_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.uptime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
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
