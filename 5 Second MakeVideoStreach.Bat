@echo off
setlocal EnableDelayedExpansion

:: ==== SETTINGS ====
set duration=5
set fade_duration=1
set fps=24
set bitrate=8000k

:: ==== CHOOSE ORIENTATION ====
:choose_resolution
echo Select video orientation:
echo [1] Horizontal 4x2 (1920x1080)
echo [2] Vertical   2x4 (1080x1920)
echo [3] Vertical   3x4 (720x960)

set /p resChoice="Enter choice [1, 2 or 3]: "
if "%resChoice%"=="1" (
    set "resolution=1920:1080"
    set "resname=16x9_1920x1080"
) else if "%resChoice%"=="2" (
    set "resolution=1080:1920"
    set "resname=9x16_1080x1920"
) else if "%resChoice%"=="3" (
    set "resolution=720:960"
    set "resname=9x12_720x960"
) else (
    echo Invalid choice. Try again.
    goto choose_resolution
)

:: ==== CHOOSE STRETCH OPTION ====
echo.
echo Stretch images to fill the resolution (may distort aspect ratio)?
echo [2] No (default, fit with padding)
echo [1] Yes (stretch to fill)
set /p stretchChoice="Enter choice [1 or 2]: "
if "%stretchChoice%"=="2" (
    set "stretch=false"
) else (
    set "stretch=true"
)

:: ==== CHOOSE FORMAT ====
echo.
echo Select export format:
echo [1] MP4 (default)
echo [2] AVI
set /p formatChoice="Enter choice (1 or 2): "

if "%formatChoice%"=="2" (
    set "container=avi"
    set "vcodec=libx264"
    set "acodec=pcm_s16le"
) else (
    set "container=mp4"
    set "vcodec=libx264"
    set "acodec=aac"
)

:: ==== VALIDATE INPUT FILES ====
if "%~1"=="" (
    echo Drag and drop image files onto this batch file.
    pause
    exit /b
)

:: ==== PARSE FILE INFO ====
set "firstimg=%~f1"
set "firstimgname=%~n1"
set "outputdir=%~dp1Generated Videos"
mkdir "%outputdir%" >nul 2>&1

:: ==== GENERATE TIMESTAMP ====
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set mm=%%a
    set dd=%%b
    set yyyy=%%c
)
for /f "tokens=1-2 delims=:." %%x in ("%time%") do (
    set hh=%%x
    set min=%%y
)
set hh=%hh: =0%
set outputname=%resname%_%firstimgname%_%yyyy%%mm%%dd%_%hh%%min%.%container%

:: ==== SETUP TEMP WORKDIR ====
set "workdir=%TEMP%\fadevideo_%RANDOM%"
mkdir "%workdir%"
set i=0

:: ==== COPY IMAGES ====
for %%F in (%*) do (
    copy "%%~F" "%workdir%\img!i!.jpg" >nul
    set /a i+=1
)
set /a count=i

:: ==== CREATE CLIPS ====
echo.
echo 🎞️ Generating clips from images...
cd /d "%workdir%"
set j=0
:generate_clips
if !j! GEQ %count% goto combine_clips

if "!stretch!"=="true" (
    set "scalefilter=scale=%resolution%,setsar=1,format=yuv420p"
) else (
    set "scalefilter=scale=%resolution%:force_original_aspect_ratio=decrease,pad=%resolution%:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,format=yuv420p"
)

:: Extend clip duration by fade_duration
set /a clip_duration=%duration% + %fade_duration%
"%~dp0ffmpeg.exe" -y -loop 1 -t !clip_duration! -i "img!j!.jpg" -vf "!scalefilter!" -r %fps% -c:v %vcodec% -b:v %bitrate% -preset veryfast "clip!j!.mp4"
echo Created: clip!j!.mp4
set /a j+=1
goto generate_clips

:combine_clips
echo.
echo 🔄 Combining clips with crossfade...

:: ==== BUILD FILTERS ====
set "inputs="
set "filters="
set /a total=%count%-1
for /L %%i in (0,1,%total%) do (
    set "inputs=!inputs! -i clip%%i.mp4"
    set "filters=!filters![%%i:v]scale=%resolution%,setsar=1[v%%i];"
)

:: ==== BUILD XFADES ====
set "xfades="
set /a offset=%duration% - %fade_duration%
set "prev=v0"
for /L %%i in (1,1,%total%) do (
    set "xfades=!xfades![!prev!][v%%i]xfade=transition=fade:duration=%fade_duration%:offset=!offset![x%%i];"
    set /a offset+=%duration%
    set "prev=x%%i"
)

set "filtergraph=!filters!!xfades!"
set "final_map=-map [!prev!]"

:: ==== CALCULATE TOTAL LENGTH ====
:: Correct total duration formula to compensate fade extension
set /a total_duration=(%count% * (%duration% + %fade_duration%)) - (%fade_duration% * (%count%-1))

echo.
echo 🔈 Generating silent audio and final video...

:: ==== FINAL FFMPEG CALL ====
cmd /V /C ""%~dp0ffmpeg.exe"!inputs! -f lavfi -t %total_duration% -i anullsrc=r=44100:cl=stereo -filter_complex "!filtergraph!" !final_map! -map %count%:a -shortest -r %fps% -c:v %vcodec% -profile:v main -pix_fmt yuv420p -b:v %bitrate% -preset veryfast -c:a %acodec% -movflags +faststart "%outputdir%\%outputname%""


echo.
echo ✅ Done! Saved to:
echo "%outputdir%\%outputname%"

:: ==== CLEANUP ====
cd /d "%~dp0"
rd /s /q "%workdir%"

timeout 5
exit
