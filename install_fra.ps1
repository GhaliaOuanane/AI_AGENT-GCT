# Script PowerShell pour installer fra.traineddata avec élévation de privilèges
# Exécute avec: powershell -ExecutionPolicy Bypass -File install_fra.ps1

# Vérifie que le script s'exécute en tant qu'administrateur
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "Ce script doit être exécuté EN TANT QU'ADMINISTRATEUR" -ForegroundColor Red
    Write-Host ""
    Write-Host "Relance avec: powershell -ExecutionPolicy Bypass -File install_fra.ps1"
    exit 1
}

Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Installation de fra.traineddata (Droits Admin OK)" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$source = "$env:USERPROFILE\Downloads\fra.traineddata"
$dest = "C:\Program Files\Tesseract-OCR\tessdata\fra.traineddata"

# Vérifie la source
if (-not (Test-Path $source)) {
    Write-Host "[ERROR] Fichier source introuvable: $source" -ForegroundColor Red
    exit 1
}

$sourceSize = (Get-Item $source).Length / 1MB
Write-Host "[OK] Source: $source ($([Math]::Round($sourceSize, 1)) MB)" -ForegroundColor Green

# Vérifie le dossier de destination
if (-not (Test-Path "C:\Program Files\Tesseract-OCR\tessdata")) {
    Write-Host "[ERROR] Dossier tessdata introuvable" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Destination: $dest" -ForegroundColor Green
Write-Host ""

# Supprime le fichier s'il existe déjà
if (Test-Path $dest) {
    Write-Host "[INFO] Suppression du fichier existant..." -ForegroundColor Yellow
    Remove-Item $dest -Force -ErrorAction Stop
}

# Copie le fichier
Write-Host "[INFO] Copie en cours..." -ForegroundColor Yellow
try {
    Copy-Item -Path $source -Destination $dest -Force -ErrorAction Stop
    Write-Host "[OK] Fichier copié avec succès!" -ForegroundColor Green
    
    # Vérifie que le fichier est là
    if (Test-Path $dest) {
        $destSize = (Get-Item $dest).Length / 1MB
        Write-Host ""
        Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "  ✅ Installation Réussie!" -ForegroundColor Green
        Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "Fichier: $dest" -ForegroundColor Green
        Write-Host "Taille:  $([Math]::Round($destSize, 1)) MB" -ForegroundColor Green
        Write-Host ""
        Write-Host "Prochaines étapes:" -ForegroundColor Cyan
        Write-Host "  1. Redémarre PowerShell" -ForegroundColor Cyan
        Write-Host "  2. Teste: tesseract --list-langs" -ForegroundColor Cyan
        Write-Host "  3. Exécute: python src/main.py" -ForegroundColor Cyan
        Write-Host ""
        exit 0
    } else {
        Write-Host "[ERROR] Le fichier n'a pas pu être copié" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Erreur lors de la copie: $_" -ForegroundColor Red
    exit 1
}
