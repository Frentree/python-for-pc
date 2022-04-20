import os
import sys
import json
import ntpath
import time
import win32service
import win32serviceutil  # ServiceFramework and commandline helper
import servicemanager  # Simple setup and logging
from win32serviceutil import StartService, QueryServiceStatus, ServiceFramework, HandleCommandLine
from lib_runas import runas
from lib_logging import log

class MyService:
    """ application stub"""

    configuration = {
        "debug":True,
        "sleep_seconds": 10,
        "dll_name": "CryptDll.dll",
        "server_address":"183.107.9.230:11119",
        "hostname": "175.203.71.27",
        "bAppendDecryptedPostfix": True,
        "service_name": "Enterprise Recon 2 Agent",

        "min_sleep_seconds": 1,
    }
    self_path = ""

    def __init__(self):
        self.load_config()

    def stop(self):
        """Stop the service"""
        log.debug("Service stop")
        self.running = False

    def load_config(self):
        if 'python.exe' == os.path.basename(sys.executable):
            conf_path = "." + "\\configuration.json"
        else:
            conf_path = os.path.dirname(sys.executable) + "\\configuration.json"
        log.info("LOAD_CONFIG: " + conf_path)
        if False == os.path.isfile(conf_path):
            log.error("file not found")
            return
        else:
            with open(conf_path, "r", encoding="utf-8-sig") as json_conf_file:
                file_content = json_conf_file.read()
                configuration = json.loads(file_content)
        configuration['hostname'] = self.get_hostname()
        configuration['min_sleep_seconds'] = 1

        log.info(configuration)

        self.configuration = configuration
        MyService.configuration = configuration

    def save_config(self):
        if 'python.exe' == os.path.basename(sys.executable):
            conf_path = "." + "\\configuration.json"
        else:
            conf_path = os.path.dirname(sys.executable) + "\\configuration.json"
        log.debug("SAVE_CONFIG: " + conf_path)

        if False == os.path.isfile(conf_path):
            log.error("file not found")
            return
        else:
            try:
                with open(conf_path, 'w', encoding="utf-8-sig") as json_out_file:
                    json.dump(self.configuration, json_out_file, indent=4, ensure_ascii=False)
                    log.debug("SAVE_CONFIG: " + json.dumps(self.configuration, ensure_ascii=False))
            except FileNotFoundError as e:
                log.error(str(e))
                pass

    def get_hostname(self):
        return os.getenv("COMPUTERNAME", "")

    def run(self):
        """Main service loop. This is where work is done!"""
        log.debug("Service start")
        self.running = True

        helpercmd = "\""+ntpath.dirname(sys.executable) + "\\" + "helper.exe\""+" -n ftclient.exe"
        log.debug(helpercmd)
        os.system(helpercmd)

        while self.running:
            try:
                log.debug(self.configuration['server_address'])
                log.debug("run as " + sys.executable)
                runas("\""+sys.executable+"\"", "do_job")
                # helpercmd = "\""+ntpath.dirname(sys.executable) + "\\" + "helper.exe\""+" -n ftclient.exe"
                # log.debug(helpercmd)
                # os.system(helpercmd)

                self.load_config()
                if True != self.configuration['flag_skip_checking_er_service']:
                    ensure_svc_running(self.configuration['service_name'])
            except Exception as e:
                log.error(e)
                pass
            finally:
                from lib_winsec import cwinsecurity
                log.error("integrity level: " + cwinsecurity.get_integrity_level())
                sleep_seconds = max(self.configuration["min_sleep_seconds"], self.configuration["sleep_seconds"])
                log.info("sleep " + str(sleep_seconds) + " seconds")
                time.sleep(sleep_seconds) # Important work
            continue
            servicemanager.LogInfoMsg("Service running...")

    def run(self):
      print("RUN SERViCE")      

class MyServiceFramework(ServiceFramework):

    _svc_name_ = 'MyService'
    _svc_display_name_ = 'My Service display name'

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.service_impl.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        """Start the service; does not return until stopped"""
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.service_impl = MyService()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        # Run the service
        self.service_impl.run()

    @staticmethod
    def init_service():
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyServiceFramework)
        servicemanager.StartServiceCtrlDispatcher()

    @staticmethod
    def handle_commandline():
        win32serviceutil.HandleCommandLine(MyServiceFramework)
