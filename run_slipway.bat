@echo off
cd /d "%~dp0"
if not exist "%~dp0firmware" mkdir "%~dp0firmware"
start "" pythonw -m slipway
