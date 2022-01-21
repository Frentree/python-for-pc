import sys
import json
import pymysql

class DBMaria:
    def __init__(self):
        print("maria db connection")
        #self.connect()

    def connect(self):
        # Connect to MariaDB Platform
        try:
            self.conn = pymysql.connect(
                user="picenter",
                password="!!picenter$$",
                host="127.0.0.1",
                port=3306,
                database="picenter"
            )
        except pymysql.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        # Get Cursor
        self.cur = self.conn.cursor()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def _select(self, field_list, table_name):
        self.connect()

        query_field_list = []
        for i in range(len(field_list)):
            query_field_list.append("`" + field_list[i] + "`")
        query = "SELECT " + ",".join(query_field_list) + " FROM " + table_name
        self.cur.execute(query)
        db_tuple_list = []
        for row in self.cur:
            db_tuple = {}
            for i in range(len(row)):
                db_tuple[field_list[i]] = str(row[i])
            db_tuple_list.append(db_tuple)

        self.close()
        return db_tuple_list

    def get_config(self):
        self.connect()
        ret = self._select(['mnt_time', 'job_time'], 'drm_config')
        self.close()
        return ret

    def get_job(self):
        self.connect()
        ret = self._select(['index', 'path', 'type'], 'drm_job')
        self.close()
        return ret

    def get_resource(self):
        self.connect()
        ret = self._select(['index', 'timestamp', 'hostname', 'total_cpu', 'total_disk', 'total_network', 'specific_cpu', 'specific_memory', 'specific_disk', 'specific_network'], 'drm_resource')
        self.close()
        return ret

    def get_log(self):
        self.connect()
        ret = self._select(['index', 'timestamp', 'hostname', 'path'], 'drm_log')
        self.close()
        return ret




    def post_config(self, mnt_time, job_time):
        self.connect()
        self.cur.execute("DELETE FROM drm_config")
        self.cur.execute("INSERT INTO drm_config (mnt_time, job_time) VALUES('"+mnt_time+"', '"+job_time+"');")
        self.close()

    def post_job(self, path, type):
        self.connect()
        self.cur.execute("DELETE FROM drm_job")
        self.cur.execute("INSERT INTO drm_job (path, type) " + "values('{}', '{}')".format(path, type))
        self.close()

    def post_resource(self, timestamp, hostname, total_cpu, total_disk, total_network, specific_cpu, specific_memory, specific_disk, specific_network):
        self.connect()
        self.cur.execute("DELETE FROM drm_resource")
        self.cur.execute("INSERT INTO drm_resource (timestamp, hostname, total_cpu, total_disk, total_network, specific_cpu, specific_memory, specific_disk, specific_network) VALUES('"+timestamp+"', '"+hostname+"', '"+total_cpu+"', '"+total_disk+"', '"+total_network+"', '"+specific_cpu+"', '"+specific_memory+"', '"+specific_disk+"', '"+specific_network+"');")
        self.close()

    def post_log(self, timestamp, hostname, path):
        self.connect()
        self.cur.execute("DELETE FROM drm_log")
        self.cur.execute("INSERT INTO drm_log (timestamp, hostname, path) VALUES('"+timestamp+"', '"+hostname+"', '"+path+"');")
        self.close()




    def get_cmd_by_ip(self, ip):
        try:
            file_handle = open("cmd_" + ip + ".json", "r")
            content = file_handle.read()
            file_handle.close()
        except FileNotFoundError as e:
            content_json = {
                "cmd_list" : [
                    "cmd_call_dll"
                ]
            }
            content = json.dumps(content_json, indent=4)

        return content

db_maria = DBMaria()

