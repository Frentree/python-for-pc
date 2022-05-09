import servicemanager
import sys
import win32serviceutil
import threading
import concurrent.futures
import time
import logging
import ctypes
from lib_logging import *

config_logging(logging.DEBUG)

'''
# output "logging" messages to DbgView via OutputDebugString (Windows only!)
OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW

def prt(record):
    record_list = record.split('\n')
    PREFIX_FOR_FILTERING = "[TT]"
    for record_item in record_list:
        OutputDebugString(PREFIX_FOR_FILTERING+record_item)

prt("prt")
'''

class workingthread(threading.Thread):
    def __init__(self, quitEvent):
        log.info("__init__")
        self.quitEvent = quitEvent
        self.waitTime = 1
        threading.Thread.__init__(self)

    def run(self):
        log.info("run")
        try:
            # Running start_flask() function on different thread, so that it doesn't blocks the code
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
            executor.submit(self.start_flask)
        except:
            pass

        # Following Lines are written so that, the program doesn't get quit
        # Will Run a Endless While Loop till Stop signal is not received from Windows Service API
        while not self.quitEvent.isSet():  # If stop signal is triggered, exit
            time.sleep(1)

    def start_flask(self):
        # This Function contains the actual logic, of windows service
        # This is case, we are running our flaskserver
        while True:
          log.info("AAA")
          time.sleep(1)

class FlaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AA Testing1"
    _svc_display_name_ = "AAA Testing1"
    _svc_description_ = "This is my service1"

    def __init__(self, args):
        log.info("__init__")
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = threading.Event()
        self.thread = workingthread(self.hWaitStop)

    def SvcStop(self):
        log.info("SvcStop")
        self.hWaitStop.set()

    def SvcDoRun(self):
        log.info("SvcDoRun")
        self.thread.start()
        self.hWaitStop.wait()
        self.thread.join()


if __name__ == '__main__':
    log.info("__main__")
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FlaskService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(FlaskService)