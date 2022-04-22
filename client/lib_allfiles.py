import sys
import os
from lib_winsec import cwinsecurity

def traverse_all_files(func):
  import psutil

  partition_list = psutil.disk_partitions()

  for partition in partition_list:
    print(partition.device)
    directory = partition.device
    for filename in os.listdir(directory):
      f = os.path.join(directory, filename)

      if os.path.isfile(f):
        #print(f)
        func(f)
        import time
        time.sleep(0.1)
  sys.exit(0)

def myFunc(filepath):
  print("### " + filepath + " ###")

if '__main__' == __name__:
  #mount_points = cwinsecurity._get_mount_points()
  #mount_points = cwinsecurity.mount_points()
  #print(mount_points)
  traverse_all_files(myFunc)
