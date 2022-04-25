import urllib3
import requests
import json
import sys
import base64
from datetime import datetime

#URL = "https://192.168.0.18:8339/beta"
#URL = "https://192.168.56.102:8339/beta"

class logclass():
    def __init__(self):
        pass
    def debug(self, msg):
        print(msg)

class er_agent():
    #URL = "https://192.168.0.18:8339/beta"
    URL = "https://192.168.56.102:8339/beta"
    userid = "admin"
    userpw_encoded = 'ZnJlbjEyMTI='
    my_profile_label = "label1"# "frentree"
    LOCATION_ROOT = "C:"
    my_location_id = ''
    my_datatype_profile_id = ''
    my_target_id = ''

    def __init__(self, log = None, er_host_addr = None):
        self.DEBUG_ON = True

        import platform
        self.my_hostname = platform.node()

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.log = logclass()
        if None != log:
            self.log = log

        if None == er_host_addr:
            return

        self.URL = "https://"+er_host_addr+":8339/beta"
        (self.my_group_id, self.my_target_id) = self.get_my_group_target_id()
        self.log.info("my group id:"+str(self.my_group_id))
        self.log.info("my target id:"+str(self.my_target_id))
        self.my_current_matches = self.my_summary_target_matches()
        self.my_datatype_profile_id = self.get_my_datatype_profile_id()
        self.log.info("my profile id:"+str(self.my_datatype_profile_id))
        #self.log.info(str(self.my_list_locations()))
        self.log.info('matches:'+str(self.my_current_matches))
        #self.get_my_matchobjects()
        if None == self.my_group_id:
            print("default group id " + self.default_group_id)
            self.create_server_target(self.my_hostname, self.default_group_id)
        locations = self.my_list_locations()
        if 0 == len(locations):
            self.location_add_local(self.my_target_id, "C:")
        self.my_location_id = ''

    def isAvailable(self):
        my_list = [
            self.my_hostname,
            self.my_location_id,
            self.my_datatype_profile_id,
            self.my_target_id,
            self.URL,
            self.userid,
            self.userpw_encoded,
        ]

        for item in my_list:
            if None == item or '' == item or 0 == item:
                return False

        try:
            self.my_list_targets()
        except requests.exceptions.ConnectTimeout as e:
            self.log.error("connection failed")
            self.log.error(str(e))
            return False
        return True

    def setMyUserId(self, userid):
        self.userid = userid

    def setMyERIP(self, erip):
        self.URL = "https://"+erip+":8339/beta"

    def load_v_drm_schedule(self, v_drm_schedule_json):
        if None == v_drm_schedule_json:
            return
        #self.log.info("LOADING DRM SCHEDULE ###################################")
        #self.log.info(v_drm_schedule_json)
        self.setMyLocationId(v_drm_schedule_json['LOCATION_ID'])
        self.setMyProfileId(v_drm_schedule_json['PROFILES'])
        self.setMyTargetId(v_drm_schedule_json['TARGET_ID'])
        self.setMyERIP(v_drm_schedule_json['IP'])
        self.setMyUserId(v_drm_schedule_json['ID'])
        self.setMyUserPW(v_drm_schedule_json['PD'])
        self.current_ap_no = v_drm_schedule_json['AP_NO']
        self.current_schedule_id = v_drm_schedule_json['SCHEDULE_ID']
        #self.log.info(json.dumps(self.get_datatype_profiles(), indent=4))

    def setMyUserPW(self, userpw):
        self.userpw_encoded = base64.b64encode(userpw.encode('ascii'))

    def get_my_matchobjects(self):
        result = self.request('get', '/targets/'+self.my_target_id+'/matchobjects')

    def get_my_group_target_id(self):
        my_target_id = None
        my_group_id = None

        self.debug('hostname:'+self.my_hostname)

        result = self.list_groups()
        for group in result:
            if 'DEFAULT GROUP' == group['name']:
                self.default_group_id = group['id']
            if 'targets' not in group: continue
            for target in group['targets']:
                if target['name'] == self.my_hostname:
                    my_group_id = group['id']
                    my_target_id = target['id']
        return (my_group_id, my_target_id)

    def debug(self, msg):
        if False == self.DEBUG_ON:
            return
        self.log.debug('[DEBUG] ' + msg)

    def prt(self, title, data):
        print(title.upper())
        print(json.dumps(data, indent=4))

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

    #region GROUPS
    def my_list_groups(self):
        return self.request('get', '/groups/'+self.my_group_id)

    def list_groups(self, list_all = True):
        url = '/groups'
        if list_all:
            # groups all has additional info.
            url += '/all'
        return self.request('get', url)

    def groups_delete(self, group_id):
        return self.request('delete', '/groups/'+str(group_id))
    #endregion GROUPS

    #region TARGETS
    def list_targets(self, target_id = ""):
        if "" != target_id:
            target_id = '/'+target_id
        return self.request('get', '/targets'+target_id)
    
    def setMyTargetId(self, target_id):
        self.my_target_id = target_id

    def my_list_targets(self):
        return self.list_targets(self.my_target_id)

    def targets_delete(self, target_id):
        return self.request('delete', '/targets/'+str(target_id))

    def create_target_group(self, group_name):
        data = {
            'name': group_name,
            'comments':'windows client'
        }
        return self.request('post', '/groups', json.dumps(data))

    def create_server_target(self, target_host_name, group_id, platform = 'Windows 10 64bit'):
        data = {
            'name': target_host_name,
            'group_id': group_id,
            'platform': platform,
        }
        return self.request('post', '/targets', json.dumps(data))
    #endregion TARGETS

    #region AGENTS
    def list_agent(self, agent_id=None):
        url = '/agents'
        if None != agent_id:
            url += '/' + agent_id
        self.request('get', url)

    def verify_agent(self, agent_id):
        self.request('post', '/agents/'+str(agent_id)+'/verify')
    #endregion AGENTS

    #region LOCATIONS
    def location_add_local(self, target_id, data_path = ""):
        data = {
            "path":data_path,
            "protocol":"file",
        }
        ret = self.request('post', '/targets/'+str(target_id)+'/locations', payload=json.dumps(data))
        if 'id' in ret:
            # success example
            # {'id': '6642630235794173719'}
            return ret['id']
        else:
            # fail example
            # {'message': 'A parent file path exists.'}
            return None

    def delete_location(self, target_id, location_id):
        return self.request('delete', '/targets/'+str(target_id)+'/locations/'+str(location_id))

    def list_locations(self, target_id):
        ret = self.request('get', '/targets/'+str(target_id)+'/locations')
        return ret

    def setMyLocationId(self, location_id):
        self.my_location_id = location_id

    def my_list_locations(self):
        return self.list_locations(self.my_target_id)

    def get_location_id_by_path(self, target_id, location_path):
        result = self.list_locations(target_id)
        self.prt("LOCATION", result)
        for location in result:
            if 'file' != location['protocol']:
                continue
            if location['path'] == location_path:
               return location['id']
        return None
    #endregion LOCATIONS

    #region DATATYPES_PROFILES
    def get_datatype_profiles(self):
        return self.request('get', '/datatypes/profiles')

    def setMyProfileId(self, profile_id):
        # 15844480846665880616: frentree
        # 17029408091763885645: label1
        self.my_datatype_profile_id = profile_id

    def get_my_datatype_profile_id(self):
        my_datatype_profile_id = None

        result = self.get_datatype_profiles()
        for profile in result:
            if profile['label'] == self.my_profile_label:
                my_datatype_profile_id = profile['id']
        return my_datatype_profile_id
    #endregion DATATYPES_PROFILES

    #region SCHEDULES
    def list_schedules(self, schedule_id=None):
        url = '/schedules'
        if None != schedule_id:
            url += '/' + str(schedule_id)
        return self.request('get', url)

    def is_schedule_completed(self, schedule_id):
        try:
            result = self.list_schedules(schedule_id)
            self.log.info(json.dumps(result, indent=4))
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
        self.log.info(json.dumps(data, indent=4))
        ret = self.request('post', '/schedules', payload=json.dumps(data))
        return ret

    # Desc.: add schedule and returns SCHEDULE_ID
    # return:
    #   success - SCHEDULE ID (str)
    #   fail - None
    def my_add_schedule(self, subpath_list, postfix = ""):
        #location_id = self.get_location_id_by_path(self.my_target_id, \
        #    self.LOCATION_ROOT) # TODO
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

    # action
    #   'deactivate'
    def update_schedule(self, schedule_id, action):
        result = self.request('post', '/schedules/'+str(schedule_id)+'/'+action)
        return result
    #endregion SCHEDULES

    #region SUMMARY
    def summary_targets(self):
        return self.request('get', '/summary/targets')
    def my_summary_target_matches(self):
        result = self.summary_targets()
        for target in result:
            if target['name'] == self.my_hostname:
                return target['matches']
        return None
    #endregion

