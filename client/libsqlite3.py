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
            "'queued')"
        #print(sql_cmd)
        try:
            self.cur.execute(sql_cmd)
            self.con.commit()
        except sqlite3.IntegrityError as e:
            #print(e)
            return

    def fileinfo_select(self, num=5):
        condition = "" # " WHERE "
        sql_cmd = "SELECT * FROM fileinfo" + condition

        self.cur.execute(sql_cmd)

        rows = self.cur.fetchall()
        for row in rows:
            print(row)
        return rows

    def fileinfo_update(self):
        msg = ""
        sql_text = "UPDATE summary SET processed_count=processed_count+1"
        self.cur.execute(sql_text)
        self.con.commit()

