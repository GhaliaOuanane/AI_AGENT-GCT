@echo off
REM Lance le script PowerShell install_fra.ps1 avec droits administrateur

setlocal enabledelayedexpansion

REM Vérifie les droits admin
whoami /groups | findstr "12288" >nul
if %errorlevel% neq 0 (
    echo Ce script doit être exécuté EN TANT QU'ADMINISTRATEUR
    echo.
    echo Clique-droit sur ce fichier et sélectionne:
    echo "Exécuter en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║       Installation de fra.traineddata (Admin OK)                  ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File install_fra.ps1

pause
