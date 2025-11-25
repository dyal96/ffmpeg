@echo off
setlocal enabledelayedexpansion

:: ---------------------------
:: Select Video File (GUI)
:: ---------------------------
echo Select Video File...
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.OpenFileDialog; $f.Filter='Video Files (*.mp4;*.mkv;*.mov)|*.mp4;*.mkv;*.mov|All Files (*.*)|*.*'; if($f.ShowDialog() -eq 'OK'){ Write-Output $f.FileName }"`) do (
    set "vid=%%i"
)

if "%vid%"=="" (
    echo No video selected. Exiting.
    pause
    exit /b
)

:: Get video folder and base name
for %%F in ("%vid%") do (
    set "vid_folder=%%~dpF"
    set "vid_name=%%~nF"
)

:: Trim possible trailing backslash issues (optional)
rem if the folder doesn't already end with \, ensure it does (it should from %%~dpF)
:: ---------------------------
:: Select Audio File (GUI)
:: ---------------------------
echo.
echo Select Audio File...
for /f "usebackq delims=" %%j in (`powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $f=New-Object System.Windows.Forms.OpenFileDialog; $f.Filter='Audio Files (*.m4a;*.mp3;*.wav)|*.m4a;*.mp3;*.wav|All Files (*.*)|*.*'; if($f.ShowDialog() -eq 'OK'){ Write-Output $f.FileName }"`) do (
    set "aud=%%j"
)

if "%aud%"=="" (
    echo No audio selected. Exiting.
    pause
    exit /b
)

:: ---------------------------
:: Create AV Videos folder next to the input video
:: ---------------------------
set "outfolder=%vid_folder%AV Videos"
if not exist "%outfolder%" mkdir "%outfolder%"

:: ---------------------------
:: Output filename: videoName_combined.mp4
:: ---------------------------
set "output=%outfolder%\%vid_name%_combined.mp4"

:: ---------------------------
:: Run ffmpeg merge (copy streams)
:: ---------------------------
echo.
echo Merging:
echo Video: "%vid%"
echo Audio: "%aud%"
echo Output: "%output%"
echo.

ffmpeg -y -i "%vid%" -i "%aud%" -c:v copy -c:a copy "%output%"

if errorlevel 1 (
    echo.
    echo ERROR: ffmpeg reported a problem.
) else (
    echo.
    echo ------------------------------------------
    echo ✔ Merge completed!
    echo Saved as: %output%
    echo ------------------------------------------
)

pause
