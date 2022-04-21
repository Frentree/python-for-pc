import requests
import json
from lib_winsec import cwinsecurity

class cApiInterface:

  def __init__(self, server_address, log):
    self.server_address = server_address
    self.log = log
    self.hostname = cwinsecurity.get_hostname()

  def c2s_jobPost(self, post_data):
    url = 'http://'+self.server_address+'/c2s_job/' + self.hostname

    self.log.debug(url)
    r = requests.post(url, json=post_data)
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))
    return ret

  def c2s_jobGet(self):
    url = 'http://'+self.server_address+'/c2s_job/' + self.hostname

    self.log.debug(url)
    r = requests.get(url)
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))
    return ret

  def drm_configGet(self):
    url = 'http://'+self.server_address+'/drm_config'

    self.log.debug(url)
    r = requests.get(url)
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))
    return ret

  def v_drm_scheduleGet(self):
    url = 'http://'+self.server_address+'/v_drm_schedule' + "/" + self.hostname

    self.log.debug(url)
    r = requests.get(url)
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))

    if 'result' not in ret:
      return None
    if len(ret['result']) < 1:
      return None

    ret = ret['result'][0]
    return ret

  def pi_schedulesPost(self, schedule_id, ap_no, DRM_STATUS):
    url = 'http://'+self.server_address+'/pi_schedules' + "/" + self.hostname
    post_data = {
      'schedule_id': schedule_id,
      'ap_no': ap_no,
      'DRM_STATUS' : DRM_STATUS,
    }
    r = requests.post(url, json=post_data)
    self.log.info("################### pi_schedulesPost " + str(DRM_STATUS))