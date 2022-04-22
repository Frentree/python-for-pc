

if '__main__' == __name__:
  print("MAIN")
  reg_list = [
    # r"^\\Users\\.*\\AppData\\Local\\Temp\\.*$",
    # r"^\\Users\\.*\\AppData\\Local\\Google\\.*$",
    # r"^\\Users\\.*\\AppData\\Local\\Packages\\.*$",
    # r"^\\Users\\.*\\AppData\\Local\\Microsoft\\.*$",
    # r"^\\Users\\.*\\AppData\\Roaming\\Code\\.*$",
    # r"^\\Users\\.*\\AppData\\Roaming\\GitHub Desktop\\.*$",
    # r"^\\Users\\.*\\AppData\\Roaming\\Microsoft\\Windows\\.*$",
    # r"^\\Users\\.*\\AppData\\Local\\Programs\\Python\\.*$",
    # r"^\\Users\\.*\\AppData\\Local\\ConnectedDevicesPlatform\\.*$",
    # r"^\\Users\\.*\\AppData\\Local\\NVIDIA Corporation\\.*$",
    # r"^\\Users\\.*\\AppData\\LocalLow\\Microsoft\\.*$",
    # r"^\\Users\\.*\\Desktop\\repos\\GitHub\\Python\\.*$",       # TODO
    # r"^\\Windows\\OffWrite.log.*$",
    # r"^\\Windows\\Softcamp\\.*$",
    # r"^\\Windows\\Logs\\.*$",
    # r"^\\Windows\\Prefetch\\.*$",
    # r"^\\Windows\\System32\\.*$",
    # r"^\\Windows\\ServiceProfiles\\NetworkService\\.*$",
    # r"^\\Windows\\ServiceProfiles\\LocalService\\.*$",
    # r"^\\Program Files\\AhnLab\\.*$",
    # r"^\\Program Files (x86)\\Ground Labs\\.*$",
#    r"\\Program Files (x86)\\Ground Labs\\Enterprise Recon 2\\.*$",
    r"^\\ProgramFiles(x).*$",
    # r"^\\ProgramData\\Microsoft\\Diagnosis\\.*$",
    # r"^\\ProgramData\\Microsoft\\Windows\\.*$",
    # r"^\\ProgramData\\Microsoft\\Search\\Data\\.*$",
    # r"^\\ProgramData\\NVIDIA Corporation\\.*$",
    # r"^\\ProgramData\\SoftCamp\\Logs\\.*$",
    # r"^\\ProgramData\\USOPrivate\\Logs\\.*$",
    # r"^\\ProgramData\\USOPrivate\\UpdateStore\\.*$",
    # r"^\\Users\\Admin\\Desktop\\repos\\GitHub\\python-for-pc\\client\\.*$",     # TODO working dir
  ]
  src_path = "\\Program Files (x86)\\Ground Labs\\Enterprise Recon 2\\agent-queue.dat-journal"
  src_path = "\\ProgramFiles(x86)\\GroundLabs\\EnterpriseRecon2"#\\agent-queue.dat-journal"

  for reg in reg_list:
    import re
    p = re.compile(reg, re.IGNORECASE)
    m = p.fullmatch(src_path)
    print(reg)
    print(src_path)
    if m != None:
      print("NOT NONE")
  print("PASS")