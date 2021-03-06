import os
import sqlite3

"""
    file state transition:
        queued
        decrypted and schedule_id is NULL
        decrypted and schedule_id is NOT NULL
"""
class csqlite3:
    def __init__(self, name, log):
        self.log = log
        self.log.debug("DB : " + name)
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
        DSCSIsEncryptedRet tinyint(3),
        schedule_id int
    )
            ''')
            self.cur.execute('''
    CREATE TABLE except_fileinfo (
        id integer primary key,
        filepath text UNIQUE
    )
            ''')
            self.con.commit()
        else:
            self.con = sqlite3.connect(self.file_path)
            self.cur = self.con.cursor()

    def __del__(self):
        self.con.close()

    # region except_fileinfo
    def except_fileinfo_insert(self, filepath):
        sql_cmd = "INSERT INTO except_fileinfo (filepath) VALUES ('" + filepath + "') "
        self.log.debug(sql_cmd)
        try:
            self.cur.execute(sql_cmd)
            self.con.commit()
        except sqlite3.IntegrityError as e:
            self.log.error(str(e))
            return

    def except_fileinfo_delete(self, filepath):
        filepath = self._filepath_preproc(filepath)
        condition = "WHERE filepath='"+ filepath +"'"
        sql_cmd = "DELETE from except_fileinfo " + condition
        self.cur.execute(sql_cmd)
        self.con.commit()

    def except_fileinfo_hasmatch(self, filepath):
        condition = " WHERE filepath='"+filepath+"'"
        sql_cmd = "SELECT * FROM except_fileinfo" + condition

        self.cur.execute(sql_cmd)

        rows = self.cur.fetchall()
        #for row in rows:
        #    print(row)
        return len(rows) > 0

    # endregion

    def fileinfo_insert(self, filepath):
        filesize = os.path.getsize(filepath)
        self.fileinfo_insert_with_size(filepath, filesize)

    def _filepath_preproc(self, filepath):
        return filepath.replace("'", "''")

    def fileinfo_insert_with_size(self, filepath, filesize):
        if None == filesize:
            filesize = os.path.getsize(filepath)

        filepath = self._filepath_preproc(filepath)
        # sql_cmd = "INSERT INTO fileinfo (filepath, filesize, state) VALUES ('" + \
        #     filepath + "', " + \
        #     str(filesize) + ", " + \
        #     "'queued')"
        sql_cmd = "INSERT INTO fileinfo (filepath, filesize, state) VALUES ('" + \
            filepath + "', " + \
            str(filesize) + ", " + \
            "'queued') " + \
            " ON CONFLICT(filepath) DO UPDATE SET state='queued';"
        self.log.debug(sql_cmd)
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
        condition = " WHERE state='"+state+"' "#and schedule_id IS NOT NULL"
        sql_cmd = "SELECT * FROM fileinfo" + condition

        self.cur.execute(sql_cmd)

        rows = self.cur.fetchall()
        #for row in rows:
        #    print(row)
        return rows

    def fileinfo_update_state(self, filepath, state):
        filepath = self._filepath_preproc(filepath)
        condition = "WHERE filepath='"+ filepath +"'"
        sql_cmd = "UPDATE fileinfo SET state='"+state+"' " + condition
        self.cur.execute(sql_cmd)
        self.con.commit()

    def fileinfo_delete(self, filepath):
        filepath = self._filepath_preproc(filepath)
        condition = "WHERE filepath='"+ filepath +"'"
        sql_cmd = "DELETE from fileinfo " + condition
        self.cur.execute(sql_cmd)
        self.con.commit()

    def fileinfo_update_schedule_id(self, filepath, schedule_id):
        filepath = self._filepath_preproc(filepath)
        condition = "WHERE filepath='"+ filepath +"'"
        sql_cmd = "UPDATE fileinfo SET schedule_id='"+schedule_id+"' " + condition
        self.cur.execute(sql_cmd)
        self.con.commit()

    def fileinfo_get_queued_file_size_total(self):
        condition = "WHERE state='decrypted' and schedule_id IS NOT NULL"
        #condition = "WHERE state='decrypted' and schedule_id IS NULL"
        sql_cmd = "SELECT sum(filesize) FROM fileinfo " + condition
        self.cur.execute(sql_cmd)
        rows = self.cur.fetchall()

        ret_value = None
        if len(rows) > 0:
            ret_value = (rows[0][0])
        if None == ret_value:
            return 0
        else:    
            return ret_value
