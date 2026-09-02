[CmdletBinding()]
param(
    [switch]$InternalFormulaAudit
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Api = Join-Path $Root "apps/api"
$Web = Join-Path $Root "apps/web"
$NodeBin = Join-Path $env:ProgramFiles "nodejs"
$LocalDevLogs = Join-Path $Root "artifacts/local-dev"

function Test-LocalPortAvailable {
    param([int]$Port)

    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try {
        # Binding tests whether this exact listener can start. A TCP connect can
        # be rejected by a stale/broken process even though it still owns the port.
        $listener.Start()
        return $true
    } catch [System.Net.Sockets.SocketException] {
        return $false
    } finally {
        $listener.Stop()
    }
}

function Get-AvailableLocalPort {
    param(
        [int]$StartPort,
        [int]$EndPort
    )

    for ($Port = $StartPort; $Port -le $EndPort; $Port++) {
        if (Test-LocalPortAvailable -Port $Port) {
            return $Port
        }
    }
    throw "No available local port was found in the range $StartPort-$EndPort."
}

function ConvertTo-EncodedPowerShellCommand {
    param([string]$Command)

    return [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($Command))
}

function Wait-ForLocalHttp {
    param(
        [string]$Url,
        [int]$TimeoutSeconds,
        [string]$LogPath
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 1
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                return
            }
        } catch {
            Start-Sleep -Milliseconds 250
        }
    } while ((Get-Date) -lt $deadline)

    throw "Local server did not become ready: $Url. Check $LogPath"
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue) -and (Test-Path $NodeBin)) {
    $env:Path = "$NodeBin;$env:Path"
}

$Npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $Npm) {
    throw "Node.js 22 or later is required. Install it and open a new PowerShell session."
}

if (-not (Test-Path (Join-Path $Api ".venv/Scripts/python.exe"))) {
    throw "Python environment is missing. Run scripts/bootstrap.ps1 first."
}

if ($InternalFormulaAudit) {
    # Do not depend on the default development stack being stopped. A stale
    # 8000/5173 process can never receive an internal-beta request.
    $ApiPort = Get-AvailableLocalPort -StartPort 8010 -EndPort 8090
    $WebPort = Get-AvailableLocalPort -StartPort 5174 -EndPort 5190
} else {
    $ApiPort = 8000
    $WebPort = 5173
    if (-not (Test-LocalPortAvailable -Port $ApiPort)) {
        throw "Local port $ApiPort is already in use. Close the existing WorkbookCare development windows before starting a new session."
    }
    if (-not (Test-LocalPortAvailable -Port $WebPort)) {
        throw "Local port $WebPort is already in use. Close the existing WorkbookCare development windows before starting a new session."
    }
}

$ApiEnvironment = ""
$WebEnvironment = ""
if ($InternalFormulaAudit) {
    # These are set in the spawned process so the API and Vite receive the
    # same explicit internal-beta mode. It deliberately uses separate ports
    # so a stale default local stack cannot be mistaken for the beta stack.
    $ApiEnvironment = "`$env:APP_ENV = 'internal_beta'; `$env:FORMULA_PATTERN_AUDIT_ENABLED = 'true'; `$env:CORS_ORIGINS = '[`"http://localhost:$WebPort`",`"http://127.0.0.1:$WebPort`"]'; "
    $ViteCacheDirectory = Join-Path $LocalDevLogs "vite-cache-$WebPort"
    $WebEnvironment = "`$env:VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED = 'true'; `$env:VITE_API_BASE_URL = 'http://127.0.0.1:$ApiPort'; `$env:WORKBOOKCARE_VITE_CACHE_DIR = '$ViteCacheDirectory'; "
}

$ApiCommand = "$ApiEnvironment Set-Location '$Api'; & .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port $ApiPort"
$WebCommand = "$WebEnvironment Set-Location '$Web'; & '$Root\node_modules\.bin\vite.cmd' --host 127.0.0.1 --port $WebPort --strictPort"

New-Item -ItemType Directory -Force -Path $LocalDevLogs | Out-Null
$ApiOutputLog = Join-Path $LocalDevLogs "api-$ApiPort.out.log"
$ApiErrorLog = Join-Path $LocalDevLogs "api-$ApiPort.err.log"
$WebOutputLog = Join-Path $LocalDevLogs "web-$WebPort.out.log"
$WebErrorLog = Join-Path $LocalDevLogs "web-$WebPort.err.log"

$ApiEncodedCommand = ConvertTo-EncodedPowerShellCommand -Command $ApiCommand
$WebEncodedCommand = ConvertTo-EncodedPowerShellCommand -Command $WebCommand

Start-Process powershell.exe -ArgumentList "-NoProfile -EncodedCommand $ApiEncodedCommand" -WindowStyle Hidden -RedirectStandardOutput $ApiOutputLog -RedirectStandardError $ApiErrorLog
Start-Process powershell.exe -ArgumentList "-NoProfile -EncodedCommand $WebEncodedCommand" -WindowStyle Hidden -RedirectStandardOutput $WebOutputLog -RedirectStandardError $WebErrorLog

Wait-ForLocalHttp -Url "http://127.0.0.1:$ApiPort/health" -TimeoutSeconds 15 -LogPath $ApiErrorLog
Wait-ForLocalHttp -Url "http://127.0.0.1:$WebPort" -TimeoutSeconds 15 -LogPath $WebErrorLog

Write-Host "API: http://127.0.0.1:$ApiPort/docs"
Write-Host "Web: http://127.0.0.1:$WebPort"
Write-Host "Logs: $LocalDevLogs"
if ($InternalFormulaAudit) {
    Write-Host "M4-C internal formula audit: enabled on isolated ports $ApiPort / $WebPort"
    Write-Host "After the free scan, use the separate formula-pattern audit panel shown before the free Finding list."
} else {
    Write-Host "M4-C internal formula audit: disabled (default-safe mode)"
    Write-Host "To test the supplied M4-C samples, restart with: .\scripts\dev.ps1 -InternalFormulaAudit"
}
