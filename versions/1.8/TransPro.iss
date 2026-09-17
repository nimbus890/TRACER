[Setup]
AppId={{32C7593A-778E-4DA9-9B44-29F5EE5D815E}
AppName=TransPro
AppVersion=1.8.0
AppPublisher=TransPro
DefaultDirName={localappdata}\Programs\TransPro
DefaultGroupName=TransPro
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=release
OutputBaseFilename=TransPro-Setup-1.8.0
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\TransPro.exe
SetupIconFile=assets\transpro.ico
CloseApplications=yes
DisableProgramGroupPage=yes

[Files]
Source: "dist\TransPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "data\*"
Source: "dist\TransPro\data\models\tiny\*"; DestDir: "{app}\data\models\tiny"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs uninsneveruninstall
Source: "dist\TransPro\data\models\visual-index\*"; DestDir: "{app}\data\models\visual-index"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs uninsneveruninstall

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Icons]
Name: "{group}\TransPro"; Filename: "{app}\TransPro.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\TransPro"; Filename: "{app}\TransPro.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\TransPro.exe"; Description: "Open TransPro"; Flags: nowait postinstall skipifsilent
