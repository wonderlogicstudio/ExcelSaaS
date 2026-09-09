# Deploys only an API Gateway bridge to the existing authenticated Cloud Run service.
# Run from Google Cloud Shell or a locally authenticated gcloud session after all
# H2 code/tests are approved. It never changes Cloud Run IAM or creates an
# anonymous invoker. API Gateway has no Seoul region; this approved beta uses
# Tokyo (asia-northeast1) and is synthetic-only until final H2 approval.
param(
  [Parameter(Mandatory)] [string]$ProjectId,
  [Parameter(Mandatory)] [string]$CloudRunUrl,
  [Parameter(Mandatory)] [string]$CloudflareAccessIssuer,
  [Parameter(Mandatory)] [string]$CloudflareAccessJwksUri,
  [Parameter(Mandatory)] [string]$CloudflareAccessAudience,
  [Parameter(Mandatory)] [string]$GatewayInvokerServiceAccount,
  [string]$ApiName = "workbookcare-beta-api",
  [string]$GatewayName = "workbookcare-beta-gateway",
  [string]$GatewayRegion = "asia-northeast1"
)

$ErrorActionPreference = "Stop"
$gcloudExecutable = (Get-Command "gcloud.cmd" -ErrorAction Stop).Source
if ($GatewayRegion -ne "asia-northeast1") {
  throw "H2 has an explicit Tokyo-only approval. Use asia-northeast1 or obtain a new approval."
}
foreach ($uriValue in @($CloudRunUrl, $CloudflareAccessIssuer, $CloudflareAccessJwksUri)) {
  $uri = $null
  if (-not [Uri]::TryCreate($uriValue, [UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -ne "https") {
    throw "Cloud Run, issuer, and JWKS values must be exact HTTPS URLs."
  }
}
if ($CloudflareAccessAudience.Length -lt 16 -or $CloudflareAccessAudience -match '[\r\n]') {
  throw "CloudflareAccessAudience is invalid. Copy the exact Access AUD tag."
}
if ($GatewayInvokerServiceAccount -notmatch '^[^@\s]+@[^@\s]+\.iam\.gserviceaccount\.com$') {
  throw "GatewayInvokerServiceAccount must be one Google service-account email."
}

$templatePath = Join-Path $PSScriptRoot "workbookcare-beta-openapi.yaml.template"
$configName = "workbookcare-beta-config-$(Get-Date -Format yyyyMMddHHmmss)"
$renderedSpec = Join-Path ([System.IO.Path]::GetTempPath()) "$configName.yaml"
$content = Get-Content $templatePath -Raw
$replacements = @{
  '${CLOUD_RUN_URL}' = $CloudRunUrl.TrimEnd('/')
  '${CLOUDFLARE_ACCESS_ISSUER}' = $CloudflareAccessIssuer.TrimEnd('/')
  '${CLOUDFLARE_ACCESS_JWKS_URI}' = $CloudflareAccessJwksUri.TrimEnd('/')
  '${CLOUDFLARE_ACCESS_AUD}' = $CloudflareAccessAudience
}
foreach ($placeholder in $replacements.Keys) {
  $content = $content.Replace($placeholder, $replacements[$placeholder])
}
[System.IO.File]::WriteAllText(
  $renderedSpec,
  $content,
  (New-Object System.Text.UTF8Encoding($false))
)

try {
  & $gcloudExecutable api-gateway apis describe $ApiName --project $ProjectId *> $null
  if ($LASTEXITCODE -ne 0) {
    & $gcloudExecutable api-gateway apis create $ApiName --project $ProjectId
  }
  if ($LASTEXITCODE -ne 0) { throw "API Gateway API creation/check failed." }

  & $gcloudExecutable api-gateway api-configs create $configName `
    --api $ApiName `
    --openapi-spec $renderedSpec `
    --backend-auth-service-account $GatewayInvokerServiceAccount `
    --project $ProjectId
  if ($LASTEXITCODE -ne 0) { throw "API Gateway API config creation failed." }

  & $gcloudExecutable api-gateway gateways describe $GatewayName `
    --location $GatewayRegion --project $ProjectId *> $null
  if ($LASTEXITCODE -eq 0) {
    & $gcloudExecutable api-gateway gateways update $GatewayName `
      --api $ApiName --api-config $configName `
      --location $GatewayRegion --project $ProjectId
  } else {
    & $gcloudExecutable api-gateway gateways create $GatewayName `
      --api $ApiName --api-config $configName `
      --location $GatewayRegion --project $ProjectId
  }
  if ($LASTEXITCODE -ne 0) { throw "API Gateway gateway deployment failed." }

  & $gcloudExecutable api-gateway gateways describe $GatewayName `
    --location $GatewayRegion --project $ProjectId `
    --format="value(defaultHostname)"
} finally {
  Remove-Item -LiteralPath $renderedSpec -Force -ErrorAction SilentlyContinue
}
