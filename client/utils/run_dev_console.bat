@echo off

c:\windows\system32\tasklist | c:\windows\system32\findstr "Dbgview" > NUL
IF ERRORLEVEL 1 (
    start %1%\utils\DebugView\dbgview.exe /k /g
)

c:\windows\system32\tasklist | c:\windows\system32\findstr "ProcessHacker.exe" > NUL
IF ERRORLEVEL 1 (
    start %1%\utils\processhacker-2.39-bin\x64\processhacker.exe
)

c:\windows\system32\tasklist | c:\windows\system32\findstr "mmc.exe" > NUL
IF ERRORLEVEL 1 (
    start services.msc
)

set VCCONSOLE="C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\VsDevCmd.bat"
"C:\Windows\System32\cmd.exe" /K "%VCCONSOLE% & cd %1% "

rem start "C:\Program Files\Microsoft VS Code\Code.exe"
rem github
rem visual studio
rem "C:\Program Files\Microsoft VS Code\Code.exe" %1%
