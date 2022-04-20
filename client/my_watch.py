import time
import os
import sys
import requests
import json
import ntpath
import pathlib
from sys import modules, executable
from lib_runas import runas
from lib_logging import config_logging, log
from lib_dscsdll import Dscs_dll
from lib import *
from win32serviceutil import StartService, QueryServiceStatus
from lib_winservice2 import MyServiceFramework, MyService

# There are two infinite loops in this framework
#   one is SERVICE loop and
#   the other is CONSOLE loop
#   - SERVICE : run CONSOLE and watchdog
#   - CONSOLE : run er node interface
#

config_logging()

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

    try:
        service.save_config()
    except Exception as e:
        log.error(e)

if __name__ == '__main__':
  #MyService.self_path = executable#sys.argv[0]
  log.debug(str(sys.argv))
  try:
    if len(sys.argv) == 1:
      MyServiceFramework.init_service()
    elif len(sys.argv) == 2:
      SC_PATH = "c:\\windows\\system32\\sc"
      if "debug" == sys.argv[1]:
          service = MyService()
          service.run()
      elif "do_job" == sys.argv[1]:
          log.debug("DO_JOB")
          proc_main()
      elif "setup" == sys.argv[1]:
          for i in range(len(sys.argv)):
              print(sys.argv[i])
          # os.system("\"" + sys.argv[0] + "\" --startup delayed install")
          os.system("\"" + sys.argv[0] + "\" --startup auto install")
          os.system(SC_PATH + " failure \"" + MyServiceFramework._svc_name_ + "\" reset= 0 actions= restart/0/restart/0/restart/0")
          log.info("\"" + sys.argv[0] + "\" start")
          os.system("\"" + sys.argv[0] + "\" start")
          #os.system(SC_PATH + " sdset myservice D:(D;;DCLCWPDTSD;;;IU)(D;;DCLCWPDTSD;;;SU)(D;;DCLCWPDTSD;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
          time.sleep(1)
      elif "closedown" == sys.argv[1]:
          for i in range(len(sys.argv)):
              print(sys.argv[i])
          #os.system(SC_PATH + " sdset myservice D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)")
          os.system(SC_PATH + " stop \"" + MyServiceFramework._svc_name_ + "")
          os.system(SC_PATH + " delete \"" + MyServiceFramework._svc_name_ + "")
          os.system("\"" + sys.argv[0] + "\" remove")
          time.sleep(1)
    else:
      MyServiceFramework.handle_commandline()

  except Exception as e:
    log.error(e)
