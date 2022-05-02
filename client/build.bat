@echo off
rem start /b kill.bat

rem taskkill /F /IM ftclient.exe
rem timeout 1
rem taskkill /F /IM x64.exe
rem timeout 1
rem taskkill /F /IM ftclient.exe
rem timeout 1
rem taskkill /F /IM x64.exe
rem timeout 1

rem taskkill /F /IM installer.exe
python -m PyInstaller -F --hidden-import=win32timezone -n ftclient main.py

rem dist\installer remove
rem dist\installer install
rem dist\installer start

copy dist\ftclient.exe ..\00.RELEASE\package.exe
cd ..\00.RELEASE
uninstall
install
cd ..\client
rem python lib_pysftp.py

rem c:\windows\system32\msiexec /x ftservice.msi
rem cd ..\installer & devenv /ReBuild Release ftservice.sln
rem cd ..\client
