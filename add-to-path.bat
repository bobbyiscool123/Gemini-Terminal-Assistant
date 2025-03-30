@echo off
setlocal enabledelayedexpansion

echo Adding AI Terminal Assistant to your system PATH...

:: Get the current directory
set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

:: Check for admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script needs to be run as Administrator to modify the system PATH.
    echo Please right-click and select "Run as administrator".
    pause
    exit /b 1
)

:: Check if already in PATH
echo Current PATH: !PATH!
if "!PATH:%CURRENT_DIR%=!" neq "!PATH!" (
    echo.
    echo The directory is already in your PATH.
    pause
    exit /b 0
)

:: Add to PATH using reg.exe instead of setx to avoid truncation
echo Adding to system PATH using registry edit...
for /F "tokens=2* skip=2" %%a in ('reg.exe query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v "Path" 2^>nul') do (
    set "syspath=%%b"
)

:: Check if path ends with semicolon
if "!syspath:~-1!" == ";" (
    set "newpath=!syspath!%CURRENT_DIR%"
) else (
    set "newpath=!syspath!;%CURRENT_DIR%"
)

:: Update the registry
reg.exe add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "!newpath!" /f
if %errorlevel% equ 0 (
    echo.
    echo Successfully added to PATH!
    echo You can now type 'terminal-assistant' from any command prompt.
    echo.
    echo IMPORTANT: You MUST restart your command prompt or reboot your computer
    echo           for these changes to take effect.
    echo.
) else (
    echo.
    echo Failed to add to PATH. Error code: %errorlevel%
    echo.
)

pause 