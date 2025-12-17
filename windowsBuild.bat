@echo off
if "%1"=="--help" goto :help

where pyinstaller >nul 2>nul
if errorlevel 1 (
  echo pyinstaller not found. Install with: pip install pyinstaller
  exit /b 1
)

set NAME=ARCS

echo Building %NAME% ...
pyinstaller --onefile --noconsole --name %NAME% --icon=data/app.ico --add-data "data;data" arcs.py
if errorlevel 1 (
  echo Build failed
  exit /b 1
)
echo Build succeeded. See dist\%NAME%.exe

goto :eof
:help
echo Usage: windowsBuild.bat [--help]
echo Builds a Windows one-file app using PyInstaller. Run on Windows.