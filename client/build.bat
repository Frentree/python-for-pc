python build.py generate_file_version

del dist\ftclient.exe
python -m PyInstaller --version-file file_version.txt -F --hidden-import=win32timezone -n ftclient main.py
copy dist\ftclient.exe  ..\00.RELEASE\package.exe

python build.py
run.bat