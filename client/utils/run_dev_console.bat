@echo off

start %1%\utils\DebugView\dbgview.exe /k /g
start %1%\utils\processhacker-2.39-bin\x64\processhacker.exe
start c:\windows\system32\cmd.exe /K cd %1%
start "C:\Program Files\Microsoft VS Code\Code.exe"

rem github
rem visual studio
rem "C:\Program Files\Microsoft VS Code\Code.exe" %1%
