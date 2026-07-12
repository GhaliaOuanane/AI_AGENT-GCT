# Script d'installation automatique de Tesseract OCR sur Windows
# Usage: powershell -ExecutionPolicy Bypass -File install_tesseract.ps1

Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         Installation Tesseract OCR pour Windows                 ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Vérifie si Tesseract est déjà installé
Write-Host "[CHECK] Vérification de l'installation existante..." -ForegroundColor Yellow
$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
$tesseractPath32 = "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

if ((Test-Path $tesseractPath) -or (Test-Path $tesseractPath32)) {
    Write-Host "[OK] Tesseract est déjà installé!" -ForegroundColor Green
    $installedPath = if (Test-Path $tesseractPath) { $tesseractPath } else { $tesseractPath32 }
    Write-Host "     Chemin: $installedPath" -ForegroundColor Green
    
    # Vérifie la version
    & "$installedPath" --version 2>$null | ForEach-Object { Write-Host "     Version: $_" -ForegroundColor Green }
} else {
    Write-Host "[ERROR] Tesseract n'est pas installé" -ForegroundColor Red
    Write-Host ""
    Write-Host "=== INSTALLATION MANUELLE REQUISE ===" -ForegroundColor Yellow
    Write-Host "Tesseract ne peut pas être installé automatiquement sur Windows." -ForegroundColor Yellow
    Write-Host "Veuillez suivre ces étapes :" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Télécharge l'installer depuis :" -ForegroundColor Cyan
    Write-Host "   https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Cherche la dernière version (ex: tesseract-ocr-w64-setup-v5.3.1.exe)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. Double-click sur le fichier .exe pour installer" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "4. Installation par défaut dans :" -ForegroundColor Cyan
    Write-Host "   C:\Program Files\Tesseract-OCR" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "5. Après installation, redémarre PowerShell et réexécute ce script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OU utilise ce lien direct :" -ForegroundColor Green
    Write-Host "https://digi.bsc.es/gitlab/ahocevar/tesseract-windows/-/releases" -ForegroundColor Green
    exit 1
}

Write-Host ""
Write-Host "[CHECK] Vérification du PATH..." -ForegroundColor Yellow

# Vérifie si Tesseract est dans le PATH
$tesseractCmd = Get-Command tesseract -ErrorAction SilentlyContinue
if ($tesseractCmd) {
    Write-Host "[OK] Tesseract trouvé dans PATH" -ForegroundColor Green
    Write-Host "     Chemin: $($tesseractCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "[WARN] Tesseract n'est pas dans le PATH" -ForegroundColor Yellow
    Write-Host "       Ajout à PATH..." -ForegroundColor Yellow
    
    # Ajoute au PATH de session
    $env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
    
    # Ajoute au PATH système (nécessite admin)
    try {
        if ([System.Environment]::GetEnvironmentVariable("Path", "Machine") -notlike "*Tesseract*") {
            Write-Host "       Ajout au PATH système (admin requis)..." -ForegroundColor Yellow
            $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
            $newPath = "C:\Program Files\Tesseract-OCR;" + $currentPath
            [System.Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
            Write-Host "[OK] Ajouté au PATH système" -ForegroundColor Green
        }
    } catch {
        Write-Host "[WARN] Impossible d'ajouter au PATH système (pas d'admin)" -ForegroundColor Yellow
        Write-Host "       PATH de session configuré pour cette session" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[CHECK] Vérification des langues disponibles..." -ForegroundColor Yellow

# Vérifie les langues
try {
    $languages = & tesseract --list-langs 2>&1
    if ($languages -like "*fra*" -or $languages -like "*french*") {
        Write-Host "[OK] Langue française (fra) disponible" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Langue française non trouvée" -ForegroundColor Yellow
        Write-Host "       Téléchargement du pack français..." -ForegroundColor Yellow
        
        $tessdataPath = "C:\Program Files\Tesseract-OCR\tessdata"
        $fraFile = "$tessdataPath\fra.traineddata"
        
        if (-not (Test-Path $tessdataPath)) {
            Write-Host "[ERROR] Dossier tessdata introuvable" -ForegroundColor Red
            exit 1
        }
        
        if (-not (Test-Path $fraFile)) {
            Write-Host "       Téléchargement fra.traineddata (~70MB)..." -ForegroundColor Cyan
            try {
                $url = "https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata"
                Invoke-WebRequest -Uri $url -OutFile $fraFile -ErrorAction Stop
                Write-Host "[OK] Pack français téléchargé et installé" -ForegroundColor Green
            } catch {
                Write-Host "[ERROR] Impossible de télécharger le pack français" -ForegroundColor Red
                Write-Host "       Télécharge manuellement depuis :" -ForegroundColor Yellow
                Write-Host "       https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata" -ForegroundColor Yellow
                Write-Host "       Et place dans : $tessdataPath" -ForegroundColor Yellow
                exit 1
            }
        } else {
            Write-Host "[OK] Pack français déjà installé" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "[ERROR] Impossible de vérifier les langues" -ForegroundColor Red
}

Write-Host ""
Write-Host "[CHECK] Configuration variables d'environnement..." -ForegroundColor Yellow

# Configure TESSDATA_PREFIX
$tessdataPath = "C:\Program Files\Tesseract-OCR\tessdata"
$currentTessdataPrefix = [System.Environment]::GetEnvironmentVariable("TESSDATA_PREFIX", "User")

if ($currentTessdataPrefix -ne $tessdataPath) {
    try {
        [System.Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", $tessdataPath, "User")
        Write-Host "[OK] TESSDATA_PREFIX configuré" -ForegroundColor Green
        Write-Host "     Chemin: $tessdataPath" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Impossible de configurer TESSDATA_PREFIX" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              ✅ Tesseract OCR configuré avec succès!            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "ℹ️  Notes :" -ForegroundColor Cyan
Write-Host "   • Si tu as ajouté Tesseract au PATH système, redémarre PowerShell" -ForegroundColor Cyan
Write-Host "   • Teste avec : tesseract --version" -ForegroundColor Cyan
Write-Host "   • Puis relance : python src/main.py" -ForegroundColor Cyan
Write-Host ""
