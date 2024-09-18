@echo off
setlocal enabledelayedexpansion
set serverLocation="C:\DayZServer/resources"
set serverPort=2302
set serverConfig=serverDZ.cfg
set serverCPU=2
set modList=
title DayZ Server batch
cd "%serverLocation%"

:start
:: Clear the mod list to avoid duplication
set "modList="

:: Extract server name from serverDZ.cfg
for /f "tokens=2 delims==" %%a in ('findstr /i "hostname" %serverConfig%') do (
    set "serverName=%%a"
    set "serverName=!serverName:~1,-1!"  :: Remove leading and trailing quotes
)

:: Remove any remaining quotes from the server name
set serverName=%serverName:"=%

:: Set the title of the command prompt window to the server name
title %serverName%

:: Output the server name for testing
echo Loading %serverName%

:: Read mods from mods.txt and build the mod list
for /f "delims=" %%a in (mods.txt) do (
    set "modList=!modList!;%%a"
)

:: Remove the leading semicolon from the mod list
set modList=%modList:~1%

:: Output the mod list for testing
echo Mod List:
echo %modList%

:: Confirm with the user before starting the server
echo Do you want to start the server with the above mod list? (Y/N)
set /p startServer=
if /i "%startServer%" neq "Y" (
    echo Server start cancelled.
    exit /b
)

echo (%time%) %serverName% started.
start "DayZ Server" /min "DayZServer_x64.exe" -profiles=Profiles "-mod=%modList%" -config=%serverConfig% -port=%serverPort% -cpuCount=%serverCPU% -dologs -adminlog -netlog -freezecheck

:: Wait for user input to stop the server
echo Press Enter to stop the server...
pause >nul

:: Confirm before killing the task
echo Are you sure you want to stop the server? (Y/N)
set /p stopServer=
if /i "%stopServer%" neq "Y" (
    echo Server stop cancelled.
    exit /b
)

:: Output exit message
echo Exiting server...

:: Terminate the DayZ server process
taskkill /im DayZServer_x64.exe /F

:: Wait a moment before restarting
timeout /t 5

:: Ask if the user wants to restart the batch file
echo Do you want to restart the batch file? (Y/N)
set /p restartBatch=
if /i "%restartBatch%" equ "Y" (
    goto start
) else (
    echo Batch file exit.
    exit /b
)
