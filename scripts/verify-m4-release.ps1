param(
    [switch]$AcceptProductOwnerFixtureWaiver
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "apps/api/.venv/Scripts/python.exe"
$M4cEvaluator = Join-Path $Root "scripts/evaluate_m4c_all.py"
$QualityEvaluator = Join-Path $Root "scripts/evaluate_formula_patterns.py"

if (-not $AcceptProductOwnerFixtureWaiver) {
    throw "M4 Release Candidate verification requires -AcceptProductOwnerFixtureWaiver while the documented source-label conflict remains."
}
if (-not (Test-Path $Python)) {
    throw "Python environment is missing. Run scripts/bootstrap.ps1 first."
}

& $Python $M4cEvaluator --accept-product-owner-fixture-waiver
if ($LASTEXITCODE -ne 0) {
    throw "M4-C waiver validation failed."
}
Write-Host "M4-C waiver evaluation passed."

Write-Host "Running M4-A.5 quality/performance evaluation."
& $Python $QualityEvaluator --performance-runs 3
if ($LASTEXITCODE -ne 0) {
    throw "M4-A.5 formula-audit quality evaluation failed."
}

Write-Host "M4-specific Release Candidate checks passed; running the general regression suite."
& (Join-Path $Root "scripts/verify.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "General verification failed."
}
