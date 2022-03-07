import logging
import datetime

logfilename = datetime.datetime.now().strftime("%Y%m%d.txt")

#logging.basicConfig(filename=logfilename)
log = logging.getLogger()
con = logging.FileHandler(filename=logfilename)
#con.setLevel(logging.DEBUG)
log.addHandler(con)

log.error("error logging test")

