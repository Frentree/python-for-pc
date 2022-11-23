import logging
import logging.handlers
import ctypes

OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW

class DbgViewHandler(logging.Handler):
  def emit(self, record):
    PREFIX_FOR_FILTERING = "[TT]"
    record = self.format(record)
    record_list = record.split('\n')
    for record_item in record_list:
      OutputDebugString(PREFIX_FOR_FILTERING+record_item)

# log = logging.getLogger("output.debug.string.example")

def init_log(logging_level, logfile_setting = None):
  #from importlib import reload
  #logging.shutdown()
  #reload(logging)

  fmt = logging.Formatter(fmt='%(asctime)s.%(msecs)03d [%(thread)5s] %(levelname)-8s %(filename)-20s %(funcName)-20s %(lineno)d %(message)s', datefmt='%Y:%m:%d %H:%M:%S')

  log = logging.getLogger("output.debug.string.example")
  if None == logging_level:
    logging_level = logging.INFO
  log.setLevel(logging_level)

  # "OutputDebugString\DebugView"
  ods = DbgViewHandler()
  ods.setLevel(logging_level)
  ods.setFormatter(fmt)
  log.addHandler(ods)

  # "Console"
  con = logging.StreamHandler()
  con.setLevel(logging_level)
  con.setFormatter(fmt)
  log.addHandler(con)

  # log file
  if None != logfile_setting:
    import datetime
    logfilename = datetime.datetime.now().strftime(logfile_setting['logfile_path'] + "\\" + "log.txt")#"%Y%m%d.txt")
    fos = logging.handlers.RotatingFileHandler(filename=logfilename, maxBytes=logfile_setting['logfile_maxbytes'], backupCount=logfile_setting['logfile_backupcount'])
    fos.setLevel(logging_level)
    fos.setFormatter(fmt)
    log.addHandler(fos)
    log.fos = fos

  log.ods = ods
  log.con = con

  return log

def setLogLevel(log, logging_level):
  log.setLevel(logging_level)

  log.ods.setLevel(logging_level)
  log.con.setLevel(logging_level)
  if hasattr(log, 'fos'):
    log.fos.setLevel(logging_level)