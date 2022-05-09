import win32serviceutil
import sys
import servicemanager
import ctypes



# output "logging" messages to DbgView via OutputDebugString (Windows only!)
OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW

def prt(record):
    record_list = record.split('\n')
    PREFIX_FOR_FILTERING = "[TT]"
    for record_item in record_list:
        OutputDebugString(PREFIX_FOR_FILTERING+record_item)



class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "TestService"
    _svc_display_name_ = "Test Service"

    def __init__(self,args):
        prt("__init__")
        win32serviceutil.ServiceFramework.__init__(self,args)
        #self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        #socket.setdefaulttimeout(60)

    def SvcStop(self):
        prt("SvcStop")
        #self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        #win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        prt("SvcDoRun")
        self.main()

    def main(self):
        prt("main")
        pass

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AppServerSvc)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AppServerSvc)    