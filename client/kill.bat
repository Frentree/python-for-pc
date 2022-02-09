c:\windows\system32\taskkill /F /IM pythonservice.exe
c:\windows\system32\taskkill /F /IM ftclient.exe

c:\windows\system32\sc stop ftservice
c:\windows\system32\sc delete ftservice

c:\windows\system32\sc stop MyService
c:\windows\system32\sc delete MyService
