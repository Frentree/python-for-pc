import win32api
import win32con

def set_file_attribute_hidden(filepath):
  win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_HIDDEN)

def getFileDescription(windows_exe):
  try:
    language, codepage = win32api.GetFileVersionInfo(windows_exe, '\\VarFileInfo\\Translation')[0]
    stringFileInfo = u'\\StringFileInfo\\%04X%04X\\%s' % (language, codepage, "FileDescription")
    description = win32api.GetFileVersionInfo(windows_exe, stringFileInfo)
  except:
    description = "unknown"
      
  return description

def getFileVersion(windows_exe):
  try:
    language, codepage = win32api.GetFileVersionInfo(windows_exe, '\\VarFileInfo\\Translation')[0]
    stringFileInfo = u'\\StringFileInfo\\%04X%04X\\%s' % (language, codepage, "FileVersion")
    version = win32api.GetFileVersionInfo(windows_exe, stringFileInfo)
  except:
    version = "unknown"
      
  return version

def getProductVersion(windows_exe):
  try:
    language, codepage = win32api.GetFileVersionInfo(windows_exe, '\\VarFileInfo\\Translation')[0]
    stringFileInfo = u'\\StringFileInfo\\%04X%04X\\%s' % (language, codepage, "ProductVersion")
    productVersion = win32api.GetFileVersionInfo(windows_exe, stringFileInfo)
  except:
    productVersion = "unknown"
      
  return productVersion