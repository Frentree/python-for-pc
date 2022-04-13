import os
import pathlib
import psutil
import json
import win32security
import subprocess
from ctypes import *

def run_subprocess(exename):
    subprocess.Popen(exename, shell=True)

def lib_getwinuserhome():
	result = pathlib.Path.home()
	return result

def lib_getwindir():
	result = os.getenv('WINDIR')
	return result

def lib_virtual_memory():
    ret = psutil.virtual_memory()
    #virtual_mem_dict = dict(ttutil_virtual_memory()._asdict())
    return str(ret.percent)

def lib_cpu_usage():
    return str(psutil.cpu_percent())

def lib_net_io_counters():
    ret = psutil.net_io_counters()
    result = {
        "bytes_sent": ret.bytes_sent,
        "bytes_recv": ret.bytes_recv,
        "packets_sent":ret.packets_sent,
        "packets_recv":ret.packets_recv,
        "errin":ret.errin,
        "errout":ret.errout,
        "dropin":ret.dropin,
        "dropout":ret.dropout,
    }
    #print("SENT: "+str(sent))
    return json.dumps(result)

def lib_disk_usage():
    #return psutil.disk_usage('/')
    return str(psutil.disk_usage('/')[3])

def lig_get_pid_list_by_name_reg(regex):
    process_list = []
    import re
    for process in psutil.process_iter():
        p = re.compile(regex, re.IGNORECASE)
        m = p.match(process.name())
        if m:
            process_list.append(process.pid)
        else:
            pass

    return process_list

def lib_get_pid_by_name_reg(regex):
    import re
    for process in psutil.process_iter():
        p = re.compile(regex, re.IGNORECASE)
        m = p.match(process.name())
        if m:
            return process.pid
        else:
            pass

    return None

def lib_find_procs_by_name(name):
    "Return a list of processes matching 'name'."
    ls = []
    for p in psutil.process_iter(['name']):
        if p.info['name'] == name:
            ls.append(p)
    return ls

def lib_print_service_list():
    for svc in psutil.win_service_iter():
        print(svc)


LPVOID = c_void_p
PVOID = LPVOID
PSID = PVOID
DWORD = c_uint32
LPSTR = c_char_p
HANDLE      = LPVOID
INVALID_HANDLE_VALUE = c_void_p(-1).value
LONG        = c_long
WORD        = c_uint16

READ_CONTROL                     = 0x00020000
STANDARD_RIGHTS_READ             = READ_CONTROL
STANDARD_RIGHTS_REQUIRED         = 0x000F0000

TOKEN_ASSIGN_PRIMARY    = 0x0001
TOKEN_DUPLICATE         = 0x0002
TOKEN_IMPERSONATE       = 0x0004
TOKEN_QUERY             = 0x0008
TOKEN_QUERY_SOURCE      = 0x0010
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_ADJUST_GROUPS     = 0x0040
TOKEN_ADJUST_DEFAULT    = 0x0080
TOKEN_ADJUST_SESSIONID  = 0x0100
TOKEN_READ = (STANDARD_RIGHTS_READ | TOKEN_QUERY)
tokenprivs  = (TOKEN_QUERY | TOKEN_READ | TOKEN_IMPERSONATE | TOKEN_QUERY_SOURCE | TOKEN_DUPLICATE | TOKEN_ASSIGN_PRIMARY | (131072 | 4))
PROCESS_QUERY_INFORMATION = 0x0400


class LUID(Structure):
    _fields_ = [
        ("LowPart",     DWORD),
        ("HighPart",    LONG),
    ]

class SID_AND_ATTRIBUTES(Structure):
    _fields_ = [
        ("Sid",         PSID),
        ("Attributes",  DWORD),
    ]

class TOKEN_USER(Structure):
    _fields_ = [
        ("User", SID_AND_ATTRIBUTES),]

class LUID_AND_ATTRIBUTES(Structure):
    _fields_ = [
        ("Luid",        LUID),
        ("Attributes",  DWORD),
    ]

