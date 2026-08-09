@echo off
setlocal enabledelayedexpansion
set PYTHONUTF8=1
title plagTalk - Build
cd /d "%~dp0"

echo.
echo  ============================================
echo   plagTalk ^| Build Script
echo  ============================================
echo.

pip install pyttsx3 pywin32 requests pyinstaller -q

pyinstaller ^
  --name plagTalk ^
  --icon icon.png ^
  --windowed ^
  --onefile ^
  --add-data "icon.png;." ^
  --add-data "version.json;." ^
  --hidden-import pyttsx3.drivers ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  --hidden-import win32com ^
  --hidden-import win32com.client ^
  --hidden-import pythoncom ^
  -y ^
  app.py

if errorlevel 1 (
    echo.
    echo  BUILD FAILED.
    pause & exit /b 1
)

:: Read version from updater.py and leave a versioned copy for release.bat to find
for /f "tokens=3 delims= " %%v in ('findstr /r "^APP_VERSION" updater.py') do set RAWVER=%%v
set VERSION=!RAWVER:"=!

set SRC=dist\plagTalk.exe
set VERSIONED=dist\plagTalk-!VERSION!.exe

if exist "%SRC%" (
    copy /y "%SRC%" "!VERSIONED!" >nul
    echo.
    echo  Output   : dist\plagTalk.exe
    echo  Versioned : !VERSIONED!
    echo.
    echo  Run release.bat to publish to GitHub.
) else (
    echo  ERROR: dist\plagTalk.exe not found after build.
    pause & exit /b 1
)

echo.
pause
endlocal
