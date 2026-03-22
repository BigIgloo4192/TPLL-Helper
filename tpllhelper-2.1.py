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
    print("ERROR: PyWin32 library not found. Please install it:\n"
          "pip install pywin32  OR  py -m pip install pywin32")
    sys.exit()

# --- Settings File Configuration ---
APP_NAME_FOR_DATA_FOLDER = "TPLLHelper" 

try:
    local_app_data_path = os.path.expandvars('%LOCALAPPDATA%')
    if not os.path.isdir(local_app_data_path):
        print(f"Warning: %LOCALAPPDATA% path ('{local_app_data_path}') not found or is not a directory.")
        raise OSError("%LOCALAPPDATA% path not valid.")

    APP_SETTINGS_DIR = os.path.join(local_app_data_path, APP_NAME_FOR_DATA_FOLDER)
    os.makedirs(APP_SETTINGS_DIR, exist_ok=True) 
    SETTINGS_FILENAME = os.path.join(APP_SETTINGS_DIR, "tpllhelper_settings.json")
    print(f"INFO: Settings file location: {SETTINGS_FILENAME}")
except Exception as e:
    print(f"WARNING: Could not set up settings directory in AppData (Error: {e}).")
    print("Settings file will be created in the script/EXE's current directory instead.")
    APP_SETTINGS_DIR = os.getcwd() # Fallback for the open folder button
    SETTINGS_FILENAME = "tpllhelper_settings.json" 

DEFAULT_CONFIG_SETTINGS = {
    "HOTKEY": '`',
    "END_HOTKEY": 'f12',
    "CHAT_KEY": '/',
    "SHOW_WINDOW_ON_STARTUP": True,
    "TOTAL_TPLL_COUNT": 0
}

HOTKEY = DEFAULT_CONFIG_SETTINGS["HOTKEY"]
END_HOTKEY = DEFAULT_CONFIG_SETTINGS["END_HOTKEY"]
CHAT_KEY = DEFAULT_CONFIG_SETTINGS["CHAT_KEY"]
SHOW_WINDOW_ON_STARTUP = DEFAULT_CONFIG_SETTINGS["SHOW_WINDOW_ON_STARTUP"]
TOTAL_TPLL_COUNT = DEFAULT_CONFIG_SETTINGS["TOTAL_TPLL_COUNT"]

MINECRAFT_TITLE_KEYWORD = "Minecraft"
GOOGLE_EARTH_TITLE = "Google Earth Pro"

GEP_ACTIVATE_WAIT = 0.02
COPY_WAIT = 0.03
MC_ACTIVATE_WAIT = 0.08
ESC_WAIT = 0.05
CHAT_OPEN_WAIT = 0.03
PRE_COPY_WAIT = 0.03
VK_SLEEP = 0.05
PRE_ENTER_WAIT = 0.03

# --- Valid Keys for Dropdown Menus ---
# Keys safe to use in Google Earth Pro without triggering default actions
TPLL_SAFE_KEYS = [
    '`', '\\', '[', ']', 
    'f1', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f12',
    'b', 'c', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'q', 't', 'v', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'esc', 'insert', 'home', 'end', 'tab'
]

# All keys (for Minecraft Chat and Exit hotkeys)
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
    'ENTER': win32con.VK_RETURN, 'ESC': win32con.VK_ESCAPE,'ESCAPE': win32con.VK_ESCAPE,
    'INS': win32con.VK_INSERT,'INSERT': win32con.VK_INSERT, 'DEL': win32con.VK_DELETE,
    'DELETE': win32con.VK_DELETE, 'HOME': win32con.VK_HOME, 'END': win32con.VK_END,
    'PGUP': win32con.VK_PRIOR, 'PAGEUP': win32con.VK_PRIOR,'PGDN': win32con.VK_NEXT,
    'PAGEDOWN': win32con.VK_NEXT, 'UP': win32con.VK_UP, 'DOWN': win32con.VK_DOWN,
    'LEFT': win32con.VK_LEFT, 'RIGHT': win32con.VK_RIGHT,'TAB': win32con.VK_TAB,
}

tpll_hotkey_listener_thread = None
app_instance = None 

