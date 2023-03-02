from re import S
import win32serviceutil  # ServiceFramework and commandline helper
import win32service  # Events
import servicemanager  # Simple setup and logging
import os
import sys
import json
import ntpath
import time
import traceback
import logging
import psutil
import requests

import lib_logging
import lib_misc
import lib_wd
import lib_dscsdll
import lib_winsvc
import lib_process
import lib_runas
import lib_apiserver
import lib_er
import lib_sqlite3
import lib_watchdog
import lib_patterns
from watchdog.observers import Observer
from lib_cpupriority import setpriority

# region development
def dev_diag():
  log.info(json.dumps(sys.argv, indent=4))
  cmd_list = [
    'is_drm_installed()',
    'is_er2_installed()',
    'lib_misc.is_os_64bit()',
    'sys.executable',
    'os.getcwd()',
  ]
  for cmd in cmd_list:
    ret = eval(cmd)
    log.info(f'[DIAG] {str(ret):<6} : {cmd}')

# endregion

# region configuration
"""
  configuration priority
  High ---------------------> Low
  [API Server]  [Local File]  [Process Embedding]

  따라서 configuration의 일반적인 로드 과정으로 local file을 로드한 후 API 서버의 설정을 로드한다.
"""
def env_load_config_file():
  if False == os.path.isfile(_G["PATH_FILE_MAINEXE"]):    # drm not installed
    path_conf_json = ".\\configuration.json"
  else:                                                   # drm installed
    path_conf_json = _G['PATH_CONF_JSON']

  log.debug("cwd : " + os.getcwd())
  log.debug("LOAD CONFIG FILE : " + path_conf_json)
  with open(path_conf_json, 'r', encoding='utf-8-sig') as json_conf_file:
    conf_content = json_conf_file.read()
    conf_dic = json.loads(conf_content)

  _G.update(conf_dic)
  # NOTE: EQUALS to
  # for k, v in conf_dic.items():
  #   log.info(k)
  log.debug(json.dumps(_G, indent=4))

  ignore_dir_regex_list = []
  if 'WATCHDOG_IGNORE_DIR_REGEX_LIST' not in _G or 0 == len(_G['WATCHDOG_IGNORE_DIR_REGEX_LIST']):
    pass
  else:
    except_path_list = _G['WATCHDOG_IGNORE_DIR_REGEX_LIST'].split(',')
    for except_path in except_path_list:
      except_path = except_path.replace("\\", "\\\\")
      except_path = except_path.replace("$", "\$")
      ignore_dir_regex_list.append("^.:"+except_path+".*$")
      log.debug("^.:"+except_path+".*$")
  _G_internal['WATCHDOG_IGNORE_DIR_REGEX_LIST'] = ignore_dir_regex_list

def env_save_config_file():
  path_conf_json = _G['PATH_CONF_JSON']
  with open(path_conf_json, 'w', encoding='utf-8-sig') as json_conf_file:
    json.dump(_G, json_conf_file, indent=4, ensure_ascii=False)
# endregion

def init_global_env():
  # NOTE: The key name for global variables should be upper case.
  # NOTE: All values should be stored as string type
  g = {}

  g['IS_DEV'] = True

  # path
  g['SYS_DRV']            = lib_misc.get_systemdrive()
  g['SYS_ROOT']           = lib_misc.get_systemroot()
  g['PATH_ER2']           = g['SYS_DRV'] + \
    "\\Program Files (x86)\\Ground Labs\\Enterprise Recon 2"
  g['PATH_ER2_SERVICE_EXE'] = f'{g["PATH_ER2"]}{os.sep}er2_service.exe'
  g['PATH_DRM']           = g['PATH_ER2'] + os.sep + 'DRM'
  g['PATH_CONF_JSON']     = g['PATH_DRM'] + os.sep + 'configuration.json'
  g['PATH_CONF_DB']       = g['PATH_DRM'] + os.sep + 'state.db'
  g['FILE_NAME_MAINEXE']  = 'ftclient.exe'
  g['PATH_FILE_MAINEXE']  = g['PATH_DRM'] + os.sep + g['FILE_NAME_MAINEXE']

  # development
  g['log_level'] = logging.DEBUG #g['INITIAL_LOGGING_LEVEL'] = logging.DEBUG

  # g['LOGFILE_PATH'] = '.' # or None
  g['LOGFILE_PATH'] = g['PATH_DRM'] if True == os.path.isfile(g["PATH_FILE_MAINEXE"]) else "."   # check whether drm not installed

  g['LOGFILE_BACKUPCOUNT'] = str(10)
  g['LOGFILE_MAXBYTES'] = str(20 * lib_misc.get_bytes_number_one_mega())  # 20 Megabytes

  # windows service
  g['SVC_NAME'] = "MyService16"
  g['SVC_DISPLAY_NAME'] = "MyService16"
  g['SVC_DESCRIPTION'] = "Service Description"
  g['SVC_NAME_ER2'] = "Enterprise Recon 2 Agent"
  g['SC_PATH'] = lib_misc.get_systemroot() + os.sep + "System32" + os.sep + "sc"
  g['SVC_HIDE'] = str(True)
  g['SVC_LOOP_DELAY_SECONDS'] = str(5)

  # Enterprise Recon 2
  g['ER2_PROCESS_NAME_REGEX_CARDRECON'] = '\d\dcardrecon\d*'
  g['ER2_QUEUE_SIZE_LIMIT'] = str(500 * lib_misc.get_bytes_number_one_mega())  # 200 Megabytes

  # dscs
  g['DSCS_ENC_TYPE']  = "mac"
  g['DSCS_NGUIDE']    = str(3)
  g['DSCS_LPSZACL']   = "1;1;0;0;1;1;0"
  g['DSCS_DEFAULT_CATEGORY_ID'] = "0000001"
  g['DSCS_DLL_FILE_NAME'] = "DSCSLink64.dll" if lib_misc.is_os_64bit() else "DSCSLink.dll"
  g['DSCS_FILEPATH_ENCODING'] = "cp949"
  g['s_no'] = "0000001" #g['DSCS_S_NO'] = "0000001"
  g['p_no'] = "0000001" #g['DSCS_P_NO'] = "0000001"
  g['DECRYPTED_POSTFIX'] = '_decrypted'
  g['DSCS_MINIMUM_FILESIZE'] = str(5)
  g['DSCS_ALL_FILES_TRAVERSED'] = str(False)
  g['DSCS_SLEEP_SECOND_IF_NOT_INSTALLED'] = str(60*60*24) # default value: 1 day

  # api server
  g['API_SERVER_ADDR'] = '183.107.9.230'
  g['API_SERVER_PORT'] = '11119'
  g['HOSTNAME'] = ''

  # DRM
  g['DRM_LOOP_DELAY_SECONDS'] = str(5)

  # CPU PRIORITY
  # - 1: BELOW_NORMAL
  # - 2: NORMAL
  # - 3: ABOVE_NORMAL
  g['CPU_PRIORITY'] = str(1)

  # watchdog
  g['WATCHDOG_TIMEOUT'] = str(5)
  ignore_ext_list = lib_patterns.get_ignore_ext_list()
  target_ext_list = lib_patterns.get_target_ext_list()
  ignore_dir_regex_list = lib_patterns.get_ignore_dir_regex_list()
  ignore_pattern_list = []
  for ignore_ext in ignore_ext_list:
    if ignore_ext in target_ext_list:
      continue
    ignore_pattern_list.append('*'+ignore_ext)
  target_pattern_list = []
  for target_ext in target_ext_list:
    target_pattern_list.append('*'+target_ext)
  g['WATCHDOG_TARGET_PATTERNS'] = ','.join(target_pattern_list)     # '*.txt;*.xls'
  g['WATCHDOG_IGNORE_PATTERNS'] = ','.join(ignore_pattern_list)     # '*.exe;*.dll'
  g['WATCHDOG_IGNORE_DIR_REGEX_LIST'] = ','.join(ignore_dir_regex_list)

  # g['WATCHDOG_TARGET_PATTERNS'] = '*.txt;*.xls'
  # g['WATCHDOG_IGNORE_PATTERNS'] = '*.py;*.exe'

  g_internal = {}
  g_internal['SLEEP_SECONDS_MINIMUM'] = str(1)

  '''
  g_internal['ignore_dir_regex_list'] = lib_patterns.get_ignore_dir_regex_list()
  if g['IS_DEV']:
    g_internal['ignore_dir_regex_list'].append('^.:\\\\Users\\\\Admin\\\\Desktop\\\\.*$')
    g_internal['ignore_dir_regex_list'].append('^.:\\\\Users\\\\Admin\\\\Documents\\\\.*$')
    g_internal['ignore_dir_regex_list'].append('^.:\\\\Users\\\\Admin\\\\Downloads\\\\.*$')
    g_internal['ignore_dir_regex_list'].append('^.:\\\\Users\\\\All Users.*$')
  '''
  return (g, g_internal)

