@echo off
setlocal EnableDelayedExpansion

rem Copies the HEV suit sounds from your Half-Life install into hl1-sounds\.
rem
rem Usage: extract_hl_sounds.bat ["path\to\Half-Life"]
rem With no path, the default Steam folder is used.

set "HL_DIR=%~1"
if not defined HL_DIR set "HL_DIR=%ProgramFiles(x86)%\Steam\steamapps\common\Half-Life"

set "SRC=%HL_DIR%\valve\sound\fvox"
set "DEST=%~dp0hl1-sounds"

set "FILES=bell time_is_now am pm hours minutes _comma _period"
set "FILES=%FILES% one two three four five six seven eight nine ten"
set "FILES=%FILES% eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen"
set "FILES=%FILES% twenty twentyfive thirty fourty fifty sixty seventy eighty ninety onehundred"

if not exist "%SRC%\time_is_now.wav" (
    echo Could not find the Half-Life HEV suit sounds in:
    echo   !SRC!
    echo.
    echo Pass the folder Half-Life is installed in, for example:
    echo   %~nx0 "D:\SteamLibrary\steamapps\common\Half-Life"
    exit /b 1
)

if not exist "%DEST%" mkdir "%DEST%" || exit /b 1

set COPIED=0
set MISSING=0
for %%F in (%FILES%) do (
    if exist "!SRC!\%%F.wav" (
        copy /y "!SRC!\%%F.wav" "!DEST!\" >nul && (
            set /a COPIED+=1
        ) || (
            echo Failed to copy: %%F.wav
            set /a MISSING+=1
        )
    ) else (
        echo Missing: %%F.wav
        set /a MISSING+=1
    )
)

rem There is no "oh" sound, so cut one from "overload".
rem Bypass lets the script run on machines that block .ps1 files by default.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0cut_oh.ps1" -Source "%SRC%\powermove_overload.wav" -OutFile "%DEST%\oh.wav" >nul
if errorlevel 1 (
    echo Failed to make: oh.wav
    set /a MISSING+=1
) else (
    set /a COPIED+=1
)

echo Saved %COPIED% files to %DEST%
if %MISSING% gtr 0 (
    echo %MISSING% files could not be copied.
    exit /b 1
)
exit /b 0
