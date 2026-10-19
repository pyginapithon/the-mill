# mill: unregister mill-wall Windows SERVICE (Admin/UAC).
# Already Admin: do the work in this window (no re-elevate).
# Unelevated / double-click: Hidden Start-Process then exit 0.
# mill-wall SERVICE only. Dest wipe only with -Dest.
# Stop+delete mill-wall SERVICE and leftover mill-wall schtask.
# Do NOT uninstall Python. Dest wipe only with -Dest.
param(
  [switch]$Dest,
  [string]$DestPath = "",
  [switch]$Packages
)
$ErrorActionPreference = "Continue"
Write-Host "HUMAN: mill uninstall SCM (Admin). In-window if already Admin; else Hidden auto-exit."
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) {
  $arg = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`""
  if ($Dest) { $arg += " -Dest" }
  if ($DestPath) { $arg += " -DestPath `"$DestPath`"" }
  if ($Packages) { $arg += " -Packages" }
  Start-Process powershell -Verb RunAs -WindowStyle Hidden -Wait -ArgumentList $arg
  exit 0
}
schtasks /End /TN mill-wall /F 2>$null | Out-Null
schtasks /Delete /TN mill-wall /F 2>$null | Out-Null
foreach ($svc in @('mill-wall')) {
  $q = sc.exe query $svc 2>&1
  if ($LASTEXITCODE -eq 0) {
    sc.exe stop $svc 2>$null | Out-Null
    sc.exe delete $svc 2>$null | Out-Null
    Write-Host "sc stop+delete $svc"
  }
}
if ($Dest -and $DestPath) {
  if (Test-Path -LiteralPath $DestPath) {
    Remove-Item -LiteralPath $DestPath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "wiped dest $DestPath"
  }
}
if ($Packages) { Write-Host "0.4: mill uninstall is mill-wall + dest" }
Write-Host "Done. Helper auto-exit."
exit 0
