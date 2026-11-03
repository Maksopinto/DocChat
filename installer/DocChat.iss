; Inno Setup script for DocChat. Keep this file ASCII-only.
;
; Build (after build.bat has produced dist\DocChat):
;   Full installer (with bin\llama and models inside):   ISCC installer\DocChat.iss
;   Light installer (without the models folder):          ISCC /DLight installer\DocChat.iss
; The result is written to installer\Output\.

#define AppName "DocChat"
#define AppVersion "0.1.0"
#define AppExe "DocChat.exe"

[Setup]
AppId={{6E0D7B52-8C0F-4B6B-9B5E-3D6C1A2F9A11}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=DocChat
; Per-user install: no administrator rights needed (important on work PCs).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=no
OutputDir=Output
#ifdef Light
OutputBaseFilename=DocChat-Setup-Light
#else
OutputBaseFilename=DocChat-Setup
#endif
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern
Compression=lzma2/normal
SolidCompression=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Needed only if the installer grows past the single-file limit (about 2 GB).
DiskSpanning=no

[Languages]
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
#ifdef Light
Source: "..\dist\DocChat\*"; DestDir: "{app}"; Excludes: "models\*"; Flags: recursesubdirs createallsubdirs ignoreversion
#else
Source: "..\dist\DocChat\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
#endif

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: startmenuicon
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; User data (documents database, settings, logs) lives in the user profile
; (.docchat folder) and is intentionally NOT removed on uninstall.
