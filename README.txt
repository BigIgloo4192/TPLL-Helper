TPLL Helper for Minecraft
Version 2.5
==========

A standalone desktop tool for Build The Earth builders. TPLL Helper automates
teleporting to real-world coordinates by capturing them directly from
Google Earth Pro and executing the /tpll command in Minecraft — all with a
single keypress.

GitHub: https://github.com/BigIgloo4192/TPLL-Helper


QUICK START
-----------
1. Download TPLLHelper-2.5.exe and place it anywhere on your computer.
2. Double-click to run. (If hotkeys don't register, try "Run as administrator".)
3. Open Google Earth Pro and navigate to your target location.
4. Hover your mouse over the Google Earth Pro window.
5. Press the TPLL Hotkey (default: backtick ` key).
6. You're there.

Google Earth Pro does NOT need to be the focused window. You can have
Minecraft in the foreground, hover over GEP, press the hotkey, and it
will activate GEP, grab coordinates, switch to Minecraft, and teleport
you automatically.


FEATURES
--------
Portable
    Single .exe file, no Python or dependencies to install.

One-Key Teleport
    Copies coordinates from Google Earth Pro, switches to Minecraft,
    opens chat, types /tpll <coords>, and hits Enter. All automatic.

Works Without GEP Focus
    The hotkey works as long as your mouse is over the GEP window,
    even if another application has focus.

Auto-Place Mode
    After teleporting, automatically jumps, looks straight down, and
    places the block in your hand. Works in both fly mode and normal
    mode. Toggle it on/off quickly from the Main tab, or set the
    default in Settings. Make sure you have a block in your hand.

Coordinate Logging
    Optionally records every teleport to a CSV file with timestamps.
    Open it in Excel or Google Sheets to review your history. Enable
    in Settings, and use "Clear Log" to reset when it gets large.
    The log file lives in the same folder as your settings.

System Tray
    Closing the window (X button) minimizes the app to your system
    tray instead of quitting. The hotkey keeps running in the
    background. Right-click the tray icon to show the window or
    exit. Use the Exit Program Hotkey to quit from anywhere.

Cumulative Session Time
    Tracks total time spent across all sessions, persisted to disk.
    Displayed alongside session uptime on the Main tab.

Coordinate Validation
    Validates that the clipboard actually contains coordinates before
    sending anything to Minecraft. No more accidental chat messages
    from stale clipboard data.

Crash-Safe Statistics
    TPLL count auto-saves to disk every 10 teleports, so a crash
    or forced close won't lose your stats.

Live Statistics
    Tracks TPLLs this session, total TPLLs all-time, last coordinates
    sent, session uptime, and total time on the Main tab.

Foolproof Settings
    All hotkeys are configured via dropdown menus — no way to type
    an invalid key. The TPLL Hotkey dropdown only shows keys that
    are safe in Google Earth Pro (won't reset your camera, etc).
    Duplicate hotkey detection prevents you from assigning the same
    key to multiple functions.

Sound Feedback
    Optional system beep on successful TPLL. Disabled by default,
    enable in Settings if you want audio confirmation.

Clean Workspace
    Settings and log files saved to %LOCALAPPDATA%\TPLLHelper so
    there's no config file cluttering your desktop. Click "Open
    Settings Folder" in the Settings tab to find them.

Auto-Start
    The TPLL hotkey activates automatically on launch.

Minimize on Startup
    Option to start minimized so it stays out of your way after
    initial setup.

About Tab
    Version info, GitHub link (clickable), and contact details.
    All text is selectable and copyable.


SETTINGS
--------
TPLL Hotkey (GEP Safe)
    The key that triggers the teleport macro. Only shows keys that
    won't interfere with Google Earth Pro's own shortcuts.
    Default: ` (backtick)

Exit Program Hotkey
    Emergency kill switch that instantly closes TPLL Helper from
    anywhere, even from the system tray.
    Default: F12

Minecraft Chat Key
    The key that opens chat in your Minecraft client. Must match
    your in-game keybind exactly.
    Default: t

Show Window on Startup
    When unchecked, the app starts minimized.

Enable Auto-Place by Default
    When checked, Auto-Place mode is on every time the app starts.

Log Coordinates to CSV File
    When checked, every teleport is recorded with a timestamp.

Play Sound on Successful TPLL
    When checked, plays a short beep after each teleport.
    Disabled by default.

All settings persist across sessions in the JSON config file.


WINDOW & TRAY BEHAVIOR
-----------------------
Clicking the X button does NOT close the app. It minimizes to
your system tray (the hidden icons area in your taskbar). The
TPLL hotkey continues to work in the background.

To fully exit the application:
    - Press the Exit Program Hotkey (default: F12), or
    - Right-click the tray icon and select "Exit"

To restore the window:
    - Double-click the tray icon, or
    - Right-click the tray icon and select "Show Window"


TROUBLESHOOTING
---------------
Hotkeys not working:
    - Check the status bar at the bottom of the Main tab. It should
      say the TPLL Hotkey is "ACTIVE".
    - Try running the .exe as administrator.
    - Make sure no other app is capturing global keyboard input.

Clipboard empty / coordinates not copying:
    - Make sure your mouse cursor is physically over the Google Earth
      Pro window when you press the hotkey.
    - If GEP just opened, give it a moment to fully load before trying.

Wrong coordinates or "Invalid coordinates" error:
    - Another application may have written to your clipboard between
      the copy and paste. Try again — this is rare.

Not switching to Minecraft:
    - Verify that Minecraft is open and its window title contains
      the word "Minecraft".
    - Check that the Minecraft Chat Key setting matches your in-game
      chat keybind.

Command appears in chat but doesn't execute:
    - The chat key setting might be wrong. If your Minecraft chat key
      is T, the app opens chat with T (no slash prefix), then types
      the full /tpll command. If your chat key is /, it opens chat
      with / pre-filled, then types /tpll — resulting in //tpll.
      Make sure your setting matches your actual keybind.

Auto-Place not placing a block:
    - Make sure you have a block selected in your hotbar.
    - On laggy servers, the teleport may take longer to complete.
      The block placement might fire before you've fully arrived.

Tray icon not appearing:
    - Check your hidden icons area (click the ^ arrow on your taskbar).
    - If running from Python source, make sure pystray and Pillow are
      installed: pip install pystray Pillow


CONTACT & SUPPORT
-----------------
GitHub:  https://github.com/BigIgloo4192/TPLL-Helper
Discord: DM realbigigloo
Email:   bigigloo4192@gmail.com
