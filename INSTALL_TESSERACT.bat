@echo off
REM Script d'installation Tesseract OCR pour Windows
REM Double-click ce fichier pour lancer l'installation

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║            Installation Tesseract OCR pour Windows                ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Vérifie si Tesseract est installé
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo [OK] Tesseract trouvé à C:\Program Files\Tesseract-OCR\tesseract.exe
    goto VERIFY_FRENCH
) else if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    echo [OK] Tesseract trouvé à C:\Program Files ^(x86^)\Tesseract-OCR\tesseract.exe
    goto VERIFY_FRENCH
) else (
    echo [ERROR] Tesseract n'est pas installé
    echo.
    echo Instructions d'installation:
    echo.
    echo 1. Télécharge l'installer depuis:
    echo    https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo 2. Cherche la dernière version:
    echo    - tesseract-ocr-w64-setup-v5.3.1.exe (64-bit, recommandé)
    echo    - tesseract-ocr-setup-v5.3.1.exe (32-bit)
    echo.
    echo 3. Double-click sur le fichier .exe
    echo.
    echo 4. Lors de l'installation, garde les chemins par défaut:
    echo    C:\Program Files\Tesseract-OCR
    echo.
    echo 5. Après installation, relance ce script
    echo.
    pause
    goto END
)

:VERIFY_FRENCH
echo.
echo [INFO] Vérification du pack français...
if exist "C:\Program Files\Tesseract-OCR\tessdata\fra.traineddata" (
    echo [OK] Pack français déjà installé
    goto CONFIGURE_PATH
) else if exist "C:\Program Files (x86)\Tesseract-OCR\tessdata\fra.traineddata" (
    echo [OK] Pack français déjà installé
    goto CONFIGURE_PATH
) else (
    echo [WARN] Pack français non trouvé
    echo.
    echo Le pack français sera téléchargé la première fois que tu exécuteras le programme.
    echo.
    goto CONFIGURE_PATH
)

:CONFIGURE_PATH
echo.
echo [INFO] Configuration du PATH...
echo.

REM Ajoute Tesseract au PATH de session
set "PATH=C:\Program Files\Tesseract-OCR;%PATH%"

REM Essaie d'ajouter au PATH système (nécessite admin)
echo Tentative d'ajout au PATH système (admin requis)...
setx PATH "C:\Program Files\Tesseract-OCR;%PATH%" >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] PATH système configuré
) else (
    echo [WARN] Impossible d'ajouter au PATH système (droits admin requis)
    echo.
    echo Solution: 
    echo   1. Clique-droit sur ce fichier
    echo   2. Sélectionne "Exécuter en tant qu'administrateur"
    echo.
)

REM Configure TESSDATA_PREFIX
echo.
echo [INFO] Configuration TESSDATA_PREFIX...
setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR\tessdata" >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] TESSDATA_PREFIX configuré
) else (
    echo [WARN] Impossible de configurer TESSDATA_PREFIX
)

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║              ✅ Configuration Terminée avec Succès!               ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.
echo Notes importantes:
echo   • Si tu as modifié le PATH système, redémarre PowerShell
echo   • Redémarre aussi l'explorateur Windows si tu as modifié le PATH
echo   • Teste avec: tesseract --version
echo   • Puis relance: python src/main.py
echo.
echo.
pause
goto END

:END
endlocal
