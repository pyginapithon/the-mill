@echo off
REM mill Windows empty-machine front door. No Python required.
REM Agents: run this file as one process. Do not execute it line by line.
REM cmd /c "curl -fsSL https://raw.githubusercontent.com/si4ai/the-mill/main/scripts/install.cmd -o install.cmd && install.cmd --agent && del install.cmd"
REM Human Admin window stays (pause + prompt). Agent: MILL_AGENT=1 or --agent (no pause).
REM Unelevated: ONE Hidden elevate helper auto-exits. Do NOT hide this whole run.
setlocal EnableExtensions
set "HERE=%~dp0"
set "MILL_ROOT=%HERE%.."
for %%A in (%*) do if /I "%%~A"=="--agent" set MILL_AGENT=1

set "BOOT=%HERE%bootstrap.ps1"
if exist "%BOOT%" goto haveboot
echo mill install.cmd: fetching bootstrap.ps1 (one file, not line by line)
set "BOOT=%TEMP%\mill-bootstrap.ps1"
curl -fsSL "https://raw.githubusercontent.com/si4ai/the-mill/main/scripts/bootstrap.ps1" -o "%BOOT%"
if errorlevel 1 (
  echo HUMAN: could not download bootstrap.ps1
  set "RC=1"
  goto stay
)
:haveboot

echo mill install.cmd: probe Python 3.10+, mill, MySQL84, dest, mill-wall SERVICE
echo mill install.cmd: calling bootstrap.ps1 (visible). mill install server --apply is inside bootstrap.ps1. Silent winget Python/Oracle.MySQL /quiet /norestart if missing (--disable-interactivity). mill-wall is FastAPI.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%BOOT%" %*
if errorlevel 1 (
  echo HUMAN: bootstrap.ps1 failed.
  set "RC=1"
  goto stay
)

set "HELPER=%USERPROFILE%\.mill\register-windows-services.ps1"
if not exist "%HELPER%" set "HELPER=%USERPROFILE%\.mill\register-windows-services.ps1"
if not exist "%HELPER%" set "HELPER=%HERE%register-windows-services.ps1"
echo   helper: %HELPER%
net session >nul 2>&1
if not errorlevel 1 (
  echo mill install.cmd: already Admin - helper runs in THIS window (human window stays)
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%HELPER%"
) else (
  echo mill install.cmd: ONE Hidden elevate Wait auto-exit helper
  powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath powershell.exe -Verb RunAs -WindowStyle Hidden -Wait -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%HELPER%\"'"
)

echo mill install.cmd: share URL LAN-first (HTTPS). This PC localhost/127.0.0.1 trusted (mill CA). Other device may Advanced -^> Proceed; do not import wall.crt.
where python >nul 2>&1 && python -c "from agent_coord.install import share_wall_urls; print(chr(10).join(share_wall_urls()))" 2>nul
if errorlevel 1 echo https://127.0.0.1/
set "RC=0"

:stay
if defined MILL_AGENT (
  echo mill install.cmd: done
  endlocal
  exit /b %RC%
)
echo mill install.cmd: done. This window stays.
echo HUMAN: press a key to keep this Admin prompt.
pause
cmd /k
