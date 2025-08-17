param(
    [switch]$NoInstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Info($msg) { Write-Host "[vscode-pack] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[vscode-pack] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[vscode-pack] $msg" -ForegroundColor Red }

# Paths
$extensionsRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$extDir = Join-Path $extensionsRoot 'apps/vscode-ext'
$packDir = Join-Path $extDir '.pack'

if (-not (Test-Path $extDir)) {
    Write-Err "VS Code extension directory not found: $extDir"
    exit 1
}

Write-Info "Using extensions root: $extensionsRoot"
Write-Info "VS Code extension dir: $extDir"

# Ensure pnpm exists
try {
    $pnpmVersion = (pnpm --version) 2>$null
    Write-Info "pnpm: $pnpmVersion"
} catch {
    Write-Warn 'pnpm not found. Installing globally via npm...'
    npm i -g pnpm | Out-Null
}

# 1) Install workspace deps (extensions workspace)
Write-Info 'Installing workspace dependencies (extensions/)...'
Push-Location $extensionsRoot
pnpm install
Pop-Location

# 2) Build the VS Code extension
Write-Info 'Building VS Code extension (tsc)...'
Push-Location $extDir
pnpm install
pnpm run build
Pop-Location

# 3) Prepare clean .pack directory
Write-Info 'Preparing clean .pack directory...'
if (Test-Path $packDir) { Remove-Item -Recurse -Force $packDir }
New-Item -ItemType Directory -Path $packDir | Out-Null

Copy-Item -Recurse -Force (Join-Path $extDir 'out') (Join-Path $packDir 'out')
Copy-Item -Recurse -Force (Join-Path $extDir 'scripts') (Join-Path $packDir 'scripts')
if (Test-Path (Join-Path $extDir 'helper')) { Copy-Item -Recurse -Force (Join-Path $extDir 'helper') (Join-Path $packDir 'helper') }
Copy-Item -Force (Join-Path $extDir 'package.json') (Join-Path $packDir 'package.json')

$readmePath  = Join-Path $packDir 'README.md'
$licensePath = Join-Path $packDir 'LICENSE'
if (-not (Test-Path $readmePath))  { Set-Content -Path $readmePath  -Value '# AI Auditor VS Code Extension' -Encoding UTF8 }
if (-not (Test-Path $licensePath)) { Set-Content -Path $licensePath -Value 'UNLICENSED' -Encoding UTF8 }

# 4) Package via vsce (dlx)
Write-Info 'Packaging VSIX via @vscode/vsce...'
Push-Location $packDir
pnpm dlx @vscode/vsce package --allow-missing-repository
Pop-Location

# 5) Locate VSIX
$vsix = Get-ChildItem -Path $packDir -Filter '*.vsix' -File | Select-Object -First 1
if (-not $vsix) {
    Write-Err 'VSIX not produced.'
    exit 1
}

Write-Info ("VSIX produced: {0}" -f $vsix.FullName)

# 6) Install into VS Code (if code CLI is available and not disabled)
if (-not $NoInstall) {
    try {
        $codeVersion = (code --version)[0]
        Write-Info "Installing into VS Code (code $codeVersion)..."
        code --install-extension $vsix.FullName | Out-Null
        Write-Info 'Installed successfully. Restart VS Code if needed.'
    } catch {
        Write-Warn "VS Code CLI (code) not found in PATH. Install manually via VS Code: Extensions -> Install from VSIX..."
    }
} else {
    Write-Info 'Skipping installation (NoInstall switch).'
}

Write-Info 'Done.'


