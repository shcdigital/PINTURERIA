; Script de Inno Setup para Gestor de Ofertas Proveesur
; Desarrollado por SHC Digital
#define MyAppName "Gestor de Ofertas Proveesur"
#define MyAppVersion "1.0"
#define MyAppPublisher "SHC Digital"
#define MyAppURL "https://shcdigital.github.io/PINTURERIA/"
#define MyAppExeName "GestorOfertas.exe"

[Setup]
AppId={{B8A7C3D1-9F4E-4A2D-9C7E-5F1B3D8E2A6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=GestorOfertas_Installer
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\icon.ico
UninstallDisplayName={#MyAppName}

[Messages]
WelcomeLabel2=Este instalador va a instalar [name/ver] en tu computadora.%n%nDesarrollado por SHC Digital

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\dist\GestorOfertas.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\drafts\*"; DestDir: "{app}\drafts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Acceso directo:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Flags: runhidden; Parameters: "--uninstall"
