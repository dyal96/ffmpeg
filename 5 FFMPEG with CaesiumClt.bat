@echo off
setlocal EnableDelayedExpansion

:: ==== SETTINGS ====
set duration=5
set fade_duration=1
set fps=24
set bitrate=8000k
set jpeg_quality=85

:: ==== PATHS (Use absolute paths to avoid drive errors) ====
set "script_dir=%~dp0"
set "ffmpeg_exe=%~dp0ffmpeg.exe"
set "caesium_exe=%~dp0caesiumclt.exe"

:: Create a local temp folder to avoid drive issues
set "workdir=%~dp0temp_processing_%RANDOM%"

:: ==== CHECK TOOLS ====
if not exist "%ffmpeg_exe%" (
    color 0C
    echo [ERROR] ffmpeg.exe not found in: "%script_dir%"
    pause
    exit /b
)

set use_caesium=true
if not exist "%caesium_exe%" (
    echo [WARNING] caesiumclt.exe not found. Optimization disabled.
    set use_caesium=false
)

:: ==== RESOLUTION SETUP ====
echo Select video orientation:
echo [1] Horizontal (1920x1080)
echo [2] Vertical   (1080x1920)
set /p resChoice="Enter choice [1 or 2]: "

if "%resChoice%"=="2" (
    set "width=1080"
    set "height=1920"
) else (
    set "width=1920"
    set "height=1080"
)
set "resolution=%width%:%height%"

:: ==== SETUP FOLDERS ====
if not exist "%workdir%" mkdir "%workdir%"
if not exist "%workdir%\raw_caesium" mkdir "%workdir%\raw_caesium"
set "outputdir=%script_dir%Generated_Videos"
if not exist "%outputdir%" mkdir "%outputdir%"

set outputname=Video_%RANDOM%.mp4

:: ==== PROCESS IMAGES ====
echo.
echo ---------------------------------------
echo [STEP 1] Processing Images...
echo ---------------------------------------

set i=0
for %%F in (%*) do (
    set "input_file=%%~fF"
    set "temp_file=%workdir%\img!i!.jpg"
    set "processed=false"

    echo Processing: %%~nF

    :: 1. Try Caesium
    if "!use_caesium!"=="true" (
        :: Removed ">nul" so you can see if Caesium throws an error
        "%caesium_exe%" -q %jpeg_quality% -o "%workdir%\raw_caesium" --width %width% --height %height% "%%~fF"
        
        :: Caesium keeps original filename. We look for it and rename/move it.
        if exist "%workdir%\raw_caesium\%%~nF.jpg" (
            move /y "%workdir%\raw_caesium\%%~nF.jpg" "!temp_file!" >nul
            set "processed=true"
        ) else if exist "%workdir%\raw_caesium\%%~nxF" (
            move /y "%workdir%\raw_caesium\%%~nxF" "!temp_file!" >nul
            set "processed=true"
        )
    )

    :: 2. Fallback Copy
    if "!processed!"=="false" (
        copy "%%~fF" "!temp_file!" >nul
        if errorlevel 1 (
            echo [ERROR] Could not copy file: %%~fF
        )
    )
    
    set /a i+=1
)
set /a count=i

:: ==== GENERATE CLIPS ====
echo.
echo ---------------------------------------
echo [STEP 2] Creating Video Clips...
echo ---------------------------------------

set j=0
:generate_clips
if !j! GEQ %count% goto combine_clips

set "clip_in=%workdir%\img!j!.jpg"
set "clip_out=%workdir%\clip!j!.mp4"

:: Filter: Format=rgb24 fixes the CMYK color crash
set "scalefilter=format=rgb24,scale=%resolution%:force_original_aspect_ratio=decrease,pad=%resolution%:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,format=yuv420p"
set /a clip_duration=%duration% + %fade_duration%

"%ffmpeg_exe%" -v error -y -loop 1 -t !clip_duration! -i "!clip_in!" -vf "!scalefilter!" -r %fps% -c:v libx264 -b:v %bitrate% -preset veryfast "!clip_out!"

set /a j+=1
goto generate_clips

:combine_clips
echo.
echo ---------------------------------------
echo [STEP 3] Finalizing...
echo ---------------------------------------

:: Build inputs logic
set "inputs="
set "filters="
set /a total=%count%-1

for /L %%i in (0,1,%total%) do (
    set "inputs=!inputs! -i "%workdir%\clip%%i.mp4""
    set "filters=!filters![%%i:v]scale=%resolution%,setsar=1[v%%i];"
)

:: Build crossfades
set "xfades="
set /a offset=%duration% - %fade_duration%
set "prev=v0"

if %count% GTR 1 (
    for /L %%i in (1,1,%total%) do (
        set "xfades=!xfades![!prev!][v%%i]xfade=transition=fade:duration=%fade_duration%:offset=!offset![x%%i];"
        set /a offset+=%duration%
        set "prev=x%%i"
    )
    set "filtergraph=!filters!!xfades!"
) else (
    set "filtergraph=!filters!"
)

set "final_map=-map [!prev!]"
set /a total_duration=(%count% * (%duration% + %fade_duration%)) - (%fade_duration% * (%count%-1))

:: Final Render
"%ffmpeg_exe%" -v error -y !inputs! -f lavfi -t %total_duration% -i anullsrc=r=44100:cl=stereo -filter_complex "!filtergraph!" !final_map! -map %count%:a -shortest -r %fps% -c:v libx264 -pix_fmt yuv420p -b:v %bitrate% -preset veryfast -c:a aac -movflags +faststart "%outputdir%\%outputname%"

echo.
echo Done! Video is in: 
echo "%outputdir%\%outputname%"

:: Cleanup
rmdir /s /q "%workdir%"

pause
exit