def main():
    #a_list = [1,20,3,4,5]
    #a_list = list(map(lambda x : print(x * 10) return x, a_list))
    #print(a_list)
    #sys.exit(0)

    from lib_logging import config_logging, log
    config_logging()

    er = er_agent("192.168.12.7", log)

    #result = er.create_server_target("DESKTOP-J6FK55A", 10155220174825011556)
    #result = er.delete_location(12138559403110519359, 12893076805411359213)
    #print(json.dumps(result, indent=4))
    # NOTE - assumptions
    # created a group
    #result = er.create_target_group('windows_group0')
    #print(json.dumps(result, indent=4))

    result = er.my_list_groups()
    #print(json.dumps(result, indent=4))
    result = er.my_list_locations()

    from libsqlite3 import csqlite3
    workdir_path = "."
    SQLITEDB_FILENAME = "state"
    sqlite3 = csqlite3(workdir_path + '/dist/' + SQLITEDB_FILENAME + ".db")
    file_list = sqlite3.fileinfo_select()

    for fileinfo in file_list:
        file_id = fileinfo[0]
        file_path = fileinfo[1]
        file_size = fileinfo[2]
        file_state = fileinfo[3]
        # schedule_id = er.my_add_schedule(subpath_list=[
        #     file_path,
        #     #'\\users\\danny\\desktop\\s3.txt',
        # ])
        # print("schedule added " + str(schedule_id))

    # file_path = '\\Users\\Admin\\Desktop\\aaa\\8.txt'
    # # file_path = 'C:\\Users\\danny\\Desktop\\s2.txt'
    # schedule_id = er.my_add_schedule(subpath_list=[
    #     file_path,
    #     #'\\users\\danny\\desktop\\s3.txt',
    # ])
    schedule_id = 145
    file_list = sqlite3.fileinfo_select_scheduled()
    print(file_list)
    #print("schedule added " + str(schedule_id))

    #result = er.list_schedules(schedule_id)
    #er.prt("list schedule", result)

    #er.is_schedule_completed(schedule_id)
    sys.exit(0)
    #for schedule_id in range(86, 100):
    #    er.update_schedule(schedule_id, 'deactivate')
    sys.exit(0)
    #     sqlite3.fileinfo_update_state(file_path, "scheduled")

    sys.exit(0)

    for fileinfo in file_list:
        print(json.dumps(fileinfo[1], indent=4))
        schedule_id = er.my_add_schedule(subpath_list=[
            '\\users\\danny\\desktop\\ssn.txt',
            #fileinfo[1],
        ])
        result = er.list_schedules()

    # TODO - get the filelist from sqlite DB ==> put the list to the er schedule
    schedule_id = er.my_add_schedule(subpath_list=[
        '\\users\\danny\\desktop\\ssn.txt',
        '\\users\\danny\\desktop\\ssn.txt',
        '\\users\\danny\\desktop\\ssn.txt',
        '\\users\\danny\\desktop\\ssn.txt',
        '\\users\\danny\\desktop\\ssn.txt',
        # 'Users\\danny\\Desktop\\ssn.txt',
        # 'Users\\danny\\Desktop\\s2.txt',
        # 'Users\\danny\\Desktop\\s3.txt',
    ])
    result = er.list_schedules()
    er.prt("list schedule", result)

    result = er.list_schedules(21)
    er.prt("list schedule", result)
    er.debug("schedule " + str(schedule_id) + " added")
    sys.exit(0)

    #result = er.update_schedule(schedule_id=37, action='deactivate')

    # Agents
    # do_er("/nodeagents", formatted=True)
    #do_er("/users", formatted=True)
    # do_er("/licenses", formatted=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print(traceback.print_stack())
        print(e)        
