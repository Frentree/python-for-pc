import os

# region internal functions
def log_and_run(log, cmd):
  log.info(cmd)
  os.system(cmd)
# endregion

def set_mp_preference_path(log, install_path):
  cmd = "powershell -Command Add-MpPreference -ExclusionPath '" + install_path + "'"
  log_and_run(log, cmd)

def set_mp_preference_process(log, exe_filename):
  cmd = "powershell -Command Add-MpPreference -ExclusionProcess '" + exe_filename + "'"
  log_and_run(log, cmd)

# region unit test
if '__main__' == __name__:
  print("lib wd")

  exe_filename = "ShareX.exe"
  cmd = "powershell -Command Add-MpPreference -ExclusionProcess '" + exe_filename + "'"
  print(cmd)
  os.system(cmd)

  #os.system("powershell -Command Add-MpPreference -ExclusionPath 'C:\\Program Files (x86)\\VMware\\VMware Workstation\\vmware.exe'")
  #os.system("powershell -Command Add-MpPreference -ExclusionPath 'C:\\Program Files (x86)\\VMware\\VMware Workstation'")
  #os.system("powershell -Command Add-MpPreference -ExclusionPath 'C:\\Users\\Admin\\Downloads\\mimikatz-master\\mimikatz-master\\x64'")
# endregion