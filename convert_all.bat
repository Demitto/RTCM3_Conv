@echo off
setlocal
py -3 "%~dp0convert_rtcm3_to_rinex.py" %*
if errorlevel 1 pause
