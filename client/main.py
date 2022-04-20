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

from sys import modules, executable
from lib_runas import runas
from lib_logging import *
from lib_dscsdll import Dscs_dll
from lib import *
from libwatchdog import parse_patterns
from lib_logging import log
from lib_er import *
from win32serviceutil import StartService, QueryServiceStatus
from watchdog.utils import WatchdogShutdown
from watchdog.tricks import LoggerTrick
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

config_logging()

class MyLoggerTrick(PatternMatchingEventHandler):
  MINIMUM_FILESIZE = 5

  def __init__(self, patterns=None, ignore_patterns=None,
                 ignore_directories=True, case_sensitive=False, log = None, dscs_dll=None):
    super().__init__(patterns=patterns, ignore_patterns=ignore_patterns,
                 ignore_directories=ignore_directories, case_sensitive=case_sensitive)
    self.log = log
    self.dscs_dll = dscs_dll

  def do_log(self, event):
    reg_list = [
        r"^\\Users\\.*\\AppData\\Local\\Temp\\.*$",
        r"^\\Users\\.*\\AppData\\Local\\Google\\.*$",
        r"^\\Users\\.*\\AppData\\Local\\Packages\\.*$",
        r"^\\Users\\.*\\AppData\\Local\\Microsoft\\.*$",
        r"^\\Users\\.*\\AppData\\Roaming\\Code\\.*$",
        r"^\\Users\\.*\\AppData\\Roaming\\GitHub Desktop\\.*$",
        r"^\\Users\\.*\\AppData\\Roaming\\Microsoft\\Windows\\.*$",
        r"^\\Users\\.*\\AppData\\Local\\Programs\\Python\\.*$",
        r"^\\Users\\.*\\AppData\\Local\\ConnectedDevicesPlatform\\.*$",
        r"^\\Users\\.*\\AppData\\Local\\NVIDIA Corporation\\.*$",
        r"^\\Users\\.*\\AppData\\LocalLow\\Microsoft\\.*$",
        r"^\\Users\\.*\\Documents\\Virtual Machines\\.*$",       # TODO
        r"^\\Users\\.*\\Desktop\\repos\\GitHub\\Python\\.*$",       # TODO
        r"^\\Users\\.*\\VirtualBox VMs\\.*$",       # TODO
        r"^\\Windows\\OffWrite.log.*$",
        r"^\\Windows\\Softcamp\\.*$",
        r"^\\Windows\\Logs\\.*$",
        r"^\\Windows\\Prefetch\\.*$",
        r"^\\Windows\\System32\\.*$",
        r"^\\Windows\\ServiceState\\EventLog\\.*$",
        r"^\\Windows\\ServiceProfiles\\NetworkService\\.*$",
        r"^\\Windows\\ServiceProfiles\\LocalService\\.*$",
        r"^\\Windows\\Temp\\.*$",
        r"^\\Windows\\SoftwareDistributions\\DataStore\\.*$",
        r"^\\Program Files\\AhnLab\\.*$",
        r"^\\Program Files \(x86\)\\Ground Labs\\.*$",
        r"^\\Program Files \(x86\)\\Ground Labs\\Enterprise Recon 2\\.*$",
        r"^\\ProgramData\\Microsoft\\EdgeUpdate\\.*$",
        r"^\\ProgramData\\Microsoft\\Diagnosis\\.*$",
        r"^\\ProgramData\\Microsoft\\Windows\\.*$",
        r"^\\ProgramData\\Microsoft\\Search\\Data\\.*$",
        r"^\\ProgramData\\NVIDIA Corporation\\.*$",
        r"^\\ProgramData\\Packages\\.*$",
        r"^\\ProgramData\\SoftCamp\\Logs\\.*$",
        r"^\\ProgramData\\USOPrivate\\Logs\\.*$",
        r"^\\ProgramData\\USOPrivate\\UpdateStore\\.*$",
        r"^\\ProgramData\\USOShared\\Logs\\.*$",
        r"^\\ProgramData\\VMware\\.*$",
        r"^\\\$Recycle\.Bin\\.*$",
        r"^\\Users\\Admin\\Desktop\\repos\\GitHub\\python-for-pc\\.git\\.*$",     # TODO working dir
        r"^\\Users\\Admin\\Desktop\\repos\\GitHub\\python-for-pc\\client\\.*$",     # TODO working dir
    ]
    for reg in reg_list:
        import re
        p = re.compile(reg, re.IGNORECASE)
        m = p.fullmatch(event.src_path)
        if m != None:
            return

    from libsqlite3 import csqlite3
    workdir_path = ntpath.dirname(sys.executable)
    sqlite3 = csqlite3(name=workdir_path + '\\state.db', log=self.log)

    target_path = ''

    # sleep a second
    #time.sleep(1)

    if 'modified' == event.event_type:
        target_path = event.src_path
    elif 'moved' == event.event_type:
        sqlite3.fileinfo_delete(event.src_path)
        target_path = event.dest_path
    elif 'deleted' == event.event_type:
        #sqlite3.fileinfo_delete(event.src_path)
        return
    else:
        return

    if event.is_directory:
        return
    try:
        filesize = os.path.getsize(target_path)
    except FileNotFoundError as e:
        self.log.error('FileNotFoundError  ' + str(e))
        return
    except PermissionError as e:
        self.log.error('PermissionError ' + str(e))
        return
    if filesize < self.MINIMUM_FILESIZE:
        self.log.info("filesize: " + str(filesize))
        return

    # self.log.info(event.event_type + " " + target_path + " (size: " + str(filesize) + ")")

    try:
        ret = self.dscs_dll.call_DSCSIsEncryptedFile(target_path)
    except Exception as e:
        self.log.error(str(e))

    if -1 == ret:
        retstr = str(ret) + '(C/S 연동 모듈 로드 실패)'
        self.log.info("file call_DSCSIsEncryptedFile : " + target_path + ", " + retstr)
    elif 0 == ret:
        retstr = str(ret) + '(일반 문서)'
        self.log.info("file call_DSCSIsEncryptedFile : " + target_path + ", " + retstr)
    elif 1 == ret:
        retstr = str(ret) + '(암호화된 문서)'
        self.log.info("file call_DSCSIsEncryptedFile : " + target_path + ", " + retstr)
        sqlite3.fileinfo_insert(target_path, filesize)
        self.log.info("file enqueued : " + target_path + ", " + retstr)

  def on_any_event(self, event):
    try:
        self.do_log(event)
    except Exception as e:
        #self.log.error(traceback.print_stack().replace("\n", ""))
        self.log.error(str(e))

