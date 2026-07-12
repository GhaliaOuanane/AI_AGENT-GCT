@echo off
REM Ce script copie fra.traineddata vers le répertoire Tesseract
REM Il doit être exécuté en tant qu'administrateur

setlocal enabledelayedexpansion

REM Vérifier les permissions administrateur
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ce script doit être exécuté en tant qu'administrateur.
    echo Clic droit sur ce fichier ^> "Exécuter en tant qu'administrateur"
    pause
    exit /b 1
)

set SOURCE=%USERPROFILE%\Downloads\fra.traineddata
set DESTINATION=C:\Program Files\Tesseract-OCR\tessdata\fra.traineddata

echo [INFO] Copie de fra.traineddata...
echo Source: !SOURCE!
echo Destination: !DESTINATION!

if not exist "!SOURCE!" (
    echo [ERROR] Fichier source introuvable: !SOURCE!
    pause
    exit /b 1
)

copy "!SOURCE!" "!DESTINATION!" /Y
if %errorlevel% equ 0 (
    echo [OK] Fichier copié avec succès!
    echo.
    echo Vous pouvez maintenant exécuter: python src/main.py
) else (
    echo [ERROR] Échec de la copie.
)

pause