class TOKEN_PRIVILEGES(Structure):
    _fields_ = [
        ("PrivilegeCount",  DWORD),
        ("Privileges",      LUID_AND_ATTRIBUTES),
    ]

class PROCESS_INFORMATION(Structure):
    _fields_ = [
        ('hProcess',    HANDLE),
        ('hThread',     HANDLE),
        ('dwProcessId', DWORD),
        ('dwThreadId',  DWORD),
    ]

class STARTUPINFO(Structure):
    _fields_ = [
        ('cb',              DWORD),
        ('lpReserved',      LPSTR),
        ('lpDesktop',       LPSTR),
        ('lpTitle',         LPSTR),
        ('dwX',             DWORD),
        ('dwY',             DWORD),
        ('dwXSize',         DWORD),
        ('dwYSize',         DWORD),
        ('dwXCountChars',   DWORD),
        ('dwYCountChars',   DWORD),
        ('dwFillAttribute', DWORD),
        ('dwFlags',         DWORD),
        ('wShowWindow',     WORD),
        ('cbReserved2',     WORD),
        ('lpReserved2',     LPVOID),    # LPBYTE
        ('hStdInput',       HANDLE),
        ('hStdOutput',      HANDLE),
        ('hStdError',       HANDLE),
    ]

def GetUserName():
    nSize = DWORD(0)
    windll.advapi32.GetUserNameA(None, byref(nSize))
    error = GetLastError()
    
    ERROR_INSUFFICIENT_BUFFER = 122
    if error != ERROR_INSUFFICIENT_BUFFER:
        raise WinError(error)
    
    lpBuffer = create_string_buffer(b'', nSize.value + 1)
    
    success = windll.advapi32.GetUserNameA(lpBuffer, byref(nSize))
    if not success:
        raise WinError()
    return lpBuffer.value

def GetTokenSid(hToken):
    """Retrieve SID from Token"""
    dwSize = DWORD(0)
    pStringSid = LPSTR()
    print("hToken: %s"%hToken.value)
    TokenUser = 1
    r=windll.advapi32.GetTokenInformation(hToken, TokenUser, byref(TOKEN_USER()), 0, byref(dwSize))
    if r!=0:
        raise WinError()
    address = windll.kernel32.LocalAlloc(0x0040, dwSize)
    windll.advapi32.GetTokenInformation(hToken, TokenUser, address, dwSize, byref(dwSize))
    pToken_User = cast(address, POINTER(TOKEN_USER))
    windll.advapi32.ConvertSidToStringSidA(pToken_User.contents.User.Sid, byref(pStringSid))
    print("error")
    sid = pStringSid.value
    windll.kernel32.LocalFree(address)
    return sid

def lib_get_pid_owner(pid):
    try:
        import win32api
        import win32con
        proc = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        token = win32security.OpenProcessToken(proc, win32con.TOKEN_QUERY)
        user_sid, user_attr = win32security.GetTokenInformation(token,
                    win32security.TokenUser)
        user = win32security.LookupAccountSid(None, user_sid)
        return user_sid, user[0], user[1]
    except win32api.error as e:
        raise 

def lib_get_process_info(pid):
    #print(GetUserName())
    try:
        import win32api
        import win32con

        proc = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        token = win32security.OpenProcessToken(proc, tokenprivs)
        user_sid, user_attr = win32security.GetTokenInformation(token,
                    win32security.TokenUser)
        user = win32security.LookupAccountSid(None, user_sid)
        print(user)

        win32api.CloseHandle(token)
        win32api.CloseHandle(token)

    except WindowsError as e:
        print("[!] Error:" + str(e))

def seDebug():
    import win32security
    import win32api
    flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)
    id = win32security.LookupPrivilegeValue(None, win32security.SE_TCB_NAME)
    privilege = [(id, win32security.SE_PRIVILEGE_ENABLED)]
    print(win32security.AdjustTokenPrivileges(token, False, privilege))