(_G, _G_internal) = init_global_env()
log = lib_logging.init_log(_G['log_level'], {
    "logfile_path"       : _G['LOGFILE_PATH'],
    # "logfile_path"       : _G['PATH_DRM'] if True == os.path.isfile(_G["PATH_FILE_MAINEXE"]) else "."   # check whether drm not installed
    "logfile_maxbytes"   : int(_G['LOGFILE_MAXBYTES']),
    "logfile_backupcount": int(_G['LOGFILE_BACKUPCOUNT']),
  } )
env_load_config_file()

# region misc.
def run_system_with_log(cmd):
  log.info(cmd)
  os.system(cmd)

def run_cmd_list_with_delay(cmd_list, delay_seconds):
  for cmd in cmd_list:
    try:
      run_system_with_log(cmd)
      time.sleep(delay_seconds)
    except Exception as e:
      log.error(traceback.format_exc())
      log.error(str(e))

def sleep_with_minimum_seconds(sleep_seconds, minimum_seconds):
  if sleep_seconds < minimum_seconds:
    sleep_seconds = minimum_seconds
  time.sleep(sleep_seconds)

def get_watchdog_pathnames():
  watchdog_pathnames = []
  for disk_partition in psutil.disk_partitions():
    log.info(json.dumps(disk_partition))#, indent=4))
    if '' != disk_partition.fstype:
      watchdog_pathnames.append(disk_partition.mountpoint)
  return watchdog_pathnames

def is_client_with_winlogonsession_running():
  is_running = False
  pid_list = lib_process.lib_get_pid_list_by_name(_G['FILE_NAME_MAINEXE'])
  for pid in pid_list:
    import win32ts
    if lib_runas.get_winlogon_sessionId() == win32ts.ProcessIdToSessionId(pid):
      is_running = True
  return is_running

def is_session0_running():
  is_running = False
  pid_list = lib_process.lib_get_pid_list_by_name(_G['FILE_NAME_MAINEXE'])
  for pid in pid_list:
    import win32ts
    if 0 == win32ts.ProcessIdToSessionId(pid):
      is_running = True
  return is_running

def match_ignore_dir_regex(reg_list, the_path):
  for reg in reg_list:
    import re
    p = re.compile(reg, re.IGNORECASE)
    m = p.fullmatch(the_path)
    if m != None:
      log.info(the_path + " ignore_dir regex matched: " + reg + " ")
      return True
    # log.info(the_path + " ignore_dir regex not matched: " + reg + " ")
  return False

def _split_name_ext_from_path(file_path):
  import ntpath
  import pathlib
  bname = ntpath.basename(file_path)
  pure_file_stem = pathlib.PurePath(bname).stem
  pure_file_ext  = pathlib.PurePath(bname).suffix
  
  file_path = ntpath.dirname(file_path)
  file_name = pure_file_stem
  file_ext  = pure_file_ext
  return (file_path, file_name, file_ext)

def match_except_format(the_path, except_format_list):
  for except_format in except_format_list:
    (file_path, file_name, file_ext) = _split_name_ext_from_path(the_path)
    ext_file = file_ext.lower()
    ext_rule = except_format#except_format[1:].lower()
    if ext_file == ext_rule:
      log.info(the_path + " format matched: " + ext_file + " " + ext_rule)
      return True
    #else:
    #  log.info(the_path + " format not matched: " + ext_file + " " + ext_rule)

  return False

def pushFileIfEncrypted(filepath, sqlite3):
  try:
    filesize = os.path.getsize(filepath)
  except FileNotFoundError as e:
    log.error('FileNotFoundError  ' + str(e))
    return
  except PermissionError as e:
    log.error('PermissionError ' + str(e))
    return
  
  if filesize <= int(_G['DSCS_MINIMUM_FILESIZE']):
    return
  if filesize >= int(_G['ER2_QUEUE_SIZE_LIMIT']):
    return

  retvalue = lib_dscsdll.Dscs_dll.static_DSCSIsEncryptedFile(log, _G['DSCS_DLL_FILE_NAME'], filepath, encoding = _G['DSCS_FILEPATH_ENCODING'])
  if True == retvalue:
    log.info(filepath + " " + "is an ENCRYPTED FILE")
    # insert into DB
    sqlite3.fileinfo_insert_with_size(filepath, filesize)
    return

def traverse_all_files_glob(func, path, sqlite3):
  haystackpath_list = []
  if None != path:
    haystackpath_list.append(path)
  else:
    haystackpath_list = get_watchdog_pathnames()

  for haystackpath in haystackpath_list:
    path = haystackpath + '*'
    log.debug("--> "+path)
    import glob
    for f in glob.glob(path, recursive=True):
      if match_ignore_dir_regex(_G_internal['WATCHDOG_IGNORE_DIR_REGEX_LIST'], f):
        log.debug("match result: -------------------> TRUE " + f)
        continue
      # else:
      #   log.info("match result: FALSE")

      if os.path.isdir(f):
        log.info("searching on : "+f)
        traverse_all_files_glob(func, f+"\\", sqlite3)
      else:
        log.debug("FILE: " + f)
        if match_except_format(f, _G['WATCHDOG_IGNORE_PATTERNS'].split(',')):
          continue
        func(f, sqlite3)

def kill_process():
  path_taskkill = lib_misc.get_systemroot() + os.sep + "System32" + os.sep + "taskkill"
  os.system(path_taskkill +' /f /im '+_G["FILE_NAME_MAINEXE"] + "\n")
  os.system(path_taskkill +' /f /im '+_G["FILE_NAME_MAINEXE"] + "\n")
  os.system(path_taskkill +' /f /im '+_G["FILE_NAME_MAINEXE"] + "\n")

# endregion

