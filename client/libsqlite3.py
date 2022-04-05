import os
import sqlite3

class csqlite3:
    def __init__(self, name):
        self.file_path = name
        if False == (os.path.isfile(self.file_path)):
            self.con = sqlite3.connect(self.file_path)
            self.cur = self.con.cursor()
            self.cur.execute('''
    CREATE TABLE fileinfo (
        id integer primary key,
        filepath text UNIQUE,
        filesize int,
        state text
    )
            ''')
            self.con.commit()
        else:
            self.con = sqlite3.connect(self.file_path)
            self.cur = self.con.cursor()

    def fileinfo_insert(self, filepath, filesize):
        sql_cmd = "INSERT INTO fileinfo (filepath, filesize, state) VALUES ('" + \
            filepath + "', " + \
            str(filesize) + ", " + \
            "'')"
        #print(sql_cmd)
        try:
            self.cur.execute(sql_cmd)
            self.con.commit()
        except sqlite3.IntegrityError as e:
            #print(e)
            return
