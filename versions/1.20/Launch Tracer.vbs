Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = root
runtime = root & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(runtime) Then
    workspace = fso.GetParentFolderName(fso.GetParentFolderName(root))
    runtime = workspace & "\.venv\Scripts\pythonw.exe"
End If
If fso.FileExists(runtime) Then
    shell.Run Chr(34) & runtime & Chr(34) & " " & Chr(34) & root & "\app.py" & Chr(34), 0, False
Else
    MsgBox "Tracer's Python runtime was not found. Open Tracer from its main workspace or restore the .venv folder.", 16, "Tracer"
End If
