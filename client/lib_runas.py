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

def runas_high(appname, param, console_session_id = None, show = False):
    import win32security
    token = win32security.OpenProcessToken(win32process.GetCurrentProcess(), 
                    win32security.TOKEN_ALL_ACCESS)

    # duplicated = win32security.DuplicateToken(token, 2)
    duplicated = win32security.DuplicateTokenEx(token,
                                                3,#2,win32con.MAXIMUM_ALLOWED,
                                                win32security.TOKEN_ALL_ACCESS, 
                                                win32security.TokenPrimary)        

    curr_proc_id = win32process.GetCurrentProcessId()
    curr_session_id = win32ts.ProcessIdToSessionId(curr_proc_id)

    # access denied! error code: 5
    win32security.SetTokenInformation(duplicated, win32security.TokenSessionId, curr_session_id)
    console_user_token = win32ts.WTSQueryUserToken(curr_session_id)




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


def runas_system(appname, param, console_session_id = None, show = False):
    console_session_id = win32ts.WTSGetActiveConsoleSessionId()
    proc_list = _lib_find_procs_by_name("winlogon.exe")
    for p in proc_list:
        pid = p.pid
        session_id = win32ts.ProcessIdToSessionId(pid)
    # print(pid)
    # print(session_id)

    console_user_token = win32ts.WTSQueryUserToken(session_id)
    # print("console user token: " + str(console_user_token))

    import win32security, win32api

    hProcess = win32api.OpenProcess(win32con.MAXIMUM_ALLOWED, False, pid)

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

if '__main__' == __name__:
    #print(get_explorer_session_id())
    #runas_high("cmd.exe", "")
    runas_system("cmd.exe", "")