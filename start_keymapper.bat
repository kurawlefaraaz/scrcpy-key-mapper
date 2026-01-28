@echo off
SET SERVER_PATH=/data/local/tmp/test-scrcpy-server.jar

echo [*] Pushing server to device...
adb push scrcpy-server %SERVER_PATH%

echo [*] Setting up port forwarding...
adb forward tcp:1234 localabstract:scrcpy

echo [*] Starting scrcpy-server in a new window...
:: This starts the server in a separate process
@REM start "scrcpy_server" adb shell CLASSPATH=%SERVER_PATH% app_process / com.genymobile.scrcpy.Server 3.3.4 tunnel_forward=true audio=false control=true video=false log_level=verbose
start "scrcpy_server" cmd /k "adb shell CLASSPATH=%SERVER_PATH% app_process / com.genymobile.scrcpy.Server 3.3.4 tunnel_forward=true audio=false control=true video=false log_level=verbose display_id=30"
echo [*] Waiting for server to initialize...
timeout /t 3 >nul

echo [*] Launching Python Keymapper...
:: This runs python in the CURRENT shell. 
:: If you close this window, the python process dies immediately.
python test_touch.py

:: Cleanup if Python exits normally
taskkill /FI "WINDOWTITLE eq scrcpy_server" /F >nul 2>&1




:: TODO: Reimplement the python code without AI
:: TODO: Test if it works on MacOS and Linux
:: TODO: Create a python and json based simple keymap manager
:: TODO: Create a python based keymap creator which tracks the logs of adb for touch press
:: TODO: Remove the Global Keylogging mechanism in favor of using tkinter based transparent Window to detect the keypress while the user is using it.

