import os
import sqlite3

class csqlite3:
  def __init__(self, file_path, log):
    self.tblname_schedule_fileinfo  = 'schedule_fileinfo'
    self.tblname_except_fileinfo    = 'except_fileinfo'

    self.log = log
    self.log.debug("DB : " + file_path)
    self.file_path = file_path
    if False == (os.path.isfile(self.file_path)):
      self.con = sqlite3.connect(self.file_path, timeout=10)
      self.cur = self.con.cursor()
      ###
      # state : 'local_queued' => 'decrypted' => 'local_scheduled'
      self.cur.execute('''
CREATE TABLE schedule_fileinfo (
  id                  integer primary key,
  filepath_org        text UNIQUE,
  filepath_decrypted  text UNIQUE,
  filesize            int,
  state               text,
  DSCSIsEncryptedRet  tinyint(3),
  schedule_id         int,
  drm_schedule_id     int,
  tries               tinyint(3)
)
      ''')
      # except_fileinfo state list:
      #   QUEUED
      #   TO_BE_DELETED
      self.cur.execute('''
CREATE TABLE except_fileinfo (
  id          integer primary key,
  state       text,
  filepath    text UNIQUE
)
      ''')
      self.con.commit()
    else:
      self.con = sqlite3.connect(self.file_path)
      self.cur = self.con.cursor()

  def __del__(self):
    self.con.close()

  def _filepath_preproc(self, filepath):
    return filepath.replace("'", "''")

  def fileinfo_insert_with_size(self, filepath, filesize):
    filepath = self._filepath_preproc(filepath)
    sql_cmd = "INSERT INTO schedule_fileinfo (filepath_org, filesize, state, tries) VALUES ('" + \
      filepath + "', " + \
      str(filesize) + ", " + \
      "'local_queued', 3) " + \
      " ON CONFLICT(filepath_org) DO UPDATE SET state='local_queued';"
    self.log.debug(sql_cmd)
    try:
      self.cur.execute(sql_cmd)
      self.con.commit()
    except sqlite3.IntegrityError as e:
      self.log.error(str(e))
      return

  def except_fileinfo_delete_record(self, filepath):
    filepath = self._filepath_preproc(filepath)
    condition = "WHERE filepath='"+ filepath +"'"
    sql_cmd = "DELETE from "+self.tblname_except_fileinfo+" "+ condition
    self.cur.execute(sql_cmd)
    self.con.commit()

  def schedule_fileinfo_delete_record(self, filepath_org):
    filepath_org = self._filepath_preproc(filepath_org)
    condition = "WHERE filepath_org='"+ filepath_org +"'"
    sql_cmd = "DELETE from "+self.tblname_schedule_fileinfo+" "+ condition
    self.cur.execute(sql_cmd)
    self.con.commit()

  def schedule_fileinfo_select_all(self):
    sql_cmd = "SELECT * FROM "+self.tblname_schedule_fileinfo+""

    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return rows

  def schedule_fileinfo_getinfo(self, fileinfo_row):
    fileinfo_dic = {}
    fileinfo_dic['id']                  = fileinfo_row[0]
    fileinfo_dic['filepath_org']        = fileinfo_row[1]
    fileinfo_dic['filepath_decrypted']  = fileinfo_row[2]
    fileinfo_dic['filesize']            = fileinfo_row[3]
    fileinfo_dic['state']               = fileinfo_row[4]
    fileinfo_dic['DSCSIsEncryptedRet']  = fileinfo_row[5]
    fileinfo_dic['schedule_id']         = fileinfo_row[6]
    fileinfo_dic['drm_schedule_id']     = fileinfo_row[7]
    fileinfo_dic['tries']               = fileinfo_row[8]
    return fileinfo_dic

  def schedule_decrease_tries(self, schedule_fileinfo_id):
    sql_cmd = "UPDATE "+self.tblname_schedule_fileinfo+" SET tries=tries-1 WHERE id="+str(schedule_fileinfo_id)
    self.log.info(sql_cmd)
    self.cur.execute(sql_cmd)
    self.con.commit()

  def schedule_fileinfo_not_completed(self):
    sql_cmd = "SELECT * FROM schedule_fileinfo WHERE state not in ('local_queued', 'decrypted')"

    self.log.debug(sql_cmd)
    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return rows

  def schedule_fileinfo_select(self, state='queued'):
    condition = " WHERE state='"+state+"'"
    sql_cmd = "SELECT * FROM schedule_fileinfo" + condition

    self.log.debug(sql_cmd)
    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return rows

  def schedule_fileinfo_update_filepath_decrypted(self, filepath_org, filepath_decrypted):
    filepath_org        = self._filepath_preproc(filepath_org)
    filepath_decrypted  = self._filepath_preproc(filepath_decrypted)

    condition = "WHERE filepath_org='"+ filepath_org +"'"
    sql_cmd = "UPDATE "+self.tblname_schedule_fileinfo+" SET filepath_decrypted='"+filepath_decrypted+"' " + condition
    self.log.debug(sql_cmd)
    self.cur.execute(sql_cmd)
    self.con.commit()

  def schedule_fileinfo_update_state(self, filepath_org, state):
    filepath_org = self._filepath_preproc(filepath_org)
    condition = "WHERE filepath_org='"+ filepath_org +"'"

    set_list = []
    set_list.append(" state='" + state + "'")
    set_part = ",".join(set_list)

    set_part = "state='"+state+"' " + ""
    sql_cmd = "UPDATE "+self.tblname_schedule_fileinfo+" SET " + " " + set_part + " " + condition
    try:
      self.log.info(sql_cmd)
      self.cur.execute(sql_cmd)
      self.con.commit()
    except Exception as e:
      self.log.error(str(e) + " sql: " + sql_cmd)
      return

  def except_fileinfo_update_state(self, filepath, state):
    filepath = self._filepath_preproc(filepath)
    condition = "WHERE filepath='"+ filepath +"'"

    set_list = []
    set_list.append(" state='" + state + "'")
    set_part = ",".join(set_list)

    set_part = "state='"+state+"' " + ""
    sql_cmd = "UPDATE "+self.tblname_except_fileinfo+" SET " + " " + set_part + " " + condition
    try:
      self.log.info(sql_cmd)
      self.cur.execute(sql_cmd)
      self.con.commit()
    except Exception as e:
      self.log.error(str(e) + " sql: " + sql_cmd)
      return

  def schedule_fileinfo_update_schedule_id(self, filepath_org, state, schedule_id, drm_schedule_id):
    filepath_org = self._filepath_preproc(filepath_org)
    condition = "WHERE filepath_org='"+ filepath_org +"'"

    set_list = []
    set_list.append("state='" + state + "'")
    set_list.append("schedule_id='"+schedule_id+"'")
    set_list.append("drm_schedule_id='"+drm_schedule_id+"'")
    set_part = ",".join(set_list)

    sql_cmd = "UPDATE "+self.tblname_schedule_fileinfo+" SET " + " " + set_part + " " + condition
    try:
      self.log.info(sql_cmd)
      self.cur.execute(sql_cmd)
      self.con.commit()
    except Exception as e:
      self.log.error(str(e) + " sql: " + sql_cmd)
      return

  # region except_fileinfo
  def except_fileinfo_insert(self, filepath, state=None):
    if None == state:
      sql_cmd = "INSERT INTO except_fileinfo (filepath) VALUES ('" + filepath + "') "
    else:
      sql_cmd = "INSERT INTO except_fileinfo (filepath, state) VALUES ('" + filepath + "', '" + state + "') "
    self.log.info(sql_cmd)
    try:
      self.cur.execute(sql_cmd)
      self.con.commit()
    except sqlite3.IntegrityError as e:
      self.log.error(str(e) + " sql: " + sql_cmd)
      return

  def except_fileinfo_delete(self, filepath):
    filepath = self._filepath_preproc(filepath)
    condition = "WHERE filepath='"+ filepath +"'"
    sql_cmd = "DELETE from except_fileinfo " + condition
    self.log.debug(sql_cmd)
    self.cur.execute(sql_cmd)
    self.con.commit()

  def schedule_fileinfo_exist(self, filepath_org):
    sql_cmd = "SELECT * FROM "+self.tblname_schedule_fileinfo+" " + \
      "WHERE UPPER(filepath_org) LIKE '%"+filepath_org+"%'"

    self.log.info(sql_cmd)
    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return len(rows) > 0

  def schedule_fileinfo_hasmatch(self, filepath_org):
    condition = " WHERE filepath_org='"+filepath_org+"'"
    sql_cmd = "SELECT * FROM "+self.tblname_schedule_fileinfo+" " + condition

    self.log.info(sql_cmd)
    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return len(rows) > 0

  # region hasmatch
  def except_fileinfo_hasmatch(self, filepath):
    condition = " WHERE filepath='"+filepath+"'"
    sql_cmd = "SELECT * FROM except_fileinfo" + condition

    self.log.info(sql_cmd)
    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return len(rows) > 0

  def schedule_fileinfo_hasmatch_filepath_decrypted(self, filepath_decrypted):
    condition = " WHERE filepath_decrypted='"+filepath_decrypted+"'"
    sql_cmd = "SELECT * FROM "+self.tblname_schedule_fileinfo+"" + condition

    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return len(rows) > 0
  # endregion

  def except_fileinfo_select_all(self):
    sql_cmd = "SELECT * FROM "+self.tblname_except_fileinfo+" "

    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return rows

  def except_fileinfo_select(self, state='TO_BE_DELETED'):
    condition = " WHERE state='"+state+"'"
    sql_cmd = "SELECT * FROM "+self.tblname_except_fileinfo+" "+ condition

    self.cur.execute(sql_cmd)

    rows = self.cur.fetchall()
    return rows

  def schedule_fileinfo_delete_by_filepath_org(self, filepath_org):
    filepath_org = self._filepath_preproc(filepath_org)
    condition = " WHERE filepath_org='"+ filepath_org +"'"
    sql_cmd = "DELETE from "+self.tblname_schedule_fileinfo+" " + condition
    self.log.debug(sql_cmd)
    self.cur.execute(sql_cmd)
    self.con.commit()

  # endregion