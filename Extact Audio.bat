@echo off
setlocal enabledelayedexpansion

:: Check if file was dragged
if "%~1"=="" (
    echo Drag and drop a video file onto this .BAT file.
    pause
    exit /b
)

:: Input file full path
set "input=%~1"

:: Create output folder
set "outfolder=%~dp0Extracted Audio"
if not exist "%outfolder%" mkdir "%outfolder%"

:: Extract filename without extension
set "name=%~n1"

:: Output file path
set "output=%outfolder%\%name%.mp3"

echo Extracting audio...
ffmpeg -i "%input%" -vn -loglevel error "%output%"

echo.
echo ✔ Audio Extracted!
echo Saved to:
echo %output%
echo.
pause
