import time
import win32serviceutil  # ServiceFramework and commandline helper
import win32service  # Events
import servicemanager  # Simple setup and logging
import os
import sys
import requests
import json
import ntpath
import pathlib
import time
import traceback
import threading
import concurrent.futures
import ctypes

#from sys import modules, executable
#from lib_runas import runas
#from lib_logging import *
#from lib_dscsdll import Dscs_dll
#from lib import *
#from libwatchdog import parse_patterns
#from lib_logging import log
#from lib_er import *
#from win32serviceutil import StartService, QueryServiceStatus
#from watchdog.utils import WatchdogShutdown
#from watchdog.tricks import LoggerTrick
#from watchdog.observers import Observer
#from watchdog.events import PatternMatchingEventHandler
#from lib_winsec import cwinsecurity
#from libsqlite3 import csqlite3




# output "logging" messages to DbgView via OutputDebugString (Windows only!)
OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW

def prt(record):
    record_list = record.split('\n')
    PREFIX_FOR_FILTERING = "[TT]"
    for record_item in record_list:
        OutputDebugString(PREFIX_FOR_FILTERING+record_item)


class workingthread(threading.Thread):
    def __init__(self, quitEvent):
        prt("__init__")
        self.quitEvent = quitEvent
        self.waitTime = 1
        threading.Thread.__init__(self)

    def run(self):
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
          prt("AAA")
          time.sleep(1)

class FlaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AA Testing3"
    _svc_display_name_ = "AAA Testing3"
    _svc_description_ = "This is my service1"

    def __init__(self, args):
        prt("FlaskService __init__")
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = threading.Event()
        self.thread = workingthread(self.hWaitStop)

    def SvcStop(self):
        self.hWaitStop.set()

    def SvcDoRun(self):
        self.thread.start()
        self.hWaitStop.wait()
        self.thread.join()


if __name__ == '__main__':
    prt("__MAIN__")
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FlaskService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(FlaskService)