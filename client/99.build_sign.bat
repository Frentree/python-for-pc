cd ..\00.RELEASE

path C:\Program Files (x86)\Microsoft SDKs\ClickOnce\SignTool
signtool.exe sign /s MY /tr http://timestamp.digicert.com /sha1 909A2269C0CC70DCAA37146B61F0EE3019B0FB69 package.exe
rem signtool.exe sign /tr http://timestamp.digicert.com /sha1 909A2269C0CC70DCAA37146B61F0EE3019B0FB69 install.exe
rem signtool.exe sign /tr http://timestamp.digicert.com /sha1 909A2269C0CC70DCAA37146B61F0EE3019B0FB69 uninstall.exe

cd ..\client