# region proc cmdline
def proc_cmdline():
  log.info(sys.argv)
  if len(sys.argv) < 2:
    if False == is_drm_installed():
      install_drm()
    return

  # region misc. commands
  if "_remove" == sys.argv[1]:
    uninstall_drm()
    sys.exit(0)

  elif "_do_job" == sys.argv[1]:
    drm_main()
    sys.exit(0)

  elif "_get_filesize" == sys.argv[1]:
    if len(sys.argv) < 3:
      log.info("you must provide the path of the target file")
      sys.exit(0)
    filepath = sys.argv[2]
    log.info(f"sys len: {len(sys.argv)}")
    log.info(f"DSCS_MINIMUM_FILESIZE: {_G['DSCS_MINIMUM_FILESIZE']}")
    log.info(f"ER2_QUEUE_SIZE_LIMIT: {_G['ER2_QUEUE_SIZE_LIMIT']}")
    log.info(f"filepath: {filepath}")
    try:
      filesize = os.path.getsize(filepath)
      log.info(f"filesize: {filesize}")
    except FileNotFoundError as e:
      log.error('FileNotFoundError  ' + str(e))
      return
    except PermissionError as e:
      log.error('PermissionError ' + str(e))
      return
    sys.exit(0)

  elif "_dscs_is_encrypted" == sys.argv[1]:
    if len(sys.argv) < 4:
      log.info("you must provide the path of the target file")
      sys.exit(0)
    filepath = sys.argv[2]
    encoding = sys.argv[3]
    log.info(f"sys len: {len(sys.argv)}")
    log.info(f"DSCS_DLL: {_G['DSCS_DLL_FILE_NAME']}")
    log.info(f"filepath: {filepath}")
    log.info(f"encoding: {encoding}")
    retvalue = lib_dscsdll.Dscs_dll.static_DSCSIsEncryptedFile(log, dscsdll_file_name = _G['DSCS_DLL_FILE_NAME'], filepath = filepath, encoding = encoding)
    if True == retvalue:
      log.info(filepath + " " + "is an ENCRYPTED FILE")
    else:
      log.info(filepath + " " + "is not an ENCRYPTED FILE")
    sys.exit(0)
  elif "_dscs_is_encrypted_with_init" == sys.argv[1]:
    dscsdll_file_name = _G['DSCS_DLL_FILE_NAME']
    lpszAcl = _G['DSCS_LPSZACL']
    log.info(f"sys len: {len(sys.argv)}")
    if len(sys.argv) < 3:
      log.info("you must provide the path of the target file")
      sys.exit(0)
    elif len(sys.argv) == 4:
      dscsdll_file_name = sys.argv[3]
    elif len(sys.argv) == 5:
      dscsdll_file_name = sys.argv[3]
      lpszAcl = sys.argv[4]

    dscs_dll = lib_dscsdll.Dscs_dll(log, dscsdll_file_name = dscsdll_file_name)
    dscs_dll.init(nGuide=int(_G['DSCS_NGUIDE']), lpszAcl=lpszAcl)

    filepath = sys.argv[2]
    retvalue = lib_dscsdll.Dscs_dll.static_DSCSIsEncryptedFile(log, dscsdll_file_name = dscsdll_file_name, filepath = filepath, encoding = _G['DSCS_FILEPATH_ENCODING'])
    if True == retvalue:
      log.info(filepath + " " + "is an ENCRYPTED FILE")
    else:
      log.info(filepath + " " + "is not an ENCRYPTED FILE")
    sys.exit(0)
  elif "_test_dscs" == sys.argv[1]:
    dscs_dll = lib_dscsdll.Dscs_dll(log, dscsdll_file_name = _G['DSCS_DLL_FILE_NAME'])
    dscs_dll.init(nGuide=int(_G['DSCS_NGUIDE']), lpszAcl=_G['DSCS_LPSZACL'])
    sys.exit(0)
  elif "_diag" == sys.argv[1]:
    dev_diag()
    sys.exit(0)
  elif "_dbg_update" == sys.argv[1]:
    apiServer = lib_apiserver.cApiServer(
      server_addr = _G['API_SERVER_ADDR'],
      server_port = _G['API_SERVER_PORT'],
      hostname = os.getenv("COMPUTERNAME", ""),
      log = log)
    print(len(sys.argv))
    filepath = ""
    if len(sys.argv) > 2:
      filepath = sys.argv[2]
    apiServer.c2s_update(filepath)
    log.info("filepath: " + filepath)

    sys.exit(0)
  # endregion

  # region DEBUG - commands for windows service
  elif "_is_er2_service_exe_exist" == sys.argv[1]:
    print(is_er2_service_exe_exist())
    sys.exit(0)

  elif "_hide_svc" == sys.argv[1]:
    lib_winsvc.hide_svc(_G['SC_PATH'], _G['SVC_NAME'])
    sys.exit(0)

  elif "_unhide_svc" == sys.argv[1]:
    run_system_with_log(lib_winsvc.get_unhide_svc_cmd(_G['SC_PATH'], _G['SVC_NAME']))
    sys.exit(0)
  # endregion

  elif "_open_configuration" == sys.argv[1]:
    exe = "C:\\windows\\system32\\notepad.exe"

    import subprocess
    subprocess.Popen("\"" + exe + "\" \"" + _G['PATH_CONF_JSON'] + "\"")
    sys.exit(0)

  # region DEBUG - commands for sqlite
  elif "_dbg_open_sqlite_db" == sys.argv[1]:
    sqlite_browser = "C:\\Users\\Admin\\Downloads\\SQLiteDatabaseBrowserPortable\\App\\SQLiteDatabaseBrowser64\\DB Browser for SQLCipher.exe"

    import subprocess
    subprocess.Popen("\"" + sqlite_browser + "\" \"" + _G['PATH_CONF_DB'] + "\"")
    sys.exit(0)

  elif "_dbg_list_sqlite_db" == sys.argv[1]:
    sqlite3 = lib_sqlite3.csqlite3(file_path=_G['PATH_CONF_DB'], log=log)

    # log.info(" == QUEUE list == ")
    print(" == QUEUE list == ")
    all_records = sqlite3.schedule_fileinfo_select_all()
    for record in all_records:
      filepath = record[1]
      # log.info(filepath + " exist: " + str(os.path.isfile(filepath)))
      # log.info(record)
      print(record)

    # log.info(" == Exception list == ")
    print(" == Exception list == ")
    all_records = sqlite3.except_fileinfo_select_all()
    for record in all_records:
      filepath = record[2]
      # log.info(filepath + " exist: " + str(os.path.isfile(filepath)))
      # log.info(record)
      print(record)
    sys.exit(0)

  elif "_dbg_query_sqlite_db" == sys.argv[1]:
    sqlite3 = lib_sqlite3.csqlite3(file_path=_G['PATH_CONF_DB'], log=log)
    print(_G['PATH_CONF_DB'])

    log.info(" == QUEUE list == ")
    all_records = sqlite3.schedule_fileinfo_select_all()
    for record in all_records:
      filepath = record[1]
      # log.info(filepath + " exist: " + str(os.path.isfile(filepath)))
      log.info(record)

    log.info(" == Exception list == ")
    all_records = sqlite3.except_fileinfo_select_all()
    for record in all_records:
      filepath = record[2]
      # log.info(filepath + " exist: " + str(os.path.isfile(filepath)))
      log.info(record)
    sys.exit(0)

  elif "_dbg_delete_record_sqlite_db" == sys.argv[1]:
    sqlite3 = lib_sqlite3.csqlite3(file_path=_G['PATH_CONF_DB'], log=log)

    if len(sys.argv) < 5:
      sys.exit(0)
    log.info(" == DELETE record == ")

    lib_logging.setLogLevel(log, logging.DEBUG)

    if ("schedule" == sys.argv[2]):
      sqlite3.schedule_fileinfo_delete_by_filepath_org(sys.argv[3])
    elif ("except" == sys.argv[2]):
      sqlite3.except_fileinfo_delete(sys.argv[3])
    sys.exit(0)

  elif "_dbg_remove_sqlite_db" == sys.argv[1]:
    os.system("del " + " \"" + _G['PATH_CONF_DB'] + "\"")
    sys.exit(0)

  elif "_dbg_get_v_drm_schedule" == sys.argv[1]:
    apiServer = lib_apiserver.cApiServer(
      server_addr = _G['API_SERVER_ADDR'],
      server_port = _G['API_SERVER_PORT'],
      hostname = os.getenv("COMPUTERNAME", ""),
      log = log)

    # get config to connect to ER2
    v_drm_schedule = apiServer.v_drm_scheduleGet()
    if None == v_drm_schedule:
      raise NameError('v_drm_schedule is not available')

    sys.exit(0)
  elif "_dbg_set_v_drm_schedule" == sys.argv[1]:
    set_DRM_STATUS = ['S', 'D', 'C']
    new_DRM_STATUS = sys.argv[2]
    if new_DRM_STATUS not in set_DRM_STATUS:
      log.info("new DRM_STATUS should be " + str(set_DRM_STATUS))
      sys.exit(0)

    apiServer = lib_apiserver.cApiServer(
      server_addr = _G['API_SERVER_ADDR'],
      server_port = _G['API_SERVER_PORT'],
      hostname = os.getenv("COMPUTERNAME", ""),
      log = log)

    # get config to connect to ER2
    v_drm_schedule = apiServer.v_drm_scheduleGet()
    if None == v_drm_schedule:
      raise NameError('v_drm_schedule is not available')

    apiServer.pi_schedulesPost(v_drm_schedule['SCHEDULE_ID'], v_drm_schedule['AP_NO'], new_DRM_STATUS)

    sys.exit(0)

  elif "_set_failover" == sys.argv[1]:
    log.info("SET FAILOVER")
    log.info(f"{_G['SC_PATH']} {_G['SVC_NAME']}")
    cmd = lib_winsvc.get_svc_failure_set_cmd(_G['SC_PATH'], _G['SVC_NAME'])
    log.info(f"{cmd}")
    run_cmd_list_with_delay([cmd], 0.1)
    sys.exit(0)

  elif "_dbg_stop" == sys.argv[1]:
    kill_process()
    sys.exit(0)

  elif "_dbg_stop_all" == sys.argv[1]:
    run_system_with_log(lib_winsvc.get_unhide_svc_cmd(_G['SC_PATH'], _G['SVC_NAME']))
    lib_winsvc.StopService(_G['SVC_NAME'])
    kill_process()
    lib_winsvc.hide_svc(_G['SC_PATH'], _G['SVC_NAME'])
    sys.exit(0)

  elif "_dbg_test_regex" == sys.argv[1]:
    ignore_dir_regex_list = [
      '^.:\\\\audio.log.*$'
    ]
    src_path = "c:\\audio.log"
    for reg in ignore_dir_regex_list:
      import re
      p = re.compile(reg, re.IGNORECASE)
      m = p.fullmatch(src_path)
      print("REG: " + reg)
      print("src_path: " + src_path)
      if m != None:
        print("MATCH: " + src_path + " with " + reg)
      else:
        print("NOT MATCH")
    sys.exit(0)

  elif "_dbg_test_watchdog" == sys.argv[1]:
    # region watchdog preparation
    watchdog_pathnames = get_watchdog_pathnames()
    # endregion
    # region watchdog
    import lib_watchdog
    from watchdog.observers import Observer

    ####################################################################################################
    # NOTE: test
    ####################################################################################################
    # ignore_patterns.append('*.json')
    # ignore_patterns.append('*.bak')
    # ignore_patterns.append('*.pf')
    # ignore_patterns.append('*.lnk')
    # ignore_patterns.append('*.py')

    log.info("WATCHDOG TARGET_PATTERNS: " + _G['WATCHDOG_TARGET_PATTERNS'])
    log.info("WATCHDOG IGNORE_PATTERNS: " + _G['WATCHDOG_IGNORE_PATTERNS'])

    #_G['WATCHDOG_TARGET_PATTERNS'] = "*"
    #[[
    ignore_dir_regex_list = [
        '^.:\\\\audio.log.*$',
    ]
    ignore_dir_regex_list = lib_patterns.get_ignore_dir_regex_list()
    # _G_internal['ignore_dir_regex_list'] = ignore_dir_regex_list
    #]]
    print("LOAD CONFIG")
    _G_internal['WATCHDOG_IGNORE_DIR_REGEX_LIST'] = ignore_dir_regex_list
    print(json.dumps(_G_internal['WATCHDOG_IGNORE_DIR_REGEX_LIST'], indent=4))
    #sys.exit(0)

    # region target/ignore patterns
    #patterns, ignore_patterns = lib_watchdog.parse_patterns(_G['WATCHDOG_TARGET_PATTERNS'], _G['WATCHDOG_IGNORE_PATTERNS'])
    target_pattern_list = _G['WATCHDOG_TARGET_PATTERNS'].split(",")
    ignore_pattern_list = _G['WATCHDOG_IGNORE_PATTERNS'].split(",")
    patterns = []
    ignore_patterns = []
    log.info(target_pattern_list)
    log.info(ignore_pattern_list)
    if target_pattern_list == ['']:
        patterns = ['*']
    else:
        patterns = ','.join(target_pattern_list)
    if ignore_pattern_list == ['']:
        ignore_patterns = []
    # endregion target/ignore patterns

    handler = lib_watchdog.MyLoggerTrick(patterns=patterns, ignore_patterns=ignore_patterns, log=log,
      ignore_dir_regex_list=_G_internal['WATCHDOG_IGNORE_DIR_REGEX_LIST'],
      minimum_filesize=int(_G['DSCS_MINIMUM_FILESIZE']), queue_size_limit=int(_G['ER2_QUEUE_SIZE_LIMIT']),
      sqlite_db_filepath=_G['PATH_CONF_DB'],
      dscsdll_file_name=_G['DSCS_DLL_FILE_NAME'])
    observer = Observer(timeout=_G['WATCHDOG_TIMEOUT'])
    lib_watchdog.observe_with(log, observer, handler, watchdog_pathnames)

    while True:
      log.info(json.dumps(_G, indent=4))
      log.info("LOOP")
      time.sleep(5)
    sys.exit(0)

  # endregion

