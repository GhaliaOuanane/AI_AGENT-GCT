@echo off
REM Script d'installation de fra.traineddata avec droits admin

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║       Installation de fra.traineddata dans Tesseract OCR         ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Vérifie les droits admin
whoami /groups | findstr "12288" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Ce script doit être exécuté EN TANT QU'ADMINISTRATEUR
    echo.
    echo Solution:
    echo   1. Clique-droit sur ce fichier
    echo   2. Sélectionne "Exécuter en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

echo [INFO] Exécution avec droits administrateur OK
echo.

REM Exécute le script Python avec droits admin
cd /d "%~dp0"

echo [INFO] Exécution du script de déplacement...
echo.

python move_fra_traineddata.py

if %errorlevel% equ 0 (
    echo.
    echo ╔════════════════════════════════════════════════════════════════════╗
    echo ║              ✅ Installation Complète!                           ║
    echo ╚════════════════════════════════════════════════════════════════════╝
    echo.
    echo Prochaines étapes:
    echo   1. Redémarre PowerShell
    echo   2. Teste: tesseract --list-langs
    echo   3. Exécute: python src/main.py
    echo.
) else (
    echo.
    echo [ERROR] Erreur lors de l'installation
    echo.
)

pause
