from watchdog.events import PatternMatchingEventHandler
import lib_sqlite3
import lib_dscsdll

class MyLoggerTrick(PatternMatchingEventHandler):
  def __init__(self, patterns=None, ignore_patterns=None,
                 ignore_directories=True, case_sensitive=False, log=None, ignore_dir_regex_list=None,
                 minimum_filesize=None, queue_size_limit=None, sqlite_db_filepath=None, dscsdll_file_name=None):
    self.ignore_blank_extension = False
    if '*' in ignore_patterns: ignore_patterns.remove('*')
    if ''  in ignore_patterns:
      self.ignore_blank_extension = True
      ignore_patterns.remove('')
    super().__init__(patterns=patterns, ignore_patterns=ignore_patterns,
                 ignore_directories=ignore_directories, case_sensitive=case_sensitive)
    self.log = log
    self.log.info(f"[init watchdog] patterns: {patterns}")
    self.ignore_dir_regex_list = ignore_dir_regex_list
    self.minimum_filesize = minimum_filesize
    self.queue_size_limit = queue_size_limit
    self.sqlite_db_filepath = sqlite_db_filepath
    self.dscsdll_file_name = dscsdll_file_name

  def do_main(self, event):
    if event.is_directory:
      return

    import ntpath, sys
    if ntpath.dirname(event.src_path) == ntpath.dirname(sys.executable):
      return

    # region extension
    import pathlib
    bname = ntpath.basename(event.src_path)
    pure_file_stem = pathlib.PurePath(bname).stem
    pure_file_ext  = pathlib.PurePath(bname).suffix
    file_name = pure_file_stem
    file_ext  = pure_file_ext
    self.log.debug("file_name : " + file_name + " extension :" + file_ext +":")
    if self.ignore_blank_extension:
      if "" == file_ext:
        self.log.debug("IGNORE BLANK EXTENSION")
        return
    # endregion extension

    for reg in self.ignore_dir_regex_list:
      import re
      p = re.compile(reg, re.IGNORECASE)
      m = p.fullmatch(event.src_path)
      #self.log.debug("REG: " + reg)
      if m != None:
        self.log.debug("MATCH(bypass): " + event.src_path + " with " + reg)
        return

    # target_path = ''
    target_path = event.src_path

    if 'modified' == event.event_type:
      target_path = event.src_path
      self.log.debug(target_path + " " + event.event_type + " --> process")
    # elif 'moved' == event.event_type:
    #   #sqlite3.fileinfo_delete(event.src_path)
    #   target_path = event.dest_path
    #   self.log.info(event.src_path + " " + event.dest_path + " " + event.event_type + " --> process")
    # elif 'deleted' == event.event_type:
    #   target_path = event.src_path
    #   #sqlite3.fileinfo_delete(event.src_path)
    #   self.log.info(target_path + " " + event.event_type + " --> pass")
    #   return
    # elif 'created' == event.event_type:
    #   target_path = event.src_path
    #   self.log.info(target_path + " " + event.event_type + " --> pass")
    #   return
    else:
      target_path = event.src_path
      self.log.debug(target_path + " " + event.event_type + " --> pass")
      return

    #self.log.info(target_path + " " + event.event_type)
    #TODO is enqueued -> return

    # if None == MyLoggerTrick.dscs_dll:
    #   return
    (retvalue, retstr) = lib_dscsdll.Dscs_dll.static_checkDSCSAgent(self.log, self.dscsdll_file_name)
    if -1 == retvalue:
      return            # DSCSIsEncryptedFile is not Callable.
    else:
      pass              # DSCSIsEncryptedFile is Callable.

    try:
      sqlite3 = lib_sqlite3.csqlite3(file_path=self.sqlite_db_filepath, log=self.log)

      if sqlite3.except_fileinfo_hasmatch(target_path):
        self.log.info("### except_fileinfo_hasmatch : true : " + target_path)
        return

      if sqlite3.schedule_fileinfo_hasmatch(target_path):
        self.log.info("### schedule_fileinfo_hasmatch : true : " + target_path)
        return

      import os
      filesize = os.path.getsize(target_path)
      if filesize < self.minimum_filesize:
        self.log.error(target_path + " filesize too small: " + str(filesize))
        return

      ret = lib_dscsdll.Dscs_dll.static_DSCSIsEncryptedFile(log=self.log, dscsdll_file_name=self.dscsdll_file_name, filepath=target_path)
      if 1 == ret:
        self.log.info("file call_DSCSIsEncryptedFile : " +target_path + ", " + str(ret) + '(암호화된 문서)')
        if filesize >= int(self.queue_size_limit):
          self.log.info("" +target_path + ", file size: " + str(filesize) + ", queue limit:" + str(self.queue_size_limit))
          return
        sqlite3.fileinfo_insert_with_size(target_path, filesize)
        self.log.info("file enqueued : " + target_path + ", " + str(ret) + '(암호화된 문서)')
      elif -1 == ret:
        self.log.info("file call_DSCSIsEncryptedFile : " +target_path + ", " + str(ret) + '(C/S 연동 모듈 로드 실패)')
      elif 0 == ret:
        self.log.info("file call_DSCSIsEncryptedFile : " +target_path + ", " + str(ret) + '(일반 문서)')
      else:
        self.log.info("file call_DSCSIsEncryptedFile : " +target_path + ", " + str(ret))

    except FileNotFoundError as e:
      self.log.error('FileNotFoundError  ' + str(e))
      return
    except PermissionError as e:
      self.log.error('PermissionError ' + str(e))
      return
    except Exception as e:
      self.log.error('Exception ' + str(e))
      return
    finally:
      del sqlite3

  def on_any_event(self, event):
    try:
      self.do_main(event)
    except Exception as e:
      import traceback
      self.log.error(traceback.format_exc())
      self.log.error(str(e))

def parse_patterns(patterns_spec, ignore_patterns_spec, separator=';'):
    """
    Parses pattern argument specs and returns a two-tuple of
    (patterns, ignore_patterns).
    """
    patterns = patterns_spec.split(separator)
    ignore_patterns = ignore_patterns_spec.split(separator)
    if ignore_patterns == ['']:
        ignore_patterns = []
    return (patterns, ignore_patterns)

def observe_with(log, observer, event_handler, pathnames):#, recursive, myservice):
  log.info("observe_with")
  log.info(pathnames)
  for pathname in set(pathnames):
    observer.schedule(event_handler, pathname, True)
  observer.start()
  observer_started = True

if '__main__' == __name__:
  from watchdog.watchmedo import main 
  main()
  print("module test")
