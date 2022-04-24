import win32security
import win32api
import win32con
import ctypes
import ctypes
import logging
import os
import platform
import re
import string
import subprocess
import sys
 
class cwinsecurity:
  token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY_SOURCE | win32security.TOKEN_QUERY)
  privs = win32security.GetTokenInformation(token, win32security.TokenPrivileges)

  _WIN32_CLIENT_NAMES = {
      '5.0': '2000',
      '5.1': 'XP',
      '5.2': 'XP',
      '6.0': 'Vista',
      '6.1': '7',
      '6.2': '8',
      '6.3': '8.1',
      '10.0': '10',
  }
  _WIN32_SERVER_NAMES = {
      '5.2': '2003Server',
      '6.0': '2008Server',
      '6.1': '2008ServerR2',
      '6.2': '2012Server',
      '6.3': '2012ServerR2',
  }

  def __init__(self):
    pass

  def get_token_privileges(self):
    for i in range(len(self.privs)):
        # name of privilege
        name = win32security.LookupPrivilegeName(None, self.privs[i][0])
        flag = self.privs[i][1]

        # check the flag value
        if flag == 0:
            flag = 'Disabled'
        elif flag == 3:
            flag = 'Enabled'

        print(name, flag)

  @staticmethod
  def get_hostname():
    return os.getenv("COMPUTERNAME", "")

  @staticmethod
  def set_file_attribute_hidden(filepath):
    win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_HIDDEN)

  @staticmethod
  def get_os_version_number():
    """Returns the normalized OS version number as a string.
  
    Returns:
      - '5.1', '6.1', '10.0', etc. There is no way to distinguish between Windows
        7 and Windows Server 2008R2 since they both report 6.1.
    """
    return cwinsecurity._get_os_numbers()[0]

  @staticmethod
  def _get_os_numbers():
    """Returns the normalized OS version and build numbers as strings.
  
    Actively work around AppCompat version lie shim.
  
    Returns:
      - 5.1, 6.1, etc. There is no way to distinguish between Windows 7
        and Windows Server 2008R2 since they both report 6.1.
    """
    # Windows is lying to us until python adds to its manifest:
    #   <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
    # and it doesn't.
    # So ask nicely to cmd.exe instead, which will always happily report the right
    # version. Here's some sample output:
    # - XP: Microsoft Windows XP [Version 5.1.2600]
    # - Win10: Microsoft Windows [Version 10.0.10240]
    # - Win7 or Win2K8R2: Microsoft Windows [Version 6.1.7601]
    import subprocess
    import re
    out = subprocess.check_output(['cmd.exe', '/c', 'ver']).strip()
    #match = re.search(rb'\[Version (\d+\.\d+)\.(\d+)\]', out, re.IGNORECASE)
    match = re.search(rb'\[Version (\d+\.\d+)\.(\d+\.\d+)]', out, re.IGNORECASE)
    return match.group(1), match.group(2)

  @staticmethod
  def get_integrity_level(log = None):
    """Returns the integrity level of the current process as a string.
  
    TODO(maruel): It'd be nice to make it work on cygwin. The problem is that
    ctypes.windll is unaccessible and it is not known to the author how to use
    stdcall convention through ctypes.cdll.
    """
    #if None != log: log.error(cwinsecurity.get_os_version_number())
    #print(cwinsecurity.get_os_version_number())
    #if cwinsecurity.get_os_version_number() == u'5.1':
    #  # Integrity level is Vista+.
    #  return None

    mapping = {
        0x0000: u'untrusted',
        0x1000: u'low',
        0x2000: u'medium',
        0x2100: u'medium high',
        0x3000: u'high',
        0x4000: u'system',
        0x5000: u'protected process',
    }

    # This was specifically written this way to work on cygwin except for the
    # windll part. If someone can come up with a way to do stdcall on cygwin, that
    # would be appreciated.
    BOOL = ctypes.c_long
    DWORD = ctypes.c_ulong
    HANDLE = ctypes.c_void_p


    TOKEN_READ = DWORD(0x20008)
    # Use the same casing as in the C declaration:
    # https://msdn.microsoft.com/library/windows/desktop/aa379626.aspx
    TokenIntegrityLevel = ctypes.c_int(25)
    ERROR_INSUFFICIENT_BUFFER = 122

    class SID_AND_ATTRIBUTES(ctypes.Structure):
      _fields_ = [
          ('Sid', ctypes.c_void_p),
          ('Attributes', DWORD),
    ]
    class TOKEN_MANDATORY_LABEL(ctypes.Structure):
        _fields_ = [
          ('Label', SID_AND_ATTRIBUTES),
    ]
        
    # All the functions used locally. First open the process' token, then query
    # the SID to know its integrity level.
    ctypes.windll.kernel32.GetLastError.argtypes = ()
    ctypes.windll.kernel32.GetLastError.restype = DWORD
    ctypes.windll.kernel32.GetCurrentProcess.argtypes = ()
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    ctypes.windll.advapi32.OpenProcessToken.argtypes = (HANDLE, DWORD, ctypes.POINTER(HANDLE))
    ctypes.windll.advapi32.OpenProcessToken.restype = BOOL
    ctypes.windll.advapi32.GetTokenInformation.argtypes = (HANDLE, ctypes.c_long, ctypes.c_void_p, DWORD, ctypes.POINTER(DWORD))
    ctypes.windll.advapi32.GetTokenInformation.restype = BOOL
    ctypes.windll.advapi32.GetSidSubAuthorityCount.argtypes = [ctypes.c_void_p]
    ctypes.windll.advapi32.GetSidSubAuthorityCount.restype = ctypes.POINTER(ctypes.c_ubyte)
    ctypes.windll.advapi32.GetSidSubAuthority.argtypes = (ctypes.c_void_p, DWORD)
    ctypes.windll.advapi32.GetSidSubAuthority.restype = ctypes.POINTER(DWORD)

    # First open the current process token, query it, then close everything.
    token = ctypes.c_void_p()
    proc_handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.advapi32.OpenProcessToken(
            proc_handle,
            TOKEN_READ,
            ctypes.byref(token)):
      logging.error('Failed to get process\' token')
      return None
    if token.value == 0:
      logging.error('Got a NULL token')
      return None
    try:
      # The size of the structure is dynamic because the TOKEN_MANDATORY_LABEL
      # used will have the SID appened right after the TOKEN_MANDATORY_LABEL in
      # the heap allocated memory block, with .Label.Sid pointing to it.
      info_size = DWORD()
      if ctypes.windll.advapi32.GetTokenInformation(
              token,
              TokenIntegrityLevel,
              ctypes.c_void_p(),
              info_size,
              ctypes.byref(info_size)):
        logging.error('GetTokenInformation() failed expectation')
        return None
      if info_size.value == 0:
        logging.error('GetTokenInformation() returned size 0')
        return None
      if ctypes.windll.kernel32.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
        logging.error(
            'GetTokenInformation(): Unknown error: %d',
            ctypes.windll.kernel32.GetLastError())
        return None
      token_info = TOKEN_MANDATORY_LABEL()
      ctypes.resize(token_info, info_size.value)
      if not ctypes.windll.advapi32.GetTokenInformation(
              token,
              TokenIntegrityLevel,
              ctypes.byref(token_info),
              info_size,
              ctypes.byref(info_size)):
        logging.error(
            'GetTokenInformation(): Unknown error with buffer size %d: %d',
            info_size.value,
            ctypes.windll.kernel32.GetLastError())
        return None
      p_sid_size = ctypes.windll.advapi32.GetSidSubAuthorityCount(
          token_info.Label.Sid)
      res = ctypes.windll.advapi32.GetSidSubAuthority(
          token_info.Label.Sid, p_sid_size.contents.value - 1)
      value = res.contents.value
      return mapping.get(value) or u'0x%04x' % value
    finally:
      ctypes.windll.kernel32.CloseHandle(token)

  @staticmethod
  def get_windir_driveletter_with_colon():
    windir = os.getenv('WINDIR')
    return os.path.splitdrive(windir)[0]

  @staticmethod
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

  @staticmethod
  def _get_mount_points():
    """Returns the list of 'fixed' drives in format 'X:\\'."""
    ctypes.windll.kernel32.GetDriveTypeW.argtypes = (ctypes.c_wchar_p,)
    ctypes.windll.kernel32.GetDriveTypeW.restype = ctypes.c_ulong
    DRIVE_FIXED = 3
    # https://msdn.microsoft.com/library/windows/desktop/aa364939.aspx
    return [
      u'%s:\\' % letter
      for letter in string.ascii_lowercase
      if ctypes.windll.kernel32.GetDriveTypeW(letter + ':\\') == DRIVE_FIXED
    ]

  @staticmethod
  def _get_disk_info(mount_point):
    """Returns total and free space on a mount point in Mb."""
    total_bytes = ctypes.c_ulonglong(0)
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
        ctypes.c_wchar_p(mount_point), None, ctypes.pointer(total_bytes),
        ctypes.pointer(free_bytes))
    return {
      u'free_mb': round(free_bytes.value / 1024. / 1024., 1),
      u'size_mb': round(total_bytes.value / 1024. / 1024., 1),
    }

  @staticmethod
  def get_os_version_name():
    """Returns the marketing name of the OS including the service pack.
  
    On Windows 10, use the build number since there will be no service pack.
    """
    # Python keeps a local map in platform.py and it is updated at newer python
    # release. Since our python release is a bit old, do not rely on it.
    is_server = sys.getwindowsversion().product_type == 3
    lookup = cwinsecurity._WIN32_SERVER_NAMES if is_server else cwinsecurity._WIN32_CLIENT_NAMES
    version_number, build_number = cwinsecurity._get_os_numbers()
    marketing_name = lookup.get(version_number, version_number)
    if version_number == '10.0':
      # Windows 10 doesn't have service packs, the build number now is the
      # reference number.
      return '%s-%s' % (marketing_name, build_number)
    service_pack = platform.win32_ver()[2] or 'SP0'
    return '%s-%s' % (marketing_name, service_pack)
 
  @staticmethod
  def get_disks_info():
    """Returns disk infos on all mount point in Mb."""
    return {p: cwinsecurity._get_disk_info(p) for p in cwinsecurity._get_mount_points()}
  
  @staticmethod
  def get_audio():
    """Returns audio device as listed by WMI."""
    wbem = _get_wmi_wbem()
    if not wbem:
      return None
    # https://msdn.microsoft.com/library/aa394463.aspx
    return [
      device.Name
      for device in wbem.ExecQuery('SELECT * FROM Win32_SoundDevice')
      if device.Status == 'OK'
    ]
  
  '''
  @staticmethod
  def get_cpuinfo():
    # Ironically, the data returned by WMI is mostly worthless.
    # Another option is IsProcessorFeaturePresent().
    # https://msdn.microsoft.com/en-us/library/windows/desktop/ms724482.aspx
    import _winreg
    k = _winreg.OpenKey(
        _winreg.HKEY_LOCAL_MACHINE,
        'HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0')
    try:
      identifier, _ = _winreg.QueryValueEx(k, 'Identifier')
      match = re.match(
          ur'^.+ Family (\d+) Model (\d+) Stepping (\d+)$', identifier)
      name, _ = _winreg.QueryValueEx(k, 'ProcessorNameString')
      vendor, _ = _winreg.QueryValueEx(k, 'VendorIdentifier')
      return {
        u'model': [
          int(match.group(1)), int(match.group(2)), int(match.group(3))
        ],
        u'name': name,
        u'vendor': vendor,
      }
    finally:
      k.Close()
  '''

  @staticmethod
  def get_physical_ram():
    """Returns the amount of installed RAM in Mb, rounded to the nearest number.
    """
    # https://msdn.microsoft.com/library/windows/desktop/aa366589.aspx
    class MemoryStatusEx(ctypes.Structure):
      _fields_ = [
        ('dwLength', ctypes.c_ulong),
        ('dwMemoryLoad', ctypes.c_ulong),
        ('dwTotalPhys', ctypes.c_ulonglong),
        ('dwAvailPhys', ctypes.c_ulonglong),
        ('dwTotalPageFile', ctypes.c_ulonglong),
        ('dwAvailPageFile', ctypes.c_ulonglong),
        ('dwTotalVirtual', ctypes.c_ulonglong),
        ('dwAvailVirtual', ctypes.c_ulonglong),
        ('dwAvailExtendedVirtual', ctypes.c_ulonglong),
      ]
    stat = MemoryStatusEx()
    stat.dwLength = ctypes.sizeof(MemoryStatusEx)  # pylint: disable=W0201
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    return int(round(stat.dwTotalPhys / 1024. / 1024.))
  
  @staticmethod
  def get_uptime():
    """Return uptime for Windows 7 and later.
  
    Excludes sleep time.
    """
    val = ctypes.c_ulonglong(0)
    if ctypes.windll.kernel32.QueryUnbiasedInterruptTime(ctypes.byref(val)) != 0:
      return val.value / 10000000.
    return 0.

if "__main__" == __name__:
  print(os.path.basename(sys.executable))
  winsec = cwinsecurity()

  winsec.get_integrity_level()
  print(winsec.get_integrity_level())
  print(winsec._get_mount_points())
  print(winsec._get_disk_info(winsec._get_mount_points()[0]))
  print(winsec.get_os_version_name())
  print(winsec.get_disks_info())
  print(winsec.get_physical_ram())
  print(winsec.get_uptime())
