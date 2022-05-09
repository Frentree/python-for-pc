import ctypes, sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if '__main__' == __name__:
  if is_admin():
      # Code of your program here
      print("ADMIN")
      executable = 'c:\\windows\\system32\\cmd.exe'
      ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, " ".join(sys.argv), None, 1)
      pass
  else:
      # Re-run the program with admin rights
      # ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

      executable = 'c:\\windows\\system32\\calc.exe'
      # ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, " ".join(sys.argv), None, 1)
      ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, "", None, 1)