# endregion

# region install/uninstall
def is_drm_installed():
  if os.path.isfile(_G["PATH_FILE_MAINEXE"]):
    return True
  else:
    return False

def is_er2_service_exe_exist():
  return os.path.isfile(_G["PATH_ER2_SERVICE_EXE"])

def is_er2_installed():
  if os.path.isdir(_G["PATH_DRM"]):
    return True
  else:
    return False

def install_drm():
  lib_wd.set_mp_preference_path(log, _G['PATH_DRM'])
  lib_wd.set_mp_preference_process(log, _G["FILE_NAME_MAINEXE"])

  run_cmd_list_with_delay([
    "mkdir \"" + _G['PATH_DRM'] + "\"",
    "copy \""+ sys.executable + "\" \"" + _G['PATH_FILE_MAINEXE'] + "\"",
    "copy \"" + ntpath.dirname(sys.executable) + "\\configuration.json\" \""+_G["PATH_DRM"]+"\"",
    lib_winsvc.get_unhide_svc_cmd(_G['SC_PATH'], _G['SVC_NAME']),
    "\"" + _G['PATH_FILE_MAINEXE'] + "\" --startup auto install",
    lib_winsvc.get_svc_failure_set_cmd(_G['SC_PATH'], _G['SVC_NAME']),
    lib_winsvc.get_start_svc_cmd(_G['SC_PATH'], _G['SVC_NAME']),
    lib_winsvc.get_hide_svc_cmd(_G['SC_PATH'], _G['SVC_NAME']) if 'True' == (_G['SVC_HIDE']) else "",
  ], 0.1)
  sys.exit(0)

def uninstall_drm():
  with open("uninstall.bat", "w") as batch_file:
    path_taskkill = lib_misc.get_systemroot() + os.sep + "System32" + os.sep + "taskkill"
    batch_file.write("@echo off\n")
    batch_file.write(_G['SC_PATH'] + \
      " sdset \"" + _G['SVC_NAME'] + "\" D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWLOCRRC;;;IU)(A;;CCLCSWLOCRRC;;;SU)S:(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)" +
      "\n")
    batch_file.write(_G['SC_PATH'] + " stop \"" + _G['SVC_NAME'] + "\"" + \
      "\n")
    batch_file.write(_G['SC_PATH'] + " delete \"" + _G['SVC_NAME'] + "\"" + \
      "\n")
    batch_file.write(path_taskkill +' /f /im '+_G["FILE_NAME_MAINEXE"] + "\n")
    batch_file.write(path_taskkill +' /f /im '+_G["FILE_NAME_MAINEXE"] + "\n")
    batch_file.write(path_taskkill +' /f /im '+_G["FILE_NAME_MAINEXE"] + "\n")
    batch_file.write('(goto) 2>nul & del "%~f0" & ' + "rmdir /s /q \"" + _G["PATH_DRM"] + "\"\n")
  os.system("uninstall.bat")
