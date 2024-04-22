@REM note : 버전 정보가 들어가있는 파일 생성
python build.py generate_file_version

@REM note : 기존 생성되었던 구버전 삭제
del dist\ftclient.exe

@REM note : ftclient(실질적으로는 package.exe) 생성
python -m PyInstaller --version-file file_version.txt -F --hidden-import=win32timezone -n ftclient main.py

@REM note : 생성된 ftclient를 package로 이름 변경
copy dist\ftclient.exe  ..\00.RELEASE\package.exe

@REM note : 생성된 패키지 파일 사인 작업
cmd /c winsign ..\00.RELEASE\package.exe

@REM note : 생성된 파일들 압축 파일로 생성
python build.py
rem python tester.py

rem python -m PyInstaller -F -n tester tester.py
rem run.bat