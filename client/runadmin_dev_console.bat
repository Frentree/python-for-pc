@echo off


rem %POWERSHELL% "start %CD%\utils\DebugView\dbgview.exe" -ArgumentList "/k","/g"
set POWERSHELL=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe Start-Process -verb RunAs
%POWERSHELL% -FilePath %CD%\utils\run_dev_console.bat %CD%

