import win32ts, win32con, win32api, win32security, win32process, win32profile

def _lib_find_procs_by_name(name):
  import psutil
  "Return a list of processes matching 'name'."
  ls = []
  for p in psutil.process_iter(['name']):
    if p.info['name'] == name:
      ls.append(p)
  return ls

def get_winlogon_sessionId():
  session_id = None
  proc_list = _lib_find_procs_by_name("winlogon.exe")
  for p in proc_list:
    session_id = win32ts.ProcessIdToSessionId(p.pid)
  return session_id

def get_winlogon_pid():
  pid_winlogon = None
  proc_list = _lib_find_procs_by_name("winlogon.exe")
  for p in proc_list:
    pid_winlogon = p.pid
  return pid_winlogon

def runas_system_with_winlogonSessionId(log, appname, param = None, show = False):
  pid_winlogon = get_winlogon_pid()
  if None == pid_winlogon:
    return

  log.info("pid_winlogon: " + str(pid_winlogon))
  hProcess = win32api.OpenProcess(win32con.MAXIMUM_ALLOWED, False, pid_winlogon)

  th = win32security.OpenProcessToken(hProcess,
    win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY |
    win32con.TOKEN_DUPLICATE | win32con.TOKEN_ASSIGN_PRIMARY | #win32con.TOKEN_ADJUST_SESSIONID |
    win32con.TOKEN_READ | win32con.TOKEN_WRITE)

  duplicated = win32security.DuplicateTokenEx(th,
    3,
    win32con.MAXIMUM_ALLOWED, 
    win32security.TokenPrimary)        

  StartInfo = win32process.STARTUPINFO()
  StartInfo.wShowWindow = win32con.SW_HIDE
  StartInfo.lpDesktop = "winsta0\\default"
  creationFlag = win32con.CREATE_UNICODE_ENVIRONMENT | win32con.CREATE_NO_WINDOW # win32con.NORMAL_PRIORITY_CLASS

  if show:
      creationFlag = win32con.CREATE_UNICODE_ENVIRONMENT | win32con.CREATE_NEW_CONSOLE # win32con.NORMAL_PRIORITY_CLASS
      StartInfo.wShowWindow = win32con.SW_SHOW

  environment = win32profile.CreateEnvironmentBlock(duplicated, False)

  if None != param:
      param = appname + " " + param
      appname = None

  handle, thread_id ,pid, tid = win32process.CreateProcessAsUser(duplicated,
      appname,
      param,
      None, 
      None,
      False,
      creationFlag,
      environment,
      None,
      StartInfo)

def runas_system(appname, param):
  pass