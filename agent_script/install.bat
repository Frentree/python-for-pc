@echo off
REM PIMC_WinPC_내부_테스트
REM 유통망
REM Agent version : 2.3.1
set IP=90.217.245.31
REM 커스텀 경로 설치 또는 DIRECTORY에 값이 있을 시 DRM은 설치되지 않습니다.
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
REM =============== 설치 파일 경로 세팅 ===============
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

REM =============== 설치 파일 복사 ===============
copy 64.bat "%temp%\PIMC"
copy er2_x64.msi "%temp%\PIMC"
copy 32.bat "%temp%\PIMC"
copy er2_x32.msi "%temp%\PIMC"
copy install.exe "%temp%\PIMC"
copy package.exe "%temp%\PIMC"
copy configuration.json "%temp%\PIMC"
copy ftclient.dll "%temp%\PIMC"

REM =============== 버전 및 경로 확인 후 설치 스크립트 진행 ===============
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