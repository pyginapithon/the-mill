# mill: register mill-wall Windows SERVICE (Admin/UAC).
# WinGet/MSI packages leave binaries only - packages are not services.
# mill-wall is a Windows SERVICE (sc create), not ONLOGON schtasks powershell.
# Launch Hidden + auto-exit. Do not leave a console - closing it must not be a human step.
# 0.4 mill-wall is FastAPI. MySQL84 start only if mill's book is already there.
$ErrorActionPreference = "Continue"
Write-Host "HUMAN: packages != services. Registering mill-wall SCM (Admin required)."
$mysqld = Get-Command mysqld.exe -ErrorAction SilentlyContinue
if ($mysqld) {
  $dataDir = Join-Path $env:ProgramData "MySQL\MySQL Server 8.4\Data"
  if (-not (Test-Path $dataDir)) {
    & $mysqld.Source --initialize-insecure
  }
  & $mysqld.Source --install MySQL84
  Write-Host "MySQL84: set root password to mill default (config password) after first start."
} else {
  Write-Host "mysqld.exe not on PATH; install MySQL via winget/MSI first."
}
# mill-wall Windows SERVICE (nssm-free). 0.4: HTTPS 443, Wall + mill API + /ws. Not nginx. Not 8765.
$svc = 'mill-wall'
$binPath = 'python -m agent_coord.server.win_wall_svc --bind 0.0.0.0 --port 443 --no-api-only'
$q = sc.exe query $svc 2>&1
if ($LASTEXITCODE -ne 0) {
  sc.exe create $svc binPath= $binPath start= auto DisplayName= "mill-wall" | Out-Null
  sc.exe description $svc "mill-wall HTTPS 443 (FastAPI/uvicorn; Wall + mill API + Hub /ws)" | Out-Null
  sc.exe failure $svc reset= 86400 actions= restart/5000/restart/5000/restart/5000 | Out-Null
  Write-Host "sc create mill-wall SERVICE"
} else {
  sc.exe config $svc binPath= $binPath start= auto | Out-Null
  Write-Host "sc config mill-wall SERVICE"
}
schtasks /Delete /TN mill-wall /F 2>$null | Out-Null
sc.exe start MySQL84 2>$null | Out-Null
sc.exe start mill-wall 2>$null | Out-Null
Write-Host "SCM: mill-wall SERVICE (MySQL84 started if present)"
Write-Host "Done. Helper auto-exit."
exit 0
