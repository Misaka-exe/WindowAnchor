@echo off
chcp 65001 >nul
title WindowAnchor Build Tool

echo ========================================
echo   WindowAnchor Build Tool
echo ========================================
echo.

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found!
    echo Please install Python 3.10 or later from https://python.org
    echo.
    pause
    exit /b 1
)
echo [OK] Python is ready.
echo.

echo [2/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    echo.
    pause
    exit /b 1
)
pip install pyinstaller
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install PyInstaller!
    echo.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

echo [3/4] Building EXE (may take 1-3 minutes)...
echo Please wait...
echo.
pyinstaller --clean WindowAnchor.spec
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
)
echo.
echo [OK] Build successful!
echo.

echo [4/4] Done!
echo.
echo Output file: dist\WindowAnchor.exe
echo.
for %%A in ("dist\WindowAnchor.exe") do echo File size: %%~zA bytes
echo.
echo You can now run dist\WindowAnchor.exe
echo.
pause
