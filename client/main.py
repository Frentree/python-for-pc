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
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from lib_winsec import cwinsecurity
from libsqlite3 import csqlite3


CONF_PATH_MIDDLE = "\\AppData\\Local\\Temp\\"
GLOBAL_ENV = {
    "INITIAL_LOGGING_LEVEL": logging.INFO,
    "WINDOWS_SERVICE_NAME": 'MyService',
    "EXE_FILENAME": "ftclient.exe",
    "DB_PATH_POSTFIX"         : CONF_PATH_MIDDLE + "state.db",
    "CONF_PATH_POSTFIX_SEARCHING_FLAG": CONF_PATH_MIDDLE + "searching_flag_conf.json",
    "CONF_PATH_POSTFIX_EXCEPT_FORMAT" : CONF_PATH_MIDDLE + "except_format_list.json",
    "CONF_PATH_POSTFIX_EXCEPT_PATH"   : CONF_PATH_MIDDLE + "except_path_list.json",
    "CONF_PATH_POSTFIX_DRM_CONF"      : CONF_PATH_MIDDLE + "configuration.json",
    "QUEUE_SIZE_LIMIT"                  : 500*1024*1024,
}


config_logging(GLOBAL_ENV["INITIAL_LOGGING_LEVEL"])


class MyLoggerTrick(PatternMatchingEventHandler):
  MINIMUM_FILESIZE = 5

  def __init__(self, patterns=None, ignore_patterns=None,
                 ignore_directories=True, case_sensitive=False, log=None, dscs_dll=None):
    super().__init__(patterns=patterns, ignore_patterns=ignore_patterns,
                 ignore_directories=ignore_directories, case_sensitive=case_sensitive)
    self.log = log
    self.dscs_dll = dscs_dll

  def do_log(self, event):
    reg_list = [
        r"^.:\\Users\\.*\\AppData\\Local\\Temp\\.*$",
        r"^.:\\Users\\.*\\AppData\\Local\\Google\\.*$",
        r"^.:\\Users\\.*\\AppData\\Local\\Packages\\.*$",
        r"^.:\\Users\\.*\\AppData\\Local\\Microsoft\\.*$",
        r"^.:\\Users\\.*\\AppData\\Roaming\\Code\\.*$",
        r"^.:\\Users\\.*\\AppData\\Roaming\\GitHub Desktop\\.*$",
        r"^.:\\Users\\.*\\AppData\\Roaming\\Microsoft\\Windows\\.*$",
        r"^.:\\Users\\.*\\AppData\\Local\\Programs\\Python\\.*$",
        r"^.:\\Users\\.*\\AppData\\Local\\ConnectedDevicesPlatform\\.*$",
        r"^.:\\Users\\.*\\AppData\\Local\\NVIDIA Corporation\\.*$",
        r"^.:\\Users\\.*\\AppData\\Local\\Kakao\\KakaoTalk\\.*$",
        r"^.:\\Users\\.*\\AppData\\LocalLow\\Microsoft\\.*$",
        r"^.:\\Users\\.*\\Documents\\Virtual Machines\\.*$",       # TODO
        r"^.:\\Users\\.*\\Desktop\\repos\\GitHub\\Python\\.*$",       # TODO
        r"^.:\\Users\\.*\\VirtualBox VMs\\.*$",       # TODO
        r"^.:\\Windows\\OffWrite.log.*$",
        r"^.:\\Windows\\Softcamp\\.*$",
        r"^.:\\Windows\\Logs\\.*$",
        r"^.:\\Windows\\Prefetch\\.*$",
        r"^.:\\Windows\\System32\\.*$",
        r"^.:\\Windows\\ServiceState\\EventLog\\.*$",
        r"^.:\\Windows\\ServiceProfiles\\NetworkService\\.*$",
        r"^.:\\Windows\\ServiceProfiles\\LocalService\\.*$",
        r"^.:\\Windows\\SysWOW64\\.*$",
        r"^.:\\Windows\\Temp\\.*$",
        r"^.:\\Windows\\SoftwareDistributions\\DataStore\\.*$",
        r"^.:\\Program Files\\AhnLab\\.*$",
        r"^.:\\Program Files \(x86\)\\Ground Labs\\.*$",
        r"^.:\\Program Files \(x86\)\\Ground Labs\\Enterprise Recon 2\\.*$",
        r"^.:\\ProgramData\\Microsoft\\EdgeUpdate\\.*$",
        r"^.:\\ProgramData\\Microsoft\\Diagnosis\\.*$",
        r"^.:\\ProgramData\\Microsoft\\Windows\\.*$",
        r"^.:\\ProgramData\\Microsoft\\Search\\Data\\.*$",
        r"^.:\\ProgramData\\NVIDIA Corporation\\.*$",
        r"^.:\\ProgramData\\Packages\\.*$",
        r"^.:\\ProgramData\\SoftCamp\\Logs\\.*$",
        r"^.:\\ProgramData\\USOPrivate\\Logs\\.*$",
        r"^.:\\ProgramData\\USOPrivate\\UpdateStore\\.*$",
        r"^.:\\ProgramData\\USOShared\\Logs\\.*$",
        r"^.:\\ProgramData\\VMware\\.*$",
        r"^.:\\\$Recycle\.Bin\\.*$",
        r"^.:\\Users\\Admin\\Desktop\\repos\\GitHub\\python-for-pc\\.git\\.*$",
        r"^.:\\Users\\Admin\\Desktop\\repos\\GitHub\\python-for-pc\\client\\.*$",

        r"^.:\\.*\\.*\.tsp$",
        r"^.:\\.*\\.*\.tmp$",

        r"^.:\\.*\\.*_decrypted.*$",
    ]
    for reg in reg_list:
        import re
        p = re.compile(reg, re.IGNORECASE)
        m = p.fullmatch(event.src_path)
        if m != None:
            return

    sqlite3 = csqlite3(name=MyService.get_path('state.db'), log=log)

    target_path = ''

    # sleep a second
    # time.sleep(1)

    if 'modified' == event.event_type:
        target_path = event.src_path
    elif 'moved' == event.event_type:
        sqlite3.fileinfo_delete(event.src_path)
        target_path = event.dest_path
    elif 'deleted' == event.event_type:
        # sqlite3.fileinfo_delete(event.src_path)
        return
    else:
        return

    if MyService.match_DRM_file_list(target_path):
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
        self.log.debug("filesize: " + str(filesize))
        return

    self.log.debug(event.event_type + " " + target_path +
                   " (size: " + str(filesize) + ")")

    try:
        ret = self.dscs_dll.call_DSCSIsEncryptedFile(target_path)
    except Exception as e:
        self.log.error(str(e))

    if -1 == ret:
        retstr = str(ret) + '(C/S 연동 모듈 로드 실패)'
        self.log.info("file call_DSCSIsEncryptedFile : " +
                      target_path + ", " + retstr)
    elif 0 == ret:
        retstr = str(ret) + '(일반 문서)'
        self.log.info("file call_DSCSIsEncryptedFile : " +
                      target_path + ", " + retstr)
    elif 1 == ret:
        retstr = str(ret) + '(암호화된 문서)'
        self.log.info("file call_DSCSIsEncryptedFile : " +
                      target_path + ", " + retstr)
        if filesize >= int(GLOBAL_ENV['QUEUE_SIZE_LIMIT']):
            return
        sqlite3.fileinfo_insert_with_size(target_path, filesize)
        self.log.info("file enqueued : " + target_path + ", " + retstr)

  def on_any_event(self, event):
    try:
        self.do_log(event)
    except Exception as e:
        # self.log.error(traceback.print_stack().replace("\n", ""))
        self.log.error(traceback.print_stack())
        self.log.error(str(e))


