import win32serviceutil
import servicemanager
import ctypes
import sys
import time

OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW

class MyServiceFramework(win32serviceutil.ServiceFramework):
  _svc_name_ = 'MyPythonService1'
  _svc_display_name_ = 'My Python Service1'
  is_running = False

  def SvcStop(self):
    OutputDebugString("MyServiceFramework __SvcStop__")
    self.is_running = False

  def SvcDoRun(self):
    self.is_running = True
    while self.is_running:
      OutputDebugString("MyServiceFramework __loop__")
      time.sleep(5)

if '__main__' == __name__:
  win32serviceutil.HandleCommandLine(MyServiceFramework)