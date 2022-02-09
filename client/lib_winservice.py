import win32service, win32api, win32con, winerror
import sys, pywintypes, os, warnings
error = RuntimeError

# Reference: https://github.com/SublimeText/Pywin32/blob/master/lib/x32/win32/lib/win32serviceutil.py

# Open a service given either it's long or short name.
def SmartOpenService(hscm, name, access):
    try:
        return win32service.OpenService(hscm, name, access)
    except win32api.error as details:
        if details.winerror not in [winerror.ERROR_SERVICE_DOES_NOT_EXIST,
                                    winerror.ERROR_INVALID_NAME]:
            raise
    name = win32service.GetServiceKeyName(hscm, name)
    return win32service.OpenService(hscm, name, access)

def StartService(serviceName, args = None, machine = None):
    hscm = win32service.OpenSCManager(machine,None,win32service.SC_MANAGER_ALL_ACCESS)
    try:

        hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
        try:
            win32service.StartService(hs, args)
        finally:
            win32service.CloseServiceHandle(hs)
    finally:
        win32service.CloseServiceHandle(hscm)

