import os
import sqlite3

class csqlite3:
    def __init__(self, name, log):
        self.log = log
        self.file_path = name
        if False == (os.path.isfile(self.file_path)):
            self.con = sqlite3.connect(self.file_path)
            self.cur = self.con.cursor()
            self.cur.execute('''
    CREATE TABLE fileinfo (
        id integer primary key,
        filepath text UNIQUE,
        filesize int,
        state text,
        schedule_id int
    )
            ''')
            self.con.commit()
        else:
            self.con = sqlite3.connect(self.file_path)
            self.cur = self.con.cursor()

    def __del__(self):
        self.con.close()

    def fileinfo_insert(self, filepath, filesize):
        # sql_cmd = "INSERT INTO fileinfo (filepath, filesize, state) VALUES ('" + \
        #     filepath + "', " + \
        #     str(filesize) + ", " + \
        #     "'queued')"
        sql_cmd = "INSERT INTO fileinfo (filepath, filesize, state) VALUES ('" + \
            filepath + "', " + \
            str(filesize) + ", " + \
            "'queued') " + \
            " ON CONFLICT(filepath) DO UPDATE SET state='queued';"
        self.log.info(sql_cmd)
        try:
            self.cur.execute(sql_cmd)
            self.con.commit()
        except sqlite3.IntegrityError as e:
            self.log.error(str(e))
            return

    def fileinfo_select(self, state='queued'):
        condition = " WHERE state='"+state+"'"
        sql_cmd = "SELECT * FROM fileinfo" + condition

        self.cur.execute(sql_cmd)

        rows = self.cur.fetchall()
        #for row in rows:
        #    print(row)
        return rows

    def fileinfo_select_scheduled(self):
        state = 'decrypted'
        condition = " WHERE state='"+state+"' and schedule_id IS NOT NULL"
        sql_cmd = "SELECT * FROM fileinfo" + condition

        self.cur.execute(sql_cmd)

        rows = self.cur.fetchall()
        #for row in rows:
        #    print(row)
        return rows

    def fileinfo_update_state(self, filepath, state):
        condition = "WHERE filepath='"+ filepath +"'"
        sql_cmd = "UPDATE fileinfo SET state='"+state+"' " + condition
        self.cur.execute(sql_cmd)
        self.con.commit()

    def fileinfo_delete(self, filepath):
        condition = "WHERE filepath='"+ filepath +"'"
        sql_cmd = "DELETE from fileinfo " + condition
        self.cur.execute(sql_cmd)
        self.con.commit()

    def fileinfo_update_schedule_id(self, filepath, schedule_id):
        condition = "WHERE filepath='"+ filepath +"'"
        sql_cmd = "UPDATE fileinfo SET schedule_id='"+schedule_id+"' " + condition
        self.cur.execute(sql_cmd)
        self.con.commit()

