import ctypes

dll_abspath = "C:\\Windows\\system32\\kernel32.dll"
dll_abspath = "C:\\Windows\\system32\\notepad.exe"
dll_handle = ctypes.windll.LoadLibrary(dll_abspath)
dll_handle.Beep(2000,500)
