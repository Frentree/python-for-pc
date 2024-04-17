@echo off
set IP=%1 >> log.txt
set DIRECTORY=%~2
set VERSION=%3
set LOG_PATH=%temp%\er2.log

if "%IP: =%"=="150.19.24.205" (
	set NETWORK="OA"
) else if "%IP: =%"=="150.19.24.206" (
	set NETWORK="VDI"
) else if "%IP: =%"=="90.217.245.31" (
	set NETWORK="Distribute"
)

echo check auth >> %LOG_PATH%

>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
	goto UACPrompt
) else (
	goto agentInstall
)

:UACPrompt
	echo generate getadmin.vbs >> %LOG_PATH%
	echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\PIMC\getadmin.vbs"
	echo UAC.ShellExecute "cmd.exe", "/c %temp%\PIMC\64.bat", "", "runas", 0 >> "%temp%\PIMC\getadmin.vbs"
	 
	"%temp%\PIMC\getadmin.vbs" >> %LOG_PATH%
	
	del "%temp%\PIMC\getadmin.vbs"
	exit /B

:agentInstall
	echo =============== start installation =============== >> %LOG_PATH%
	if exist "%DIRECTORY%\DRM\ftclient.exe" (
		echo =============== installed. start uninstalling ===============
		if exist "%DIRECTORY%\DRM" (
			"%temp%\PIMC\package.exe" _remove
			"%DIRECTORY%\DRM\ftclient.exe" _unhide_svc
			"%DIRECTORY%\DRM\ftclient.exe" _dbg_stop_all
			REM "%DIRECTORY%\DRM\ftclient.exe" remove_svc
			"%DIRECTORY%\DRM\ftclient.exe" _remove
			"taskkill /f /im ftclient.exe"
			"taskkill /f /im ftclient.exe"
			rmdir /s /q "%DIRECTORY%\DRM"
		)
		if exist "%DIRECTORY%\DRM\ftclient.exe" (
			"%DIRECTORY%\DRM\ftclient.exe" _dbg_stop
			"%DIRECTORY%\DRM\ftclient.exe" _dbg_stop_all
			"%temp%\PIMC\uninstall.exe"
			rmdir /s /q "%DIRECTORY%\DRM"
		)
	)
	REM DLL 파일 복사 추가(테스트)
	REM xcopy "%temp%\PIMC\ftclient.dll" "%DIRECTORY%\DRM\DSCSLink64.dll" /Y

	timeout 3

	REM PS&M 영역만 DSCSLink64.dll 파일 복사해서 사용
	REM copy /y C:\Windows\DSCSLink64.dll C:\Windows\DSCSLink641.dll	

	echo =============== setting recon service active =============== >> %LOG_PATH%
	sc sdset "Enterprise Recon 2 Agent" "D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)"
	sc query "Enterprise Recon 2 Agent"

	if %errorlevel% == 0 (
		echo =============== Backup the agent.cfg =============== >> %LOG_PATH%
		if exist "%DIRECTORY%\agent.cfg" (
			icacls "%DIRECTORY%\agent.cfg" /grant Administrators:DW
			copy "%DIRECTORY%\agent.cfg" "%temp%\ER\agent.cfg"
		)
		echo =============== ER2 Agent Stop for uninstalling =============== >> %LOG_PATH%
		net stop "Enterprise Recon 2 Agent"
		echo =============== ER2 Agent Stopped. uninstall start =============== >> %LOG_PATH%
		wmic product where name="Enterprise Recon 2 Agent (x64)" uninstall
		echo =============== ER2 Agent uninstall complete =============== >> %LOG_PATH%
	)

REM   =============== delete folder ===============	
	rmdir /s /q "%DIRECTORY%"
	mkdir "%DIRECTORY%"

	echo =============== Restore the agent.cfg =============== >> %LOG_PATH%
	if exist "%temp%\ER\agent.cfg" (
		copy /y "%temp%\ER\agent.cfg" "%DIRECTORY%\agent.cfg"
	)

	echo =============== start install ER2 msi File =============== >> %LOG_PATH%
	msiexec.exe /i "%temp%\PIMC\er2_x64.msi" /QN INSTALLDIR="%DIRECTORY%\" TARGETIP=%IP%

	echo =============== Check Mac address =============== >> %LOG_PATH%
	sc stop "Enterprise Recon 2 Agent"
	move "%DIRECTORY%\agent.cfg" "%DIRECTORY%\backup.cfg"
	setlocal enabledelayedexpansion
	for /f "skip=1 tokens=2 delims==" %%a in ('wmic nic where "NetConnectionStatus=2 and PhysicalAdapter=True" get MACAddress /value') do (
	  set "mac=%%a"
	  if "!mac!" neq "" (
	    set "internet_mac=!mac::=!"
	    goto output
	  )
	)
	endlocal
	
	:output
	echo mac_address %internet_mac% >> %LOG_PATH%
		
	echo ^<cfg^> > "%DIRECTORY%\agent.cfg"
	type "%DIRECTORY%\backup.cfg" | find "remote" >> "%DIRECTORY%\agent.cfg"
	REM echo   ^<domain^>%internet_mac%^</domain^> >> "%DIRECTORY%\agent.cfg"
	type "%DIRECTORY%\backup.cfg" | find "localkey" >> "%DIRECTORY%\agent.cfg"
	echo ^</cfg^> >> "%DIRECTORY%\agent.cfg"
	
	sc start "Enterprise Recon 2 Agent"
	del "%DIRECTORY%\backup.cfg"

	if exist "%DIRECTORY%\agent.cfg" (
		echo =============== Hide ER2 Service from list =============== >> %LOG_PATH%
		sc failure "Enterprise Recon 2 Agent" actions= restart/5000/restart/5000/restart/5000 reset=1
		sc sdset "Enterprise Recon 2 Agent" "D:(D;;DCLCWPDTSD;;;IU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)"

		echo =============== Remove uninstall file =============== >> %LOG_PATH%
		for /f "tokens=1 delims= " %%a IN ('reg query HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\ /f "http://www.groundlabs.com/support" /s ^| find "HKEY"') do (
			reg delete %%a /f>null
		)

		echo =============== DRM Install Start ===============
		if exist "%DIRECTORY%\DRM" (
			echo =============== drm folder exist ===============
		) else (
			echo =============== make drm folder ===============
			mkdir "%DIRECTORY%\DRM"				
		)
		copy "%temp%\PIMC\configuration.json" "%DIRECTORY%\DRM\"
		REM DLL 파일 복사 추가(테스트)
		rem copy "%temp%\PIMC\ftclient.dll" "%DIRECTORY%\DRM\frentree.dll"
		copy "%temp%\PIMC\ftclient.dll" "C:\Windows\frentree.dll"

		

		cd "%DIRECTORY%\DRM\"
		echo =============== Proceed DRM Install ===============
		"%temp%\PIMC\install.exe"
		if exist "%DIRECTORY%\DRM" (
			"%temp%\PIMC\package.exe"
		)
		if exist "%DIRECTORY%\DRM\ftclient.exe" (
			echo =============== complete drm ===============
		) else (
			mkdir "%DIRECTORY%\DRM"
			"%temp%\PIMC\package.exe"
		)

		echo %VERSION% > "%DIRECTORY: "=%\%VERSION%.ver
		echo %NETWORK% > "%DIRECTORY: "=%\%NETWORK%.net

		echo =============== Remove rest file ===============
		REM del /s /q "C:\Temp\er2.log"
		echo =============== Finish installation ===============
	) else (
		REM =============== fail ===============
		exit -1
	)

	REM pause