def save_settings_to_file(settings_data):
    global TOTAL_TPLL_COUNT
    try:
        settings_to_save = settings_data.copy()
        settings_to_save["TOTAL_TPLL_COUNT"] = TOTAL_TPLL_COUNT
        with open(SETTINGS_FILENAME, 'w') as f:
            json.dump(settings_to_save, f, indent=4)
        print(f"Settings (including total TPLLs: {TOTAL_TPLL_COUNT}) saved to {SETTINGS_FILENAME}")
        return True
    except Exception as e:
        error_message = f"Error saving settings to '{SETTINGS_FILENAME}': {e}"
        print(error_message)
        if app_instance: app_instance.update_status_async(error_message, is_error=True)
    return False

def load_or_create_settings():
    global HOTKEY, END_HOTKEY, CHAT_KEY, SHOW_WINDOW_ON_STARTUP, TOTAL_TPLL_COUNT
    effective_settings = DEFAULT_CONFIG_SETTINGS.copy()
    file_needs_update = False
    is_first_ever_run = not os.path.exists(SETTINGS_FILENAME) 
    
    print(f"Attempting to load settings from '{SETTINGS_FILENAME}'...")
    try:
        if not is_first_ever_run:
            with open(SETTINGS_FILENAME, 'r') as f:
                loaded_from_file = json.load(f)
            print(f"Successfully parsed '{SETTINGS_FILENAME}'.")
            for key, default_value in DEFAULT_CONFIG_SETTINGS.items():
                if key in loaded_from_file:
                    file_value = loaded_from_file[key]
                    expected_type = type(default_value)
                    if isinstance(file_value, expected_type):
                        if expected_type == str and not file_value.strip():
                            effective_settings[key] = default_value; file_needs_update = True
                        else:
                            effective_settings[key] = file_value
                    else:
                        effective_settings[key] = default_value; file_needs_update = True
                else:
                    file_needs_update = True
    except FileNotFoundError: 
        is_first_ever_run = True 
    except json.JSONDecodeError:
        file_needs_update = True 
        if app_instance: app_instance.update_status_async(f"Error decoding settings file. Using defaults.", is_error=True)
    except Exception as e:
        file_needs_update = True
        if app_instance: app_instance.update_status_async(f"Error loading settings: {e}. Using defaults.", is_error=True)
    
    if is_first_ever_run: 
        effective_settings = DEFAULT_CONFIG_SETTINGS.copy() 
        effective_settings["SHOW_WINDOW_ON_STARTUP"] = True 
        save_settings_to_file(effective_settings) 
    elif file_needs_update: 
        save_settings_to_file(effective_settings)

    HOTKEY = effective_settings["HOTKEY"]
    END_HOTKEY = effective_settings["END_HOTKEY"]
    CHAT_KEY = effective_settings["CHAT_KEY"]
    SHOW_WINDOW_ON_STARTUP = effective_settings["SHOW_WINDOW_ON_STARTUP"]
    TOTAL_TPLL_COUNT = int(effective_settings.get("TOTAL_TPLL_COUNT", 0))

load_or_create_settings() 

def simulate_key(key_str):
    vk_code = 0; shift_pressed = False; ctrl_pressed = False; alt_pressed = False
    if key_str.upper() in SPECIAL_VK_MAP: vk_code = SPECIAL_VK_MAP[key_str.upper()]
    elif len(key_str) == 1:
        scan_result = win32api.VkKeyScan(key_str)
        if scan_result == -1:
            try:
                vk_code = win32api.VkKeyScan(key_str.lower()) & 0xFF
                if vk_code == 0: vk_code = ord(key_str.upper())
            except: print(f"Error: Cannot determine VK code for '{key_str}'."); return False 
        else:
            vk_code = scan_result & 0xFF; modifiers = scan_result >> 8
            shift_pressed = (modifiers & 1) != 0; ctrl_pressed = (modifiers & 2) != 0; alt_pressed = (modifiers & 4) != 0
    else: print(f"Error: Cannot simulate key '{key_str}'."); return False 
    if vk_code == 0: print(f"Error: Failed to determine VK code for '{key_str}'."); return False
    try:
        if shift_pressed: win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0); time.sleep(VK_SLEEP / 2)
        win32api.keybd_event(vk_code, 0, 0, 0); time.sleep(VK_SLEEP)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        if shift_pressed: time.sleep(VK_SLEEP / 2); win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
        return True
    except Exception as e:
        print(f"Error during key simulation for '{key_str}': {e}"); return False
    return False

