rem TODO - copy configuration_183.107.9.230.json ..\00.RELEASE
copy configuration.json ..\00.RELEASE
cd ..\00.RELEASE

rem uninstall
rem c:\windows\system32\timeout 3
rem install
cd ..\client
exit /b 0

rem set src_file=main
rem python %src_file%.py stop && timeout 2 && python %src_file%.py update && python %src_file%.py start