import urllib3
import requests
import json
import sys
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
    userpw = "fren1212"
    my_profile_label = "label1"
    LOCATION_ROOT = "C:" # or "C:"

    def __init__(self, er_host_addr):
        self.DEBUG_ON = True

        self.URL = "https://"+er_host_addr+":8339/beta"

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.log = logclass()
        (self.my_group_id, self.my_target_id) = self.get_my_group_target_id()
        self.debug("my group id:"+str(self.my_group_id))
        self.debug("my target id:"+str(self.my_target_id))
        self.my_current_matches = self.my_summary_target_matches()
        self.my_datatype_profile_id = self.get_my_datatype_profile_id()
        self.debug("my profile id:"+str(self.my_datatype_profile_id))
        self.debug('matches:'+self.my_current_matches)
        #self.get_my_matchobjects()

    def get_my_matchobjects(self):
        result = self.request('get', '/targets/'+self.my_target_id+'/matchobjects')
        print(json.dumps(result, indent=4))

    def get_my_group_target_id(self):
        my_target_id = None
        my_group_id = None

        import platform
        self.my_hostname = platform.node()
        self.my_hostname = 'DESKTOP-J6FK55A'      # NOTE: dev
        # target name: DESKTOP-J6FK55A ==> vbox vm win, id: 14952095194870184286
        self.debug('hostname:'+self.my_hostname)

        result = self.list_groups()
        for group in result:
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

        print("URL:"+req_url)
        if 'post' == method:
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            res = requests.post(req_url, headers=headers, auth=(self.userid, self.userpw), verify=False, data = payload)
        elif 'get' == method:
            res = requests.get(req_url, auth=(self.userid, self.userpw), verify=False)
        elif 'delete' == method:
            headers = {'Content-Type': 'application/json'}
            res = requests.delete(req_url, headers=headers, auth=(self.userid, self.userpw), verify=False)

        ret = res.json()
        return ret

    #region GROUPS
    def list_groups(self, list_all = True):
        url = '/groups'
        if list_all:
            # groups all has additional info.
            url += '/all'
        return self.request('get', url)
    #endregion GROUPS

    #region TARGETS
    def list_targets(self, target_id = ""):
        if "" != target_id:
            target_id = '/'+target_id
        return self.request('get', '/targets'+target_id)
    
    def my_list_targets(self):
        return self.list_targets(self.my_target_id)

    def delete_target(self, target_id):
        self.request('delete', '/targets/'+str(target_id))

    def create_target_group(self):
        data = {
            'name':'windows-client',
            'comments':'windows client'
        }
        self.request('post', '/groups', json.dumps(data))

    def create_server_target(self):
        data = {
            'name':'my windows client1',
            'group_id':'14161356768415448827',
            'platform': 'Windows 10 64bit',
        }
        self.request('post', '/targets', json.dumps(data))
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
    def add_local_location(self, target_id, data_path):
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
        self.request('delete', '/targets/'+str(target_id)+'/locations/'+str(location_id))

    def list_locations(self, target_id):
        ret = self.request('get', '/targets/'+str(target_id)+'/locations')
        return ret

    def my_list_locations(self):
        return self.list_locations(self.my_target_id)

    def get_location_id_by_path(self, target_id, location_path):
        ret = self.list_locations(target_id)
        for location in ret:
            if 'file' != location['protocol']:
                continue
            if location['path'] == location_path:
               return location['id']
        return None
    #endregion LOCATIONS

    #region DATATYPES_PROFILES
    def get_datatype_profiles(self):
        return self.request('get', '/datatypes/profiles')

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
                self.my_datatype_profile_id,         # frentree      TODO
            ],
        }
        ret = self.request('post', '/schedules', payload=json.dumps(data))
        return ret

    # Desc.: add schedule and returns SCHEDULE_ID
    # return:
    #   success - SCHEDULE ID (str)
    #   fail - None
    def my_add_schedule(self, subpath_list):
        location_id = self.get_location_id_by_path(self.my_target_id, \
            self.LOCATION_ROOT) # TODO
        self.debug('location_id:'+str(location_id))
        new_label = self.my_hostname+"_"+datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug('new label:' + new_label)

        location_list = []

        for subpath in subpath_list:
            location_list.append({
                'id':location_id,
                'subpath':subpath,
            })
        result = self.add_schedule(self.my_target_id, new_label, location_list)
        # NOTE: schedule id will be just one whether the param subpath is multiple or not
        # success example : {'id': '44'}
        if 'id' in result:
            return result['id']
        else:
            return None

    # action
    #   'deactivate'
    def update_schedule(self, schedule_id, action):
        return self.request('post', '/schedules/'+str(schedule_id)+'/'+action)
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
    er = er_agent("192.168.56.102")

    # NOTE - assumptions
    # created a group

    result = er.my_list_targets()
    result = er.my_list_locations()

    from libsqlite3 import csqlite3
    workdir_path = "."
    params = {
        "project_name": "prj1",
    }
    sqlite3 = csqlite3(workdir_path + '/' + params["project_name"] + ".db")
    file_list = sqlite3.fileinfo_select()

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
    main()
