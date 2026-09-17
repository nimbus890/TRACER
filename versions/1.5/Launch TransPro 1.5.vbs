Set shell = CreateObject("WScript.Shell")
Set environment = shell.Environment("Process")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
root = files.GetParentFolderName(files.GetParentFolderName(folder))
environment("TRANSPRO_DATA") = root & "\data"
shell.Run Chr(34) & root & "\.venv\Scripts\pythonw.exe" & Chr(34) & " " & Chr(34) & folder & "\app.py" & Chr(34), 0, False