def perform_tpll_action():
    global TOTAL_TPLL_COUNT
    start_time = time.time()
    gep_activated_wait_actual = 0
    action_status = "TPLL Action started..."
    if app_instance: app_instance.update_status_async(action_status)
    try:
        user32 = ctypes.windll.user32 # Direct line to Windows window management

        # 1. Grab Google Earth Pro coords
        cursor_pos = win32gui.GetCursorPos()
        hwnd_under_cursor = win32gui.WindowFromPoint(cursor_pos)
        if not hwnd_under_cursor: return
        hwnd_main_app = win32gui.GetAncestor(hwnd_under_cursor, win32con.GA_ROOTOWNER)
        if not hwnd_main_app: hwnd_main_app = hwnd_under_cursor
        if not hwnd_main_app: return
        
        window_title_under_mouse = win32gui.GetWindowText(hwnd_main_app)
        if GOOGLE_EARTH_TITLE not in window_title_under_mouse: return
        
        current_active_hwnd = user32.GetForegroundWindow()
        if hwnd_main_app != current_active_hwnd:
            user32.SetForegroundWindow(hwnd_main_app)
            time.sleep(GEP_ACTIVATE_WAIT)
            
        pyperclip.copy("") 
        time.sleep(PRE_COPY_WAIT)
        keyboard.press_and_release('ctrl+shift+c')
        time.sleep(COPY_WAIT)
        coords = pyperclip.paste()
        
        if not coords:
            action_status = "Error: Clipboard empty (Google Earth Pro)."
            print(action_status)
            if app_instance: app_instance.update_status_async(action_status, is_error=True)
            return
            
        coords = coords.strip()
        final_command = f"/tpll {coords}"
        
        # 2. Find Minecraft Window natively
        mc_hwnd = 0
        def enum_windows_callback(hwnd, _):
            nonlocal mc_hwnd
            if win32gui.IsWindowVisible(hwnd) and MINECRAFT_TITLE_KEYWORD in win32gui.GetWindowText(hwnd):
                mc_hwnd = hwnd
                
        win32gui.EnumWindows(enum_windows_callback, None)
        
        if mc_hwnd == 0:
            action_status = f"Error: No Minecraft window found ('{MINECRAFT_TITLE_KEYWORD}')."
            print(action_status)
            if app_instance: app_instance.update_status_async(action_status, is_error=True)
            return
            
        # 3. Activate Minecraft using bulletproof ctypes
        try:
            # Tap ALT to bypass the Windows terminal focus block
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0) 
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0) 
            
            # SW_RESTORE is 9 in the Windows API
            if user32.IsIconic(mc_hwnd):
                user32.ShowWindow(mc_hwnd, 9)
                
            # Force it to the front natively
            user32.SetForegroundWindow(mc_hwnd)
            time.sleep(MC_ACTIVATE_WAIT)
            
        except Exception as e: 
            action_status = f"Error activating Minecraft."
            print(f"{action_status} Details: {e}")
            if app_instance: app_instance.update_status_async(action_status, is_error=True)
            return
            
        # 4. Execute Command
        keyboard.press_and_release('esc')
        time.sleep(ESC_WAIT)
        if not simulate_key(CHAT_KEY):
            action_status = f"Error: Failed to simulate chat key '{CHAT_KEY}'."
            print(action_status)
            if app_instance: app_instance.update_status_async(action_status, is_error=True)
            return
            
        time.sleep(CHAT_OPEN_WAIT)
        keyboard.write(final_command)
        time.sleep(PRE_ENTER_WAIT)
        keyboard.press_and_release('enter')
        
        if app_instance:
            app_instance.session_tpll_count += 1
            app_instance.session_tpll_count_var.set(app_instance.session_tpll_count)
            TOTAL_TPLL_COUNT += 1
            app_instance.total_tpll_count_var.set(TOTAL_TPLL_COUNT)
            
        end_time = time.time()
        action_status = f"Action complete. (Total: {end_time - start_time:.3f}s)"
        print(action_status) 
        if app_instance: app_instance.update_status_async(action_status)
        
    except Exception as e:
        action_status = f"Error in tpll action: {e}"
        print(action_status)
        if app_instance: app_instance.update_status_async(action_status, is_error=True)

