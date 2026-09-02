param(
    [switch]$AcceptProductOwnerFixtureWaiver
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "apps/api/.venv/Scripts/python.exe"
$Evaluator = Join-Path $Root "scripts/evaluate_m4c_all.py"

if (-not (Test-Path $Python)) {
    throw "Python environment is missing. Run scripts/bootstrap.ps1 first."
}

$Arguments = @()
if ($AcceptProductOwnerFixtureWaiver) {
    $Arguments += "--accept-product-owner-fixture-waiver"
}

& $Python $Evaluator @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "M4-C final validation is blocked. Read artifacts/m4c-final/evaluation.json."
}
