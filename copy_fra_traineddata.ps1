# Script PowerShell pour copier fra.traineddata vers Tesseract (avec auto-élévation admin)

# Vérifier si le script s'exécute en tant qu'administrateur
$isAdmin = [bool]([System.Security.Principal.WindowsIdentity]::GetCurrent().Groups -match "S-1-5-32-544")

if (-not $isAdmin) {
    Write-Host "[INFO] Ré-exécution du script en tant qu'administrateur..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$source = "$env:USERPROFILE\Downloads\fra.traineddata"
$destination = "C:\Program Files\Tesseract-OCR\tessdata\fra.traineddata"

Write-Host "[INFO] Copie de fra.traineddata..." -ForegroundColor Cyan
Write-Host "Source: $source" -ForegroundColor Gray
Write-Host "Destination: $destination" -ForegroundColor Gray
Write-Host ""

# Vérifier que le fichier source existe
if (-not (Test-Path $source)) {
    Write-Host "[ERROR] Fichier source introuvable: $source" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

# Vérifier que le répertoire de destination existe
if (-not (Test-Path (Split-Path $destination))) {
    Write-Host "[ERROR] Répertoire de destination introuvable: $(Split-Path $destination)" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

try {
    Copy-Item -Path $source -Destination $destination -Force -ErrorAction Stop
    Write-Host "[OK] Fichier copié avec succès!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Vous pouvez maintenant exécuter: python src/main.py" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Échec de la copie: $_" -ForegroundColor Red
    exit 1
}

Read-Host "`nAppuyez sur Entrée pour quitter"
