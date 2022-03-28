import urllib3
import requests
import json
import sys

URL = "https://192.168.0.18:8339/beta"

class er_agent():
    URL = "https://192.168.0.18:8339/beta"
    userid = "admin"
    userpw = "fren1212"
    formatted = True

    def __init__(self):
        print('er agent init')
        print(self.URL)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def request(self, method, url, payload=None):
        req_url = URL + url

        print("URL:"+req_url)
        if 'post' == method:
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            res = requests.post(req_url, headers=headers, auth=(self.userid, self.userpw), verify=False, data = payload)
        elif 'get' == method:
            res = requests.get(req_url, auth=(self.userid, self.userpw), verify=False)
        elif 'delete' == method:
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            res = requests.delete(req_url, headers=headers, auth=(self.userid, self.userpw), verify=False)

        ret = res.json()
        if True == self.formatted:
           print(json.dumps(ret, indent=4))
        else:
           print(ret)

    def list_groups(self):
        self.request('get', '/groups')

    def list_targets(self, target_id = ""):
        if "" != target_id:
            target_id = '/'+target_id
        self.request('get', '/targets'+target_id)

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

    def get_agent(self):
        self.request('get', '/agents')

    def list_locations(self, target_id):
        self.request('get', '/targets/'+str(target_id)+'/locations')

    def add_local_location(self, target_id, data_path):
        data = {
            "path":data_path,
            "protocol":"file",
        }
        self.request('post', '/targets/'+str(target_id)+'/locations', payload=json.dumps(data))

    def get_datatype_profiles(self):
        self.request('get', '/datatypes/profiles')

    def list_schedules(self):
        self.request('get', '/schedules')

    def add_schedule(self, label, target_id):
        data = {
            'label':label,
            'targets': {
                'id':target_id,
            }
        }
        self.request('post', '/schedules', payload=json.dumps(data))

def do_er(url, formatted=True):
    print("do er " + url)
    url = URL + url
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    res = requests.get(url,
                        auth=("admin", "fren1212"),
                        verify=False)#"C:\\Users\\danny\\Documents\\python-for-pc\\client\cert.cer")
                        #verify="D:\DEV\drive_watcher\erpy\prj\cert.cer")
    #curl -u admin:fren1212 -X GET 'https://192.168.0.18:8339/beta/groups/all' -H 'Accept:application/json' -k
    ret = res.json()
    #print(json.dumps(ret[0]['targets'][0], indent=4))
    # print(json.dumps(ret, indent=4))
    if True == formatted:
        print(json.dumps(ret, indent=4))
    else:
        print(ret)
    
if __name__ == '__main__':
    print("main")

    er = er_agent()

    #er.list_groups()
    # NOTE
    # created a group - "14161356768415448827"

    # windows client1 target id : "12138559403110519359"

    er.list_targets(target_id="12138559403110519359")
    er.list_locations(target_id="12138559403110519359")

    #er.add_local_location(target_id='12138559403110519359', data_path='C:\\Users\\danny\\Desktop\\ssn.txt')
    # ==> l0cation added: "12893076805411359213"

    #er.get_datatype_profiles()
    er.list_schedules()
    er.add_schedule(label='my new schedule', target_id="12138559403110519359")
    # schedule added: id : 3
    sys.exit(0)

    # ADD AND SCAN LOCAL FILES ON A SERVER TARGET : Step1 - create target group
    # er.create_target_group()

    # er.list_targets()
    #er.delete_target('8062799675773646641')"",

    # ADD AND SCAN LOCAL FILES ON A SERVER TARGET : Step2 - add server target
    #er.create_server_target()

    # ADD AND SCAN LOCAL FILES ON A SERVER TARGET : Step3 - install and get node agent id
    # er.get_agent()
    # ==> agent id : '5005293123342876564'

    # ADD AND SCAN LOCAL FILES ON A SERVER TARGET : Step4 - verify node agent
    # TODO

    er.list_locations(target_id='14952095194870184286')

    er.add_local_location(target_id='14952095194870184286', data_path='C:\\Users\\danny\\Desktop\\ssn.txt')
    sys.exit(0)

    # groups/all이 groups보다 더 많은 정보를 포함함
    do_er("/groups/all")
    # do_er("/groups")

    # do_er("/summary/history")
    # do_er("/summary/totalmatches")
    # do_er("/summary/groups")

    # target name: DESKTOP-J6FK55A ==> vbox vm win, id: 14952095194870184286
    do_er("/summary/targets")

    # do_er("/summary/groups")
    # do_er("/summary/targettypes")
    #do_er("/summary/fileformats")

    # do_er("/targets/14952095194870184286/matchobjects")
    # do_er("/targets/14952095194870184285/matchobjects")
    # do_er("/summary/targettypes")
    # do_er("/summary/targettypes")
    # do_er("/summary/targettypes")
    # do_er("/summary/targettypes")

    # do_er("/groups/all", formatted=True)
    # do_er("/groups/8543377516941597111", formatted=True)

    #do_er("/schedules/1", formatted=True)

    # Agents
    # do_er("/agents", formatted=True)
    # do_er("/nodeagents", formatted=True)

    #do_er("/users", formatted=True)

    # do_er("/licenses", formatted=True)
