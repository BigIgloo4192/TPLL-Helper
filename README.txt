# TPLL Helper for Minecraft

TPLL Helper is a Python script designed to assist players in projects like "Build The Earth" by automating the process of teleporting to specific real-world coordinates within Minecraft. It captures coordinates from Google Earth Pro and executes the `/tpll` command in Minecraft.

## Features

* **Automated `/tpll` Execution:** Copies coordinates from Google Earth Pro and pastes them into the Minecraft chat with the `/tpll` command.
* **Graphical User Interface (GUI):**
    * Easy-to-use interface for managing settings and controlling the hotkeys.
    * Tabbed layout ("Main" and "Settings").
    * Displays TPLL usage statistics (session count, total count) and program uptime.
* **Configurable Hotkeys:**
    * Set custom hotkeys for the main TPLL action.
    * Set a custom hotkey to exit the entire application.
    * Set a custom Minecraft chat key used by the script.
    * Settings are saved in a `tpllhelper_settings.json` file.
* **Auto-Start Hotkeys:** The TPLL hotkey automatically becomes active when the application starts.
* **Conditional Startup Visibility:** Option to start the GUI minimized on subsequent launches.
* **Custom Application Icon:** Supports a custom `.ico` file for the window and taskbar icon.
* **Status Updates:** Provides feedback on actions, errors, and hotkey status within the GUI.

## Requirements

* **Python 3.x**
* **Windows Operating System** (due to `pywin32` and window management specifics)
* **Required Python Libraries:**
    * `keyboard`
    * `pyperclip`
    * `pygetwindow`
    * `pywin32`

## Installation

1.  **Download the Script:**
    * Save the Python script (e.g., `tpll_helper.py`) to a folder on your computer.

2.  **Install Python:**
    * If you don't have Python installed, download and install it from [python.org](http://python.org/). Make sure to check the box "Add Python to PATH" during installation.

3.  **Install Required Libraries:**
    * Open a command prompt (CMD) or PowerShell.
    * Navigate to the folder where you saved the script using the `cd` command (e.g., `cd C:\Users\YourName\Desktop\TPLL_Helper`).
    * Install the libraries by running the following command:
        ```bash
        pip install keyboard pyperclip pygetwindow pywin32
        ```

4.  **(Optional) Custom Icon:**
    * To use a custom icon for the application window and taskbar:
        * Create or download an icon file in `.ico` format (e.g., `tpll_helper_icon.ico`).
        * Place this `.ico` file in the **same directory** as the `tpll_helper.py` script.
    * If the icon file is not found, a default window icon will be used.

## How to Run

1.  Navigate to the directory where you saved `tpll_helper.py` using a command prompt or PowerShell.
2.  Run the script using:
    ```bash
    python tpll_helper.py
    ```
3.  **Administrator Privileges:** If hotkeys do not seem to work, you might need to run the script with administrator privileges. Right-click your command prompt/PowerShell and select "Run as administrator," then navigate to the script directory and run it.

## Using the Application

### First Run

* On the very first launch, the GUI window will appear normally.
* A `tpllhelper_settings.json` file will be automatically created in the script's directory with default hotkey settings.
* The TPLL Hotkey and the Exit Program Hotkey will be active immediately.

### GUI Overview

The application window has two main tabs:

**1. Main Tab:**

* **Instructions:** Basic steps on how to use the TPLL functionality.
* **Statistics:**
    * *TPLLs this session:* Counts how many times the TPLL action has been successfully performed since the app started.
    * *Total TPLLs (all time):* A persistent counter of all TPLLs made, loaded from and saved to the settings file.
    * *Program Uptime:* Shows how long the TPLL Helper application has been running in the current session.
* **Start/Stop TPLL Hotkey Buttons:**
    * **Start TPLL Hotkey:** Activates the hotkey for copying coordinates and sending the `/tpll` command. (This is started automatically by default).
    * **Stop TPLL Hotkey:** Deactivates the TPLL hotkey. The Exit Program Hotkey remains active.
