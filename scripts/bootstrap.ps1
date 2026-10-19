# mill empty-machine bootstrap (Windows PowerShell) - silent CLI, no installer wizards.
# Chicken-egg: machine may have no mill/python. Agent runs this (not a HUMAN wizard).
# Windows front door is scripts/install.cmd (calls this script; agent-visible).
# Probe/reuse is handled by mill install server --apply (ensure-deps).
$ErrorActionPreference = "Stop"
Write-Host "mill bootstrap: ensure Python 3.10+ (silent winget if missing)"

function Test-PythonOk {
  try {
    $v = & python -c "import sys; print('%d.%d'%sys.version_info[:2])" 2>$null
    if (-not $v) { return $false }
    $parts = $v.Split('.')
    $maj = [int]$parts[0]; $min = [int]$parts[1]
    return ($maj -gt 3) -or ($maj -eq 3 -and $min -ge 10)
  } catch { return $false }
}

if (-not (Test-PythonOk)) {
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if (-not $winget) { throw "Python 3.10+ missing and winget not found. Install Python 3.12 via silent CLI, then re-run." }
  & winget install --id Python.Python.3.12 -e --disable-interactivity --accept-package-agreements --accept-source-agreements
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
  if (-not (Test-PythonOk)) { throw "Python still missing after winget. Open a new shell and re-run bootstrap.ps1." }
}

$repo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $repo "pyproject.toml"))) { $repo = (Get-Location).Path }

Write-Host "mill bootstrap: pip install mill (repo . or the-mill)"
if (Test-Path (Join-Path $repo "agent_coord")) {
  Push-Location $repo
  try { python -m pip install . } finally { Pop-Location }
} else {
  python -m pip install the-mill
}

Write-Host "mill bootstrap: mill install server --apply (probe + ensure-missing, silent CLI)"
$mill = Get-Command mill -ErrorAction SilentlyContinue
if ($mill) {
  & mill install server --apply
} else {
  python -m agent_coord install server --apply
}
Write-Host "mill bootstrap: done"
