import logging
import datetime

log = logging.getLogger()
logfilename = datetime.datetime.now().strftime("%Y%m%d.txt")
log.addHandler(logging.FileHandler(filename=logfilename))

log.error("error logging test")