* **Status Bar (at the bottom of the window):** Displays the current status of the hotkeys, results of actions, or error messages.

**2. Settings Tab:**

* **TPLL Hotkey:** Enter the key or key combination you want to use for the main TPLL action (e.g., `` ` ``, `alt+t`).
* **Exit Program Hotkey:** Enter the key that will close the entire TPLL Helper application (e.g., `f12`).
* **Minecraft Chat Key:** Enter the key that opens the chat in your Minecraft client (e.g., `/`, `t`).
* **Show window on startup:**
    * If checked (default for first run), the GUI window will appear normally each time you start the application.
    * If unchecked, the GUI window will start minimized to the taskbar on subsequent launches (after the first run). You can click its taskbar icon to open it.
* **Save All Settings Button:** Click this to save any changes made in the fields above to the `tpllhelper_settings.json` file.
    * *Note:* If the TPLL Hotkey is active and you change its setting, you'll need to click "Stop TPLL Hotkey" and then "Start TPLL Hotkey" for the new TPLL hotkey to take effect. Changes to the "Exit Program Hotkey" require an application restart for the hotkey itself to update (though the setting will save).

### Performing a TPLL Action

1.  Ensure the TPLL Helper application is running and the TPLL Hotkey is active (check the status bar on the Main tab).
2.  Open Google Earth Pro and navigate to your desired location.
3.  Move your mouse cursor so it is **over the Google Earth Pro window**.
4.  Press your configured **TPLL Hotkey** (default is the backtick key: `` ` ``).
5.  The script will then:
    * Attempt to activate the Google Earth Pro window (if not already active).
    * Simulate `Ctrl+Shift+C` to copy coordinates from Google Earth Pro.
    * Activate your Minecraft window.
    * Press `Escape` (to close any menus/chat).
    * Press your configured Minecraft Chat Key.
    * Type `/tpll ` followed by the copied coordinates.
    * Press `Enter`.

### Exiting the Program

* Press your configured **Exit Program Hotkey** (default is `F12`). This will close the application.
* Alternatively, you can click the 'X' button on the GUI window. If the TPLL Hotkey is active, you'll be asked for confirmation.

## Configuration File (`tpllhelper_settings.json`)

The script uses a JSON file named `tpllhelper_settings.json` (created in the same directory as the script) to store your custom settings. You can manually edit this file if needed, but it's generally recommended to use the Settings tab in the GUI.

**Example `tpllhelper_settings.json`:**

```json
{
    "HOTKEY": "`",
    "END_HOTKEY": "f12",
    "CHAT_KEY": "/",
    "SHOW_WINDOW_ON_STARTUP": true,
    "TOTAL_TPLL_COUNT": 0
}
HOTKEY: The key for the main TPLL action.
END_HOTKEY: The key to exit the entire application.
CHAT_KEY: The key that opens chat in Minecraft.
SHOW_WINDOW_ON_STARTUP: true to show the GUI window normally on launch, false to start it minimized (after the first run).
TOTAL_TPLL_COUNT: Stores the total number of successful TPLL actions performed.

### Troubleshooting

Hotkeys not working:
    * Ensure the TPLL Helper application is running and the TPLL Hotkey is "active" (check the status bar in the GUI).
    * Try running the script with administrator privileges.
    * Make sure no other application is aggressively capturing all keyboard input.

Coordinates not copying / Wrong command in Minecraft:
    * Ensure your mouse is over the Google Earth Pro window when pressing the TPLL Hotkey.
    * Verify the "Minecraft Chat Key" in the settings matches the key you use to open chat in Minecraft.
Custom Icon Not Showing:
    * Ensure you have an .ico file named tpll_helper_icon.ico (or whatever you named it and updated in the script) in the same directory as the script.
    * The .ico file should be valid and preferably multi-resolution.
    * The taskbar icon for Python scripts can sometimes be inconsistent; packaging as an .exe provides the most reliable custom icon experience.

## Questions/Suggestions:
    * DM realbigigloo on Discord
    * Email: bigigloo4192@gmail.com
