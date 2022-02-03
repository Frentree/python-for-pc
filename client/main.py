import servicemanager
import sys
import time
import random
import requests
import json
import platform
import logging
import ntpath
import re

import lib_logging

from pathlib import Path

from lib_logging import log
from lib import *
from lib_BaseWinservice import BaseWinservice
from lib_dscsdll import Dscs_dll

configuration = {
    "debug":True,
    "sleep_seconds": 2,
    "dll_name": "CryptDll.dll",
    "server_address":"183.107.9.230:11119",
    "hostname": "175.203.71.27",
    "bAppendDecryptedPostfix": False,
}

def DO_load_existing_config():
    global configuration
    if False == os.path.isfile("configuration.json"):
        print("file not found")
    else:
        with open("configuration.json", "r", encoding="utf-8-sig") as json_conf_file:
            file_content = json_conf_file.read()
            configuration = json.loads(file_content)
            #print(configuration)

def DO_update_config(content):
    try:
        with open('configuration.json', 'w') as json_out_file:
            json.dump(content, json_out_file, indent=4, ensure_ascii=False)
            #json.dump(content, json_out_file)
    except FileNotFoundError as e:
        logging.error(str(e))

DO_load_existing_config()
configuration['hostname'] = platform.node()
DO_update_config(configuration)
#print(configuration)
#print("###")
#sys.exit(0)

if 2 == len(sys.argv) and "DEBUG" == sys.argv[1]:
    class BaseWinservice:
        @classmethod
        def parse_command_line(cls):
            '''
            ClassMethod to parse the command line
            '''
            a = cls()
            a.SvcRun()

        def SvcStop(self):
            pass

        def SvcRun(self):
            logging.debug("SvcRun")
            self.start()
            self.main()

        def SvcDoRun(self):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def main(self):
            pass

def DO_proc_job(dscs_dll, cmd):
    job_type = cmd['type']
    job_path = cmd['path']
    job_index = cmd['index']
    logging.info("COMMAND: type({:10s}) path({})".format(str(job_type), str(job_path)))

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
            logging.error(job_result['message'])
            break

        if 'decrypt' == job_type:
            funcname = "DSCSDecryptFile"
            bname = ntpath.basename(job_path)
            pure_file_stem = pathlib.PurePath(bname).stem
            pure_file_ext  = pathlib.PurePath(bname).suffix
            filepath2 = ntpath.dirname(job_path) + "\\" + pure_file_stem + ("_decrypted" if configuration['bAppendDecryptedPostfix'] else "") + pure_file_ext
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
            ret = dscs_dll.call_DSCSMacEncryptFile(job_path, "0000061")
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

