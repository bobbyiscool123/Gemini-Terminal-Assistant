@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Set the path to the installation directory (where this file is)
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
set "AGENT_SCRIPT=%INSTALL_DIR%\run_agent.py"

:: For debugging
echo Installation directory: %INSTALL_DIR%

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

:: Handle drive switching safely
set "DRIVE=%INSTALL_DIR:~0,2%"
echo Changing to drive %DRIVE%

:: Save current drive
for /f "tokens=1,2 delims=:" %%A in ('cd') do set "CURRENT_DRIVE=%%A:"

:: Change drives first if needed
if not "%CURRENT_DRIVE%"=="%DRIVE%" (
    %DRIVE%
    if errorlevel 1 (
        echo Error: Could not change to drive %DRIVE%
        exit /b 1
    )
)

:: Then change directory
cd "%INSTALL_DIR%"
if errorlevel 1 (
    echo Error: Could not change to directory %INSTALL_DIR%
    exit /b 1
)

echo Current directory: %CD%

:: Enable quick termination with Ctrl+C
if "%~1" == "" (
    :: No arguments - run in interactive mode
    python "%AGENT_SCRIPT%"
) else (
    :: Arguments provided - run the command and exit
    set args=%*
    
    echo Running command: %args%
    python "%AGENT_SCRIPT%" --execute "%args%"
)

:: Return the error code from Python
exit /b %ERRORLEVEL%
