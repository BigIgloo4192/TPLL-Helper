# TPLL Helper for Minecraft (Version 2.1)

TPLL Helper is a standalone desktop application designed to assist players in projects like "Build The Earth" by automating the process of teleporting to specific real-world coordinates within Minecraft. It captures coordinates directly from Google Earth Pro and instantly executes the `/tpll` command in your active Minecraft window.

## Features

* **Fully Portable:** Distributed as a single, standalone `.exe` file. No Python installation required!
* **Automated `/tpll` Execution:** Copies coordinates from Google Earth Pro, natively swaps to your Minecraft window, and pastes the command into chat automatically.
* **Graphical User Interface (GUI):**
    * Tabbed layout ("Main" and "Settings").
    * Displays live TPLL usage statistics (session count, total count) and program uptime.
* **Foolproof Configuration:**
    * Settings are now managed via dropdown menus to prevent invalid keys.
    * The main TPLL Hotkey prevents you from selecting keys that trigger default actions in Google Earth Pro (like resetting your camera).
* **Clean Workspace:** Settings are automatically saved to your hidden Windows AppData folder (`%LOCALAPPDATA%\TPLLHelper`), so you don't have to keep track of a `.json` file on your desktop.
* **Auto-Start Hotkeys:** The TPLL hotkey automatically becomes active when the application starts.
* **Conditional Startup Visibility:** Option to start the GUI minimized to your taskbar on subsequent launches so it stays out of your way.

## How to Install & Run

1. Download the `tpllhelper-2.1.exe` file.
2. Place it anywhere on your computer (like your Desktop or a dedicated BTE folder).
3. Double-click to run! (Note: If your hotkeys do not seem to register, try right-clicking the `.exe` and selecting "Run as administrator").

## Using the Application

1. Ensure the TPLL Helper application is running and the TPLL Hotkey is active (check the status bar on the Main tab).
2. Open Google Earth Pro and navigate to your desired location.
3. Move your mouse cursor so it is hovering over the Google Earth Pro window.
4. Press your configured TPLL Hotkey (default is the backtick key: `).
5. The program will automatically grab the coordinates, pull Minecraft to the front, and teleport you!

## Managing Settings

The Settings Tab allows you to change your hotkeys. 
* **TPLL Hotkey:** The key that grabs coordinates. 
* **Exit Program Hotkey:** An emergency "Kill Switch" that instantly closes the TPLL application (default is `f12`).
* **Minecraft Chat Key:** The key that opens the chat in your Minecraft client (default is `/`).

To manually view your configuration file, click the "Open Settings Folder" button to instantly navigate to the hidden AppData directory.

## Troubleshooting

* **Hotkeys not working:**
    * Ensure the TPLL Helper is running and the TPLL Hotkey is "active" (check the status bar).
    * Make sure no other application is aggressively capturing all keyboard input.
* **Coordinates not copying / Not switching to Minecraft:**
    * Ensure your mouse is over the Google Earth Pro window when pressing the TPLL Hotkey.
    * Verify the "Minecraft Chat Key" in the settings matches the exact key you use to open chat in Minecraft.

## Contact & Support
* Discord: DM realbigigloo
* Email: bigigloo4192@gmail.com