def observe_with(observer, event_handler, pathnames, recursive, myservice):
    myservice.running = False
    observer_started = False
    try:
        myservice.running = True
        log.info("service process's integrity level: " +
                 cwinsecurity.get_integrity_level(log))
        MyService.integrity_level = cwinsecurity.get_integrity_level(log)
        MyService.process_type = "service"

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
                        non_system_process_exists = True

                        if '' == MyService.user_id:
                            MyService.user_id = user0
                            log.info("user: " + str(MyService.user_id))
                        break

                if False == non_system_process_exists:
                    log.info("run as " + sys.executable)
                    # runas("\""+sys.executable+"\"", "do_job")
                    runas(""+sys.executable+"", "do_job", None, False)

                    import sys
                    import psutil
                    pid_list = lib_get_pid_list_by_name_reg(r'ftclient.exe')
                    non_system_process_exists = False
                    for pid in pid_list:
                        log.info("*** PID: " + str(pid))
                        (user_sid, user0, user1) = lib_get_pid_owner(pid)
                        if None != user0 and 'system' != user0.lower():
                            non_system_process_exists = True

                            log.info("user: " + str(user0))
                            log.info("MyService.user_id: " + str(MyService.user_id))
                            if '' == MyService.user_id:
                                MyService.user_id = user0
                                log.info("user: " + str(MyService.user_id))
                            break
                        else:
                            log.info("else user: " + str(user0))


                else:
                    log.debug("console process is running")

                # helpercmd = "\""+ntpath.dirname(sys.executable) + "\\" + "helper.exe\""+" -n "+GLOBAL_ENV["EXE_FILENAME"]
                # log.debug(helpercmd)
                # os.system(helpercmd)

                # myservice.load_config()
                ensure_svc_running(myservice.configuration['service_name'])

                if True == non_system_process_exists and False == observer_started:
                    for pathname in set(pathnames):
                        observer.schedule(event_handler, pathname, recursive)
                    observer.start()
                    observer_started = True

            except Exception as e:
                log.error(traceback.print_stack())
                log.error(e)
            finally:
                sleep_seconds = max(myservice.configuration["min_sleep_seconds"],
                    myservice.configuration["sleep_seconds"])
                log.debug("sleep " + str(sleep_seconds) + " seconds")
                time.sleep(sleep_seconds)  # Important work
                # time.sleep(observer.timeout)
            continue
            servicemanager.LogInfoMsg("Service running...")

    except WatchdogShutdown:
        observer.stop()
    observer.join()


