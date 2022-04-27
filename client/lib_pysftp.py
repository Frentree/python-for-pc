import pysftp
import datetime

myHostname = "183.107.9.230"
myUsername = "gen"
myPassword = "rhehfl123"

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
with pysftp.Connection(host=myHostname, port=2223, username=myUsername, password=myPassword, cnopts=cnopts) as sftp:
    print("Connection succesfully stablished ... ")

    # Switch to a remote directory
    sftp.cwd('/var/www/html/2022.04.27_ftclient')

    # Obtain structure of the remote directory '/var/www/vhosts'
    directory_structure = sftp.listdir_attr()

    filename = datetime.datetime.now().strftime("/var/www/html/2022.04.27_ftclient/installer_%H%M%S.exe")
    sftp.put('C:\\Users\\Admin\\Desktop\\repos\\GitHub\\python-for-pc\\client\\dist\\installer.exe',
      filename)

    # Print data
    for attr in directory_structure:
        print(attr.filename, attr)

# connection closed automatically at the end of the with statement




