import os
import sys
import json
import datetime
import zipfile

# note : 설치파일 압축하기 위한 소스
def build_zip(dir_path, postfix, API_SERVER_ADDR, DSCS_ALL_FILES_TRAVERSED, add_runbat = False):
  # note : 상위 경로 접근 후 기존 생성된 설치파일 압축파일 삭제 
  os.chdir(dir_path)
  os.system("del " + 'ftclient_installer_'+postfix+'.zip')

  # note : 새로이 압축할 zip 파일 생성
  my_zip = zipfile.ZipFile('ftclient_installer_'+postfix+'.zip', 'w')

  # note : 설정파일 세팅에 맞게 복사
  path_conf_json = "configuration_"+postfix+".json"
  os.system("copy configuration.json " + path_conf_json)

  # note : 경로 및 설정파일 확인(경로 체크)
  print("dir_path : " + dir_path)
  print("path_conf_json : " + path_conf_json)

  with open(path_conf_json, 'r', encoding='utf-8-sig') as json_conf_file:
    # note : 설정파일을 읽어 Dictionary로 저장
    conf_content = json_conf_file.read()
    conf_dic = json.loads(conf_content)

  # note : 설정파일 내 기초적인 항목 추가(서버명, 전체 체크 여부)
  conf_dic['API_SERVER_ADDR']           = API_SERVER_ADDR
  conf_dic['DSCS_ALL_FILES_TRAVERSED']  = DSCS_ALL_FILES_TRAVERSED

  # note : 작성된 dictionary 데이터를 설정 파일에 맞게 기입
  with open(path_conf_json, 'w', encoding='utf-8-sig') as json_conf_file:
    json.dump(conf_dic, json_conf_file, indent=4, ensure_ascii=False)
  
  # note : 생성된 설정파일 및 실행, 설치 지원파일등을 같이 압축파일에 추가
  my_zip.write('configuration_'+postfix+'.json',  'configuration.json', compress_type = zipfile.ZIP_DEFLATED)
  my_zip.write('install.exe',                     'install.exe',        compress_type = zipfile.ZIP_DEFLATED)
  my_zip.write('uninstall.exe',                   'uninstall.exe',      compress_type = zipfile.ZIP_DEFLATED)
  my_zip.write('package.exe',                     'package.exe',        compress_type = zipfile.ZIP_DEFLATED)
  if add_runbat:
    my_zip.write('run.bat',                       'run.bat',            compress_type = zipfile.ZIP_DEFLATED)

  # note : 압축된 파일을 return
  return os.getcwd() + os.sep + 'ftclient_installer_'+postfix+'.zip'

# note : 최초개발자가 관리 및 확인하기 위한 파일 전송 부분, 계약 파기로 인해 불필요한 함수, 정리 필요
def upload(filename_src, filename_dst):
  import pysftp
  import datetime
  import zipfile

  if not os.path.exists("env.json"):
    return

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

# note : 파일 버전 생성 함수, 파일 버전은 ftclient.exe가 빌드될 시점으로, yyyymmdd_hhmm 으로 생성됨
def generate_file_version(file_version):
  # note : 데이터 작성될 파일에 대한 버전 정보는 file_version.txt에 생성(버퍼 성향의 파일)
  run_filename = 'file_version.txt'
  # note : 기존에 파일이 존재 시 삭제
  if os.path.exists(run_filename):
    os.remove(run_filename)

  # note : 데이터 생성, 인코딩 타입은 UTF-8 타입으로 생성
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
  # note : 버전 내용에 대한 데이터는 변수로 받아와 사용
  file_content = file_content.replace('___FILE_VERSION___', file_version)
  # 파일 생성 후 파일 닫기
  f.write(file_content)
  f.close()

# note : build.py 본문
if __name__ == '__main__':
  #cmd = 'python -m PyInstaller -F --hidden-import=win32timezone -n ftclient main.py'
  #os.system(cmd)
  
  # note : 설치 파일등 작업 위치 지정
  dir_path = "..\\00.RELEASE"

  # note : 버전정보 추출을 위한 데이터 정리
  datestr     = (datetime.datetime.now().strftime("%Y%m%d"))
  datetimestr = (datetime.datetime.now().strftime("%Y%m%d_%H%M"))
  print(datetimestr)
  
  # note : build.py에서 옵션값으로 값이 들어왔을 때 버전 파일을 생성하자
  if len(sys.argv) > 1 and sys.argv[1] == "generate_file_version":
    generate_file_version(datetimestr)
    sys.exit(0)

  # note : 배포 파일 생성 시 배치 실행(설치 시 정상 작동 체크 하기 위해)
  os.chdir(dir_path)
  run_filename = 'run.bat'
  
  if not os.path.exists(dir_path + "\\" + run_filename):
    print("overhere")
    f = open(run_filename, 'a')  # open file in append mode
    f.write('uninstall.exe\n')
    f.write('timeout 5\n')
    f.write('install.exe\n')
    f.close()
  
  print(dir_path)

  # note : 해당 설정에 따른 설치파일에 대한 압축파일 생성
  # build_zip(dir_path, datestr+"_"+"150.19.24.208_traversed",      "150.19.24.208", "True")
  build_zip(dir_path, datestr+"_"+"150.19.24.208_not_traversed",  "150.19.24.208", "False")
  # build_zip(dir_path, datestr+"_"+"183.107.9.230_traversed",      "183.107.9.230", "True")
  # build_zip(dir_path, datestr+"_"+"183.107.9.230_not_traversed",  "183.107.9.230", "False")

  # note : 이하 최초개발자에게 파일을 업로드 하기 위한 소스
  # 183.107.9.230_not_traversed
  # installer_2b_uploaded = build_zip(dir_path, datestr,  "183.107.9.230", "False", True)

  # upload(installer_2b_uploaded, "update.zip")
