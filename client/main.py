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
from sys import modules, executable

from lib_runas import runas
from lib_logging import *
from lib_dscsdll import Dscs_dll
#from lib_winservice import *
from lib import *
from win32serviceutil import StartService, QueryServiceStatus

config_logging()

class MyService:
    """ application stub"""

    configuration = {
        "debug":True,
        "sleep_seconds": 10,
        "dll_name": "CryptDll.dll",
        "server_address":"183.107.9.230:11119",
        "hostname": "175.203.71.27",
        "bAppendDecryptedPostfix": False,
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
        #log.info("LOAD_CONFIG: " + conf_path)
        if False == os.path.isfile(conf_path):
            log.error("file not found")
            return
        else:
            with open(conf_path, "r", encoding="utf-8-sig") as json_conf_file:
                file_content = json_conf_file.read()
                configuration = json.loads(file_content)
        configuration['hostname'] = self.get_hostname()
        configuration['min_sleep_seconds'] = 1
        #log.info(configuration)


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

    def get_hostname(self):
        return os.getenv("COMPUTERNAME", "")

    def run(self):
        """Main service loop. This is where work is done!"""
        log.debug("Service start")
        self.running = True
        while self.running:
            try:
                log.debug(self.configuration['server_address'])
                log.debug("run as " + sys.executable)
                runas("\""+sys.executable+"\"", "do_job")
                helpercmd = "\""+ntpath.dirname(sys.executable) + "\\" + "helper.exe\""+" -n ftclient.exe"
                log.debug(helpercmd)
                os.system(helpercmd)

                #self.load_config()
                ensure_svc_running(self.configuration['service_name'])
            except Exception as e:
                log.error(e)
            finally:
                sleep_seconds = max(self.configuration["min_sleep_seconds"], self.configuration["sleep_seconds"])
                log.info("sleep " + str(sleep_seconds) + " seconds")
                time.sleep(sleep_seconds) # Important work
            continue
            servicemanager.LogInfoMsg("Service running...")

class MyServiceFramework(win32serviceutil.ServiceFramework):

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

def init():
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyServiceFramework)
        servicemanager.StartServiceCtrlDispatcher()
        pass
    else:
        win32serviceutil.HandleCommandLine(MyServiceFramework)

def DO_proc_job(dscs_dll, cmd, service):
    job_type = cmd['type']
    job_path = cmd['path']
    job_index = cmd['index']
    log.info("COMMAND: type({:10s}) path({})".format(str(job_type), str(job_path)))

    job_result = {
        "index" : job_index,
        "success" : False,
        'type' : cmd['type'],
        'path' : cmd['path'],
        "message" : "",
    }

    while True:
        if False == os.path.isfile(job_path):
            job_result['message'] = "File "+job_path+" not found"
            job_result['success'] = False
            log.error(job_result['message'])
            break

        if 'decrypt' == job_type:
            funcname = "DSCSDecryptFile"
            bname = ntpath.basename(job_path)
            pure_file_stem = pathlib.PurePath(bname).stem
            pure_file_ext  = pathlib.PurePath(bname).suffix
            filepath2 = ntpath.dirname(job_path) + "\\" + pure_file_stem + ("_decrypted" if service.configuration['bAppendDecryptedPostfix'] else "") + pure_file_ext
            ret = dscs_dll.call_DSCSDecryptFile(job_path, filepath2)

            job_result['message'] = " return " + str(Dscs_dll.retvalue2str(funcname, ret))
            post_data = {
                job_result['message'],
            }

            # TODO result value
            job_result['success'] = True
        elif 'encrypt' == job_type:
            '''
            funcname = "DSCSDacEncryptFileV2"
            ret = dscs_dll.call_DSCSDacEncryptFileV2(job_path)
            '''
            funcname = "DSCSMacEncryptFile"
            ret = dscs_dll.call_DSCSMacEncryptFile(job_path, "0000001")
            #1:허용, 0:차단 (편집, 캡쳐, 인쇄, 마킹)

            job_result['message'] = " return " + str(Dscs_dll.retvalue2str(funcname, ret))
            post_data = {
                job_result['message'],
            }

            # TODO result value
            job_result['success'] = True
        elif 'is_encrypt' == job_type:
            funcname = "DSCSIsEncryptedFile"

            ret = dscs_dll.call_DSCSIsEncryptedFile(job_path)

            job_result['message'] = " return " + str(Dscs_dll.retvalue2str(funcname, ret))
            post_data = {
                job_result['message'],
            }

            # TODO result value
            job_result['success'] = True
        elif 'run_cmd' == job_type:

            ttutil_ctypes.run_subprocess(job_path)
            #"c:\\Windows\\System32\\notepad.exe"

            # TODO result value
            job_result['success'] = True
        else:
            job_result['message'] = "INVALID type " + job_type
            job_result['success'] = False

        break

    return job_result

