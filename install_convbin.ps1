[CmdletBinding()]
param(
    [string]$Repo = "tomojitakasu/RTKLIB",
    [string]$Tag = "latest",
    [string]$Destination,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[get-convbin] $Message"
}

$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot)) {
    $scriptRoot = (Get-Location).Path
}

if ([string]::IsNullOrWhiteSpace($Destination)) {
    $Destination = Join-Path $scriptRoot "convbin.exe"
}

$Destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Destination)
if ((Test-Path -LiteralPath $Destination) -and -not $Force) {
    Write-Step "convbin.exe already exists: $Destination"
    Write-Step "Use -Force to replace it."
    exit 0
}

$headers = @{
    "User-Agent" = "RTCM3_Conv-install-convbin"
    "Accept" = "application/vnd.github+json"
}

if ($Tag -eq "latest") {
    $releaseUrl = "https://api.github.com/repos/$Repo/releases/latest"
} else {
    $releaseUrl = "https://api.github.com/repos/$Repo/releases/tags/$Tag"
}

Write-Step "reading release metadata: $releaseUrl"
$release = Invoke-RestMethod -Uri $releaseUrl -Headers $headers
$assets = @($release.assets)

$asset = $assets |
    Where-Object { $_.name -match '\.zip$' } |
    Sort-Object @{ Expression = { if ($_.name -match '(?i)(bin|win|rtklib)') { 0 } else { 1 } } }, Name |
    Select-Object -First 1

if (-not $asset) {
    throw "No downloadable zip asset was found in release '$($release.tag_name)'. Open https://github.com/$Repo/releases and download the Windows binary package manually."
}

$tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("rtklib_convbin_" + [guid]::NewGuid().ToString("N"))
$extractDir = Join-Path $tmpRoot "extract"
$zipPath = Join-Path $tmpRoot $asset.name

try {
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    Write-Step "downloading $($asset.name) from $($release.tag_name)"
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -Headers $headers

    Write-Step "extracting archive"
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $convbin = Get-ChildItem -Path $extractDir -Recurse -Filter "convbin.exe" -File | Select-Object -First 1
    if (-not $convbin) {
        throw "convbin.exe was not found inside $($asset.name)."
    }

    $destDir = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null

    Copy-Item -LiteralPath $convbin.FullName -Destination $Destination -Force
    Write-Step "installed: $Destination"
} finally {
    if (Test-Path -LiteralPath $tmpRoot) {
        Remove-Item -LiteralPath $tmpRoot -Recurse -Force
    }
}