def observe_with(observer, event_handler, pathnames, recursive, myservice):
    for pathname in set(pathnames):
        observer.schedule(event_handler, pathname, recursive)
    observer.start()
    try:
        myservice.running = True
        from lib_winsec import cwinsecurity
        log.info("service process's integrity level: " + cwinsecurity.get_integrity_level(log))

        while myservice.running:
            try:
                log.debug(myservice.configuration['server_address'])

                import sys
                import psutil
                pid_list = lib_get_pid_list_by_name_reg(r'ftclient.exe')
                non_system_process_exists = False
                for pid in pid_list:
                    (user_sid, user0, user1) = lib_get_pid_owner(pid)
                    if None != user0 and 'system' != user0.lower():
                        log.debug("user: " + user0)
                        non_system_process_exists = True

                if False == non_system_process_exists:
                    log.debug("runas console process")
                    log.debug("run as " + sys.executable)
                    runas("\""+sys.executable+"\"", "do_job")
                else:
                    log.debug("console process is running")

                #helpercmd = "\""+ntpath.dirname(sys.executable) + "\\" + "helper.exe\""+" -n ftclient.exe"
                #log.debug(helpercmd)
                #os.system(helpercmd)

                #myservice.load_config()
                ensure_svc_running(myservice.configuration['service_name'])
            except Exception as e:
                log.error(traceback.print_stack())
                log.error(e)
            finally:
                sleep_seconds = max(myservice.configuration["min_sleep_seconds"],
                    myservice.configuration["sleep_seconds"])
                log.debug("sleep " + str(sleep_seconds) + " seconds")
                time.sleep(sleep_seconds) # Important work
                #time.sleep(observer.timeout)
            continue
            servicemanager.LogInfoMsg("Service running...")

    except WatchdogShutdown:
        observer.stop()
    observer.join()

