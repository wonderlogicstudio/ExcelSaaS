$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "apps/api/.venv/Scripts/python.exe"
$Verifier = Join-Path $Root "scripts/verify_m4c_sample_pack.py"

if (-not (Test-Path $Python)) {
    throw "Python environment is missing. Run scripts/bootstrap.ps1 first."
}

& $Python $Verifier
if ($LASTEXITCODE -ne 0) {
    throw "M4-C supplied sample-pack verification failed."
}
