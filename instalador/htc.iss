; Instalador de HTC: por usuario (sin admin) en %LOCALAPPDATA%\Programs\HTC.
; Los datos (datos/, config.json) se crean junto al exe y no se borran al desinstalar.
#define Version "0.21.2"
[Setup]
AppId={{6B1F0C2E-4D1A-4C8E-9E57-48544301C11B}
AppName=Racha
AppVerName=Racha {#Version}
AppVersion={#Version}
SetupIconFile=htc.ico
DefaultDirName={localappdata}\Programs\HTC
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Racha-Setup-{#Version}
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\HTC.exe

[Files]
Source: "..\dist\HTC\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\scripts\*.py"; DestDir: "{app}\scripts"; Excludes: "test_*.py,humo_exe.py"; Flags: ignoreversion
Source: "..\scripts\web\*"; DestDir: "{app}\scripts\web"; Flags: recursesubdirs ignoreversion
Source: "..\scripts\fixtures\*"; DestDir: "{app}\scripts\fixtures"; Flags: recursesubdirs ignoreversion
Source: "..\docs\config.ejemplo.json"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; accesos directos de cuando la app se llamaba HTC (la carpeta y el .exe conservan el nombre para actualizar encima)
Type: files; Name: "{userprograms}\HTC.lnk"
Type: files; Name: "{userdesktop}\HTC.lnk"

[Dirs]
Name: "{app}\datos\raw"

[Icons]
Name: "{userprograms}\Racha"; Filename: "{app}\HTC.exe"
Name: "{userdesktop}\Racha"; Filename: "{app}\HTC.exe"; Tasks: escritorio

[Tasks]
Name: escritorio; Description: "Acceso directo en el escritorio"
Name: inicio; Description: "Arrancar Racha con Windows (se abre solo cuando abres LoL)"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "HTC"; ValueData: """{app}\HTC.exe"" --fondo"; Flags: uninsdeletevalue; Tasks: inicio

[Run]
Filename: "{app}\HTC.exe"; Parameters: "--fondo"; Flags: nowait runhidden; Tasks: inicio; Check: not WizardSilent
Filename: "{app}\HTC.exe"; Description: "Abrir Racha"; Flags: nowait postinstall skipifsilent
; auto-actualización (la app corre este instalador con /VERYSILENT /RACHA=--fondo o /RACHA=): Racha vuelve a abrirse como estaba
Filename: "{app}\HTC.exe"; Parameters: "{param:RACHA|}"; Flags: nowait; Check: WizardSilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM HTC.exe"; Flags: runhidden; RunOnceId: "CerrarHTC"

[Code]
// HTC en --fondo no tiene ventana: el Restart Manager no lo cierra y HTC.exe queda bloqueado al actualizar
function PrepareToInstall(var NeedsRestart: Boolean): String;
var R: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM HTC.exe', '', SW_HIDE, ewWaitUntilTerminated, R);
  Result := '';
end;
