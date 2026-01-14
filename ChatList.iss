; Скрипт Inno Setup для создания инсталлятора ChatList
; Версия: 1.0.0

#define MyAppName "ChatList"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ChatList"
#define MyAppURL "https://github.com/nikprog1/ChatList"
#define MyAppExeName "ChatList-1.0.0.exe"
#define MyAppId "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}"

[Setup]
; Основные настройки установщика
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=installer
OutputBaseFilename=ChatList-Setup-{#MyAppVersion}
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Основной исполняемый файл
Source: "dist\ChatList-1.0.0.exe"; DestDir: "{app}"; Flags: ignoreversion
; Файл иконки (если нужен отдельно)
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
; Пример файла окружения (опционально, для справки)
; Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(".env.example")
; README файл (опционально)
; Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists("README.md")

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\app.ico"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\app.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Удаление файлов при деинсталляции
Type: files; Name: "{app}\ChatList.db"
Type: files; Name: "{app}\*.log"
Type: filesandordirs; Name: "{app}\logs"
; Удаление файлов настроек (опционально, раскомментируйте если нужно)
; Type: files; Name: "{app}\.env.local"
; Type: files; Name: "{app}\.env"

[Code]
// Пользовательский код для проверок и дополнительной логики
procedure InitializeWizard;
begin
  // Можно добавить проверки версии Windows, наличия .NET Framework и т.д.
end;

function InitializeUninstall(): Boolean;
begin
  // Дополнительные проверки перед деинсталляцией
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  // Дополнительные действия на разных этапах деинсталляции
  case CurUninstallStep of
    usUninstall:
      begin
        // Действия перед началом деинсталляции
      end;
    usPostUninstall:
      begin
        // Действия после завершения деинсталляции
      end;
  end;
end;
