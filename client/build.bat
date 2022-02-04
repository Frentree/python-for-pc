python -m PyInstaller -F --hidden-import=win32timezone -n ftclient main.py
copy dist\ftclient.exe ..\installer\ftservice