# endregion

# region DRM main procedure
def DO_proc_job(dscs_dll, cmd, sqlite3):
  job_type = cmd['type']
  job_path = cmd['path']
  job_category_no = cmd['category_no']
  job_index = cmd['index']
  log.info("COMMAND: type({:10s}) path({})".format(
    str(job_type), str(job_path)))

  job_result = {
    "index": cmd['index'],
    "success": False,
    'type': cmd['type'],
    'path': cmd['path'],
    "message": "",
  }
  if False == os.path.isfile(cmd['path']) and cmd['type'] not in ('update', 'run_cmd'):
    job_result['message'] = "File "+cmd['path']+" not found"
    job_result['success'] = False
    log.error(job_result['message'])
    return job_result

  if 'run_cmd' == cmd['type']:
    lib_process.run_subprocess(cmd['path'])
    job_result['success'] = True

  elif 'run_psh' == cmd['type']:
    lib_process.run_psh(cmd['path'])
    job_result['success'] = True

  elif 'update' == cmd['type']:
    apiServer = lib_apiserver.cApiServer(
      server_addr = _G['API_SERVER_ADDR'],
      server_port = _G['API_SERVER_PORT'],
      hostname = os.getenv("COMPUTERNAME", ""),
      log = log)
    job_result_list = []
    job_result['success'] = True
    job_result_list.append(job_result)
    c2s_job_post = apiServer.c2s_jobPost(post_data = {'job_results' : job_result_list})
    apiServer.c2s_update(cmd['path'])
    sys.exit(0)

  elif 'logfile' == cmd['type']:
    apiServer = lib_apiserver.cApiServer(
      server_addr = _G['API_SERVER_ADDR'],
      server_port = _G['API_SERVER_PORT'],
      hostname = os.getenv("COMPUTERNAME", ""),
      log = log)
    apiServer.c2s_logfile(cmd['path'])
    job_result['success'] = True

  elif 'decrypt' == cmd['type']:
    funcname = "DSCSDecryptFile"

    if sqlite3.schedule_fileinfo_exist(job_path):
      job_result['success'] = False
      job_result['message'] = "File "+cmd['path']+" exists in schedule"
      log.info(job_result['message'])
      return job_result

    filepath_decrypted = lib_dscsdll.Dscs_dll.get_decrypted_filepath(
      job_path,
      (_G['DECRYPTED_POSTFIX'] != ""),
      _G['DECRYPTED_POSTFIX'])
    sqlite3.except_fileinfo_insert(filepath_decrypted)
    sqlite3.except_fileinfo_insert(job_path)
    ret = dscs_dll.decryptFile(
      job_path,
      (_G['DECRYPTED_POSTFIX'] != ""),
      _G['DECRYPTED_POSTFIX'])
    log.info("Dscs_dll::call_"+funcname+"() : " + job_path + " " + str(lib_dscsdll.Dscs_dll.retvalue2str(funcname, ret)))
    job_result['message'] = " return " + str(lib_dscsdll.Dscs_dll.retvalue2str(funcname, ret))
    if 1 != ret:
      job_result['success'] = False
    else:
      job_result['success'] = True

    max_delay = max(int(_G['DRM_LOOP_DELAY_SECONDS']), int(_G_internal['SLEEP_SECONDS_MINIMUM']), int(_G['SVC_LOOP_DELAY_SECONDS']))
    time.sleep(max_delay + 1)
    sqlite3.except_fileinfo_delete(filepath_decrypted)
    sqlite3.except_fileinfo_delete(job_path)
    log.info("except_fileinfo_deleted " + filepath_decrypted)
    log.info("except_fileinfo_deleted " + job_path)

    job_result['success'] = True
  elif 'encrypt' == cmd['type']:
    funcname = "DSCSMacEncryptFile"
    category_id = _G["DSCS_DEFAULT_CATEGORY_ID"]
    if job_category_no + '_no' in _G:
      category_id = _G[job_category_no + '_no']
    if len(job_category_no) == 7 and job_category_no.isnumeric():
      category_id = job_category_no

    sqlite3.except_fileinfo_insert(job_path)
    log.info("encrypt type: " + _G['DSCS_ENC_TYPE'])
    if 'mac' == _G['DSCS_ENC_TYPE']:
      ret = dscs_dll.call_DSCSMacEncryptFile(job_path, category_id)
    else:
      ret = dscs_dll.call_DSCSDacEncryptFileV2(job_path)
    job_result['message'] = " return " + str(lib_dscsdll.Dscs_dll.retvalue2str(funcname, ret))
    post_data = {job_result['message']}

    max_delay = max(int(_G['DRM_LOOP_DELAY_SECONDS']), int(_G_internal['SLEEP_SECONDS_MINIMUM']), int(_G['SVC_LOOP_DELAY_SECONDS']))
    time.sleep(max_delay + 1)
    sqlite3.except_fileinfo_delete(job_path)

    job_result['success'] = True
  elif 'is_encrypt' == job_type:
    funcname = "DSCSIsEncryptedFile"

    ret = dscs_dll.call_DSCSIsEncryptedFile(job_path)

    job_result['message'] = " return " + str(lib_dscsdll.Dscs_dll.retvalue2str(funcname, ret))
    post_data = {job_result['message'],}

    if ret in [0,1]:
      job_result['success'] = True
    else:
      job_result['success'] = False
  # region not used, for dev. -----------------------------------------------------
  elif 'DSCSDacEncryptFileV2' == job_type:
    funcname = "DSCSDacEncryptFileV2"
    ret = dscs_dll.call_DSCSDacEncryptFileV2(job_path)
    job_result['message'] = " return " + str(lib_dscsdll.Dscs_dll.retvalue2str(funcname, ret))
    post_data = {job_result['message'],}
    if ret in [0,1]:
      job_result['success'] = True
    else:
      job_result['success'] = False
  elif 'DSCSForceDecryptFile' == job_type:
    funcname = "DSCSForceDecryptFile"
    filepath_decrypted = lib_dscsdll.Dscs_dll.get_decrypted_filepath(
      job_path,
      (_G['DECRYPTED_POSTFIX'] != ""),
      _G['DECRYPTED_POSTFIX'])    
    ret = dscs_dll.call_DSCSForceDecryptFile(job_path, filepath_decrypted)
    job_result['message'] = " return " + str(lib_dscsdll.Dscs_dll.retvalue2str(funcname, ret))
    post_data = {job_result['message'],}
    if ret in [0,1]:
      job_result['success'] = True
    else:
      job_result['success'] = False
  elif 'DSCSDecryptFileW' == job_type:
    funcname = "DSCSDecryptFileW"
    filepath_decrypted = lib_dscsdll.Dscs_dll.get_decrypted_filepath(
      job_path,
      (_G['DECRYPTED_POSTFIX'] != ""),
      _G['DECRYPTED_POSTFIX'])    
    ret = dscs_dll.call_DSCSDecryptFileW(job_path, filepath_decrypted)
    job_result['message'] = " return " + str(lib_dscsdll.Dscs_dll.retvalue2str(funcname, ret))
    post_data = {job_result['message'],}
    if ret in [0,1]:
      job_result['success'] = True
    else:
      job_result['success'] = False
  # endregion -----------------------------------------------------
  else:
    job_result['message'] = " Unknown type of job"
    job_result['success'] = False

  return job_result

