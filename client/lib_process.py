import os, sys
import psutil
import subprocess

def run_subprocess(exename):
  subprocess.Popen(exename, shell=True)

def get_self_pid():
  return os.getpid()

def lib_get_pid_list_by_name(process_name):
  pid_list = []
  for process in psutil.process_iter():
    if process_name.lower() == process.name().lower():
      pid_list.append(process.pid)

  return pid_list

def pid_by_name_reg(regex):
    import re
    for process in psutil.process_iter():
        p = re.compile(regex, re.IGNORECASE)
        m = p.match(process.name())
        if m:
            return process.pid
        else:
            pass

    return None

def is_service_process(pid):
  import win32ts
  session_id = win32ts.ProcessIdToSessionId(pid)
  if 1 == session_id:
    return False
  else:
    return True

def is_running_from_python():
  # python main.py 형태로 실행하면 sys.executable이 'python.exe'이다.
  if 'python.exe' == os.path.basename(sys.executable).lower():
    return True
  else:
    return False
