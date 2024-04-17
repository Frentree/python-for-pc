del dist\unittest.exe
python -m PyInstaller -F --hidden-import=win32timezone -n unittest main.py
