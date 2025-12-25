@echo off
if "%1"=="--help" goto :help

where pyinstaller >nul 2>nul
if errorlevel 1 (
  echo pyinstaller not found. Install with: pip install pyinstaller
  exit /b 1
)

set NAME=ARCS

echo Building %NAME% (using spec at data\ARCS.spec) ...
pushd ..
pyinstaller data\ARCS.spec
if errorlevel 1 (
  echo Build failed
  popd
  exit /b 1
)
popd
echo Build succeeded. See dist\%NAME%\%NAME%.exe

goto :eof
:help
echo Usage: windowsBuild.bat [--help]
echo Builds a Windows one-file app using PyInstaller. Run on Windows.