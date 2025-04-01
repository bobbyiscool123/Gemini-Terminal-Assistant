@echo off
setlocal EnableExtensions EnableDelayedExpansion

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

:: Handle drive switching safely
set "DRIVE=%INSTALL_DIR:~0,2%"

:: Save current drive
for /f "tokens=1,2 delims=:" %%A in ('cd') do set "CURRENT_DRIVE=%%A:"

:: Change drives first if needed
if not "%CURRENT_DRIVE%"=="%DRIVE%" (
    %DRIVE% >nul 2>&1
    if errorlevel 1 (
        echo Error: Could not change to drive %DRIVE%
        exit /b 1
    )
)

:: Then change directory
cd "%INSTALL_DIR%" >nul 2>&1
if errorlevel 1 (
    echo Error: Could not change to directory %INSTALL_DIR%
    exit /b 1
)

:: Enable quick termination with Ctrl+C
if "%~1" == "" (
    :: No arguments - run in interactive mode
    echo Installation directory: %INSTALL_DIR%
    echo Current directory: %CD%
    python "%AGENT_SCRIPT%"
) else (
    :: If the first argument is a recognized special command, handle it directly
    if /I "%~1" == "version" (
        python "%AGENT_SCRIPT%" --execute "version"
    ) else if /I "%~1" == "--version" (
        python "%AGENT_SCRIPT%" --execute "version"
    ) else if /I "%~1" == "-v" (
        python "%AGENT_SCRIPT%" --execute "version"
    ) else if /I "%~1" == "help" (
        python "%AGENT_SCRIPT%" --execute "help"
    ) else if /I "%~1" == "--help" (
        python "%AGENT_SCRIPT%" --execute "help"
    ) else if /I "%~1" == "-h" (
        python "%AGENT_SCRIPT%" --execute "help"
    ) else (
        :: Check for special commands without using findstr
        set "cmd_lower=%*"
        set "cmd_lower=!cmd_lower:Find=find!"
        set "cmd_lower=!cmd_lower:FILES=files!"
        set "cmd_lower=!cmd_lower:LARGER=larger!"
        set "cmd_lower=!cmd_lower:CPU=cpu!"
        set "cmd_lower=!cmd_lower:MEMORY=memory!"
        set "cmd_lower=!cmd_lower:SHOW=show!"
        set "cmd_lower=!cmd_lower:MONITOR=monitor!"
        set "cmd_lower=!cmd_lower:REAL-TIME=real-time!"
        set "cmd_lower=!cmd_lower:REALTIME=realtime!"
        set "cmd_lower=!cmd_lower:USAGE=usage!"
        
        :: For Windows-specific file search commands, handle them specially
        if /I "!cmd_lower!" == "find all files larger than 10mb in the current directory" (
            :: Simple command to find large files using PowerShell
            echo Searching for files larger than 10 MB...
            powershell -Command "Get-ChildItem -Path . -Recurse -File | Where-Object { $_.Length -gt 10MB } | ForEach-Object { Write-Host ('Size: {0:N2} MB - Path: {1}' -f ($_.Length / 1MB), $_.FullName) }"
        ) else if /I "!cmd_lower:find files larger=!" NEQ "!cmd_lower!" (
            :: Default to 10MB if size not specified
            set "size=10"
            
            echo Searching for files larger than !size! MB...
            powershell -Command "Get-ChildItem -Path . -Recurse -File | Where-Object { $_.Length -gt !size!MB } | ForEach-Object { Write-Host ('Size: {0:N2} MB - Path: {1}' -f ($_.Length / 1MB), $_.FullName) }"
        ) else if /I "!cmd_lower:show cpu=!" NEQ "!cmd_lower!" (
            :: Handle CPU/memory monitoring commands
            if /I "!cmd_lower:memory=!" NEQ "!cmd_lower!" (
                echo Monitoring system resources...
                
                :: Display top CPU-consuming processes
                echo.
                echo Top CPU consumers:
                powershell -Command "Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID | Format-Table -AutoSize"
                
                :: Display memory usage
                echo.
                echo Memory usage:
                powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object @{Name='TotalMemory_MB';Expression={[math]::Round($_.TotalVisibleMemorySize/1KB,2)}}, @{Name='FreeMemory_MB';Expression={[math]::Round($_.FreePhysicalMemory/1KB,2)}}, @{Name='UsedMemory_MB';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/1KB,2)}}, @{Name='MemoryUsage_Percent';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100,2)}} | Format-Table -AutoSize"
                
                :: Display CPU usage
                echo.
                echo CPU usage:
                powershell -Command "$CPU = (Get-Counter '\Processor(_Total)\%% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue; Write-Host ('CPU usage: {0:N2}%%' -f $CPU)"
                
                :: Optional: open Task Manager for continuous monitoring
                echo.
                echo To see continuous updates, opening Task Manager...
                start taskmgr
            ) else (
                :: CPU monitoring only
                echo Monitoring CPU usage...
                
                :: Display top CPU-consuming processes
                echo.
                echo Top CPU consumers:
                powershell -Command "Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID | Format-Table -AutoSize"
                
                :: Display CPU usage
                echo.
                echo CPU usage:
                powershell -Command "$CPU = (Get-Counter '\Processor(_Total)\%% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue; Write-Host ('CPU usage: {0:N2}%%' -f $CPU)"
            )
        ) else if /I "!cmd_lower:show memory=!" NEQ "!cmd_lower!" (
            :: Memory monitoring only
            echo Monitoring memory usage...
            
            :: Display memory usage
            echo.
            echo Memory usage:
            powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object @{Name='TotalMemory_MB';Expression={[math]::Round($_.TotalVisibleMemorySize/1KB,2)}}, @{Name='FreeMemory_MB';Expression={[math]::Round($_.FreePhysicalMemory/1KB,2)}}, @{Name='UsedMemory_MB';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/1KB,2)}}, @{Name='MemoryUsage_Percent';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100,2)}} | Format-Table -AutoSize"
            
            :: Display processes by memory usage
            echo.
            echo Top memory consumers:
            powershell -Command "Get-Process | Sort-Object -Property WorkingSet -Descending | Select-Object -First 10 Name, @{Name='Memory (MB)';Expression={[math]::Round($_.WorkingSet/1MB,2)}}, CPU, ID | Format-Table -AutoSize"
        ) else if /I "!cmd_lower:monitor=!" NEQ "!cmd_lower!" (
            :: Check if we're monitoring CPU or memory or system
            set "monitor_cpu="
            set "monitor_memory="
            set "monitor_system="
            
            if /I "!cmd_lower:cpu=!" NEQ "!cmd_lower!" set "monitor_cpu=1"
            if /I "!cmd_lower:memory=!" NEQ "!cmd_lower!" set "monitor_memory=1"
            if /I "!cmd_lower:ram=!" NEQ "!cmd_lower!" set "monitor_memory=1" 
            if /I "!cmd_lower:system=!" NEQ "!cmd_lower!" set "monitor_system=1"
            
            if defined monitor_cpu if defined monitor_memory (
                echo Monitoring system resources...
                
                :: Display top CPU-consuming processes
                echo.
                echo Top CPU consumers:
                powershell -Command "Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID | Format-Table -AutoSize"
                
                :: Display memory usage
                echo.
                echo Memory usage:
                powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object @{Name='TotalMemory_MB';Expression={[math]::Round($_.TotalVisibleMemorySize/1KB,2)}}, @{Name='FreeMemory_MB';Expression={[math]::Round($_.FreePhysicalMemory/1KB,2)}}, @{Name='UsedMemory_MB';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/1KB,2)}}, @{Name='MemoryUsage_Percent';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100,2)}} | Format-Table -AutoSize"
                
                :: Display CPU usage
                echo.
                echo CPU usage:
                powershell -Command "$CPU = (Get-Counter '\Processor(_Total)\%% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue; Write-Host ('CPU usage: {0:N2}%%' -f $CPU)"
                
                :: Optional: open Task Manager for continuous monitoring
                echo.
                echo To see continuous updates, opening Task Manager...
                start taskmgr
            ) else if defined monitor_cpu (
                :: CPU monitoring only  
                echo Monitoring CPU usage...
                
                :: Display top CPU-consuming processes
                echo.
                echo Top CPU consumers:
                powershell -Command "Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID | Format-Table -AutoSize"
                
                :: Display CPU usage
                echo.
                echo CPU usage:
                powershell -Command "$CPU = (Get-Counter '\Processor(_Total)\%% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue; Write-Host ('CPU usage: {0:N2}%%' -f $CPU)"
            ) else if defined monitor_memory (
                :: Memory monitoring only
                echo Monitoring memory usage...
                
                :: Display memory usage
                echo.
                echo Memory usage:
                powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object @{Name='TotalMemory_MB';Expression={[math]::Round($_.TotalVisibleMemorySize/1KB,2)}}, @{Name='FreeMemory_MB';Expression={[math]::Round($_.FreePhysicalMemory/1KB,2)}}, @{Name='UsedMemory_MB';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/1KB,2)}}, @{Name='MemoryUsage_Percent';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100,2)}} | Format-Table -AutoSize"
                
                :: Display processes by memory usage
                echo.
                echo Top memory consumers:
                powershell -Command "Get-Process | Sort-Object -Property WorkingSet -Descending | Select-Object -First 10 Name, @{Name='Memory (MB)';Expression={[math]::Round($_.WorkingSet/1MB,2)}}, CPU, ID | Format-Table -AutoSize"
            ) else if defined monitor_system (
                :: Full system monitoring
                echo Monitoring system resources...
                
                :: Display top CPU-consuming processes
                echo.
                echo Top CPU consumers:
                powershell -Command "Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet, ID | Format-Table -AutoSize"
                
                :: Display memory usage
                echo.
                echo Memory usage:
                powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object @{Name='TotalMemory_MB';Expression={[math]::Round($_.TotalVisibleMemorySize/1KB,2)}}, @{Name='FreeMemory_MB';Expression={[math]::Round($_.FreePhysicalMemory/1KB,2)}}, @{Name='UsedMemory_MB';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/1KB,2)}}, @{Name='MemoryUsage_Percent';Expression={[math]::Round(($_.TotalVisibleMemorySize-$_.FreePhysicalMemory)/$_.TotalVisibleMemorySize*100,2)}} | Format-Table -AutoSize"
                
                :: Display CPU usage
                echo.
                echo CPU usage:
                powershell -Command "$CPU = (Get-Counter '\Processor(_Total)\%% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue; Write-Host ('CPU usage: {0:N2}%%' -f $CPU)"
                
                :: Optional: open Task Manager for continuous monitoring
                echo.
                echo To see continuous updates, opening Task Manager...
                start taskmgr
            ) else (
                :: For all other commands, pass to the Python script
                echo Running command: %*
                python "%AGENT_SCRIPT%" --execute "%*"
            )
        ) else (
            :: For all other commands, pass to the Python script
            echo Running command: %*
            python "%AGENT_SCRIPT%" --execute "%*"
        )
    )
)

:: Return the error code from Python
exit /b %ERRORLEVEL%
