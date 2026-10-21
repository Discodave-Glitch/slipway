@echo off
setlocal
cd /d "%~dp0"
title Slipway setup
echo.
echo   SLIPWAY - setup
echo   ===============
echo.

rem ---- 1. find Python 3.10 or newer -------------------------------------------------
set "PY="
where py >nul 2>nul
if %errorlevel%==0 (
    rem prefer 3.12 / 3.11: the MIDI library has ready-made builds for them (not always for the newest Python)
    for %%V in (3.12 3.11 3.13) do if not defined PY (
        py -%%V -c "import sys" >nul 2>nul
        if not errorlevel 1 set "PY=py -%%V"
    )
)
if not defined PY where py >nul 2>nul
if not defined PY if %errorlevel%==0 (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
    where python >nul 2>nul
    if %errorlevel%==0 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
        if not errorlevel 1 set "PY=python"
    )
)
if not defined PY goto :nopython

rem ---- 2. check tkinter (the window toolkit) ----------------------------------------
%PY% -c "import tkinter" >nul 2>nul
if errorlevel 1 goto :notk

rem ---- 2b. make the firmware folder now, before Slipway is ever started ----------------
if not exist "%~dp0firmware" mkdir "%~dp0firmware"
if exist "%~dp0firmware" echo   Firmware folder ready: %~dp0firmware
if not exist "%~dp0firmware" echo   Could not make the firmware folder here. Slipway will keep its downloads in your settings folder instead.
echo.

rem ---- 3. the two MIDI libraries the installer needs --------------------------------
echo   Installing the MIDI libraries (mido, python-rtmidi)...
%PY% -m pip install --disable-pip-version-check mido python-rtmidi
if errorlevel 1 (
    echo.
    echo   The MIDI libraries did not install. Slipway will still start, and will offer to
    echo   try again the first time you press "Launch on FM-1". Continuing.
)
echo.

rem ---- 4. shortcuts with the Slipway logo -------------------------------------------
set "PYW="
for /f "usebackq delims=" %%I in (`%PY% -c "import sys,os; print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))"`) do set "PYW=%%I"
if not exist "%PYW%" (
    echo   Could not find pythonw.exe, so no shortcut was made. Use run_slipway.bat instead.
    goto :done
)
set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

echo   Making shortcuts (Desktop and Start menu) with the Slipway logo...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell; $dirs=@([Environment]::GetFolderPath('Desktop'), (Join-Path ([Environment]::GetFolderPath('Programs')) '')); foreach($d in $dirs){ if(Test-Path $d){ $s=$w.CreateShortcut((Join-Path $d 'Slipway.lnk')); $s.TargetPath='%PYW%'; $s.Arguments='-m slipway'; $s.WorkingDirectory='%HERE%'; $s.IconLocation='%HERE%\slipway\slipway.ico'; $s.Description='Launch custom firmware onto your M-VAVE FM-1'; $s.Save() } }"
if errorlevel 1 (
    echo   The shortcuts could not be made. Use run_slipway.bat instead.
) else (
    echo   Done. Look for "Slipway" on your Desktop and in the Start menu.
)

:done
echo.
echo   Setup finished. Starting Slipway...
start "" "%PYW%" -m slipway
echo.
pause
exit /b 0

:nopython
echo   Slipway needs Python 3.10 or newer, and it was not found.
echo.
echo   1. Download Python from https://www.python.org/downloads/ (the big yellow button).
echo   2. Open the installer. On its FIRST screen, at the bottom, tick the box
echo      "Add python.exe to PATH". It is not ticked by default, and Slipway cannot
echo      find Python without it. Then click "Install Now".
echo   3. Close the installer, then double-click install.bat again.
echo.
echo   Already installed Python but forgot the box? Run the Python installer again,
echo   choose "Modify", click Next, and tick "Add Python to environment variables".
echo.
pause
exit /b 1

:notk
echo   Your Python has no tkinter (the window toolkit). Re-run the Python installer,
echo   choose Modify, and tick "tcl/tk and IDLE". Then run install.bat again.
echo.
pause
exit /b 1
