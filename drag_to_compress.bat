@echo off
setlocal enabledelayedexpansion

REM Create output directory if it doesn't exist
mkdir "Compress files"

REM Loop through all dragged files
for %%F in (%*) do (
    if exist "%%~F" (
        set "fullpath=%%~F"
        set "filename=%%~nF"
        echo Compressing: %%~nxF
        ffmpeg -i "%%~F" -b:v 1000k -bufsize 1000k -c:a copy "Compress files\!filename!_compress.mp4"
    ) else (
        echo Skipped invalid file: %%~F
    )
)

echo Done!
pause