class MyService:
    """ application stub"""
    user_id = ""
    prev_network_usage = None
    integrity_level = ""
    process_type = ""
    dscs = None
    sqlite3 = None

    configuration = {
        "debug": True,
        "sleep_seconds": 5,
        "dll_name": "CryptDll.dll",
        "server_address": "183.107.9.230:11119",
        "hostname": "175.203.71.27",
        "bAppendDecryptedPostfix": True,
        "service_name": "Enterprise Recon 2 Agent",

        "min_sleep_seconds": 1,
    }
    self_path = ""

    def __init__(self):
        log.info("MyService __init__")
        try:
            self.load_config()
        except Exception as e:
            log.error(e)

    def stop(self):
        """Stop the service"""
        log.debug("Service stop")
        self.running = False

    def load_config(self):
        conf_path = MyService.get_path('configuration.json')
        # if 'python.exe' == os.path.basename(sys.executable):
        #    conf_path = "." + "\\configuration.json"
        # else:
        #    conf_path = os.path.dirname(sys.executable) + "\\configuration.json"

        # use configuration with the exe
        if (os.path.isfile(os.path.dirname(sys.executable) + "\\configuration.json")):
            conf_path = os.path.dirname(sys.executable) + "\\configuration.json"

        log.info("LOAD_CONFIG: " + conf_path)
        if False == os.path.isfile(conf_path):
            log.error("file not found")
            return
        else:
            with open(conf_path, "r", encoding="utf-8-sig") as json_conf_file:
                file_content = json_conf_file.read()
                configuration = json.loads(file_content)
        configuration['hostname'] = MyService.get_hostname()
        configuration['min_sleep_seconds'] = 1
        # log.info(configuration)

        self.configuration = configuration
        MyService.configuration = configuration

    def save_config(self):
        conf_path = MyService.get_path('configuration.json')
        # if 'python.exe' == os.path.basename(sys.executable):
        #     conf_path = "." + "\\configuration.json"
        # else:
        #     conf_path = os.path.dirname(sys.executable) + "\\configuration.json"
        log.debug("SAVE_CONFIG: " + conf_path)

        try:
            with open(conf_path, 'w', encoding="utf-8-sig") as json_out_file:
                json.dump(self.configuration, json_out_file,
                            indent=4, ensure_ascii=False)
                log.debug("SAVE_CONFIG: " +
                            json.dumps(self.configuration, ensure_ascii=False))
        except FileNotFoundError as e:
            log.error(str(e))

    @staticmethod
    def get_hostname():
        return os.getenv("COMPUTERNAME", "")

    def run(self):      # the service process loop
        """Main service loop. This is where work is done!"""
        log.info("Service start")

        myarg = {
            "patterns": "*",  # "*.txt",#;*.tmp",
            "ignore_patterns": "*.tmp;*.dll;*.pyd;*.exe",  # "*.log;/$Recycle.Bin*",
            "timeout": 5,
            "pathnames": ['\\'],
            "recursive": True,
        }

        disk_partitions = psutil.disk_partitions()
        pathnames = []
        for disk_partition in disk_partitions:
            if '' != disk_partition.fstype:
                pathnames.append(disk_partition.mountpoint)
        myarg['pathnames'] = pathnames
        log.info(pathnames)
        log.info(disk_partitions)
        log.info(json.dumps(disk_partitions, indent=4))

        patterns, ignore_patterns = parse_patterns(
            myarg['patterns'], myarg['ignore_patterns'])
        while True:
            try:
                dscs_dll = Dscs_dll()

                handler = MyLoggerTrick(patterns=patterns,
                    ignore_patterns=ignore_patterns, log=log, dscs_dll=dscs_dll)
                observer = Observer(timeout=myarg['timeout'])
                observe_with(observer, handler,
                            myarg['pathnames'], myarg['recursive'], self)
            except FileNotFoundError as e:
                log.error(traceback.print_stack())
                log.error(e)
            except Exception as e:
                log.error(traceback.print_stack())
                log.error(str(e))
            finally:
                time.sleep(5) # Important work

    @staticmethod
    def get_store_path():
        mount_point = cwinsecurity.get_windir_driveletter_with_colon()
        # if '' == MyService.user_id:
        #     log.error("########## GET STORE PATH ")
        #     MyService.user_id = os.getenv('USERNAME')
        userprofile = mount_point+"\\Users\\"+MyService.user_id
        store_path = (userprofile+CONF_PATH_MIDDLE)
        return store_path

    @staticmethod
    def save_drm_config(drm_config):
        except_path_list = drm_config['except_path'].split(',')
        the_path_list = []
        for except_path in except_path_list:
            the_path_list.append(except_path.lower())
        the_path_list.sort()
        with open(MyService.get_path('except_path_list.json'), 'w') as outfile:
            json.dump(the_path_list, outfile, indent=4)

        except_format_list = drm_config['except_format'].split(',')
        the_format_list = []
        for except_format in except_format_list:
            the_format_list.append(except_format.lower())
        the_format_list.sort()
        with open(MyService.get_path('except_format_list.json'), 'w') as outfile:
            json.dump(the_format_list, outfile, indent=4)

    @staticmethod
    def get_searching_flag_conf():
        try:
            with open(MyService.get_path('searching_flag_conf.json'), "r") as json_file:
                searching_flag_conf = json.load(json_file)
                MyService.searching_flag_conf = searching_flag_conf
                return searching_flag_conf['flag']
        except FileNotFoundError as e:
            log.error(e)
            return False

        return False

    @staticmethod
    def set_searching_flag_conf():
        the_list = {
            "flag": True,
        }
        with open(MyService.get_path('searching_flag_conf.json'), 'w') as outfile:
            json.dump(the_list, outfile, indent=4)

    @staticmethod
    def unset_searching_flag_conf():
        os.system("del "+MyService.get_path('searching_flag_conf.json'))

    @staticmethod
    def load_except_path_list():
        with open(MyService.get_path('except_path_list.json'), "r") as json_file:
            except_path_list = json.load(json_file)
            MyService.except_path_list = except_path_list

        MyService.except_path_list.extend(MyService.get_DRM_file_list())

    @staticmethod
    def load_except_format_list():
        with open(MyService.get_path('except_format_list.json'), "r") as json_file:
            except_format_list = json.load(json_file)
            MyService.except_format_list = except_format_list

    @staticmethod
    def match_except_path(the_path):
        for except_path in MyService.except_path_list:
            path1 = the_path.lower()
            path2 = (cwinsecurity.get_windir_driveletter_with_colon() + except_path).lower()
            #print("<-->: "+path1 +", "+path2)
            if path1.startswith(path2):
                return True

        return False

    @staticmethod
    def match_blacklist_format(the_path):
        MyService.except_format_blacklist = [
            ".pptx",
            ".txt",
            ".xlsx",
            ".docx",
        ]
        for except_format in MyService.except_format_blacklist:
            (file_path, file_name, file_ext) = cwinsecurity._split_name_ext_from_path(the_path)
            if file_ext.lower() == except_format.lower():
                #print("format matched:"+file_ext)
                return True

        return False

    @staticmethod
    def match_except_format(the_path):
        for except_format in MyService.except_format_list:
            (file_path, file_name, file_ext) = cwinsecurity._split_name_ext_from_path(the_path)
            if file_ext.lower() == except_format.lower():
                #print("format matched:"+file_ext)
                return True

        return False

    @staticmethod
    def get_DRM_file_list():
        DRM_file_list = [
            MyService.get_path('configuration.json'),
            MyService.get_path('except_path_list.json'),
            MyService.get_path('except_format_list.json'),
            MyService.get_path('searching_flag_conf.json'),
            MyService.get_path('state.db'),
        ]
        return DRM_file_list

    @staticmethod
    def match_DRM_file_list(the_path):
        if the_path in MyService.get_DRM_file_list():
            return True
        return False

    @staticmethod
    def get_path(pathtype):
        # if '' == MyService.user_id:
        #     log.error("########## GET_PATH ")
        #     log.error(traceback.format_exc())
        #     MyService.user_id = os.getenv('USERNAME')
        userprofile = cwinsecurity.get_windir_driveletter_with_colon()+"\\Users\\"+MyService.user_id
        if 'configuration.json' == pathtype:
            the_path = (userprofile+GLOBAL_ENV["CONF_PATH_POSTFIX_DRM_CONF"])
        elif 'except_path_list.json' == pathtype:
            the_path = (userprofile+GLOBAL_ENV["CONF_PATH_POSTFIX_EXCEPT_PATH"])
        elif 'except_format_list.json' == pathtype:
            the_path = (userprofile+GLOBAL_ENV["CONF_PATH_POSTFIX_EXCEPT_FORMAT"])
        elif 'searching_flag_conf.json' == pathtype:
            the_path = (userprofile+GLOBAL_ENV["CONF_PATH_POSTFIX_SEARCHING_FLAG"])
        elif 'state.db' == pathtype:
            the_path = (userprofile+GLOBAL_ENV["DB_PATH_POSTFIX"])

        return the_path


