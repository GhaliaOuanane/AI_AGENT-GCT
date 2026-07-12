@echo off
REM Lance install_fra.vbs avec droits administrateur

setlocal

REM Crée un script VBScript qui demande l'élévation
set "vbsFile=%temp%\elevate.vbs"

(
echo Set objShell = CreateObject("Shell.Application"^)
echo Set objFSO = CreateObject("Scripting.FileSystemObject"^)
echo strPath = objFSO.GetParentFolderName(WScript.ScriptFullName^)
echo objShell.ShellExecute "cscript.exe", "%cd%\install_fra.vbs", , "runas", 1
) > "%vbsFile%"

cscript.exe "%vbsFile%"

REM Nettoie le fichier temporaire
del "%vbsFile%"

exit /b 0
