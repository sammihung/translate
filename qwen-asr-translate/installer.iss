; Inno Setup Script for QwenASR Translate
; Download Inno Setup: https://jrsoftware.org/isdl.php

#define MyAppName "QwenASR Translate"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Your Name"
#define MyAppExeName "QwenASR Translate.exe"

[Setup]
; 基本設定
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=QwenASR-Translate-Setup-{#MyAppVersion}
SetupIconFile=compiler:SetupClassicIcon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; 系統需求
MinVersion=10.0.18362
ArchitecturesAllowed=x64compatible
PrivilegesRequired=admin

; 安裝選項
DisableDirPage=no
DisableReadyPage=no
ShowLanguageDialog=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "traditionalchinese"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"
Name: "simplechinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; 主程式資料夾
Source: "dist\QwenASR Translate\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; 安裝完成後執行程式
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; 安裝後檢查 Ollama
Filename: "https://ollama.ai/download"; Description: "Download Ollama (Required for Translation)"; Flags: shellexec postinstall skipifsilent

[Code]
// 安裝前檢查
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // 檢查是否已安裝 Ollama
  if not RegKeyExists(HKLM, 'SOFTWARE\Ollama') then
  begin
    if MsgBox('Ollama is not installed. It is required for translation feature.' + #13#10 + #13#10 + 'Do you want to continue installation?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;

// 安裝完成後顯示提示
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    MsgBox('Installation completed!' + #13#10 + #13#10 + 
           'Please note:' + #13#10 + 
           '1. Ollama is required for translation' + #13#10 + 
           '2. Download from: https://ollama.ai' + #13#10 + 
           '3. Run: ollama pull translategemma:4b-it-q4_K_M',
           mbInformation, MB_OK);
  end;
end;
