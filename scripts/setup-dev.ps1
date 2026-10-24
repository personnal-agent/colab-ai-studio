# ==============================================================================
# Colab AI Studio - Setup de l'environnement de developpement (Windows PowerShell)
# ==============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Colab AI Studio - Setup de l'environnement de developpement (Windows)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Configuration des Git Hooks locaux
Write-Host "`n[1/4] Configuration des Git Hooks (.githooks)..." -ForegroundColor Yellow
try {
    & git config core.hooksPath .githooks
    $configured = & git config --get core.hooksPath
    Write-Host "  [OK] core.hooksPath configure sur '$configured'" -ForegroundColor Green
} catch {
    Write-Error "  [ERREUR] Impossible de configurer Git. Verifiez que git est installe."
}

# 2. Verification de .gitattributes
Write-Host "`n[2/4] Verification de .gitattributes..." -ForegroundColor Yellow
if (Test-Path ".gitattributes") {
    Write-Host "  [OK] .gitattributes est present (normalisation LF garantie)." -ForegroundColor Green
} else {
    Write-Warning "  [ATTENTION] .gitattributes est absent."
}

# 3. Verification des Runtimes
Write-Host "`n[3/4] Verification des runtimes (Python et Node.js)..." -ForegroundColor Yellow
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    $pyVersion = (& python --version 2>&1)
    Write-Host "  [OK] Python detecte : $pyVersion" -ForegroundColor Green
} else {
    Write-Warning "  [ATTENTION] Python introuvable dans le PATH (requis >= 3.10)."
}

$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVersion = (& node --version 2>&1)
    Write-Host "  [OK] Node.js detecte : $nodeVersion" -ForegroundColor Green
} else {
    Write-Warning "  [ATTENTION] Node.js introuvable dans le PATH (requis >= 20)."
}

# 4. Verification de gitleaks
Write-Host "`n[4/4] Verification de l'outil de securite gitleaks..." -ForegroundColor Yellow
$gitleaksCmd = Get-Command gitleaks -ErrorAction SilentlyContinue
if ($gitleaksCmd) {
    $gitleaksVer = (& gitleaks version 2>&1)
    Write-Host "  [OK] gitleaks est installe : $gitleaksVer" -ForegroundColor Green
} else {
    Write-Warning "  [ATTENTION] gitleaks est absent du PATH Windows."
    Write-Host "     Requis par le hook pre-commit pour empecher la fuite de secrets." -ForegroundColor Yellow
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "     Installation facile via winget : winget install Gitleaks.Gitleaks" -ForegroundColor Cyan
    } else {
        Write-Host "     Telechargement : https://github.com/gitleaks/gitleaks/releases" -ForegroundColor Cyan
    }
}

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "  Configuration terminee. Les hooks locaux sont prets !" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
