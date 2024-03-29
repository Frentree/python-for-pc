import requests
import json

class cApiServer:
  def __init__(self, server_addr, server_port, hostname, log):
    self.server_addr = server_addr
    self.server_port = server_port
    self.hostname = hostname
    self.log = log

  def c2s_jobPost(self, post_data):
    url = 'http://'+self.server_addr+':'+self.server_port+'/c2s_job/' + self.hostname

    self.log.debug(url)
    r = requests.post(url, json=post_data)
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))

    return ret

  def c2s_jobGet(self):
    url = 'http://'+self.server_addr+':'+self.server_port+'/c2s_job/' + self.hostname

    self.log.debug(url)
    r = requests.get(url)
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))

    return ret

  def drm_resourcePost(self, post_data):
    url = 'http://'+self.server_addr+':'+self.server_port+'/drm_resource'

    self.log.debug(url)
    self.log.debug(post_data)
    r = requests.post(url, json=post_data)
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))
    return ret

  def drm_configGet(self):
    import lib_winsec, sys
    desc = lib_winsec.getProductVersion(sys.executable)
    url = 'http://'+self.server_addr+':'+self.server_port+'/drm_config?host='+self.hostname+"&desc="+desc

    self.log.debug(url)
    r = requests.get(url)
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))

    return ret['result']

  def v_drm_scheduleGet(self):
    url = 'http://'+self.server_addr+':'+self.server_port+'/v_drm_schedule' + "/" + self.hostname

    self.log.debug(url)
    r = requests.get(url)
    ret = r.json()
    self.log.info(json.dumps(ret, indent=4))

    if 'result' not in ret:
      return None
    if len(ret['result']) < 1:
      return None

    ret = ret['result'][0]
    return ret

  def pi_schedulesPost(self, schedule_id, ap_no, DRM_STATUS):
    url = 'http://'+self.server_addr+':'+self.server_port+'/pi_schedules'
    post_data = {
      'schedule_id': schedule_id,
      'ap_no': ap_no,
      'DRM_STATUS' : DRM_STATUS,
    }

    self.log.debug(url)
    self.log.debug(post_data)
    r = requests.post(url, json=post_data)
    self.log.debug(str(r))
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))

    self.log.info("################### pi_schedulesPost " + str(schedule_id) + " " + str(DRM_STATUS))

  # upload
  def c2s_logfile(self, logpath):
    url = 'http://'+self.server_addr+':'+self.server_port+'/c2s_log/' + self.hostname

    self.log.debug(url)
    logfile_handle = open(logpath, "rb")
    r = requests.post(url, files = {"file": logfile_handle})
    self.log.debug(str(r))
    ret = r.json()
    self.log.debug(json.dumps(ret, indent=4))

  # download
  def c2s_update(self, filepath):
    url = 'http://'+self.server_addr+':'+self.server_port+'/c2s_update/'

    post_data = {
      'filepath': filepath,
    }
    self.log.info(url)
    r = requests.get(url, json=post_data)
    self.log.info(str(r))
    with open(filepath, "wb") as file:
      file.write(r.content)
    import tempfile
    tempDir = tempfile.TemporaryDirectory()
    import os
    if False:    # auto remove
      with tempfile.TemporaryDirectory() as tmpdirname:
        self.log.info('created temporary directory ' + tmpdirname)
        import zipfile
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
          zip_ref.extractall(tmpdirname)
          cmd = "cd " +str(tmpdirname) + " & " + " run.bat"
          os.system(cmd)
          self.log.info(cmd)
    else:
      tmpdirname = tempfile.mkdtemp()
      self.log.info('created temporary directory ' + tmpdirname)
      import zipfile
      with zipfile.ZipFile(filepath, 'r') as zip_ref:
        zip_ref.extractall(tmpdirname)

        os.chdir(tmpdirname)
        cmd = "cd " +str(tmpdirname) + " & " + " run.bat"
        self.log.info(cmd)
        os.system(cmd)

        cmd = "rmdir /S /Q \"" + str(tmpdirname) + "\""
        self.log.info(cmd)
        os.system(cmd)