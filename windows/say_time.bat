@echo off
rem Writes the current time to current_time.wav.
rem
rem Usage: say_time.bat [-Time "10:47 PM"] [-OutFile file.wav] [-GapMs 100]

rem Bypass lets the script run on machines that block .ps1 files by default.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0say_time.ps1" %*
exit /b %ERRORLEVEL%
