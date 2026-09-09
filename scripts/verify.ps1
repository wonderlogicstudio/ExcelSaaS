$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Api = Join-Path $Root "apps/api"
$NodeBin = Join-Path $env:ProgramFiles "nodejs"

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue) -and (Test-Path $NodeBin)) {
    $env:Path = "$NodeBin;$env:Path"
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "Node.js 22 or later is required. Install it and open a new PowerShell session."
}

Push-Location $Root
& npm.cmd run verify:web
if ($LASTEXITCODE -ne 0) {
    throw "Web verification failed."
}
& npm.cmd run test:edge
if ($LASTEXITCODE -ne 0) {
    throw "Hosted-beta Worker verification failed."
}
Pop-Location

Push-Location $Api
& .\.venv\Scripts\python.exe -m pytest -p no:cacheprovider
if ($LASTEXITCODE -ne 0) {
    throw "API tests failed."
}
& .\.venv\Scripts\python.exe -m ruff check --no-cache .
if ($LASTEXITCODE -ne 0) {
    throw "API lint verification failed."
}
Pop-Location

& (Join-Path $Root "apps/api/.venv/Scripts/python.exe") (Join-Path $Root "scripts/verify_m4c_sample_pack.py")
if ($LASTEXITCODE -ne 0) {
    throw "M4-C supplied sample-pack verification failed."
}

Write-Host "All verification steps passed."
