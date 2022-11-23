import json
import base64
import requests

from datetime import datetime

class er_agent():
  def __init__(self, hostname, log=None):
    self.my_hostname = hostname
    self.log = log
    self.unload_v_drm_schedule()

  def load_v_drm_schedule(self, v_drm_schedule_json):
    self.URL = "https://"+v_drm_schedule_json['IP']+":8339/beta"

    self.my_location_id           = v_drm_schedule_json['LOCATION_ID']
    self.my_datatype_profile_id   = v_drm_schedule_json['PROFILES']
    self.my_target_id             = v_drm_schedule_json['TARGET_ID']
    self.userid                   = v_drm_schedule_json['ID']
    self.current_ap_no            = v_drm_schedule_json['AP_NO']
    self.current_drm_schedule_id  = v_drm_schedule_json['SCHEDULE_ID']
    self.memory                   = v_drm_schedule_json['MEMORY']
    self.throughput               = v_drm_schedule_json['THROUGHPUT']

    import base64
    self.userpw_encoded = base64.b64encode(v_drm_schedule_json['PD'].encode('ascii'))

  def unload_v_drm_schedule(self):
    self.my_location_id           = None
    self.my_datatype_profile_id   = None
    self.my_target_id             = None
    self.userid                   = None
    self.current_ap_no            = None
    self.current_drm_schedule_id  = None
    self.memory                   = None
    self.throughput               = None
    self.userpw_encoded           = None

  def request(self, method, url, payload=None):
    req_url = self.URL + url

    self.log.debug("ER URL:"+req_url)
    userpw = base64.b64decode(self.userpw_encoded).decode('ascii')
    if 'post' == method:
      headers = {'Content-Type': 'application/json; charset=utf-8'}
      res = requests.post(req_url, headers=headers, auth=(self.userid, userpw), verify=False, data = payload)
    elif 'get' == method:
      res = requests.get(req_url, auth=(self.userid, userpw), verify=False)
    elif 'delete' == method:
      headers = {'Content-Type': 'application/json'}
      res = requests.delete(req_url, headers=headers, auth=(self.userid, userpw), verify=False)

    try:
      ret = res.json()
    except json.JSONDecodeError as e:
      return ""
    return ret

  #region SCHEDULES
  def list_schedules(self, schedule_id=None):
    url = '/schedules'
    if None != schedule_id:
      url += '/' + str(schedule_id)
    return self.request('get', url)

  def is_schedule_completed(self, schedule_id):
    try:
      result = self.list_schedules(schedule_id)
      self.log.info(json.dumps(result, indent=4, ensure_ascii=False))
      if 'targets' not in result: return False
      if len(result['targets']) < 1: return False
      if 'locations' not in result['targets'][0]: return False
      if len(result['targets'][0]['locations']) < 1: return False
      if 'status' not in result['targets'][0]['locations'][0]: return False
      if 'completed' != result['targets'][0]['locations'][0]['status']: return False
    except Exception as e:
      import traceback
      self.log.error(traceback.format_exc())
      self.log.error(e)
      return False
    return True

  # data structure of location list
  #   [
  #       {
  #           'id':'...'
  #           'subpath':'...'
  #       },
  #   ]
  def add_schedule(self, target_id, label, location_list):
    data = {
      'label':label,
      'targets': {
        'id':target_id,
        'locations': location_list,
      },
      "profiles": [
        self.my_datatype_profile_id,
      ],
    }
    if self.memory != None:
      if self.memory == 0:
        data['memory'] = 1024
      else:
        data['memory'] = self.memory
    if self.throughput != None:
      if self.throughput == 0:
        data['throughput'] = 50
      else:
        data['throughput'] = self.throughput

    self.log.info(json.dumps(data, indent=4, ensure_ascii=False))
    ret = self.request('post', '/schedules', payload=json.dumps(data))
    return ret

  # Desc.: add schedule and returns SCHEDULE_ID
  # NOTE: blank subpath list means all the files in the disk
  # return:
  #   success - SCHEDULE ID (str)
  #   fail - None
  def my_add_schedule(self, subpath_list, postfix = ""):
    new_label = self.my_hostname+"_"+datetime.now().strftime("%Y%m%d %H%M%S_DRM")

    if "" != postfix:
      new_label = new_label + "_" + postfix
    location_id = self.my_location_id

    location_list = []
    for subpath in subpath_list:
      location_list.append({
        'id':location_id,
        'subpath':subpath,
      })
    result = self.add_schedule(self.my_target_id, new_label, location_list)
    self.log.info(json.dumps(result, indent=4))
    # NOTE: schedule id will be just one whether the param subpath is multiple or not
    # success example : {'id': '44'}
    if 'id' in result:
      return result['id']
    else:
      return None
  #endregion

  #region
  def list_locations(self, target_id):
    ret = self.request('get', '/targets/'+str(target_id)+'/locations')
    return ret
  def summary_targets(self):
    return self.request('get', '/summary/targets')
  def list_targets(self, target_id = ""):
    if "" != target_id:
      target_id = '/'+target_id
    return self.request('get', '/targets'+target_id)
  #endregion

if __name__ == '__main__':
  import lib_logging, sys, logging
  log = lib_logging.init_log(logging.DEBUG)
  er = er_agent("DESKTOP1", log)
  print(log)
  er.load_v_drm_schedule({
    'IP': "192.168.12.7",
    "LOCATION_ID": '10115313857004559053',
    'LOCATION_ID': '',
    'PROFILES': '',
    'TARGET_ID': '',
    'ID': 'admin',
    'AP_NO': '',
    'SCHEDULE_ID': '',
    'PD': 'fren1212',
  })

  if 'list_locations' == sys.argv[1]:
    print("TARGET ID: " + sys.argv[2])
    result = er.list_locations(sys.argv[2])
    print("=== locations ===")
    print(json.dumps(result, indent=4))
    result = er.list_targets(sys.argv[2])
    print("=== targets ===")
    print(json.dumps(result, indent=4))
  elif 'list_schedules' == sys.argv[1]:
    result = er.list_schedules(sys.argv[2])
    print(json.dumps(result, indent=4))