class MyService:
    """ application stub"""

    configuration = {
        "debug": True,
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

    def run(self):      # the service process loop
        """Main service loop. This is where work is done!"""
        log.info("Service start")

        myarg = {
            "patterns": "*",#"*.txt",#;*.tmp",
            "ignore_patterns": "*.dll;*.pyd;*.exe",#"*.log;/$Recycle.Bin*",
            "timeout": 5,
            "pathnames": ['\\'],
            "recursive": True,
        }

        patterns, ignore_patterns = parse_patterns(myarg['patterns'], myarg['ignore_patterns'])
        try:
            try:
                dscs_dll = Dscs_dll()
            except FileNotFoundError as e:
                log.error(e)
                #sys.exit(0)
                return

            handler = MyLoggerTrick(patterns=patterns,
                ignore_patterns=ignore_patterns, log=log, dscs_dll=dscs_dll)
            observer = Observer(timeout=myarg['timeout'])
            observe_with(observer, handler, myarg['pathnames'], myarg['recursive'], self)
        except Exception as e:
            log.error(traceback.print_stack())
            log.error(str(e))

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

def DO_proc_job(dscs_dll, cmd, service):    # the console process procedure
    from libsqlite3 import csqlite3
    workdir_path = ntpath.dirname(sys.executable)
    sqlite3 = csqlite3(name=workdir_path + '/state.db', log=log)

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
            log.info("DECRYPT ##################################")
            ret = dscs_dll.decryptFile(job_path, service.configuration['bAppendDecryptedPostfix'])

            if 1 == ret:    # decryption success
                sqlite3.fileinfo_update_state(filepath=job_path, state="decrypted")

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

            run_subprocess(job_path)
            #"c:\\Windows\\System32\\notepad.exe"

            # TODO result value
            job_result['success'] = True
        else:
            job_result['message'] = "INVALID type " + job_type
            job_result['success'] = False

        break

    return job_result

def ensure_svc_running(svc_name):
    log.debug("ensure service running: " + svc_name)
    service = psutil.win_service_get(svc_name)
    if 'stopped' == service.status():
        StartService(svc_name)

def proc_main():        # the console process loop
    try:
        dscs_dll = Dscs_dll()
    except FileNotFoundError as e:
        log.error(e)
        return

    er = er_agent("192.168.12.7", log)

    service = MyService()
    log.debug(service.configuration)

    from lib_winsec import cwinsecurity
    log.info("restAPI client's integrity level: " + cwinsecurity.get_integrity_level(log))

    while True:
        # GET JOB
        try:
            url = 'http://'+service.configuration['server_address']+'/c2s_job' + "/" + service.configuration["hostname"]
            log.debug(url)
            r = requests.get(url)
            ret = r.json()
            log.debug(ret)

            service.configuration['sleep_seconds'] = max(int(ret['config'][0]['sleep_seconds']), service.configuration["min_sleep_seconds"])

            job_result_list = []
            for cmd in ret['job']:
                job_result = DO_proc_job(dscs_dll, cmd, service)
                job_result_list.append(job_result)
                #logging.info(json.dumps(job_result, indent=4, ensure_ascii=False))

            #[[ cardrecon process
            # process name pattern : 53cardrecon193247928347982
            cardrecon_pid = lib_get_pid_by_name_reg(r'\d\dcardrecon\d*')
            log.debug("cardrecon pid : " + str(cardrecon_pid))
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

            # [[[[[[[[[[[[[ ER node interface

            from libsqlite3 import csqlite3
            workdir_path = ntpath.dirname(sys.executable)
            sqlite3 = csqlite3(name=workdir_path + '\\state.db', log=log)

            # proc queued
            file_list = sqlite3.fileinfo_select(state='queued')
            for fileinfo in file_list:
                file_id = fileinfo[0]
                file_path = fileinfo[1]
                file_size = fileinfo[2]
                file_state = fileinfo[3]

                filepath2 = dscs_dll.decryptFile(file_path, service.configuration['bAppendDecryptedPostfix'])

                if None != filepath2:    # decryption success
                    cwinsecurity.set_file_attribute_hidden(filepath2)
                    log.info("file decrypted : " + filepath2)
                    sqlite3.fileinfo_update_state(filepath=file_path, state="decrypted")

                    # TODO add schedule
                    schedule_id = er.my_add_schedule(subpath_list=[
                        filepath2,
                        #'\\users\\danny\\desktop\\s3.txt',
                    ])
                    sqlite3.fileinfo_update_schedule_id(file_path, schedule_id)
                    log.info("schedule added " + str(schedule_id))

            # proc decrypted & has schedule_id
            file_list = sqlite3.fileinfo_select_scheduled()
            for fileinfo in file_list:
                file_path = fileinfo[1]
                file_schedule_id = fileinfo[4]

                if er.is_schedule_completed(file_schedule_id):
                    #sqlite3.fileinfo_delete(file_path)
                    sqlite3.fileinfo_update_state(filepath=file_path, state="completed")
                    log.info(file_path + " completed (schedule_id:"+str(file_schedule_id)+")")
                    decrypted_filepath = Dscs_dll.get_decrypted_filepath(file_path, service.configuration['bAppendDecryptedPostfix'])
                    os.remove(decrypted_filepath)

            # ]]]]]]]]]]]]]

            service.save_config()
            sleep_seconds = max(service.configuration["min_sleep_seconds"],
                service.configuration["sleep_seconds"])
            log.debug("sleep " + str(sleep_seconds) + " seconds")
            time.sleep(sleep_seconds) # Important work
        except requests.exceptions.ConnectionError as e:
            log.error(str(e))
            return
        except json.decoder.JSONDecodeError as e:
            log.error(str(e))
            return
        except Exception as e:
            log.error(traceback.print_stack())
            log.error(str(e))
            return

def proc_install():
    from lib_winsec import cwinsecurity
    mount_points = cwinsecurity._get_mount_points()
    SC_PATH = mount_points[0]+"windows\\system32\\sc"
    if len(sys.argv) == 2:
        if "setup" == sys.argv[1]:
            for i in range(len(sys.argv)):
                print(sys.argv[i])
            # os.system("\"" + sys.argv[0] + "\" --startup delayed install")
            os.system("\"" + sys.argv[0] + "\" --startup auto install")
            os.system(SC_PATH + " failure \"" + MyServiceFramework._svc_name_ + "\" reset= 0 actions= restart/0/restart/0/restart/0")
            os.system("\"" + sys.argv[0] + "\" start")
            #os.system(SC_PATH + " sdset myservice D:(D;;DCLCWPDTSD;;;IU)(D;;DCLCWPDTSD;;;SU)(D;;DCLCWPDTSD;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
            time.sleep(1)
            sys.exit(0)
        elif "closedown" == sys.argv[1]:
            for i in range(len(sys.argv)):
                print(sys.argv[i])
            #os.system(SC_PATH + " sdset myservice D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
            os.system(SC_PATH + " stop \"" + MyServiceFramework._svc_name_ + "")
            os.system(SC_PATH + " delete \"" + MyServiceFramework._svc_name_ + "")
            os.system("\"" + sys.argv[0] + "\" remove")
            time.sleep(1)
            sys.exit(0)
        elif "debug" == sys.argv[1]:
            service = MyService()

            # import psutil
            # pid_list = lig_get_pid_list_by_name_reg(r'ftclient.exe')
            # non_system_process_exists = False
            # for pid in pid_list:
            #     (user_sid, user0, user1) = lib_get_pid_owner(pid)
            #     if None != user0 and 'system' != user0.lower():
            #         non_system_process_exists = True

            # if False == non_system_process_exists:
            #     print("runas console process")
            #     # TODO runas
            # else:
            #     print("console process is running")

            service.run()
            sys.exit(0)
        elif "do_job" == sys.argv[1]:
            log.debug("DO_JOB")
            proc_main()
            sys.exit(0)
        elif "test_dscs" == sys.argv[1]:
            dscs_dll = Dscs_dll()
            bAppendPrefix = False
            job_path = 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11.txt'
            dscs_dll.decryptFile(job_path, bAppendPrefix=bAppendPrefix)
            sys.exit(0)

if __name__ == '__main__':
    try:
        log.debug(str(sys.argv))
        MyService.self_path = executable#sys.argv[0]
        proc_install()
        init()
    except Exception as e:
        log.error(traceback.print_stack())
        log.error(e)