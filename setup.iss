[Setup]
AppName=downVideos
AppVersion=1.6
DefaultDirName={sd}\downVideos
DefaultGroupName=downVideos
OutputDir=.
OutputBaseFilename=downVideos_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=.\downVideos.ico
DisableDirPage=yes

[Files]
Source: "\downVideos\downVideos.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "\downVideos\downVideos.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "\downVideos\ffmpeg\*"; DestDir: "{app}\ffmpeg"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\downVideos"; Filename: "{app}\downVideos.exe"
Name: "{commondesktop}\downVideos"; Filename: "{app}\downVideos.exe"

[Run]
Filename: "{app}\downVideos.exe"; Description: "Executar downVideos"; Flags: nowait postinstall skipifsilent