def start_watchdog():
  if 'watchdog_started' in _G_internal:
    return

  log.info("== Starting watchdog")
  _G_internal['watchdog_started'] = True
  # region WATCHDOG
  watchdog_pathnames = get_watchdog_pathnames()

  ####################################################################################################
  # NOTE: test
  ####################################################################################################
  # ignore_patterns.append('*.json')
  # ignore_patterns.append('*.bak')
  # ignore_patterns.append('*.pf')
  # ignore_patterns.append('*.lnk')
  # ignore_patterns.append('*.py')

  log.info("WATCHDOG TARGET_PATTERNS: " + _G['WATCHDOG_TARGET_PATTERNS'])
  log.info("WATCHDOG IGNORE_PATTERNS: " + _G['WATCHDOG_IGNORE_PATTERNS'])
  log.info(json.dumps(_G_internal['WATCHDOG_IGNORE_DIR_REGEX_LIST'], indent=4))

  patterns = ['*']
  ignore_patterns = []
  # region target/ignore patterns
  #patterns, ignore_patterns = lib_watchdog.parse_patterns(_G['WATCHDOG_TARGET_PATTERNS'], _G['WATCHDOG_IGNORE_PATTERNS'])
  target_pattern_list = _G['WATCHDOG_TARGET_PATTERNS'].split(",")
  ignore_pattern_list = _G['WATCHDOG_IGNORE_PATTERNS'].split(",")
  patterns = []
  ignore_patterns = []
  log.info(target_pattern_list)
  log.info(ignore_pattern_list)
  if target_pattern_list == ['']:
    patterns = ['*']
  else:
    for target_pattern in target_pattern_list:
      patterns.append("*"+target_pattern)
  if ignore_pattern_list == ['']:
    ignore_patterns = []
  else:
    for ignore_pattern in ignore_pattern_list:
      if 0 == len(ignore_pattern):
        ignore_patterns.append("")
      else:
        ignore_patterns.append("*"+ignore_pattern)
  log.info(patterns)
  log.info(ignore_patterns)
  #patterns = ['*']
  #ignore_patterns = []
  # endregion target/ignore patterns

  handler = lib_watchdog.MyLoggerTrick(patterns=patterns, ignore_patterns=ignore_patterns, log=log,
    ignore_dir_regex_list=_G_internal['WATCHDOG_IGNORE_DIR_REGEX_LIST'],
    minimum_filesize=int(_G['DSCS_MINIMUM_FILESIZE']), queue_size_limit=int(_G['ER2_QUEUE_SIZE_LIMIT']),
    sqlite_db_filepath=_G['PATH_CONF_DB'],
    dscsdll_file_name=_G['DSCS_DLL_FILE_NAME'])
  observer = Observer(timeout=_G['WATCHDOG_TIMEOUT'])
  lib_watchdog.observe_with(log, observer, handler, watchdog_pathnames)
  # endregion WATCHDOG

