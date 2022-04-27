import logging
import ctypes

# output "logging" messages to DbgView via OutputDebugString (Windows only!)
OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW

class DbgViewHandler(logging.Handler):
    def emit(self, record):
        PREFIX_FOR_FILTERING = "[TT]"
        record = self.format(record)
        record_list = record.split('\n')
        for record_item in record_list:
            OutputDebugString(PREFIX_FOR_FILTERING+record_item)

log = logging.getLogger("output.debug.string.example")

def config_logging(logging_level):
    if None == logging_level:
        logging_level = logging.INFO
    log.setLevel(logging_level)

    # format
    fmt = logging.Formatter(fmt='%(asctime)s.%(msecs)03d [%(thread)5s] %(levelname)-8s %(filename)-20s %(funcName)-20s %(lineno)d %(message)s', datefmt='%Y:%m:%d %H:%M:%S')

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

    log.ods = ods
    log.con = con

def setLogLevel(level):
    log.ods.setLevel(level)
    log.con.setLevel(level)