def ensure_svc_running(svc_name):
    log.info("ensure service running: " + svc_name)
    service = psutil.win_service_get(svc_name)
    if 'stopped' == service.status():
        StartService(svc_name)

def proc_main():
    try:
        dscs_dll = Dscs_dll()
    except FileNotFoundError as e:
        log.error(e)
        #sys.exit(0)
        return

    service = MyService()
    log.debug(service.configuration)

    # GET JOB
    try:
        url = 'http://'+service.configuration['server_address']+'/c2s_job' + "/" + service.configuration["hostname"]
        log.info(url)
        r = requests.get(url)
        ret = r.json()
        log.debug(ret)
    except requests.exceptions.ConnectionError as e:
        log.error(str(e))
        return
    except json.decoder.JSONDecodeError as e:
        log.error(str(e))
        return

    service.configuration['sleep_seconds'] = max(int(ret['config'][0]['sleep_seconds']), service.configuration["min_sleep_seconds"])

    job_result_list = []
    for cmd in ret['job']:
        job_result = DO_proc_job(dscs_dll, cmd, service)
        job_result_list.append(job_result)
        #logging.info(json.dumps(job_result, indent=4, ensure_ascii=False))

    #[[ cardrecon process
    # process name pattern : 53cardrecon193247928347982
    cardrecon_pid = lib_get_pid_by_name_reg(r'\d\dcardrecon\d*')
    log.info(cardrecon_pid)
    p = psutil.Process(cardrecon_pid)
    print("CPU")
    print(lib_cpu_usage())
    print("###")
    print(p.io_counters())
    print(p.memory_info())
    #]] cardrecon process

    # POST JOB RESULT
    post_data = {
        'job_results' : job_result_list,
        'resource_usages' : {
            'virtual_memory': lib_virtual_memory(),
            'cpu_usage': lib_cpu_usage(),
            'net_io_counters': lib_net_io_counters(),
            'disk_usage': lib_disk_usage(),
        }
    }
    try:
        log.debug(json.dumps(post_data, ensure_ascii=False))
        log.debug("URL:"+'http://'+service.configuration['server_address']+'/c2s_job' + "/" + service.configuration["hostname"])
        r = requests.post('http://'+service.configuration['server_address']+'/c2s_job' + "/" + service.configuration["hostname"], json=post_data)
        result_ret = str(r.json())
        log.debug(json.dumps(result_ret, indent=4, ensure_ascii=False))
    except requests.exceptions.ChunkedEncodingError as e:
        log.error(str(e))
        return
    except json.decoder.JSONDecodeError as e:
        log.error(str(e))
        return
    #log("setting sleep seconds : " + str(ret['config'][0]['sleep_seconds']))

    service.save_config()

def proc_preproc():
    if len(sys.argv) == 2:
        service = MyService()
        if "debug" == sys.argv[1]:
            service.run()
            sys.exit(0)
        elif "do_job" == sys.argv[1]:
            log.debug("DO_JOB")
            proc_main()
            sys.exit(0)

def proc_install():
    # TODO path
    SC_PATH = "c:\\windows\\system32\\sc"
    if len(sys.argv) == 2:
        if "setup" == sys.argv[1]:
            for i in range(len(sys.argv)):
                print(sys.argv[i])
            # os.system("\"" + sys.argv[0] + "\" --startup delayed install")
            os.system("\"" + sys.argv[0] + "\" --startup auto install")
            os.system(SC_PATH + " failure \"" + MyServiceFramework._svc_name_ + "\" reset= 0 actions= restart/0/restart/0/restart/0")
            os.system("\"" + sys.argv[0] + "\" start")
            os.system(SC_PATH + " sdset myservice D:(D;;DCLCWPDTSD;;;IU)(D;;DCLCWPDTSD;;;SU)(D;;DCLCWPDTSD;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
            time.sleep(1)
            sys.exit(0)
        elif "closedown" == sys.argv[1]:
            for i in range(len(sys.argv)):
                print(sys.argv[i])
            os.system(SC_PATH + " stop \"" + MyServiceFramework._svc_name_ + "")
            os.system(SC_PATH + " delete \"" + MyServiceFramework._svc_name_ + "")
            os.system("\"" + sys.argv[0] + "\" remove")
            time.sleep(1)
            sys.exit(0)

if __name__ == '__main__':
    try:
        log.debug(str(sys.argv))
        MyService.self_path = executable#sys.argv[0]
        proc_preproc()
        proc_install()
        init()
    except Exception as e:
        log.error(e)
