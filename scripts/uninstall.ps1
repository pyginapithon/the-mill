# mill Windows OOTB cleanup (standalone; no mill required). Agent-visible console.
# Human Admin window stays (in-window helper). Agent leftover elevate helpers Hidden + auto-exit.
# Helper stops+deletes mill-wall SERVICE.
# leftover schtasks, leftover httpd -X / mysqld --console. Dest wipe / packages only if flags.
# Do not uninstall Python. Do not treat console as Pass.
param(
  [switch]$Dest,
  [switch]$Packages,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Rest
)
$ErrorActionPreference = "Continue"
Write-Host "mill uninstall.ps1: standalone cleanup (SCM)"

foreach ($a in @($Rest)) {
  if ($a -eq "--dest" -or $a -eq "-Dest") { $Dest = $true }
  if ($a -eq "--packages" -or $a -eq "-Packages") { $Packages = $true }
}

$here = $PSScriptRoot
$helper = Join-Path $here "unregister-windows-services.ps1"
if (-not (Test-Path $helper)) {
  $cand = Join-Path $env:USERPROFILE ".mill\unregister-windows-services.ps1"
  if (Test-Path $cand) { $helper = $cand }
}
if (-not (Test-Path $helper)) {
  Write-Host "HUMAN: unregister-windows-services.ps1 missing."
  exit 1
}

$destPath = Join-Path $env:USERPROFILE ".mill"
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($admin) {
  Write-Host "mill uninstall.ps1: already Admin - helper runs in THIS window (human window stays)"
  Write-Host "  helper: $helper"
  $fileArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $helper)
  if ($Dest) { $fileArgs += @("-Dest", "-DestPath", $destPath) }
  if ($Packages) { $fileArgs += "-Packages" }
  & powershell.exe @fileArgs
} else {
  $arg = "-NoProfile -ExecutionPolicy Bypass -File `"$helper`""
  if ($Dest) { $arg += " -Dest -DestPath `"$destPath`"" }
  if ($Packages) { $arg += " -Packages" }
  Write-Host "mill uninstall.ps1: ONE Hidden elevate Wait auto-exit"
  Write-Host "  helper: $helper"
  Start-Process -FilePath powershell.exe -Verb RunAs -WindowStyle Hidden -Wait -ArgumentList $arg
}
Write-Host "mill uninstall.ps1: done"
exit 0