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
echo   1. Get it from https://www.python.org/downloads/
echo   2. Run the installer and tick "Add python.exe to PATH" (and leave "tcl/tk" ticked).
echo   3. Run install.bat again.
echo.
pause
exit /b 1

:notk
echo   Your Python has no tkinter (the window toolkit). Re-run the Python installer,
echo   choose Modify, and tick "tcl/tk and IDLE". Then run install.bat again.
echo.
pause
exit /b 1
