Option Explicit

Dim pythonPath

'***********************************************************
'ここを各自Python 2.7のパスに書き換えてください
pythonPath = ""
'pythonPath = "C:\Python27\python.exe"
'***********************************************************

If Wscript.Arguments.Count = 0 Then
  MsgBox "変換するディレクトリをドラッグ＆ドロップしてください。", 48, "azw2zip"
  Wscript.Quit
End If

Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")

Dim vbsPath
vbsPath = fso.getParentFolderName(WScript.ScriptFullName)

Dim WshShell
Set WshShell = WScript.CreateObject("WScript.Shell")

If pythonPath = "" Then
  MsgBox "Pythonのパスが設定されていません。" & vbCrLf & "azw2zip.vbs を編集して python.exe のパスを設定してください。", 48, "azw2zip"
  EditVBS(vbsPath & "\azw2zip.vbs")
  Wscript.Quit
End If

If fso.FileExists(pythonPath) = False Then
  MsgBox pythonPath + " が見つかりません。" & vbCrLf & "azw2zip.vbs を編集して python.exe のパスを設定してください。", 48, "azw2zip"
  EditVBS(vbsPath & "\azw2zip.vbs")
  Wscript.Quit
End If

Dim pythonCmd

pythonCmd = pythonPath + " """ & vbsPath & "\azw2zip.py"" """ & Wscript.Arguments.Item(0) & """ """ & vbsPath & """"
'zipでなくEPUBで出力するなら下の行のコメントを解除
'pythonCmd = pythonPath + " """ & vbsPath & "\azw2zip.py"" -e """ & Wscript.Arguments.Item(0) & """ """ & vbsPath & """"

WshShell.Run(pythonCmd)

Set WshShell = Nothing
Set fso = Nothing

'メモ帳でこのファイルを開く
Sub EditVBS(FilePath)
  WshShell.Run "%windir%\system32\notepad.exe """ & FilePath & """", 1, False
End Sub
