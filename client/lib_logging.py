import logging
import ctypes

# output "logging" messages to DbgView via OutputDebugString (Windows only!)
OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW

class DbgViewHandler(logging.Handler):
    def emit(self, record):
        PREFIX_FOR_FILTERING = "[TT]"
        OutputDebugString(PREFIX_FOR_FILTERING+self.format(record))

log = logging.getLogger("output.debug.string.example")
def config_logging():
 
    # format
    fmt = logging.Formatter(fmt='%(asctime)s.%(msecs)03d [%(thread)5s] %(levelname)-8s %(funcName)-20s %(lineno)d %(message)s', datefmt='%Y:%m:%d %H:%M:%S')

    log.setLevel(logging.DEBUG)
    #log.setLevel(logging.INFO)

    # "OutputDebugString\DebugView"
    ods = DbgViewHandler()
    ods.setLevel(logging.DEBUG)
    ods.setFormatter(fmt)
    log.addHandler(ods)

    # "Console"
    con = logging.StreamHandler()
    con.setLevel(logging.DEBUG)
    con.setFormatter(fmt)
    log.addHandler(con)