class FTService(BaseWinservice):
    _svc_name_ = "ftservice"
    _svc_display_name_ = "FT Service"
    _svc_description_ = "FT Service Description"

    def start(self):
        logging.debug("FTService start")
        self.isrunning = True

    def stop(self):
        logging.debug("FTService stop")
        self.isrunning = False

    def main(self):
        #rc = None
        #while rc != win32event.WAIT_OBJECT_0:
        #    try:
        #        dscs_dll = Dscs_dll()
        #    except FileNotFoundError as e:
        #        logging.error(e)
        #        return
        #    mysvc = MyService(dscs_dll)
        #    mysvc.svc()
        #    rc = win32event.WaitForSingleObject(self.hWaitStop, 10) # milliseconds

        #self.dscs_dll = dscs_dll
        logging.debug("FTService main")
        while self.isrunning:
            #logging.info(os.environ['USERPROFILE']) #C:\Users\username
            #logging.info(os.getlogin())
            #logging.info(os.getenv('username'))
            #import subprocess
            #subprocess.call(['C:\\Users\\danny\\Desktop\\ft\\ftclient\\dist\\ConsoleApplication2.exe', 'C:\\Users\\danny\\Desktop\\ft\\ftclient\\dist\\dscsdll.exe'])
            #sys.exit(0)
            print("SERVER " + configuration['server_address'])
            sys.exit(0)

            try:
                dscs_dll = Dscs_dll()
            except FileNotFoundError as e:
                logging.error(e)
                sys.exit(0)

            # GET JOB
            try:
                url = 'http://'+configuration['server_address']+'/c2s_job' + "/" + configuration["hostname"]
                logging.info(url)
                r = requests.get(url)
                ret = r.json()
                logging.debug(ret)
            except requests.exceptions.ConnectionError as e:
                logging.error(str(e))
                return
            except json.decoder.JSONDecodeError as e:
                logging.error(str(e))
                return

            configuration['sleep_seconds'] = int(ret['config'][0]['sleep_seconds'])

            job_result_list = []
            for cmd in ret['job']:
                job_result = DO_proc_job(dscs_dll, cmd)
                job_result_list.append(job_result)
                #logging.info(json.dumps(job_result, indent=4, ensure_ascii=False))

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
                logging.debug(json.dumps(post_data, indent=4, ensure_ascii=False))
                r = requests.post('http://'+configuration['server_address']+'/c2s_job' + "/" + configuration["hostname"], json=post_data)
                result_ret = str(r.json())
                logging.debug(json.dumps(result_ret, indent=4, ensure_ascii=False))
            except requests.exceptions.ChunkedEncodingError as e:
                logging.error(str(e))
                return
            except json.decoder.JSONDecodeError as e:
                logging.error(str(e))
                return

            #log("setting sleep seconds : " + str(ret['config'][0]['sleep_seconds']))
            time.sleep(configuration['sleep_seconds'])


def proc_install():
    if len(sys.argv) == 2:
        if "setup" == sys.argv[1]:
            for i in range(len(sys.argv)):
                print(sys.argv[i])
            os.system("\"" + sys.argv[0] + "\" --startup delayed install")
            os.system("sc failure \"" + FTService._svc_name_ + "\" reset= 0 actions= restart/0/restart/0/restart/0")
            os.system("\"" + sys.argv[0] + "\" start")
            #time.sleep(20)
            sys.exit(0)
        elif "closedown" == sys.argv[1]:
            for i in range(len(sys.argv)):
                print(sys.argv[i])
            os.system("\"" + sys.argv[0] + "\" remove")
            #time.sleep(20)
            sys.exit(0)

if __name__ == '__main__':
    print("MAIN")
    sys.exit(0)

    import subprocess
    #subprocess.call(['C:\\windows\\system32\\Notepad.exe', 'C:\\test.txt'])
    #subprocess.call(['C:\\Users\\danny\\Desktop\\ft\\ftclient\\dist\\ConsoleApplication2.exe', 'C:\\Users\\danny\\Desktop\\ft\\ftclient\\dist\\dscsdll.exe'])
    #os.system('"C:\\Users\\danny\\Desktop\\ft\\ftclient\\dist\\ConsoleApplication2.exe"')#' "C:\\Users\\danny\\Desktop\\ft\\ftclient\\dist\\dscsdll.exe"')
    #logging.info(os.environ['USERPROFILE'])
    #try:
    #    dscs_dll = Dscs_dll()
    #except FileNotFoundError as e:
    #    logging.error(e)
    #    sys.exit(0)
    #logging.info(os.getlogin())
    #logging.info(os.getenv('username'))
    #sys.exit(0)
    for proc in psutil.process_iter():
        # process name pattern : 53cardrecon193247928347982
        p = re.compile(r'\d\dcardrecon\d*', re.IGNORECASE)
        m = p.match(proc.name())
        if m:
            #print(proc.name())
            print('Match found: ', m.group())
            pass
        else:
            pass
            #print('No match')
    #sys.exit(0)

    proc_install()

    # TODO copy two dll files

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FTService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # install/update/remove/start/stop/restart or debug the service
        # One of those command line options must be specified
        #win32serviceutil.HandleCommandLine(FTService)
        FTService.parse_command_line()
