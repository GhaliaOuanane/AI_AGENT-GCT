' Script VBScript pour copier fra.traineddata avec élévation de privilèges
' Clic-droit → Exécuter en tant qu'administrateur

Dim objFSO, source, dest

Set objFSO = CreateObject("Scripting.FileSystemObject")

source = "C:\Users\ghali\Downloads\fra.traineddata"
dest = "C:\Program Files\Tesseract-OCR\tessdata\fra.traineddata"

' Vérifie la source
If Not objFSO.FileExists(source) Then
    MsgBox "Fichier source introuvable: " & source, 16, "Erreur"
    WScript.Quit 1
End If

' Affiche un message
MsgBox "Copie de fra.traineddata en cours...", 64, "Installation"

' Copie le fichier
On Error Resume Next
objFSO.CopyFile source, dest, True
On Error GoTo 0

' Vérifie que le fichier est là
If objFSO.FileExists(dest) Then
    MsgBox "✅ Installation Réussie!" & vbCrLf & vbCrLf & "Fichier: " & dest, 64, "Succès"
    WScript.Quit 0
Else
    MsgBox "❌ Erreur: Le fichier n'a pas pu être copié" & vbCrLf & vbCrLf & "Destination: " & dest, 16, "Erreur"
    WScript.Quit 1
End If
