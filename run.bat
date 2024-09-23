@echo off
setlocal enabledelayedexpansion
SET SERVERIP=YourServerIP
SET QUERYPORT=27016
set serverLocation="C:\DayZServer/resources"
set serverPort=2302
set serverConfig=serverDZ.cfg
set serverCPU=2
set modList=
title DayZ Server batch
cd "%serverLocation%"

python "C:\DayZServer\resources\buildtypes.py" 

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
echo Do you want to start the server with the above mod list? (Y/N) [Enter=Yes]
set /p startServer=
if /i "%startServer%"=="" set startServer=Y
if /i "%startServer%" neq "Y" (
    echo Server start cancelled.
    exit /b
)

ECHO (%time%) %serverName% started.
python "C:\DayZServer\resources\buildtypes.py" 

start "DayZ Server" /min "DayZServer_x64.exe" -profiles=Profiles -maxMem=2048 "-mod=%modList%" -config=%serverConfig% -port=%serverPort% -cpuCount=%serverCPU% -dologs -adminlog -netlog -freezecheck

:: Wait 3 minutes before querying the server
timeout /t 180 /nobreak

:: Query the server
ECHO Querying Server %SERVERIP%:%QUERYPORT%
powershell.exe -Command (new-object System.Net.WebClient).DownloadString('http://dayzsalauncher.com/api/v1/query/%SERVERIP%/%QUERYPORT%')

:: Wait for user input to stop the server
echo Press Enter to stop the server...
pause >nul

:: Confirm before killing the task
echo Are you sure you want to stop the server? (Y/N) [Enter=Yes]
set /p stopServer=
if /i "%stopServer%"=="" set stopServer=Y
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
echo Do you want to restart the batch file? (Y/N) [Enter=Yes]
set /p restartBatch=
if /i "%restartBatch%"=="" set restartBatch=Y
if /i "%restartBatch%" equ "Y" (
    goto start
) else (
    echo Batch file exit.
    exit /b
)
