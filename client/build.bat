start /b kill.bat
python -m PyInstaller -F --hidden-import=win32timezone -n ftclient main.py
copy dist\ftclient.exe ..\installer\ftservice
c:\windows\system32\msiexec /x ftservice.msi
cd ..\installer & devenv /ReBuild Release ftservice.sln
cd ..\client
