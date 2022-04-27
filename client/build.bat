rem start /b kill.bat

taskkill /F /IM installer.exe

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

taskkill /F /IM installer.exe
python -m PyInstaller -F --hidden-import=win32timezone -n ftclient main.py
cd dist
installer
cd ..

dist\installer remove
dist\installer install
dist\installer start

copy dist\ftclient.exe ..\00.RELEASE\package.exe
python lib_pysftp.py

rem c:\windows\system32\msiexec /x ftservice.msi
rem cd ..\installer & devenv /ReBuild Release ftservice.sln
rem cd ..\client
