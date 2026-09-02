$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

$NodeBin = Join-Path $env:ProgramFiles "nodejs"
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue) -and (Test-Path $NodeBin)) {
    $env:Path = "$NodeBin;$env:Path"
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "Node.js 22 or later is required. Install it and open a new PowerShell session."
}

$Python = @(
    & py -0p 2>$null |
        ForEach-Object {
            if ($_ -match "-V:(?<version>\d+\.\d+)") {
                [PSCustomObject]@{
                    Version = [version]$Matches.version
                    Selector = "-$($Matches.version)"
                }
            }
        } |
        Where-Object { $_.Version -ge [version]"3.12" } |
        Sort-Object Version -Descending |
        Select-Object -First 1
)

if (-not $Python) {
    throw "Python 3.12 or later is required. Install it without removing Python 3.10."
}

$PythonSelector = $Python[0].Selector

Write-Host "[1/2] Installing web dependencies..."
Push-Location $Root
$env:NPM_CONFIG_OFFLINE = "false"
& npm.cmd install
if ($LASTEXITCODE -ne 0) {
    throw "Web dependency installation failed."
}
Pop-Location

Write-Host "[2/2] Preparing Python virtual environment..."
$Api = Join-Path $Root "apps/api"
Push-Location $Api
if (-not (Test-Path ".venv")) {
    & py $PythonSelector -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Python virtual-environment creation failed."
    }
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Pop-Location

Write-Host "Bootstrap complete. Run scripts/dev.ps1 next."
