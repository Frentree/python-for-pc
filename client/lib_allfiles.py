import sys
import os
import glob
import json
import time
import psutil

from lib_logging import *
from lib_winsec import cwinsecurity

config_logging()
setLogLevel(logging.DEBUG)

def traverse_all_files_glob(func, path = None):
  partition_list = []
  if None != path:
    partition_list.append(path)
  else:
    disk_partitions = psutil.disk_partitions()
    for disk_partition in disk_partitions:
      partition_list.append(disk_partition.device)

  for partition in partition_list:
    path = partition+'*'
    # print("path: " + path)
    for f in glob.glob(path, recursive=True):
      #time.sleep(0.1)
      if os.path.isdir(f):
        traverse_all_files_glob(func, f+"\\?")
      #print(f)
      func(f, "Admin")

def traverse_all_files(func):
  partition_list = psutil.disk_partitions()
  for partition in partition_list:
    print(partition.device)
    directory = partition.device
    for filename in os.listdir(directory):
      f = os.path.join(directory, filename)

      if os.path.isfile(f):
        #print(f)
        func(f, "Admin")
        #time.sleep(0.1)
  sys.exit(0)

class cdummy:
  MINIMUM_FILESIZE = 5
  def __init__(self, log):
    self.log = log

  def myFunc(self, filepath, user_id):
    #print("### " + filepath + " ###")
    from libsqlite3 import csqlite3
    mount_points = cwinsecurity._get_mount_points()
    userprofile = mount_points[0]+"Users\\"+user_id
    db_path = (userprofile+"\\AppData\\Local\\Temp" + "\\state.db")
    #self.log.info("db path: " + db_path)
    sqlite3 = csqlite3(name=db_path, log=self.log)

    target_path = filepath

    # sleep a second
    #time.sleep(1)

    try:
        filesize = os.path.getsize(target_path)
    except FileNotFoundError as e:
        self.log.error('FileNotFoundError  ' + str(e))
        return
    except PermissionError as e:
        self.log.error('PermissionError ' + str(e))
        return
    if filesize < self.MINIMUM_FILESIZE:
        self.log.debug("filesize: " + str(filesize))
        return

    (file_path, file_name, file_ext) = cwinsecurity._split_name_ext_from_path(target_path)
    self.log.info("file_path : " + file_path)
    #self.log.info("file_name : " + file_name)
    #time.sleep(1)

    with open("pathlist.json", "r", encoding='UTF-8-sig') as json_file:
      file_path_whitelist = json.load(json_file)
    if file_path.lower() in file_path_whitelist:
      return

    file_path_whitelist.append(file_path.lower())
    file_path_whitelist.sort()
    with open("pathlist.json", 'w') as outfile:
      json.dump(file_path_whitelist, outfile, indent=4)
    #time.sleep(1)

    # with open("extlist.json", "r") as json_file:
    #   file_ext_whitelist = json.load(json_file)
    # if file_ext.lower() in file_ext_whitelist:
    #   return

    # file_ext_whitelist.append(file_ext.lower())
    # file_ext_whitelist.sort()
    # with open("extlist.json", 'w') as outfile:
    #   json.dump(file_ext_whitelist, outfile, indent=4)

    #self.log.info("file_ext : " + file_ext)
    #target_path = target_path.replace("'", "''")
    # self.log.info("path: " + target_path + " (size: " + str(filesize) + ")")
    #sqlite3.fileinfo_insert(target_path, filesize)


if '__main__' == __name__:
  #mount_points = cwinsecurity._get_mount_points()
  #mount_points = cwinsecurity.mount_points()
  #print(mount_points)
  # traverse_all_files(myFunc)
  dummy = cdummy(log)
  #traverse_all_files_glob(dummy.myFunc, "C:\\Program Files\\Adobe\\Adobe Photoshop CC 2019\\Presets\\\Lighting Effects")
  traverse_all_files_glob(dummy.myFunc)