class MyServiceFramework(win32serviceutil.ServiceFramework):

    #_svc_name_ = 'MyService'
    #_svc_display_name_ = _svc_name_
    _svc_name_ = 'MyService'
    _svc_display_name_ = 'My Service display name'    
    _svc_description_ = _svc_name_ + " description"

    def __init__(self, args):
        log.info("##################################### init")
        OutputDebugString("[TT]"+"AAAAAAA")
        win32serviceutil.ServiceFramework.__init__(self, args)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.service_impl.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        log.info("##################################### SVC DO RUN")
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
    sqlite3 = csqlite3(name=MyService.get_path('state.db'), log=log)

    job_type = cmd['type']
    job_path = cmd['path']
    job_index = cmd['index']
    log.info("COMMAND: type({:10s}) path({})".format(
        str(job_type), str(job_path)))

    job_result = {
        "index": job_index,
        "success": False,
        'type': cmd['type'],
        'path': cmd['path'],
        "message": "",
    }

    while True:
        if False == os.path.isfile(job_path):
            job_result['message'] = "File "+job_path+" not found"
            job_result['success'] = False
            log.error(job_result['message'])
            break

        if 'decrypt' == job_type:
            funcname = "DSCSDacEncryptFileV2"
            log.info("DECRYPT ##################################")
            ret = dscs_dll.decryptFile(
                job_path, service.configuration['bAppendDecryptedPostfix'])

            if 1 == ret:    # decryption success
                sqlite3.fileinfo_update_state(
                    filepath=job_path, state="decrypted")

            job_result['message'] = " return " + str(ret)
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
            log.info(json.dumps(service.configuration, indent=4))
            category_id = "0000001"
            log.info("############## category id : " + category_id)
            ret = dscs_dll.call_DSCSMacEncryptFile(job_path, category_id)
            # 1:허용, 0:차단 (편집, 캡쳐, 인쇄, 마킹)

            job_result['message'] = " return " + \
                str(Dscs_dll.retvalue2str(funcname, ret))
            post_data = {
                job_result['message'],
            }

            # TODO result value
            job_result['success'] = True
        elif 'is_encrypt' == job_type:
            funcname = "DSCSIsEncryptedFile"

            ret = dscs_dll.call_DSCSIsEncryptedFile(job_path)

            job_result['message'] = " return " + \
                str(Dscs_dll.retvalue2str(funcname, ret))
            post_data = {
                job_result['message'],
            }

            # TODO result value
            job_result['success'] = True
        elif 'run_cmd' == job_type:

            run_subprocess(job_path)
            # "c:\\Windows\\System32\\notepad.exe"

            # TODO result value
            job_result['success'] = True
        else:
            job_result['message'] = "INVALID type " + job_type
            job_result['success'] = False

        break

    return job_result


