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

REM Detect if repo path is under OneDrive; if so, build using temporary folders in %%TEMP%% to avoid permission/sync conflicts
set PROJECT_DIR=%CD%
set USE_TEMP=0
echo %PROJECT_DIR% | findstr /I "OneDrive" >nul
if %errorlevel%==0 (
  set USE_TEMP=1
)

if %USE_TEMP%==1 (
  set WORKPATH=%TEMP%\pyi_work_%NAME%
  set DISTPATH=%TEMP%\pyi_dist_%NAME%
  if not exist "%WORKPATH%" mkdir "%WORKPATH%"
  if not exist "%DISTPATH%" mkdir "%DISTPATH%"
  echo Detected OneDrive repository path; building in temporary folders:
  echo   workpath: "%WORKPATH%"
  echo   distpath: "%DISTPATH%"
) else (
  set WORKPATH=
  set DISTPATH=
)

REM Default: use the .spec file for builds (ensures data/ARCS.spec is used and ReportLab is collected)
REM Pass --script to build using arcs.py instead (script-based build uses --onedir --noupx)
if "%1"=="--script" (
  if "%USE_TEMP%"=="1" (
    pyinstaller --onedir --noupx --workpath "%WORKPATH%" --distpath "%DISTPATH%" arcs.py
  ) else (
    pyinstaller --onedir --noupx arcs.py
  )
) else (
  if "%USE_TEMP%"=="1" (
    pyinstaller --workpath "%WORKPATH%" --distpath "%DISTPATH%" data\ARCS.spec
  ) else (
    pyinstaller data\ARCS.spec
  )
)
if errorlevel 1 (
  echo Build failed
  popd
  exit /b 1
)

REM Post-build diagnostics: if built in temp, attempt to copy artifacts back to repo; otherwise run original checks
if "%USE_TEMP%"=="1" (
  if exist "%DISTPATH%\%NAME%" (
    echo Build produced "%DISTPATH%\%NAME%"; attempting to copy to repo dist\%NAME% ...
    if not exist dist mkdir dist
    xcopy /E /I /Y "%DISTPATH%\%NAME%" "dist\%NAME%\" >nul 2>&1
    if errorlevel 1 (
      echo Could not copy artifacts back to repo; artifacts remain in "%DISTPATH%\%NAME%".
    ) else (
      echo Artifacts copied to dist\%NAME%.
    )
  ) else (
    echo Temporary dist not found: "%DISTPATH%\%NAME%".
  )

  echo Checking for python DLLs in temporary dist...
  dir /b "%DISTPATH%\%NAME%\python*.dll" >nul 2>&1
  if errorlevel 1 (
    dir /b dist\%NAME%\python*.dll >nul 2>&1
  )
) else (
  REM non-temp path, check original dist
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
)

popd
if "%USE_TEMP%"=="1" (
  if exist dist\%NAME% (
    echo Build succeeded. See dist\%NAME%\%NAME%.exe
  ) else (
    echo Build succeeded. Artifacts are at "%DISTPATH%\%NAME%"
  )
) else (
  echo Build succeeded. See dist\%NAME%\%NAME%.exe
)

goto :eof
:help
echo Usage: windowsBuild.bat [--help] [--script]
echo Builds using data\ARCS.spec by default (includes ReportLab and other collected data).
echo Use --script to build directly from arcs.py with --onedir --noupx.