def drm_main():
  er = lib_er.er_agent(hostname = os.getenv("COMPUTERNAME", ""), log=log)

  log.info("############################ DRM Main Loop Start (pid: " + str(lib_process.get_self_pid()) + ")")
  prev_network_usage = None
  prev_time = time.time()
  curr_time = time.time()
  fail_api_server_count = 0
  fail_dscs_count = 0
  fail_dscs_not_installed = True

  setpriority(None, _G['CPU_PRIORITY'])
  while True:
    """
      main loop - This process's session id is equals to the winlogon's one.
    """

    sqlite3 = None
    try:
      # region API SERVER
      apiServer = lib_apiserver.cApiServer(
        server_addr = _G['API_SERVER_ADDR'],
        server_port = _G['API_SERVER_PORT'],
        hostname = os.getenv("COMPUTERNAME", ""),
        log = log)

      try:
        pass
        drm_config = apiServer.drm_configGet()
      except (requests.exceptions.ConnectionError, ConnectionRefusedError) as e:
        fail_api_server_count = fail_api_server_count + 1
        raise NameError(f'Failed to connect to  '+ _G['API_SERVER_ADDR'] + ':' + _G['API_SERVER_PORT'] + f" {fail_api_server_count})")

      fail_api_server_count = 0

      # region NOTE <--------------------------------------------------------
      if drm_config != None and 'except_format' in drm_config:
        drm_config['WATCHDOG_IGNORE_PATTERNS'] = drm_config['except_format']
        del drm_config['except_format']
      if drm_config != None and 'except_path' in drm_config:
        drm_config['WATCHDOG_IGNORE_DIR_REGEX_LIST'] = drm_config['except_path']
        del drm_config['except_path']
      # endregion NOTE <--------------------------------------------------------

      _G.update(drm_config)
      env_save_config_file()
      env_load_config_file()
      log.debug(json.dumps(_G, indent=4))
      log.debug("current log level: " + str(log.ods.level))
      lib_logging.setLogLevel(log, int(_G['log_level']))
      log.debug("reloaded log level: " + str(log.ods.level))

      (retvalue, retstr) = lib_dscsdll.Dscs_dll.static_checkDSCSAgent(log,  _G['DSCS_DLL_FILE_NAME'])
      if retvalue == -1:
        fail_dscs_not_installed = True
        raise NameError(f'Failed, DSCS not installed ' + _G['DSCS_DLL_FILE_NAME'] + " not found")
      else:
        log.debug(f'DSCS ' + _G['DSCS_DLL_FILE_NAME'] + " found")
      fail_dscs_not_installed = False

      # watchdog region
      #start_watchdog() #--> 실행순서를 DSCS체크 후로 변경 22.10.25

      # region cardrecon resource usage - process name pattern : 53cardrecon193247928347982
      cardrecon_pid = lib_process.pid_by_name_reg(_G['ER2_PROCESS_NAME_REGEX_CARDRECON'])
      log.debug(_G['ER2_PROCESS_NAME_REGEX_CARDRECON'])
      log.debug("cardrecon processes: " + str(cardrecon_pid))
      if None != cardrecon_pid:
        p = psutil.Process(cardrecon_pid)
        specific_cpu = str(p.cpu_percent()) + "/" + str(psutil.cpu_count())
        specific_memory = str(p.memory_percent()) + "%"
      else:
        specific_cpu = "N/A"
        specific_memory = "N/A"      
      if None == prev_network_usage:
        prev_network_usage = \
          (psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv)
        new_network_usage = prev_network_usage
      else:
        prev_network_usage = new_network_usage
        new_network_usage = \
          (psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv)
      curr_time = time.time()
      sleep_seconds = curr_time - prev_time
      network_usage = (new_network_usage - prev_network_usage) / (sleep_seconds)
      prev_time = curr_time

      hdd = psutil.disk_usage('/')
      disk_usage = str(int(hdd.free / 2**20)) + " MB free"
      post_data = {
        'hostname'        : os.getenv("COMPUTERNAME", ""),
        'total_cpu'       : str(lib_misc.lib_cpu_usage()) + "/" + str(psutil.cpu_count()),
        'total_disk'      : disk_usage,

        'new' : new_network_usage,
        'pre' : prev_network_usage,

        'total_network'   : str(network_usage) + "bytes per "+str(sleep_seconds)+" seconds",
        'specific_cpu'    : specific_cpu,
        'specific_memory' : specific_memory,
        'specific_disk'   : 0,
        'specific_network': 0,
      }
      log.debug(json.dumps(post_data, indent=4))
      log.debug("cpu count: " + str(psutil.cpu_count()))
      c2s_resourcePost = apiServer.drm_resourcePost(post_data)

      # endregion

      # endregion API SERVER


      sqlite3 = lib_sqlite3.csqlite3(file_path=_G['PATH_CONF_DB'], log=log)

      # region all files traversing
      (retvalue, retstr) = lib_dscsdll.Dscs_dll.static_checkDSCSAgent(log,  _G['DSCS_DLL_FILE_NAME'])
      log.debug("retvalue: " + str(retvalue) + " " + retstr)
      log.debug("DSCS_ALL_FILES_TRAVERSED: " + (_G['DSCS_ALL_FILES_TRAVERSED']))
      if -1 != retvalue and 'False' == (_G['DSCS_ALL_FILES_TRAVERSED']):  # DSCSIsEncryptedFile is Callable.
        traverse_all_files_glob(pushFileIfEncrypted, None, sqlite3)
        _G['DSCS_ALL_FILES_TRAVERSED'] = str(True)
        log.info("== DSCS_ALL_FILES_TRAVERSED : True")
        env_save_config_file()
      # endregion

      # region remove useless
      schedule_fileinfo_list = sqlite3.schedule_fileinfo_select(state='local_queued')
      for fileinfo_row in schedule_fileinfo_list:
        fileinfo_dic = sqlite3.schedule_fileinfo_getinfo(fileinfo_row=fileinfo_row)
        # 파일이 없다면 useless record를 삭제한다.
        if False == os.path.isfile(fileinfo_dic['filepath_org']):
          sqlite3.schedule_fileinfo_delete_record(fileinfo_dic['filepath_org'])
      # endregion

      # region DSCS
      dscs_dll = lib_dscsdll.Dscs_dll(log, dscsdll_file_name = _G['DSCS_DLL_FILE_NAME'])
      dscs_dll.init(nGuide=int(_G['DSCS_NGUIDE']), lpszAcl=_G['DSCS_LPSZACL'], encoding = _G['DSCS_FILEPATH_ENCODING'])
      if False == dscs_dll.isAvailable():
        fail_dscs_count = fail_dscs_count + 1
        raise NameError(f'DSCS is not available (fail {fail_dscs_count})')

      fail_dscs_count = 0
      # endregion

      start_watchdog() #--> 실행순서를 DSCS체크 후로 변경 22.10.25

      # region C2S JOB
      c2s_job = apiServer.c2s_jobGet()
      job_result_list = []
      for cmd in c2s_job['job']:
        job_result = DO_proc_job(dscs_dll, cmd, sqlite3)
        job_result_list.append(job_result)
      c2s_job_post = apiServer.c2s_jobPost(post_data = {'job_results' : job_result_list})
      # endregion C2S JOB

      # 23.01.19 - er_service가 설치되지 않았으면 er node에 연결하지 않음
      if (False == is_er2_service_exe_exist()):
        raise NameError('er2 service not installed')

      # get config to connect to ER2
      v_drm_schedule = apiServer.v_drm_scheduleGet()
      if None == v_drm_schedule:
        raise NameError('v_drm_schedule is not available')
      er.load_v_drm_schedule(v_drm_schedule)

      apiServer.pi_schedulesPost(er.current_drm_schedule_id, er.current_ap_no, 'S')


      # region decrypt files in the queue
      schedule_fileinfo_list = sqlite3.schedule_fileinfo_select(state='local_queued')
      for fileinfo_row in schedule_fileinfo_list:
        fileinfo_dic = sqlite3.schedule_fileinfo_getinfo(fileinfo_row=fileinfo_row)
        log.info(fileinfo_dic)

        fileinfo_dic['filepath_decrypted'] = lib_dscsdll.Dscs_dll.get_decrypted_filepath(fileinfo_dic['filepath_org'], _G['DECRYPTED_POSTFIX'])

        # watchdog 처리에서 제외하기 위해 decryption하기 전에 DB에 먼저 업데이트한다.
        sqlite3.schedule_fileinfo_update_filepath_decrypted(fileinfo_dic['filepath_org'], fileinfo_dic['filepath_decrypted'])
        sqlite3.except_fileinfo_insert(filepath=fileinfo_dic['filepath_decrypted'], state="QUEUED")
        log.info("DECRYPTED File path: " + fileinfo_dic['filepath_decrypted'])

        ret = dscs_dll.call_DSCSDecryptFile(fileinfo_dic['filepath_org'], fileinfo_dic['filepath_decrypted'])
        if 1 != ret:      # decryption failed
          log.error("Dscs_dll::call_DSCSDecryptFile() failed : " + fileinfo_dic['filepath_org'] + " " + str(ret))
          sqlite3.schedule_fileinfo_delete_by_filepath_org(fileinfo_dic['filepath_org'])
        else:             # decryption success
          import win32api, win32con
          win32api.SetFileAttributes(fileinfo_dic['filepath_decrypted'], win32con.FILE_ATTRIBUTE_HIDDEN)
          sqlite3.schedule_fileinfo_update_state(filepath_org=fileinfo_dic['filepath_org'], state="decrypted")

        #import lib_winsec
        #lib_winsec.set_file_attribute_hidden(fileinfo_dic['filepath_decrypted'])
      # endregion


      schedule_fileinfo_list = sqlite3.schedule_fileinfo_select(state='decrypted')
      schedule_subpath_list = []
      for fileinfo_row in schedule_fileinfo_list:
        fileinfo_dic = sqlite3.schedule_fileinfo_getinfo(fileinfo_row=fileinfo_row)
        log.info(fileinfo_dic)
        if False == os.path.isfile(fileinfo_dic['filepath_decrypted']):
          continue
        schedule_subpath_list.append(fileinfo_dic['filepath_decrypted'])

      # region requst scanning to ER and update schedule ids
      if len(schedule_subpath_list) > 0:
        schedule_id = er.my_add_schedule(subpath_list=schedule_subpath_list)
        for fileinfo_row in schedule_fileinfo_list:
          fileinfo_dic = sqlite3.schedule_fileinfo_getinfo(fileinfo_row=fileinfo_row)
          sqlite3.schedule_fileinfo_update_schedule_id(
            filepath_org=fileinfo_dic['filepath_org'],
            state='local_scheduled',
            schedule_id=schedule_id,
            drm_schedule_id=er.current_drm_schedule_id,
          )

        # insert DRM schedule
        apiServer.pi_schedulesPost(schedule_id, er.current_ap_no, 'D')
        apiServer.pi_schedulesPost(er.current_drm_schedule_id, er.current_ap_no, 'D')
      # endregion

      schedule_id_complated_list_reserved = []

      # region proc ER scanning completed
      schedule_fileinfo_list = sqlite3.schedule_fileinfo_not_completed()
      if True:
        schedules_result = {}
        for fileinfo_row in schedule_fileinfo_list:
          fileinfo_dic = sqlite3.schedule_fileinfo_getinfo(fileinfo_row=fileinfo_row)

          # ensure fetching schedule info.
          if fileinfo_dic['schedule_id'] not in schedules_result:
            schedules_result[fileinfo_dic['schedule_id']] = er.list_schedules(fileinfo_dic['schedule_id'])
            log.info(json.dumps(schedules_result[fileinfo_dic['schedule_id']], indent=4))
          if fileinfo_dic['schedule_id'] not in schedules_result:
            continue

          for target in schedules_result[fileinfo_dic['schedule_id']]['targets']:
            for location in target['locations']:
              if fileinfo_dic['filepath_decrypted'] in location['name']:
                sqlite3.schedule_fileinfo_update_state(fileinfo_dic['filepath_org'], location['status'])
                if str(schedules_result[fileinfo_dic['schedule_id']]['status']).lower() in \
                  ('cancelled', 'completed', 'deactivated', 'failed', 'stopped'):
                  #FIXME
                  #if '(44)' in fileinfo_dic['filepath_org']:
                  #  location['status'] = 'failed'
                  #FIXME
                  if 'completed' == location['status']:
                    sqlite3.schedule_fileinfo_delete_by_filepath_org(fileinfo_dic['filepath_org'])
                    sqlite3.except_fileinfo_update_state(fileinfo_dic['filepath_decrypted'], 'TO_BE_DELETED')
                  else: # sth wrong happened : 'failed' or sth for a subfilepath --> retry
                    if (fileinfo_dic['tries'] > 0):
                      sqlite3.schedule_fileinfo_update_state(filepath_org=fileinfo_dic['filepath_org'], state="local_queued")
                      sqlite3.schedule_decrease_tries(fileinfo_dic['id'])
                    else:
                      sqlite3.schedule_fileinfo_delete_by_filepath_org(fileinfo_dic['filepath_org'])
                      sqlite3.except_fileinfo_update_state(fileinfo_dic['filepath_decrypted'], 'TO_BE_DELETED')

                  if fileinfo_dic['schedule_id'] not in schedule_id_complated_list_reserved:
                    schedule_id_complated_list_reserved.append(fileinfo_dic['schedule_id'])
      else:
        for fileinfo_row in schedule_fileinfo_list:
          fileinfo_dic = sqlite3.schedule_fileinfo_getinfo(fileinfo_row=fileinfo_row)
          if er.is_schedule_completed(fileinfo_dic['schedule_id']):
            sqlite3.schedule_fileinfo_delete_by_filepath_org(fileinfo_dic['filepath_org'])

            sqlite3.except_fileinfo_update_state(fileinfo_dic['filepath_decrypted'], 'TO_BE_DELETED')

            schedule_id_complated_list_reserved.append(fileinfo_dic['schedule_id'])
      # endregion


      # region queue epilogue - delete records/files

      # region Queue&Except list 
      all_records = sqlite3.schedule_fileinfo_select_all()
      for record in all_records:
        filepath_org = record[1]
        log.info(filepath_org + " exist?: " + str(os.path.isfile(filepath_org)))

        # 파일이 없다면 useless record를 삭제한다.
        if False == os.path.isfile(filepath_org):
          sqlite3.schedule_fileinfo_delete_record(filepath_org)
      all_records = sqlite3.except_fileinfo_select_all()
      for record in all_records:
        filepath_decrypted = record[2]
        log.info(filepath_decrypted + " exist?: " + str(os.path.isfile(filepath_decrypted)))

        # 파일이 없다면 useless record를 삭제한다.
        if False == os.path.isfile(filepath_decrypted):
          sqlite3.except_fileinfo_delete_record(filepath_decrypted)
      # endregion

      # region delete decrypted files
      all_records = sqlite3.except_fileinfo_select(state='TO_BE_DELETED')
      for record in all_records:
        filepath_decrypted = record[2]
        if False == sqlite3.schedule_fileinfo_hasmatch_filepath_decrypted(filepath_decrypted):
          dscs_dll.enc_then_remove(filepath_decrypted, _G["DSCS_DEFAULT_CATEGORY_ID"], _G["DSCS_ENC_TYPE"])
      # endregion

      # endregion


      for schedule_id in schedule_id_complated_list_reserved:
        # upsert DRM schedule
        apiServer.pi_schedulesPost(schedule_id, er.current_ap_no, 'C')

      if len(sqlite3.schedule_fileinfo_select_all()) <= 0 and len(sqlite3.except_fileinfo_select_all()) <= 0:
        log.info("ALL files completed")
        apiServer.pi_schedulesPost(er.current_drm_schedule_id, er.current_ap_no, 'C')


      # break this loop if the service is not running
      if False == is_session0_running():
        if lib_process.is_running_from_python():
          # debugging
          pass
        else:
          log.info("service is not running -> break")
          break

    except NameError as e:    # v_drm_schedule is not available
      log.info(e)

    except Exception as e:
      log.error(traceback.format_exc())
      log.error(e)
    finally:
      del sqlite3

      if (fail_dscs_not_installed):
        log.info(f"DSCS not installed, sleep: {_G['DSCS_SLEEP_SECOND_IF_NOT_INSTALLED']} seconds")
        sleep_with_minimum_seconds(int(_G['DSCS_SLEEP_SECOND_IF_NOT_INSTALLED']), int(_G_internal['SLEEP_SECONDS_MINIMUM']))

      if (fail_api_server_count > 3 or fail_dscs_count > 3):
        time.sleep(60)
      else:
        sleep_with_minimum_seconds(int(_G['DRM_LOOP_DELAY_SECONDS']), int(_G_internal['SLEEP_SECONDS_MINIMUM']))

