@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Drag and drop a video file onto this script.
    pause
    exit /b
)

set "input=%~1"
set "filename=%~n1"

echo Input file: %input%
echo.

set /p targetSizeMB=Enter target size (in MB): 

if "%targetSizeMB%"=="" (
    echo Invalid size.
    pause
    exit /b
)

:: Get duration in seconds using ffprobe
for /f "delims=" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%input%"') do set duration=%%a

:: Remove decimal part
for /f "tokens=1 delims=." %%a in ("%duration%") do set durationSec=%%a

if "%durationSec%"=="" (
    echo Failed to detect duration.
    pause
    exit /b
)

:: Convert MB to bits
set /a targetSizeBits=%targetSizeMB%*8388608

:: Reserve 128 kbps for audio
set /a audioBitrate=128000

:: Calculate video bitrate
set /a videoBitrate=(targetSizeBits/durationSec)-audioBitrate

if %videoBitrate% LEQ 0 (
    echo Target size too small.
    pause
    exit /b
)

set "output=%~dp1%filename%_compress_%targetSizeMB%mb.mp4"

echo.
echo Duration: %durationSec% seconds
echo Video bitrate: %videoBitrate% bps
echo Output: %output%
echo.

ffmpeg -y -i "%input%" -c:v libx264 -b:v %videoBitrate% -preset medium -c:a aac -b:a 128k "%output%"

echo.
echo Done!
pause