def tpll_hotkey_loop():
    global app_instance, HOTKEY
    current_hotkey_for_this_thread = HOTKEY 
    try:
        keyboard.add_hotkey(current_hotkey_for_this_thread, perform_tpll_action, trigger_on_release=False)
        status_msg = f"TPLL Hotkey '{current_hotkey_for_this_thread}' is now ACTIVE."
        if app_instance: app_instance.update_status_async(status_msg)
        while app_instance and app_instance.tpll_hotkey_should_run:
            time.sleep(0.1)
    except Exception as e: 
        error_msg = f"TPLL hotkey listener error: {e}"
        if app_instance: app_instance.after(0, lambda: app_instance.handle_listener_thread_stop(error_msg, is_error=True))
    finally:
        try:
            keyboard.remove_hotkey(current_hotkey_for_this_thread) 
        except: pass
        if app_instance:
            app_instance.after(0, app_instance.handle_listener_thread_stop, "TPLL Hotkey INACTIVE (listener ended).")

class TPLLHelperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        global app_instance, SHOW_WINDOW_ON_STARTUP, TOTAL_TPLL_COUNT
        app_instance = self 
        
        self.title("TPLL Helper")
        try:
            icon_path = "tpll_helper_icon.ico" 
            if hasattr(sys, '_MEIPASS'): icon_path = os.path.join(sys._MEIPASS, icon_path)
            elif getattr(sys, 'frozen', False): icon_path = os.path.join(os.path.dirname(sys.executable), icon_path)
            else: icon_path = os.path.join(os.path.dirname(__file__), icon_path)
            if os.path.exists(icon_path): self.iconbitmap(icon_path)
        except: pass
            
        self.initial_width = 480
        self.initial_height = 360  # Increased height to fit new button and text
        self.geometry(f"{self.initial_width}x{self.initial_height}") 
        self.resizable(False, False) 

        self.tpll_hotkey_should_run = False 
        self.exit_hotkey_registered_token = None 
        self.app_start_time = time.monotonic()
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
        self.iconify()

    def create_widgets(self):
        container = ttk.Frame(self, padding="5")
        container.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1); self.rowconfigure(0, weight=1)
        self.notebook = ttk.Notebook(container)
        
        main_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_tab_frame, text='Main')
        self.populate_main_tab(main_tab_frame)
        
        settings_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_tab_frame, text='Settings')
        self.populate_settings_tab(settings_tab_frame)
        
        self.notebook.grid(row=0, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1); container.columnconfigure(0, weight=1)
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
        
        stats_frame = ttk.LabelFrame(parent_frame, text="Statistics", padding="5")
        stats_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        stats_frame.columnconfigure(1, weight=1)
        ttk.Label(stats_frame, text="TPLLs this session:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.session_tpll_count_var).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, text="Total TPLLs (all time):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.total_tpll_count_var).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, text="Program Uptime:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(stats_frame, textvariable=self.uptime_var).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        button_frame = ttk.Frame(parent_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10) 
        self.start_button = ttk.Button(button_frame, text="Start TPLL Hotkey", command=self.start_tpll_hotkey_listener_ui)
        self.start_button.pack(side=tk.LEFT, padx=5) 
        self.stop_button = ttk.Button(button_frame, text="Stop TPLL Hotkey", command=self.stop_tpll_hotkey_listener_ui)
        self.stop_button.pack(side=tk.LEFT, padx=5) 

    def populate_settings_tab(self, parent_frame):
        parent_frame.columnconfigure(1, weight=1)
        
        # Added instructional text to Settings
        help_text = "Select valid keys from the dropdown menus below."
        ttk.Label(parent_frame, text=help_text, font=("", 9, "italic")).grid(column=0, row=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # TPLL Hotkey uses the restricted safe list so users don't trigger Google Earth actions
        ttk.Label(parent_frame, text="TPLL Hotkey (GEP Safe):").grid(column=0, row=1, sticky=tk.W, pady=5, padx=5)
        self.hotkey_entry = ttk.Combobox(parent_frame, textvariable=self.hotkey_var, values=TPLL_SAFE_KEYS, state="readonly", width=18)
        self.hotkey_entry.grid(column=1, row=1, sticky="ew", pady=5, padx=5)
        
        # Exit and Chat hotkeys use the full list of available keys
        ttk.Label(parent_frame, text="Exit Program Hotkey:").grid(column=0, row=2, sticky=tk.W, pady=5, padx=5)
        self.end_hotkey_entry = ttk.Combobox(parent_frame, textvariable=self.end_hotkey_var, values=ALL_KEYS, state="readonly", width=18)
        self.end_hotkey_entry.grid(column=1, row=2, sticky="ew", pady=5, padx=5)
        
        ttk.Label(parent_frame, text="Minecraft Chat Key:").grid(column=0, row=3, sticky=tk.W, pady=5, padx=5)
        self.chat_key_entry = ttk.Combobox(parent_frame, textvariable=self.chat_key_var, values=ALL_KEYS, state="readonly", width=18)
        self.chat_key_entry.grid(column=1, row=3, sticky="ew", pady=5, padx=5)
        
        self.show_window_check = ttk.Checkbutton(parent_frame, text="Show window on startup", variable=self.show_window_on_startup_var)
        self.show_window_check.grid(column=0, row=4, columnspan=2, sticky=tk.W, pady=10, padx=5)
        
        # Frame to hold the buttons side-by-side
        btn_frame = ttk.Frame(parent_frame)
        btn_frame.grid(column=0, row=5, columnspan=2, pady=10)
        
        self.save_button = ttk.Button(btn_frame, text="Save All Settings", command=self.save_gui_settings)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Added Open Folder button
        self.open_folder_button = ttk.Button(btn_frame, text="Open Settings Folder", command=self.open_settings_folder)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
    def open_settings_folder(self):
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
        HOTKEY = new_tpll_hotkey; END_HOTKEY = new_exit_hotkey 
        CHAT_KEY = new_chat_key; SHOW_WINDOW_ON_STARTUP = new_show_window
        
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
        else: self.update_status_async("Error saving settings.", is_error=True)

    def start_tpll_hotkey_listener_ui(self):
        global tpll_hotkey_listener_thread, HOTKEY 
        if self.tpll_hotkey_should_run or (tpll_hotkey_listener_thread and tpll_hotkey_listener_thread.is_alive()):
            self.update_status_async("TPLL Hotkey is already active.", is_error=True)
            return
        current_gui_tpll_hotkey = self.hotkey_var.get().strip()
        if not current_gui_tpll_hotkey:
            messagebox.showerror("Input Error", "TPLL Hotkey field must be filled.")
            return
        HOTKEY = current_gui_tpll_hotkey 
        try:
            self.tpll_hotkey_should_run = True 
            self._update_button_states()
            tpll_hotkey_listener_thread = threading.Thread(target=tpll_hotkey_loop, daemon=True)
            tpll_hotkey_listener_thread.start()
        except Exception as e:
            self.tpll_hotkey_should_run = False 
            self._update_button_states()
            error_msg = f"Error starting TPLL hotkey: {e}"
            self.update_status_async(error_msg, is_error=True)
            messagebox.showerror("Hotkey Error", f"Could not start TPLL hotkey listener: {e}")

    def stop_tpll_hotkey_listener_ui(self):
        global tpll_hotkey_listener_thread
        if not self.tpll_hotkey_should_run and (not tpll_hotkey_listener_thread or not tpll_hotkey_listener_thread.is_alive()):
            self.handle_listener_thread_stop("TPLL Hotkey is already inactive.")
            return
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
        global END_HOTKEY 
        try:
            if hasattr(self, 'exit_hotkey_registered_token') and self.exit_hotkey_registered_token:
                try: keyboard.remove_hotkey(self.exit_hotkey_registered_token)
                except Exception: pass
            self.exit_hotkey_registered_token = keyboard.add_hotkey(END_HOTKEY, self.program_exit_handler, trigger_on_release=False, suppress=True)
        except Exception as e:
            error_msg = f"Error registering Exit Hotkey '{END_HOTKEY}': {e}"
            messagebox.showerror("Fatal Error", f"{error_msg}\nApp exit via this hotkey may FAIL.")
            self.update_status_async(error_msg, is_error=True)
            
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
        global tpll_hotkey_listener_thread, TOTAL_TPLL_COUNT
        current_settings = {
            "HOTKEY": HOTKEY, "END_HOTKEY": END_HOTKEY, "CHAT_KEY": CHAT_KEY,
            "SHOW_WINDOW_ON_STARTUP": SHOW_WINDOW_ON_STARTUP, 
            "TOTAL_TPLL_COUNT": TOTAL_TPLL_COUNT
        }
        save_settings_to_file(current_settings)
        self.tpll_hotkey_should_run = False
        if tpll_hotkey_listener_thread and tpll_hotkey_listener_thread.is_alive():
            tpll_hotkey_listener_thread.join(timeout=0.3) 
        if hasattr(self, 'exit_hotkey_registered_token') and self.exit_hotkey_registered_token:
            try: keyboard.remove_hotkey(self.exit_hotkey_registered_token)
            except Exception: pass
        self.destroy()

    def update_uptime_label(self):
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