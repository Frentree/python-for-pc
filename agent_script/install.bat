@echo off
REM PIMC_WinPC_����_�׽�Ʈ
REM �����
REM Agent version : 2.3.1
set IP=90.217.245.31
REM Ŀ���� ��� ��ġ �Ǵ� DIRECTORY�� ���� ���� �� DRM�� ��ġ���� �ʽ��ϴ�.
REM set DIRECTORY="C:\Program Files (x86)\Ground Labs\Enterprise Recon 2"
set DIRECTORY=
set VERSION=1.0.9_drm_test
set LOG_PATH=%temp%\er2.log
REM set LOG_PATH=%temp%\..\..\..\Desktop

if exist "C:\Temp" (
	if exist "C:\Temp\er2.log" (
		del /s /q "C:\Temp\er2.log"
	)
) else (
	mkdir C:\Temp
)
echo start installation > %LOG_PATH%

cls
REM =============== ��ġ ���� ��� ���� ===============
if exist "%temp%\ER\agent.cfg" (
	echo agent.cfg exists
	copy /s /q %temp%\ER\agent.cfg c:\temp\bak.cfg
) else (
	rmdir /s /q "%temp%\ER"
	del /s /q "%temp%\ER"
)
if exist "%temp%\PIMC" (
	rmdir /s /q "%temp%\PIMC"
)
if exist "%temp%\ftclient" (
	rmdir /s /q "%temp%\ftclient"
)
if exist "C:\Temp\er2.log" (
	del /s /q "C:\Temp\er2.log"
)
cd >> %LOG_PATH%
mkdir "%temp%\ER"
mkdir "%temp%\PIMC"

REM =============== ��ġ ���� ���� ===============
copy 64.bat "%temp%\PIMC"
copy er2_x64.msi "%temp%\PIMC"
copy 32.bat "%temp%\PIMC"
copy er2_x32.msi "%temp%\PIMC"
copy install.exe "%temp%\PIMC"
copy package.exe "%temp%\PIMC"
copy configuration.json "%temp%\PIMC"
copy ftclient.dll "%temp%\PIMC"

REM =============== ���� �� ��� Ȯ�� �� ��ġ ��ũ��Ʈ ���� ===============
if exist %windir%\SysWOW64 (
	if "%DIRECTORY%"=="" (
echo install x64 bit default location >> %LOG_PATH%
		dir >> %LOG_PATH%
		.\64.bat %IP% "C:\Program Files (x86)\Ground Labs\Enterprise Recon 2" %VERSION% %LOG_PATH% >> %LOG_PATH%
	) else (
		echo install x64 bit custom location >> %LOG_PATH%
		dir >> %LOG_PATH%
		.\64.bat %IP% %DIRECTORY% %DRM% %VERSION% %LOG_PATH% >> %LOG_PATH%
	)
	echo error with %errorlevel% >> %LOG_PATH%

	echo =============== 64 Remove rest file ===============
	REM rmdir /s /q "%temp%\ER"
	rmdir /s /q "%temp%\PIMC"
	rmdir /s /q "%temp%\ftclient"
) else (
	if "%DIRECTORY%"=="" (
		echo install x32 bit default location >> %LOG_PATH%
		.\32.bat %IP% "C:\Program Files\Ground Labs\Enterprise Recon 2" %VERSION% >> %LOG_PATH%
		echo test3
	) else (
		echo install x32 bit custom location >> %LOG_PATH%
		.\32.bat %IP% %DIRECTORY% %VERSION% >> %LOG_PATH%
	)

	echo error with %errorlevel% >> %LOG_PATH%

	echo =============== 32 Remove rest file ===============
	REM rmdir /s /q "%temp%\ER"
	rmdir /s /q "%temp%\PIMC"
	rmdir /s /q "%temp%\ftclient"	
)

exit 0

pause