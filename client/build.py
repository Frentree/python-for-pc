import os
import sys
import json
import datetime
import zipfile

def build_zip(dir_path, postfix, API_SERVER_ADDR, DSCS_ALL_FILES_TRAVERSED, add_runbat = False):
  os.chdir(dir_path)
  os.system("del " + 'ftclient_installer_'+postfix+'.zip')
  my_zip = zipfile.ZipFile('ftclient_installer_'+postfix+'.zip', 'w')
  path_conf_json = "configuration_"+postfix+".json"
  os.system("copy configuration.json " + path_conf_json)

  with open(path_conf_json, 'r', encoding='utf-8-sig') as json_conf_file:
    conf_content = json_conf_file.read()
    conf_dic = json.loads(conf_content)

  conf_dic['API_SERVER_ADDR']           = API_SERVER_ADDR
  conf_dic['DSCS_ALL_FILES_TRAVERSED']  = DSCS_ALL_FILES_TRAVERSED

  with open(path_conf_json, 'w', encoding='utf-8-sig') as json_conf_file:
    json.dump(conf_dic, json_conf_file, indent=4, ensure_ascii=False)
  
  my_zip.write('configuration_'+postfix+'.json',  'configuration.json', compress_type = zipfile.ZIP_DEFLATED)
  my_zip.write('install.exe',                     'install.exe',        compress_type = zipfile.ZIP_DEFLATED)
  my_zip.write('uninstall.exe',                   'uninstall.exe',      compress_type = zipfile.ZIP_DEFLATED)
  my_zip.write('package.exe',                     'package.exe',        compress_type = zipfile.ZIP_DEFLATED)
  if add_runbat:
    my_zip.write('run.bat',                       'run.bat',            compress_type = zipfile.ZIP_DEFLATED)

  return os.getcwd() + os.sep + 'ftclient_installer_'+postfix+'.zip'

def upload(filename_src, filename_dst):
  import pysftp
  import datetime
  import zipfile

  with open("env.json", 'r', encoding='utf-8-sig') as json_env_file:
    env_contents = json_env_file.read()
    env_dic = json.loads(env_contents)

  cnopts = pysftp.CnOpts()
  cnopts.hostkeys = None
  with pysftp.Connection(host=env_dic['myHostname'], port=2223, username=env_dic['myUsername'], password=env_dic['myPassword'], cnopts=cnopts) as sftp:
    print("Connection succesfully stablished ... ")

    # Switch to a remote directory
    #sftp.cwd('/var/www/html/2022.04.27_ftclient')
    sftp.cwd('/home/gen/workspace/DLL/DllProject/Server/downloads')

    # Obtain structure of the remote directory '/var/www/vhosts'
    directory_structure = sftp.listdir_attr()

    # filename = datetime.datetime.now().strftime("/var/www/html/2022.04.27_ftclient/installer_%H%M%S.exe")
    # sftp.put('C:\\Users\\Admin\\Desktop\\repos\\GitHub\\python-for-pc\\client\\dist\\installer.exe',
    #   filename)
    print(f"REMOVE {filename_dst}")
    try:
      sftp.remove(filename_dst)
    except FileNotFoundError as e:
      pass

    print(f"UPLOAD {filename_src}")
    sftp.put(filename_src, filename_dst)

    # Print data
    for attr in directory_structure:
      print(attr.filename, attr)

  # connection closed automatically at the end of the with statement

  print("Uploaded " + filename_dst)

def generate_file_version(file_version):
  run_filename = 'file_version.txt'
  if os.path.exists(run_filename):
    os.remove(run_filename)

  f = open(run_filename, 'a')  # open file in append mode
  file_content = '''# UTF-8
#
VSVersionInfo(
  ffi=FixedFileInfo(
# filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
# Set not needed items to zero 0.
filevers=(1, 0, 0, 0),
prodvers=(1, 0, 0, 0),
# Contains a bitmask that specifies the valid bits 'flags'r
mask=0x3f,
# Contains a bitmask that specifies the Boolean attributes of the file.
flags=0x0,
# The operating system for which this file was designed.
# 0x4 - NT and there is no need to change it.
OS=0x4,
# The general type of file.
# 0x1 - the file is an application.
fileType=0x1,
# The function of the file.
# 0x0 - the function is not defined for this fileType
subtype=0x0,
# Creation date and time stamp.
date=(0, 0)
),
  kids=[
StringFileInfo(
  [
  StringTable(
    u'040904B0',
    [StringStruct(u'CompanyName', u'frentree'),
    StringStruct(u'InternalName', u''),
    StringStruct(u'LegalCopyright', u''),
    StringStruct(u'OriginalFilename', u''),
    StringStruct(u'ProductName', u'ftclient.exe'),
    StringStruct(u'ProductVersion', u'___FILE_VERSION___')])
  ]), 
VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''
  file_content = file_content.replace('___FILE_VERSION___', file_version)

  f.write(file_content)
  f.close()

if __name__ == '__main__':
  #cmd = 'python -m PyInstaller -F --hidden-import=win32timezone -n ftclient main.py'
  #os.system(cmd)
  dir_path = "..\\00.RELEASE"
  datestr     = (datetime.datetime.now().strftime("%Y%m%d"))
  datetimestr = (datetime.datetime.now().strftime("%Y%m%d_%H%M"))
  print(datetimestr)

  if len(sys.argv) > 1 and sys.argv[1] == "generate_file_version":
    generate_file_version(datetimestr)
    sys.exit(0)

  os.chdir(dir_path)
  run_filename = 'run.bat'
  if not os.path.exists(run_filename):
    f = open(run_filename, 'a')  # open file in append mode
    f.write('uninstall.exe\n')
    f.write('timeout 5\n')
    f.write('install.exe\n')
    f.close()

  build_zip(dir_path, datestr+"_"+"150.19.24.208_traversed",      "150.19.24.208", "True")
  build_zip(dir_path, datestr+"_"+"150.19.24.208_not_traversed",  "150.19.24.208", "False")
  build_zip(dir_path, datestr+"_"+"183.107.9.230_traversed",      "183.107.9.230", "True")
  build_zip(dir_path, datestr+"_"+"183.107.9.230_not_traversed",  "183.107.9.230", "False")

  # 183.107.9.230_not_traversed
  installer_2b_uploaded = build_zip(dir_path, datestr,  "183.107.9.230", "False", True)

  upload(installer_2b_uploaded, "update.zip")
