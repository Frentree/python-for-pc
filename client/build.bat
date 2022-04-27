rem start /b kill.bat

cd dist
installer remove
cd ..

rem taskkill /F /IM ftclient.exe
rem timeout 1
rem taskkill /F /IM x64.exe
rem timeout 1
rem taskkill /F /IM ftclient.exe
rem timeout 1
rem taskkill /F /IM x64.exe
rem timeout 1

python -m PyInstaller -F --hidden-import=win32timezone -n installer main.py
cd dist
installer
cd ..


copy dist\ftclient.exe ..\installer\ftservice

rem c:\windows\system32\msiexec /x ftservice.msi
rem cd ..\installer & devenv /ReBuild Release ftservice.sln
rem cd ..\client
