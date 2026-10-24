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
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Error "  [ERREUR] Git n'est pas installe ou introuvable dans le PATH."
    exit 1
}

& git config core.hooksPath .githooks
if ($LASTEXITCODE -ne 0) {
    Write-Error "  [ERREUR] Echec de l'ecriture de core.hooksPath (code de sortie: $LASTEXITCODE)."
    exit 1
}

$configured = (& git config --get core.hooksPath 2>&1)
if ($LASTEXITCODE -ne 0 -or $configured -ne ".githooks") {
    Write-Error "  [ERREUR] Impossible de verifier core.hooksPath ou valeur inattendue : '$configured' (code: $LASTEXITCODE)."
    exit 1
}
Write-Host "  [OK] core.hooksPath configure sur '$configured'" -ForegroundColor Green

# 2. Verification de .gitattributes et normalisation active des hooks en LF
Write-Host "`n[2/4] Verification de .gitattributes et normalisation LF..." -ForegroundColor Yellow
if (Test-Path ".gitattributes") {
    Write-Host "  [OK] .gitattributes est present." -ForegroundColor Green
} else {
    Write-Warning "  [ATTENTION] .gitattributes est absent."
}

$hooksDir = Join-Path $RepoRoot ".githooks"
$crlfCount = 0
if (Test-Path $hooksDir) {
    Get-ChildItem -Path $hooksDir -Recurse -File | ForEach-Object {
        $filePath = $_.FullName
        $bytes = [System.IO.File]::ReadAllBytes($filePath)
        if ($bytes -contains 13) {
            $crlfCount++
            $text = [System.Text.Encoding]::UTF8.GetString($bytes)
            $normalized = $text -replace "`r`n", "`n" -replace "`r", "`n"
            [System.IO.File]::WriteAllBytes($filePath, [System.Text.Encoding]::UTF8.GetBytes($normalized))
        }
    }
}

if ($crlfCount -gt 0) {
    Write-Host "  [OK] $crlfCount fichier(s) sous .githooks normalise(s) vers LF." -ForegroundColor Green
} else {
    Write-Host "  [OK] Tous les fichiers sous .githooks sont deja au format LF." -ForegroundColor Green
}

# 3. Verification des Runtimes (Python >= 3.10 et Node.js >= 20)
Write-Host "`n[3/4] Verification des runtimes (Python >= 3.10 et Node.js >= 20)..." -ForegroundColor Yellow
$runtimeErrors = 0

$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    try {
        $pyVerStr = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null)
        if ($LASTEXITCODE -eq 0 -and $pyVerStr) {
            $pyParts = $pyVerStr.Trim().Split('.')
            $pyMajor = [int]$pyParts[0]
            $pyMinor = [int]$pyParts[1]
            if ($pyMajor -gt 3 -or ($pyMajor -eq 3 -and $pyMinor -ge 10)) {
                Write-Host "  [OK] Python detecte : version $pyVerStr (>= 3.10 valide)" -ForegroundColor Green
            } else {
                Write-Error "  [ERREUR] Python version $pyVerStr non supportee (requis >= 3.10 pour le backend)."
                $runtimeErrors++
            }
        } else {
            Write-Error "  [ERREUR] Impossible d'interroger la version de Python."
            $runtimeErrors++
        }
    } catch {
        Write-Error "  [ERREUR] Exception lors de la verification de Python : $_"
        $runtimeErrors++
    }
} else {
    Write-Error "  [ERREUR] Python introuvable dans le PATH (requis >= 3.10 pour le backend)."
    $runtimeErrors++
}

$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    try {
        $nodeRaw = (& node -v 2>$null)
        if ($LASTEXITCODE -eq 0 -and $nodeRaw) {
            $cleanVer = $nodeRaw.Trim().TrimStart('v')
            $nodeMajor = [int]($cleanVer.Split('.')[0])
            if ($nodeMajor -ge 20) {
                Write-Host "  [OK] Node.js detecte : version v$cleanVer (>= 20 valide)" -ForegroundColor Green
            } else {
                Write-Error "  [ERREUR] Node.js version v$cleanVer non supportee (requis >= 20 pour le frontend)."
                $runtimeErrors++
            }
        } else {
            Write-Error "  [ERREUR] Impossible d'interroger la version de Node.js."
            $runtimeErrors++
        }
    } catch {
        Write-Error "  [ERREUR] Exception lors de la verification de Node.js : $_"
        $runtimeErrors++
    }
} else {
    Write-Error "  [ERREUR] Node.js introuvable dans le PATH (requis >= 20 pour le frontend)."
    $runtimeErrors++
}

if ($runtimeErrors -gt 0) {
    exit 1
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
