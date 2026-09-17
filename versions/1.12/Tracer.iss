[Setup]
AppId={{32C7593A-778E-4DA9-9B44-29F5EE5D815E}
AppName=Tracer
AppVersion=1.12.0
AppPublisher=Tracer
DefaultDirName={localappdata}\Programs\Tracer
DefaultGroupName=Tracer
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=release
OutputBaseFilename=Tracer-Setup-1.12.0
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Tracer.exe
SetupIconFile=assets\transpro.ico
CloseApplications=yes
DisableProgramGroupPage=yes

[Files]
Source: "dist\Tracer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "data\*"
Source: "dist\Tracer\data\models\tiny\*"; DestDir: "{app}\data\models\tiny"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs uninsneveruninstall
Source: "dist\Tracer\data\models\visual-index\*"; DestDir: "{app}\data\models\visual-index"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs uninsneveruninstall

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Icons]
Name: "{group}\Tracer"; Filename: "{app}\Tracer.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Tracer"; Filename: "{app}\Tracer.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Tracer.exe"; Description: "Open Tracer"; Flags: nowait postinstall skipifsilent
