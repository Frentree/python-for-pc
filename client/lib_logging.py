import logging
import ctypes

# output "logging" messages to DbgView via OutputDebugString (Windows only!)
OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW

class DbgViewHandler(logging.Handler):
    def emit(self, record):
        PREFIX_FOR_FILTERING = "[TT]"
        record = self.format(record)
        record = record.replace("\n", "")
        OutputDebugString(PREFIX_FOR_FILTERING+record)

log = logging.getLogger("output.debug.string.example")

def config_logging():

    # format
    fmt = logging.Formatter(fmt='%(asctime)s.%(msecs)03d [%(thread)5s] %(levelname)-8s %(filename)-20s %(funcName)-20s %(lineno)d %(message)s', datefmt='%Y:%m:%d %H:%M:%S')

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

    log.ods = ods
    log.con = con

def setLogLevel(level):
    log.ods.setLevel(level)
    log.con.setLevel(level)