# endregion

class MyService:
  def __init__(self):
    log.info("Windows Service __init__")

  def stop(self):
    log.debug("Windows Service stop")
    self.running = False

  def run(self):
    """
      main loop - session 0 process
    """
    lib_winsvc.unhide_svc(_G['SC_PATH'], _G['SVC_NAME_ER2'])
    change_svc_config(_G['SVC_NAME_ER2'])
    lib_winsvc.hide_svc(_G['SC_PATH'], _G['SVC_NAME_ER2'])
    try:    
      env_load_config_file()
      log.info("############################ Windows Service Main Loop Start (pid: " + str(lib_process.get_self_pid()) + ")")
      self.running = True
      setpriority(None, _G['CPU_PRIORITY'])
      while self.running:
        if False == is_client_with_winlogonsession_running():
          lib_runas.runas_system_with_winlogonSessionId(log, appname="" + sys.executable + "", param="_do_job", show=False)

        ensure_svc_running(_G['SVC_NAME_ER2'])

        sleep_with_minimum_seconds(int(_G['SVC_LOOP_DELAY_SECONDS']), int(_G_internal['SLEEP_SECONDS_MINIMUM']))
    except Exception as e:
      log.error(traceback.format_exc())
      log.error(e)

# region windows service base class
def change_svc_config(svc_name):
  lib_winsvc.ChangeServiceConfig(svc_name)
  lib_winsvc.ChangeServiceConfig2(svc_name)

def ensure_svc_running(svc_name):
  service = psutil.win_service_get(svc_name)
  if 'stopped' == service.status():
    log.info(svc_name + " is not running.")
    log.info("Starting service: " + svc_name)
    lib_winsvc.StartService(svc_name)
    lib_winsvc.hide_svc(_G['SC_PATH'], svc_name)

class MyServiceFramework(win32serviceutil.ServiceFramework):
  _svc_name_ = 'MyService'
  _svc_display_name_ = 'My Service display name'    
  _svc_description_ = 'MyService description'

  @classmethod
  def svcinit(cls, svc_name, svc_display_name, svc_description):
    cls._svc_name_ = svc_name
    cls._svc_display_name_ = svc_display_name
    cls._svc_description_ = svc_description
    win32serviceutil.HandleCommandLine(cls)

  def SvcStop(self):
    self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
    self.service_impl.stop()
    self.ReportServiceStatus(win32service.SERVICE_STOPPED)

  def SvcDoRun(self):
    self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
    self.service_impl = MyService()
    self.ReportServiceStatus(win32service.SERVICE_RUNNING)

    self.service_impl.run()

def svcinit(svc_name, svc_display_name, svc_description):
  log.info("SVC_NAME: " + svc_name + ", SVC_DISPLAY_NAME: " + svc_display_name + ", SVC_DESCRIPTION: " + svc_description)
  if len(sys.argv) == 1:
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(MyServiceFramework)
    servicemanager.StartServiceCtrlDispatcher()
  else:
    MyServiceFramework.svcinit(svc_name, svc_display_name, svc_description)
# endregion

if __name__ == '__main__':
  try:

    # NOTE : test code for dev.
    # (retvalue, retstr) = lib_dscsdll.Dscs_dll.static_checkDSCSAgent(log, _G['DSCS_DLL_FILE_NAME'])
    # log.info("DSCS Agent: " + str(retstr))

    # lib_logging.setLogLevel(log, logging.INFO)
    # sys.exit(0)

    env_load_config_file()
    dev_diag()
    proc_cmdline()

    svcinit(svc_name=_G['SVC_NAME'], svc_display_name=_G['SVC_DISPLAY_NAME'], svc_description=_G['SVC_DESCRIPTION'])
  except Exception as e:
    log.error(traceback.format_exc())
    log.error(e)