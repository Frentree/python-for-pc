import os
import psutil

# region byte numbers
def get_bytes_number_one_kilo():
  return 2**10

def get_bytes_number_one_mega():
  return 2**10 * get_bytes_number_one_kilo()

def get_bytes_number_one_giga():
  return 2**10 * get_bytes_number_one_mega()
# endregion

def get_systemdrive():
  ret = os.getenv('SystemDrive')
  return ret

def get_systemroot():
  ret = os.getenv('SystemRoot')
  return ret

def is_os_64bit():
  import platform
  return platform.machine().endswith('64')

def lib_cpu_usage():
    return str(psutil.cpu_percent())