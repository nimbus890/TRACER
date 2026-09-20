[Setup]
AppId={{32C7593A-778E-4DA9-9B44-29F5EE5D815E}
AppName=Tracer
AppVersion=2.0.0
AppPublisher=SCG
DefaultDirName={localappdata}\Programs\Tracer
DefaultGroupName=Tracer
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=Tracer-Setup-2.0.0
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Tracer.exe
SetupIconFile=assets\transpro.ico
CloseApplications=yes
DisableProgramGroupPage=yes

[Files]
Source: "..\portable\Tracer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "data\*"
Source: "..\portable\Tracer\data\models\*"; DestDir: "{app}\data\models"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs uninsneveruninstall

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Icons]
Name: "{group}\Tracer"; Filename: "{app}\Tracer.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Tracer"; Filename: "{app}\Tracer.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Tracer.exe"; Description: "Open Tracer"; Flags: nowait postinstall skipifsilent
