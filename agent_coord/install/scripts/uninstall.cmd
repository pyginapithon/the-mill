@echo off
REM mill Windows OOTB cleanup front door (agent runs this; not Admin paste).
REM Human Admin window stays (pause + prompt). Agent: MILL_AGENT=1 or --agent (no pause).
REM Agent-visible console (do NOT hide the whole run). Silent CLI; no wizards.
REM Pass-through: --dest (wipe office dest). mill-wall SERVICE always.
setlocal EnableExtensions
set "MILL_ROOT=%~dp0.."
for %%A in (%*) do if /I "%%~A"=="--agent" set MILL_AGENT=1
pushd "%MILL_ROOT%" >nul

echo mill uninstall.cmd: probe-first cleanup (mill-wall SERVICE; dest with --dest).
echo   flags: %*

where mill >nul 2>&1
if not errorlevel 1 (
  echo   mill: OK - mill uninstall --apply %*
  mill uninstall --apply %*
  set "RC=%ERRORLEVEL%"
  goto stay
)

python -c "import agent_coord" >nul 2>&1
if not errorlevel 1 (
  echo   mill: via python -m agent_coord uninstall --apply %*
  python -m agent_coord uninstall --apply %*
  set "RC=%ERRORLEVEL%"
  goto stay
)

echo   mill: missing - standalone uninstall.ps1 (no mill required)
set "PS1=%~dp0uninstall.ps1"
if not exist "%PS1%" (
  echo HUMAN: uninstall.ps1 missing and mill not installed. pip install the-mill then re-run.
  set "RC=1"
  goto stay
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
set "RC=%ERRORLEVEL%"

:stay
popd
if defined MILL_AGENT (
  echo mill uninstall.cmd: done
  endlocal & exit /b %RC%
)
echo mill uninstall.cmd: done. This window stays.
echo HUMAN: press a key to keep this Admin prompt.
pause
cmd /k
