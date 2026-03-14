@echo off
echo ============================================
echo   TypeGuard — Build Standalone Executable
echo ============================================
echo.

REM Install PyInstaller if not present
pip install pyinstaller

echo.
echo Building TypeGuard.exe ...
echo.

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --noconsole ^
    --name TypeGuard ^
    --add-data "typeguard\assets\templates\dashboard.html;typeguard\assets\templates" ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --hidden-import pystray._win32 ^
    --hidden-import typeguard.install ^
    typeguard\main.py

echo.
if exist "dist\TypeGuard.exe" (
    echo ============================================
    echo   BUILD SUCCESSFUL!
    echo ============================================
    echo.
    echo   Your executable is at: dist\TypeGuard.exe
    echo.
    echo   HOW TO USE:
    echo     1. Double-click TypeGuard.exe to run
    echo     2. TypeGuard.exe --install   (set up auto-start, needs Admin)
    echo     3. TypeGuard.exe --uninstall (remove auto-start)
    echo.
    echo   SHARE WITH FRIENDS:
    echo     Just send them the TypeGuard.exe file!
    echo     They double-click to run, right-click --install for auto-start.
) else (
    echo ============================================
    echo   BUILD FAILED
    echo ============================================
    echo   Check the output above for errors.
)
echo.
pause