def ensure_svc_running(svc_name):
    service = psutil.win_service_get(svc_name)
    if 'stopped' == service.status():
        log.info("ensure service running: " + svc_name)
        StartService(svc_name)

def traverse_all_files_glob(func, path=None):
    partition_list = []
    if None != path:
        partition_list.append(path)
    else:
        disk_partitions = psutil.disk_partitions()
        for disk_partition in disk_partitions:
            partition_list.append(disk_partition.device)

    for partition in partition_list:
        path = partition+'*'
        import glob
        for f in glob.glob(path, recursive=True):
            if True == MyService.match_except_path(f):
                continue

            if os.path.isdir(f):
                log.info("searching on : "+f)
                traverse_all_files_glob(func, f+"\\?")
            else:
                if True == MyService.match_blacklist_format(f):
                    log.debug("Format matched: " + f)
                    func(f)
                    continue

                if True == MyService.match_except_format(f):
                    #log.info("format matched " + f)
                    #print("f", end="", flush=True)
                    continue
                else:
                    log.debug("format matched : " + f)
                    func(f)
                #print("file_path : " + file_path)
                #print("file_name : " + file_name)
                #print("file_ext : " + file_ext)
                #func(f, "Admin")

def pushFileIfEncrypted(filepath):
    ret = MyService.dscs.call_DSCSIsEncryptedFile(filepath)
    if 1 == ret:
        log.info("############## PUSH FILE IF ENCRYPTED : " + filepath)
        log.info("IS ENCRYPTED True : " + str(filepath))

        try:
            filesize = os.path.getsize(filepath)
        except FileNotFoundError as e:
            log.error('FileNotFoundError  ' + str(e))
            return
        except PermissionError as e:
            log.error('PermissionError ' + str(e))
            return
        
        if filesize >= int(GLOBAL_ENV['QUEUE_SIZE_LIMIT']):
            return
        MyService.sqlite3.fileinfo_insert_with_size(filepath, filesize)

