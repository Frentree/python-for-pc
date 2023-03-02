import os
import win32service
import win32api, winerror

def get_svc_failure_set_cmd(sc_path, svc_name):
  delay = 60000
  cmd = f"{sc_path} failure \"{svc_name}\" reset= 0 actions= restart/{delay}/restart/{delay}/restart/{delay}"
  return cmd

def get_start_svc_cmd(sc_path, svc_name):
  cmd = "" + sc_path + "" + " start \"" + svc_name + "\""
  return cmd

def get_stop_svc_cmd(sc_path, svc_name):
  cmd = "" + sc_path + "" + " stop \"" + svc_name + "\""
  return cmd

def get_unhide_svc_cmd(sc_path, svc_name):
  cmd = sc_path + ' sdset ' + "\"" + svc_name + "\" " + \
    'D:' + \
    '(A;;CCLCSWRPWPDTLOCRRC;;;SY)' + \
    '(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)' + \
    '(A;;CCLCSWLOCRRC;;;IU)' + \
    '(A;;CCLCSWLOCRRC;;;SU)' + \
    'S:' + \
    '(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)'
  return cmd

# service가 hide된 상태에서는 sc start 또는 sc stop 명령어가 정상동작하지 않는다.
def get_hide_svc_cmd(sc_path, svc_name):
  cmd = sc_path + ' sdset ' + "\"" + svc_name + "\" " + \
    'D:' + \
    '(D;;DCLCWPDTSD;;;IU)' + \
    '(D;;DCLCWPDTSD;;;SU)' + \
    '(D;;DCLCWPDTSD;;;BA)' + \
    '(A;;CCLCSWLOCRRC;;;IU)' + \
    '(A;;CCLCSWLOCRRC;;;SU)' + \
    '(A;;CCLCSWRPWPDTLOCRRC;;;SY)' + \
    '(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)' + \
    'S:' + \
    '(AU;FA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;WD)'
  return cmd

def unhide_svc(sc_path, svc_name):
  os.system(get_unhide_svc_cmd(sc_path, svc_name))

def hide_svc(sc_path, svc_name):
  os.system(get_hide_svc_cmd(sc_path, svc_name))

# Open a service given either it's long or short name.
def SmartOpenService(hscm, name, access):
  try:
    return win32service.OpenService(hscm, name, access)
  except win32api.error as details:
    if details.winerror not in [winerror.ERROR_SERVICE_DOES_NOT_EXIST,
                                winerror.ERROR_INVALID_NAME]:
      raise
  name = win32service.GetServiceKeyName(hscm, name)
  return win32service.OpenService(hscm, name, access)

def StartService(serviceName, args = None, machine = None):
  hscm = win32service.OpenSCManager(machine,None,win32service.SC_MANAGER_ALL_ACCESS)
  try:
    hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
    try:
      win32service.StartService(hs, args)
    finally:
      win32service.CloseServiceHandle(hs)
  finally:
    win32service.CloseServiceHandle(hscm)

def ChangeServiceConfig(serviceName, machine = None):
  hscm = win32service.OpenSCManager(machine,None,win32service.SC_MANAGER_ALL_ACCESS)
  try:
    hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
    try:
      startType = win32service.SERVICE_AUTO_START
      win32service.ChangeServiceConfig(hs, win32service.SERVICE_NO_CHANGE,startType,win32service.SERVICE_NO_CHANGE,None, None, 0, None, None, None, None)
    except (win32service.error, NotImplementedError):
      raise NameError("ChangeServiceConfig2 failed to set restart behavior")
    finally:
      win32service.CloseServiceHandle(hs)    
  finally:
    win32service.CloseServiceHandle(hscm)

# https://mail.python.org/pipermail/python-win32/2017-January/013807.html
def ChangeServiceConfig2(serviceName, machine = None):
  hscm = win32service.OpenSCManager(machine,None,win32service.SC_MANAGER_ALL_ACCESS)
  try:
    hs = SmartOpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
    try:
      win32service.ChangeServiceConfig2(hs, win32service.SERVICE_CONFIG_FAILURE_ACTIONS_FLAG, True)

      service_failure_actions = {
        'ResetPeriod': 60*60,       # Time in seconds after which to reset the failure count to zero.
        'RebootMsg': u'',           # Not using reboot option
        'Command': u'',             # Not using run-command option
        'Actions': [
          (win32service.SC_ACTION_RESTART, 1000*5),   # first action after failure, delay in ms
          (win32service.SC_ACTION_RESTART, 1000*5),   # second action after failure
          (win32service.SC_ACTION_NONE, 1000*5)            # subsequent actions after failure
        ]
      }
      win32service.ChangeServiceConfig2(hs, win32service.SERVICE_CONFIG_FAILURE_ACTIONS, service_failure_actions)
    except (win32service.error, NotImplementedError):
      raise NameError("ChangeServiceConfig2 failed to set restart behavior")
    finally:
      win32service.CloseServiceHandle(hs)    
  finally:
    win32service.CloseServiceHandle(hscm)

def __StopServiceWithTimeout(hs, waitSecs = 30):
  import pywintypes
  try:
    status = win32service.ControlService(hs, win32service.SERVICE_CONTROL_STOP)
  except pywintypes.error as exc:
    if exc.winerror!=winerror.ERROR_SERVICE_NOT_ACTIVE:
      raise
  for i in range(waitSecs):
    status = win32service.QueryServiceStatus(hs)
    if status[1] == win32service.SERVICE_STOPPED:
      break
    win32api.Sleep(1000)
  else:
    raise pywintypes.error(winerror.ERROR_SERVICE_REQUEST_TIMEOUT, "ControlService", win32api.FormatMessage(winerror.ERROR_SERVICE_REQUEST_TIMEOUT)[:-2])

def StopService(serviceName, machine = None, waitSecs = 30):
  hscm = win32service.OpenSCManager(machine,None,win32service.SC_MANAGER_ALL_ACCESS)
  try:
    hs = win32service.OpenService(hscm, serviceName, win32service.SERVICE_ALL_ACCESS)
    try:
      __StopServiceWithTimeout(hs, waitSecs)
    finally:
      win32service.CloseServiceHandle(hs)

  finally:
    win32service.CloseServiceHandle(hscm) 