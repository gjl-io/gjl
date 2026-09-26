# SPDX-License-Identifier: MIT
# Copyright (c) 2026 gjl. All rights reserved.
#
# gjl Installer for Windows
# Usage:
#   irm https://gjl.io/install.ps1 | iex
# CLI-only (exclude Desktop GUI):
#   $env:GJL_CLI_ONLY=1; irm https://gjl.io/install.ps1 | iex
# Or with options:
#   & ([scriptblock]::Create((irm https://gjl.io/install.ps1))) -CliOnly
# Or via curl:
#   curl.exe -fsSL https://gjl.io/install.ps1 | powershell -Command - -CliOnly

[CmdletBinding()]
param(
    [switch]$CliOnly,
    [string]$Version = ""
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Enforce TLS 1.2+ for secure download
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$owner = "gjl-io"
$repo = "gjl"

# 1. Determine processor architecture
$arch = switch ($env:PROCESSOR_ARCHITECTURE) {
    'AMD64' { 'amd64' }
    'ARM64' { 'arm64' }
    default { throw "Unsupported processor architecture: $env:PROCESSOR_ARCHITECTURE. gjl supports amd64 and arm64." }
}

# 2. Determine target release version/tag
if ([string]::IsNullOrWhiteSpace($Version) -and [string]::IsNullOrWhiteSpace($env:GJL_VERSION) -eq $false) {
    $Version = $env:GJL_VERSION
}

$tag = $Version
if ([string]::IsNullOrWhiteSpace($tag)) {
    Write-Host "Resolving latest gjl release..." -ForegroundColor Cyan
    try {
        $releasesApiUrl = "https://api.github.com/repos/$owner/$repo/releases"
        $headers = @{ "User-Agent" = "gjl-Installer-PowerShell" }
        $releases = Invoke-RestMethod -Uri $releasesApiUrl -Headers $headers -UseBasicParsing -TimeoutSec 10
        if ($releases -is [array] -and $releases.Count -gt 0) {
            $tag = $releases[0].tag_name
        } elseif ($releases.tag_name) {
            $tag = $releases.tag_name
        }
    } catch {
        # Fallback to default initial release tag if GitHub API query fails
        $tag = "v0.0.1-alpha.1"
    }
}

if ([string]::IsNullOrWhiteSpace($tag)) {
    $tag = "v0.0.1-alpha.1"
}

# 3. Detect GUI environment availability
# Windows ARM64 does not provide desktop package (CLI only).
# Windows Server Core, Nano, or systems without explorer.exe lack GUI subsystem.
$argMatchCli = $false
if ($args -and ($args -match '(?i)^(-{1,2}cli(-?only)?|cli)$')) {
    $argMatchCli = $true
}
$isCliForced = $CliOnly.IsPresent -or $argMatchCli -or ($env:GJL_CLI_ONLY -in @('1', 'true', 'True', 'yes', 'Yes'))
$isArm64 = ($arch -eq 'arm64')

$isHeadless = $false
try {
    $regKey = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $installType = (Get-ItemProperty -Path $regKey -Name InstallationType -ErrorAction SilentlyContinue).InstallationType
    if ($installType -match 'Server Core|Nano') {
        $isHeadless = $true
    }
} catch {
    # Non-fatal if registry read is unavailable
}

if (-not (Test-Path (Join-Path $env:SystemRoot 'explorer.exe'))) {
    $isHeadless = $true
}

$installDesktop = (-not $isCliForced) -and (-not $isArm64) -and (-not $isHeadless)

# 4. Perform Download and Installation
$installBase = Join-Path $env:LOCALAPPDATA 'Programs\gjl'
if (-not (Test-Path -LiteralPath $installBase)) {
    New-Item -ItemType Directory -Path $installBase -Force | Out-Null
}

$pathToAdd = ""
$targetGjl = ""
$targetDesktop = ""

if ($installDesktop) {
    # Full Desktop + CLI bundle (ZIP)
    $artifactName = "gjl-windows-$arch.zip"
    $downloadUrl = "https://github.com/$owner/$repo/releases/download/$tag/$artifactName"
    $tempZip = Join-Path $installBase "gjl-download-$PID.zip"
    $tempStage = Join-Path $installBase "stage-$PID"

    Write-Host "Downloading gjl Desktop & CLI ($tag, $artifactName)..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip -UseBasicParsing
        if (-not (Test-Path -LiteralPath $tempZip) -or (Get-Item -LiteralPath $tempZip).Length -le 0) {
            throw "Downloaded archive is empty or missing."
        }

        Write-Host "Extracting gjl bundle..." -ForegroundColor Cyan
        if (Test-Path -LiteralPath $tempStage) {
            Remove-Item -LiteralPath $tempStage -Recurse -Force -ErrorAction SilentlyContinue
        }
        Expand-Archive -LiteralPath $tempZip -DestinationPath $tempStage -Force

        # Copy extracted files to destination
        Get-ChildItem -LiteralPath $tempStage | ForEach-Object {
            $destItem = Join-Path $installBase $_.Name
            if ($_.PSIsContainer) {
                if (Test-Path -LiteralPath $destItem) {
                    Remove-Item -LiteralPath $destItem -Recurse -Force -ErrorAction SilentlyContinue
                }
                Move-Item -LiteralPath $_.FullName -Destination $destItem -Force
            } else {
                Move-Item -LiteralPath $_.FullName -Destination $destItem -Force
            }
        }
    } finally {
        if (Test-Path -LiteralPath $tempZip) {
            Remove-Item -LiteralPath $tempZip -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -LiteralPath $tempStage) {
            Remove-Item -LiteralPath $tempStage -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    $targetGjl = Join-Path $installBase 'gjl.exe'
    $candidateDesktop = Get-ChildItem -LiteralPath $installBase -Filter "*.exe" | Where-Object { $_.Name -ne 'gjl.exe' } | Select-Object -First 1
    $targetDesktop = if ($candidateDesktop) { $candidateDesktop.FullName } else { Join-Path $installBase 'gjl-desktop.exe' }
    $pathToAdd = $installBase
} else {
    # Standalone CLI binary
    $binDir = Join-Path $installBase 'bin'
    if (-not (Test-Path -LiteralPath $binDir)) {
        New-Item -ItemType Directory -Path $binDir -Force | Out-Null
    }

    $binaryName = "gjl-windows-$arch.exe"
    $downloadUrl = "https://github.com/$owner/$repo/releases/download/$tag/$binaryName"
    $tempExe = Join-Path $binDir "gjl.exe.tmp-$PID"
    $targetGjl = Join-Path $binDir 'gjl.exe'

    $reason = if ($isArm64) { "Windows ARM64" } elseif ($isCliForced) { "CLI-only requested" } else { "Headless environment detected" }
    Write-Host "Downloading gjl CLI ($reason: $tag, $binaryName)..." -ForegroundColor Cyan

    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempExe -UseBasicParsing
        if (-not (Test-Path -LiteralPath $tempExe) -or (Get-Item -LiteralPath $tempExe).Length -le 0) {
            throw "Downloaded binary is empty or missing."
        }
        Move-Item -LiteralPath $tempExe -Destination $targetGjl -Force
    } finally {
        if (Test-Path -LiteralPath $tempExe) {
            Remove-Item -LiteralPath $tempExe -Force -ErrorAction SilentlyContinue
        }
    }

    $pathToAdd = $binDir
}

# 5. Update PATH Environment Variable (User + Current Process)
$userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
$pathParts = @($userPath -split ';' | Where-Object { [string]::IsNullOrWhiteSpace($_) -eq $false })
$needsPathUpdate = $true
foreach ($part in $pathParts) {
    if ($part.TrimEnd('\') -eq $pathToAdd.TrimEnd('\')) {
        $needsPathUpdate = $false
        break
    }
}

if ($needsPathUpdate) {
    $newPath = ($pathParts + $pathToAdd) -join ';'
    [Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
    Write-Host "Added $pathToAdd to your User PATH environment variable." -ForegroundColor Green
}

# Update current session PATH so commands work immediately
$currentSessionParts = @($env:PATH -split ';' | Where-Object { [string]::IsNullOrWhiteSpace($_) -eq $false })
$needsSessionUpdate = $true
foreach ($part in $currentSessionParts) {
    if ($part.TrimEnd('\') -eq $pathToAdd.TrimEnd('\')) {
        $needsSessionUpdate = $false
        break
    }
}
if ($needsSessionUpdate) {
    $env:PATH = "$env:PATH;$pathToAdd"
}

# 6. Display Success & Getting Started Guide
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
if ($installDesktop) {
    Write-Host "gjl was successfully installed!" -ForegroundColor Green
    Write-Host "  CLI:     $targetGjl"
    Write-Host "  Desktop: $targetDesktop"
    Write-Host ""
    Write-Host "To get started right away in this terminal:" -ForegroundColor Cyan
    Write-Host "  gjl run     # Start local relay daemon" -ForegroundColor Yellow
    Write-Host "  gjl gui     # Launch Desktop management GUI" -ForegroundColor Yellow
} else {
    Write-Host "gjl CLI was successfully installed!" -ForegroundColor Green
    Write-Host "  CLI:     $targetGjl"
    Write-Host ""
    Write-Host "To get started right away in this terminal:" -ForegroundColor Cyan
    Write-Host "  gjl run     # Start local relay daemon" -ForegroundColor Yellow
    Write-Host "  gjl --help  # View CLI management commands" -ForegroundColor Yellow
}
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
