[Setup]
AppName=Timeline 2 Images
AppVersion={#AppVersion}
AppPublisher=David Hamber
AppPublisherURL=https://github.com/davidhamber/timeline-2-images
AppSupportURL=https://github.com/davidhamber/timeline-2-images/issues
AppUpdatesURL=https://github.com/davidhamber/timeline-2-images/releases
DefaultDirName={pf}\Timeline2Images
DefaultGroupName=Timeline 2 Images
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64
OutputDir=dist
OutputBaseFilename=timeline2images-{#AppVersion}-windows-installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
LicenseFile=LICENSE.txt
ShowLanguageDialog=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\timeline2images.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\timeline2images-gui.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\Timeline 2 Images (GUI)"; Filename: "{app}\timeline2images-gui.exe"; IconIndex: 0
Name: "{group}\Timeline 2 Images (CLI)"; Filename: "{cmd}"; Parameters: "/k ""{app}\timeline2images.exe"" --help"; IconIndex: 0
Name: "{commondesktop}\Timeline 2 Images"; Filename: "{app}\timeline2images-gui.exe"; IconIndex: 0
Name: "{group}\{cm:UninstallProgram,Timeline 2 Images}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\timeline2images-gui.exe"; Description: "Launch Timeline 2 Images"; Flags: postinstall skipifsilent nowait

[UninstallDelete]
Type: filesandfolders; Name: "{localappdata}\timeline-2-images"
