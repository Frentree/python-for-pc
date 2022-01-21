import json
from flask import request, render_template
from app import app
from app.database.maria import *
from datetime import datetime

def get_year_month_day_str():
    now = datetime.now()
    return (now.strftime("%Y:%m:%d %H:%M:%S"))

@app.route("/")
def home():
    return render_template("home.html")




@app.route("/drm_config", methods=['GET'])
def drm_config_get():
    response = {
        "is_success" : "true",
        "result" : db_maria.get_config(),
    }
    return json.dumps(response, indent=4)

@app.route("/drm_job", methods=['GET'])
def drm_job_get():
    response = {
        "is_success" : "true",
        "result" : db_maria.get_job(),
    }
    return json.dumps(response, indent=4)

@app.route("/drm_resource", methods=['GET'])
def drm_resource_get():
    response = {
        "is_success" : "true",
        "result" : db_maria.get_resource(),
    }
    return json.dumps(response, indent=4)

@app.route("/drm_log", methods=['GET'])
def drm_log_get():
    response = {
        "is_success" : "true",
        "result" : db_maria.get_log(),
    }
    return json.dumps(response, indent=4)



@app.route("/drm_config", methods=['POST'])
def drm_config_post():
    mnt_time = get_year_month_day_str()
    job_time = get_year_month_day_str()
    db_maria.post_config(mnt_time, job_time)
    response = {
        "is_success" : "true",
    }
    return json.dumps(response, indent=4)

@app.route("/drm_job", methods=['POST'])
def drm_job_post():
    path = "ppppp"
    type = "ttttt"
    db_maria.post_job(path, type)
    response = {
        "is_success" : "true",
    }
    return json.dumps(response, indent=4)

@app.route("/drm_resource", methods=['POST'])
def drm_resource_post():
    timestamp = get_year_month_day_str()
    db_maria.post_resource(timestamp, 'hostname', 'total_cpu', 'total_disk', 'total_network', 'specific_cpu', 'specific_memory', 'specific_disk', 'specific_network')
    response = {
        "is_success" : "true",
    }
    return json.dumps(response, indent=4)

@app.route("/drm_log", methods=['POST'])
def drm_log_post():
    hostname = "hhhhh"
    path = "ppppp"
    timestamp = get_year_month_day_str()
    db_maria.post_log(timestamp, hostname, path)
    response = {
        "is_success" : "true",
    }
    return json.dumps(response, indent=4)









######
# DEPRECATED
######

@app.route("/cmd_call_dll", methods=['GET', 'POST'])
def cmd_call_dll():
    print("client accepted: " + request.remote_addr)
    print("DLL result: " + "")
    client_data = (request.form.to_dict(flat=False))
    print(client_data)
    return "welcome"

@app.route("/cmd_rsc_usage", methods=['GET', 'POST'])
def cmd_rsc_usage():
    #print(request.get_json())
    #print(request.json)
    #print(request.data)
    print("client accepted: " + request.remote_addr)
    db_maria.foo()
    client_data = (request.form.to_dict(flat=False))
    #print(jsonify(request.data))

    file_handle = open(request.remote_addr + ".json", "r")
    content = file_handle.read()
    print(content)
    file_handle.close()

    file_handle = open(request.remote_addr + ".json", "w")
    file_handle.write(json.dumps(client_data, indent=4))
    file_handle.close()
    return "welcome"

@app.route("/get_cmd_list", methods=['GET', 'POST'])
def get_cmd():
    client_data = (request.form.to_dict(flat=False))

    cmd = db_maria.get_cmd_by_ip(request.remote_addr)
    print("["+request.remote_addr+"] get_cmd")

    return cmd