def proc_main():        # the console process loop
    try:
        dscs_dll = Dscs_dll()
    except FileNotFoundError as e:
        log.error(e)
        return

    er = er_agent(log)

    service = MyService()
    MyService.user_id = os.getenv('USERNAME')

    log.debug(service.configuration)

    from lib_winsec import cwinsecurity
    log.info("API client's integrity level: " + cwinsecurity.get_integrity_level(log))
    MyService.integrity_level = cwinsecurity.get_integrity_level(log)
    MyService.process_type = "console"
    
    while True:
        # GET JOB
        try:
            sqlite3 = csqlite3(name=MyService.get_path('state.db'), log=log)

            from lib_apiinterface import cApiInterface
            apiInterface = cApiInterface(service.configuration['server_address'], log)

            drm_config = apiInterface.drm_configGet()
            MyService.save_drm_config(drm_config)
            MyService.load_except_path_list()
            MyService.load_except_format_list()
            service.configuration['sleep_seconds'] = max(int(drm_config['sleep_seconds']), service.configuration["min_sleep_seconds"])
            service.configuration['log_level'] = int(drm_config['log_level'])
            sleep_seconds = max(service.configuration["min_sleep_seconds"],
                service.configuration["sleep_seconds"])
            service.configuration['s_no'] = drm_config['s_no']
            service.configuration['p_no'] = drm_config['p_no']
            log.info(drm_config)
            log.debug("sleep " + str(sleep_seconds) + " seconds")
            service.save_config()







            # region [[[[[[[[[[[[[[[[[[[[ cardrecon process
            # process name pattern : 53cardrecon193247928347982
            cardrecon_pid = lib_get_pid_by_name_reg(r'\d\dcardrecon\d*')
            log.info("cardrecon pid : " + str(cardrecon_pid))
            p = psutil.Process(cardrecon_pid)
            if None != p:
                specific_cpu = str(p.cpu_percent()) + "/" + str(psutil.cpu_count())
                specific_memory = str(p.memory_percent()) + "%"
            #log.info("CPU : " + str(lib_cpu_usage()))
            #print(json.dumps(lib_cpu_usage(), indent=4))
            #print(json.dumps(p.io_counters(), indent=4))
            #print(json.dumps(p.memory_info(), indent=4))
            #log.info("IO: " + str(p.io_counters()))
            #log.info("MEMORY: " + str(p.memory_info()))
            if None == MyService.prev_network_usage:
                MyService.prev_network_usage = \
                    (psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv)
                new_network_usage = MyService.prev_network_usage
            else:
                MyService.prev_network_usage = new_network_usage
                new_network_usage = \
                    (psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv)
            network_usage = (new_network_usage - MyService.prev_network_usage) / sleep_seconds
            post_data = {
                'hostname'        : MyService.get_hostname(),
                'total_cpu'       : str(lib_cpu_usage()) + "/" + str(psutil.cpu_count()),
                'total_disk'      : str(lib_disk_usage()) + "%",

                'new' : new_network_usage,
                'pre' : MyService.prev_network_usage,

                'total_network'   : str(network_usage) + "bytes per "+str(sleep_seconds)+" seconds",
                'specific_cpu'    : specific_cpu,
                'specific_memory' : specific_memory,
                'specific_disk'   : 0,
                'specific_network': 0,
            }
            log.debug(json.dumps(post_data, indent=4))
            log.debug("cpu count: " + str(psutil.cpu_count()))
            #log.info(json.dumps(p.net_io_counters(), indent=4))
            c2s_job = apiInterface.drm_resourcePost(post_data)
            # endregion ]]]]]]]]]]]]]]]]] cardrecon process

            if False == dscs_dll.isAvailable():
                MyService.dscs = None
                raise NameError('DSCS is not available')

            # searching can't be started without DSCS
            if False == MyService.get_searching_flag_conf():
                MyService.dscs = dscs_dll
                MyService.sqlite3 = sqlite3
                traverse_all_files_glob(pushFileIfEncrypted)
                MyService.set_searching_flag_conf()



            # region [[[[[[[[[[[[[[[[[[[ C2S JOB
            c2s_job = apiInterface.c2s_jobGet()
            log.info(json.dumps(c2s_job, indent=4))
            job_result_list = []
            for cmd in c2s_job['job']:
                job_result = DO_proc_job(dscs_dll, cmd, service)
                job_result_list.append(job_result)
                log.info(json.dumps(job_result, indent=4, ensure_ascii=False))

            # POST JOB RESULT
            post_data = {
                'job_results' : job_result_list,
            }
            c2s_job_post = apiInterface.c2s_jobPost(post_data)
            # endregion ]]]]]]]]]]]]]]]]] C2S JOB


            # get config to connect to Recon
            v_drm_schedule = apiInterface.v_drm_scheduleGet()

            if None == v_drm_schedule:
                raise NameError('v_drm_schedule is not available')

            er.load_v_drm_schedule(v_drm_schedule)
            log.info(json.dumps(v_drm_schedule, indent=4))

            if False == er.isAvailable():
                raise NameError('Recon is not available')

            # region ER node interface [[[[[[[[[[[[[[[[[[[[


            # update V DRM schedule
            apiInterface.pi_schedulesPost(er.current_schedule_id, er.current_ap_no, 'S')


            # region proc queued
            file_list = sqlite3.fileinfo_select(state='queued')
            for fileinfo in file_list:
                file_id = fileinfo[0]
                file_path = fileinfo[1]
                file_size = fileinfo[2]
                file_state = fileinfo[3]

                filepath2 = dscs_dll.decryptFile(file_path, service.configuration['bAppendDecryptedPostfix'])
                log.info("FILE : " + str(filepath2))

                size_limit = GLOBAL_ENV['QUEUE_SIZE_LIMIT']
                size_sum = int(sqlite3.fileinfo_get_queued_file_size_total()) + file_size
                if size_sum > size_limit:
                    log.info("########################## SIZE LIMIT exceeded : " + str(size_limit))
                    continue

                if None != filepath2:    # decryption success
                    cwinsecurity.set_file_attribute_hidden(filepath2)
                    log.info("file decrypted : " + filepath2)
                    sqlite3.fileinfo_update_state(filepath=file_path, state="decrypted")

                    # TODO add schedule
                    schedule_id = er.my_add_schedule(subpath_list=[filepath2], postfix=str(file_id))
                    sqlite3.fileinfo_update_schedule_id(file_path, schedule_id)
                    log.info("schedule added " + str(schedule_id))

                    # insert DRM schedule
                    apiInterface.pi_schedulesPost(schedule_id, er.current_ap_no, 'D')
                else:                   # decryption failed
                    sqlite3.fileinfo_delete(file_path)
            # endregion proc queued

            # region proc decrypted & has schedule_id
            file_list = sqlite3.fileinfo_select_scheduled()
            for fileinfo in file_list:
                file_path = fileinfo[1]
                file_DSCSIsEncryptedRet = fileinfo[4]
                file_schedule_id = fileinfo[5]
                log.debug("FILE : " + str(file_path))

                decrypted_filepath = Dscs_dll.get_decrypted_filepath(file_path, service.configuration['bAppendDecryptedPostfix'])
                if er.is_schedule_completed(file_schedule_id):
                    # sqlite3.fileinfo_delete(file_path)
                    sqlite3.fileinfo_update_state(filepath=file_path, state="completed")
                    log.info("schedule completed " + str(file_schedule_id))

                    # upsert DRM schedule
                    apiInterface.pi_schedulesPost(file_schedule_id, er.current_ap_no, 'C')
                    log.debug(file_path + " completed (schedule_id:"+str(file_schedule_id)+")")
                    sqlite3.fileinfo_delete(file_path)
                    os.remove(decrypted_filepath)
                '''
                else:
                    try:
                        if None == file_DSCSIsEncryptedRet:
                            os.remove(decrypted_filepath)
                    except FileNotFoundError as e:
                        log.error(traceback.format_exc())
                        log.error(str(e))
                    finally:
                        sqlite3.fileinfo_delete(file_path)
                        log.info(" DELETE ##################################")
                '''

            # endregion proc decrypted & has schedule_id

        except requests.exceptions.ChunkedEncodingError as e:
            log.error(traceback.format_exc())
            log.error(str(e))
            return
        except requests.exceptions.ConnectionError as e:
            log.error(traceback.format_exc())
            log.error(str(e))
            return
        except json.decoder.JSONDecodeError as e:
            log.error(traceback.format_exc())
            log.error(str(e))
            return
        except NameError as e:
            log.error(traceback.format_exc())
            log.error(e)
        except Exception as e:
            log.error(traceback.format_exc())
            log.error(str(e))
            return
        finally:
            if logging.INFO == service.configuration['log_level'] or logging.DEBUG == service.configuration['log_level']:
                log.setLevel(service.configuration['log_level'])
                setLogLevel(service.configuration['log_level'])
                log.debug('set log level to ' + str(service.configuration['log_level']))
            time.sleep(sleep_seconds) # Important work

