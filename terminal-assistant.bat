@echo off
setlocal enabledelayedexpansion

:: Get the directory where the batch file is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "AGENT_SCRIPT=%SCRIPT_DIR%\run_agent.py"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher.
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist "%SCRIPT_DIR%\.env" (
    echo Creating .env file template...
    echo GOOGLE_API_KEY=your_api_key_here > "%SCRIPT_DIR%\.env"
    echo Please edit the .env file with your Gemini API key.
    pause
    exit /b 1
)

:: Check for requirements
if not exist "%SCRIPT_DIR%\venv" (
    echo Setting up environment...
    cd /d "%SCRIPT_DIR%"
    python -m venv venv
    call "%SCRIPT_DIR%\venv\Scripts\activate.bat"
    pip install -r requirements.txt
) else (
    call "%SCRIPT_DIR%\venv\Scripts\activate.bat"
)

:: Run the agent with all passed arguments
cd /d "%SCRIPT_DIR%"

:: Check if there are any command line arguments
if "%~1"=="" (
    :: No arguments - run in interactive mode
    python "%AGENT_SCRIPT%"
) else (
    :: Arguments provided - pass them directly
    python "%AGENT_SCRIPT%" %*
)

:: Deactivate the virtual environment
call deactivate

exit /b 0
