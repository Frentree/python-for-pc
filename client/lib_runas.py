#from lib_logging import *
#import ctypes
#import subprocess
#import os
import win32process
import win32con
import win32profile
import win32ts

def _lib_find_procs_by_name(name):
    import psutil
    "Return a list of processes matching 'name'."
    ls = []
    for p in psutil.process_iter(['name']):
        if p.info['name'] == name:
            ls.append(p)
    return ls

def get_explorer_session_id():
    proc_list = _lib_find_procs_by_name("explorer.exe")
    for p in proc_list:
        pid = p.pid
        session_id = win32ts.ProcessIdToSessionId(pid)
        return session_id
    return None

def runas(appname, param, console_session_id = None, show = False):
    #appname = "C:\\WINDOWS\\system32\\cmd.exe"
    if None == console_session_id:
        console_session_id = get_explorer_session_id()
        if None == console_session_id:
            console_session_id = win32ts.WTSGetActiveConsoleSessionId()
    console_user_token = win32ts.WTSQueryUserToken(console_session_id)

    StartInfo = win32process.STARTUPINFO()
    StartInfo.wShowWindow = win32con.SW_HIDE
    StartInfo.lpDesktop = "winsta0\\default"
    creationFlag = win32con.CREATE_UNICODE_ENVIRONMENT | win32con.CREATE_NO_WINDOW # win32con.NORMAL_PRIORITY_CLASS

    if show:
        creationFlag = win32con.CREATE_UNICODE_ENVIRONMENT | win32con.CREATE_NEW_CONSOLE # win32con.NORMAL_PRIORITY_CLASS
        StartInfo.wShowWindow = win32con.SW_SHOW

    environment = win32profile.CreateEnvironmentBlock(console_user_token, False)

    if None != param:
        param = appname + " " + param
        appname = None

    handle, thread_id ,pid, tid = win32process.CreateProcessAsUser(console_user_token,
        appname,
        param,
        None, 
        None,
        False,
        creationFlag,
        environment,
        None,
        StartInfo)

if '__main__' == __name__:
    print(get_explorer_session_id())