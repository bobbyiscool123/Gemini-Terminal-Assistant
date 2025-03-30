@echo off
setlocal enabledelayedexpansion

:: Set the path to the installation directory (where this file is)
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
set "AGENT_SCRIPT=%INSTALL_DIR%\run_agent.py"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher.
    pause
    exit /b 1
)

:: Create/ensure .env file exists
if not exist "%INSTALL_DIR%\.env" (
    echo Creating .env file...
    echo GOOGLE_API_KEY=your_api_key_here > "%INSTALL_DIR%\.env"
    echo Please edit the .env file with your API key.
    pause
    exit /b 1
)

:: Change to the installation directory
cd /d "%INSTALL_DIR%"

:: Check if arguments were provided
if "%~1" == "" (
    :: No arguments - run in interactive mode
    python "%AGENT_SCRIPT%"
) else (
    :: Arguments provided - run the command and exit
    :: Collect all arguments including spaces
    set "args=%*"
    
    :: Run the agent with the arguments
    python "%AGENT_SCRIPT%" --execute "%args%"
)

exit /b 0
