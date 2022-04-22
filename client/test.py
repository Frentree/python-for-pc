name_value_list = {
  'schedule_id' : '',
  'ap_no' : '',
  'DRM_STATUS' : '',
  'schedule_status' : '',
  "schedule_id": "1121",
  "ap_no": "1",
  "schedule_status": "",
  "schedule_label": "None",
  "schedule_repeat_days": "None",
  "schedule_repeat_months": "None",
  "schedule_datatype_profiles": "None",
  "schedule_next_scan": "None",
  "schedule_target_id": "None",
  "schedule_target_name": "None",
  "schedule_cpu": "None",
  "schedule_capture": "None",
  "schedule_trace": "None",
  "schedule_pause_days": "None",
  "schedule_pause_from": "None",
  "schedule_pause_to": "None",
  "regdate": "None",
  "NET_TYPE": "None",
  "DRM_STATUS": "D"
}

#for item in name_value_list:
#  print(item)
#  print(name_value_list[item])

import sys
import os
import ntpath
#%userprofile%\AppData\Local\Temp
userprofile = os.getenv("userprofile", "")
print(userprofile+"\\AppData\\Local\\Temp")
workdir_path = ntpath.dirname(sys.executable)
print(workdir_path)

cmd = "copy '" + workdir_path + "\\configuration.json' '"+userprofile+"\\AppData\\Local\\Temp'"
print(cmd)
os.system(cmd)

from lib_runas import *

str = "aaa\nbbb\nccc"
str_list = str.split('\n')
print(str_list)
#getuserId()