def proc_install():
    if len(sys.argv) == 2:
        if "setup" == sys.argv[1]:
            mount_points = cwinsecurity._get_mount_points()
            SC_PATH = mount_points[0]+"windows\\system32\\sc"
            for i in range(len(sys.argv)):
                print(sys.argv[i])
            # os.system("\"" + sys.argv[0] + "\" --startup delayed install")
            os.system("\"" + sys.argv[0] + "\" --startup auto install")
            os.system(SC_PATH + " failure \"" + MyServiceFramework._svc_name_ + "\" reset= 0 actions= restart/0/restart/0/restart/0")
            os.system("\"" + sys.argv[0] + "\" start")
            # os.system(SC_PATH + " sdset myservice D:(D;;DCLCWPDTSD;;;IU)(D;;DCLCWPDTSD;;;SU)(D;;DCLCWPDTSD;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
            workdir_path = ntpath.dirname(sys.executable)
            userprofile = os.getenv("userprofile", "")
            cmd = "copy \"" + workdir_path + "\\configuration.json\" \""+userprofile+"\\AppData\\Local\\Temp\""
            os.system(cmd)
            time.sleep(1)
            sys.exit(0)
        elif "closedown" == sys.argv[1]:
            mount_points = cwinsecurity._get_mount_points()
            SC_PATH = mount_points[0]+"windows\\system32\\sc"
            for i in range(len(sys.argv)):
                print(sys.argv[i])
            os.system(SC_PATH + " sdset myservice D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
            os.system(SC_PATH + " stop \"" + MyServiceFramework._svc_name_ + "")
            os.system(SC_PATH + " delete \"" + MyServiceFramework._svc_name_ + "")
            sys.exit(0)
        elif "do_job" == sys.argv[1]:
            log.debug("DO_JOB")
            proc_main()
            sys.exit(0)
        elif "insert_into_db" == sys.argv[1]:
            sqlite3 = csqlite3(name=MyService.get_path('state.db'), log=log)

            file_list = [
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11.txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (2).txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (3).txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (4).txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (5).txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (6).txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (7).txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (8).txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (9).txt',
                'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11 - 복사본 (10).txt',
            ]
            for filepath in file_list:
                sqlite3.fileinfo_insert(filepath)
            sys.exit(0)
        elif "test_dscs" == sys.argv[1]:
            dscs_dll = Dscs_dll()
            bAppendPrefix = False
            job_path = 'C:\\Users\\Admin\\Desktop\\repos\\GitHub\\testdoc 공백 특수ㅁㄴㅇㄹ가나♣♣11.txt'
            dscs_dll.decryptFile(job_path, bAppendPrefix=bAppendPrefix)
            sys.exit(0)
        elif "stop_svc" == sys.argv[1]:
            mount_points = cwinsecurity._get_mount_points()
            SC_PATH = mount_points[0]+"windows\\system32\\sc"
            os.system(SC_PATH + " sdset myservice D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
            os.system(SC_PATH + " stop \"" + MyServiceFramework._svc_name_ + "")
            os.system(SC_PATH + " delete \"" + MyServiceFramework._svc_name_ + "")
            os.system("taskkill /F /IM "+GLOBAL_ENV["EXE_FILENAME"])
            #time.sleep(1)
            os.system("taskkill /F /IM "+GLOBAL_ENV["EXE_FILENAME"])
            sys.exit(0)
        elif "tasklist" == sys.argv[1]:
            os.system("tasklist | findstr "+GLOBAL_ENV["EXE_FILENAME"])
            sys.exit(0)
        elif "open_except_path_json" == sys.argv[1]:
            os.system("code "+MyService.get_path('except_path_list.json'))
            sys.exit(0)
        elif "open_except_format_json" == sys.argv[1]:
            os.system("code "+MyService.get_path('except_format_list.json'))
            sys.exit(0)
        elif "disk_partitions" == sys.argv[1]:
            disk_partitions = psutil.disk_partitions()
            print(disk_partitions[0])
            print(json.dumps(disk_partitions, indent=4))
            sys.exit(0)
        elif "resource_monitor" == sys.argv[1]:
            #cardrecon_pid = lib_get_pid_by_name_reg(r'\d\dcardrecon\d*')
            cardrecon_pid = lib_get_pid_by_name_reg(r'python*')
            log.info("cardrecon pid : " + str(cardrecon_pid))
            p = psutil.Process(cardrecon_pid)
            log.info("CPU : " + str(lib_cpu_usage()))
            log.info("IO: " + str(p.io_counters()))
            log.info("MEMORY: " + str(p.memory_info()))
            sys.exit(0)
        elif "remove_svc" == sys.argv[1]:
            MyService.unset_searching_flag_conf()
            os.system("del " + MyService.get_path('state.db'))
            mount_points = cwinsecurity._get_mount_points()
            SC_PATH = mount_points[0]+"windows\\system32\\sc"
            install_path = cwinsecurity.get_systemdrive() + "\\Program Files (x86)\\Ground Labs\\Enterprise Recon 2\\DRM\\"
            cmd_list = [
                SC_PATH + " sdset myservice D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)",
                SC_PATH + " stop \"" + MyServiceFramework._svc_name_ + "",
                SC_PATH + " delete \"" + MyServiceFramework._svc_name_ + "",
                'taskkill /f /im '+GLOBAL_ENV["EXE_FILENAME"],
                'taskkill /f /im '+GLOBAL_ENV["EXE_FILENAME"],
                'taskkill /f /im '+GLOBAL_ENV["EXE_FILENAME"],
                "rmdir /s /q \"" + install_path + "\"",
            ]

            for cmd in cmd_list:
                log.info(cmd)
                os.system(cmd)
                time.sleep(0.1)
            sys.exit(0)



        ##### Commands for Debugging
        elif "dbg_set_searching_flag_conf" == sys.argv[1]:
            MyService.user_id = os.getenv('USERNAME')
            MyService.set_searching_flag_conf()
            sys.exit(0)
        elif "dbg_unset_searching_flag_conf" == sys.argv[1]:
            MyService.user_id = os.getenv('USERNAME')
            MyService.unset_searching_flag_conf()
            sys.exit(0)
        elif "dbg_get_queued_file_size_total" == sys.argv[1]:
            MyService.user_id = os.getenv('USERNAME')
            sqlite3 = csqlite3(name=MyService.get_path('state.db'), log=log)
            total_size = sqlite3.fileinfo_get_queued_file_size_total()
            log.info("FILE size total : " + str(total_size))
            kilobytes = int(int(total_size) / 1024)
            log.info(str(kilobytes) + " kilobytes")

            sys.exit(0)
        elif "dbg_open_except_path_list" == sys.argv[1]:
            code_path = "C:\\Program Files\\Microsoft VS Code\\Code.exe"
            import subprocess
            MyService.user_id = os.getenv('USERNAME')
            subprocess.Popen("\"" + code_path + "\" " + MyService.get_path('except_path_list.json'))
            sys.exit(0)
        elif "dbg_open_configuration" == sys.argv[1]:
            code_path = "C:\\Program Files\\Microsoft VS Code\\Code.exe"
            import subprocess
            MyService.user_id = os.getenv('USERNAME')
            subprocess.Popen("\"" + code_path + "\" " + MyService.get_path('configuration.json'))
            sys.exit(0)
        elif "dbg_open_sqlite_db" == sys.argv[1]:
            sqlite_browser = "C:\\Users\\Admin\\Downloads\\SQLiteDatabaseBrowserPortable\\App\\SQLiteDatabaseBrowser64\\DB Browser for SQLCipher.exe"

            import subprocess
            MyService.user_id = os.getenv('USERNAME')
            subprocess.Popen("\"" + sqlite_browser + "\" " + MyService.get_path('state.db'))
            sys.exit(0)

        '''
        elif "debug_svc" == sys.argv[1]:
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
        '''

if __name__ == '__main__':
    try:
        install_path = cwinsecurity.get_systemdrive() + "\\Program Files (x86)\\Ground Labs\\Enterprise Recon 2\\DRM\\"
        full_dirpath = cwinsecurity.get_systemdrive() + "\\Program Files (x86)\\Ground Labs\\Enterprise Recon 2\\DRM"
        full_path = "\"" + install_path + GLOBAL_ENV["EXE_FILENAME"] + "\""
        if (len(sys.argv) == 1 and False == os.path.isfile(install_path + GLOBAL_ENV["EXE_FILENAME"])):
            MyService.unset_searching_flag_conf()

            log.info(full_path + " not exist")
            log.info(sys.executable)
            mount_points = cwinsecurity._get_mount_points()
            SC_PATH = mount_points[0]+"windows\\system32\\sc"
            workdir_path = ntpath.dirname(sys.executable)

            cmd_list = [
                #SC_PATH + " sdset myservice D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)",
                SC_PATH + " stop \"" + MyServiceFramework._svc_name_ + "",
                SC_PATH + " delete \"" + MyServiceFramework._svc_name_ + "",
                'taskkill /f /im '+GLOBAL_ENV["EXE_FILENAME"],
                'taskkill /f /im '+GLOBAL_ENV["EXE_FILENAME"],
                'taskkill /f /im '+GLOBAL_ENV["EXE_FILENAME"],
                "rmdir /s /q \"" + install_path + "\"",
                "mkdir \"" + full_dirpath + "\"",
                "copy "+sys.executable+" " + full_path,
                "copy \"" + workdir_path + "\\configuration.json\" \""+install_path+"\"",
                full_path + " --startup auto install",
                SC_PATH + " failure \"" + MyServiceFramework._svc_name_ + "\" reset= 0 actions= restart/0/restart/0/restart/0",
                full_path + " start",
            ]

            for cmd in cmd_list:
                log.info(cmd)
                os.system(cmd)
                time.sleep(0.1)

            # os.system(SC_PATH + " sdset myservice D:(D;;DCLCWPDTSD;;;IU)(D;;DCLCWPDTSD;;;SU)(D;;DCLCWPDTSD;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
            #userprofile = os.getenv("userprofile", "")
            #cmd = "copy \"" + workdir_path + "\\configuration.json\" \""+userprofile+"\\AppData\\Local\\Temp\""
            #os.system(cmd)
            sys.exit(0)
        #log.info(str(sys.argv))
        MyService.self_path = executable#sys.argv[0]
        proc_install()
        init()
    except Exception as e:
        log.error(traceback.print_stack())
        log.error(e)