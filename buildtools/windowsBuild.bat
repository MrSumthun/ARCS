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
REM If caller passes --spec, build using the .spec file; otherwise use --onedir + --noupx on the script
if "%1"=="--spec" (
  pyinstaller data\ARCS.spec
) else (
  pyinstaller --onedir --noupx arcs.py
)
if errorlevel 1 (
  echo Build failed
  popd
  exit /b 1
)

REM Post-build diagnostics: check for python DLLs in the output and try copying from the current Python if missing
if exist dist\%NAME% (
  echo Build produced dist\%NAME%; checking for python DLLs...
  dir /b dist\%NAME%\python*.dll >nul 2>&1
  if errorlevel 1 (
    echo No python DLLs found in dist\%NAME%. Attempting to copy from current Python install...
    for /f "delims=" %%p in ('python -c "import sys,glob,os;print(os.linesep.join(glob.glob(os.path.join(sys.base_prefix, 'python*.dll'))))"') do copy "%%p" "dist\%NAME%\" >nul 2>&1
    echo After copy, listing files:
  )
  dir /b dist\%NAME%\python*.dll || echo No python DLLs present
) else (
  echo dist\%NAME% not found
)

popd
echo Build succeeded. See dist\%NAME%\%NAME%.exe

goto :eof
:help
echo Usage: windowsBuild.bat [--help]
echo Builds a Windows one-file app using PyInstaller. Run on Windows.