import logging
import tempfile
import time
import subprocess

#logging_filename = tempfile.gettempdir()+"\\ftservice.log"
logging_filename = "c:"+"\\ftservice.log"
#logging_filename = "C:\\Users\\danny\\AppData\\Local\\Temp\\ftservice.log"
#logging_filename = tempfile.gettempdir()+"\\ftservice.log"

logging.basicConfig(
	filename = logging_filename,
	level = logging.DEBUG,
	format = '%(asctime)s %(levelname)-7.7s %(message)s',
)

#[[ log message to console
console = logging.StreamHandler()

console.setLevel(logging.DEBUG)
#console.setLevel(logging.INFO)

# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s %(levelname)-7.7s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger().addHandler(console)
#]] log message to console

def logging_open_logfile():
	print(logging_filename)
	programName = "notepad.exe"
	subprocess.Popen([programName, logging_filename])

def logging_truncate_logfile():
	# Open the file
	file_handle = open(logging_filename, "r+")

	# Now truncate the file
	file_handle.truncate()

def log(msg):
	logging.info(msg)

#logging_filename = tempfile.gettempdir()+"\\ftservice.log"
#logging_filename = "c:"+"\\ftservice.log"
#def log(msg):
#    try:
#        with open(logging_filename, 'a') as f:
#            f.write(str(msg) + "\n")
#    except Exception as e:
#        print(e)
#    print(msg)





