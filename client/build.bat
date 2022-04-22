rem start /b kill.bat

cd dist
ftclient closedown
cd ..

taskkill /F /IM ftclient.exe
timeout 1
taskkill /F /IM x64.exe
timeout 1
taskkill /F /IM ftclient.exe
timeout 1
taskkill /F /IM x64.exe
timeout 1

python -m PyInstaller -F --hidden-import=win32timezone -n ftclient main.py
cd dist
ftclient setup
cd ..


rem copy dist\ftclient.exe ..\installer\ftservice
rem c:\windows\system32\msiexec /x ftservice.msi
rem cd ..\installer & devenv /ReBuild Release ftservice.sln
rem cd ..\client
