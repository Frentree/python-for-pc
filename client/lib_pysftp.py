import pysftp
import datetime
import zipfile

myHostname = "183.107.9.230"
myUsername = "gen"
myPassword = "rhehfl123"


fantasy_zip = zipfile.ZipFile('ftclient_installer.zip', 'w')

fantasy_zip.write('..\\00.RELEASE\\configuration.json', 'configuration.json', compress_type = zipfile.ZIP_DEFLATED)
fantasy_zip.write('..\\00.RELEASE\\install.exe', 'install.exe', compress_type = zipfile.ZIP_DEFLATED)
fantasy_zip.write('..\\00.RELEASE\\uninstall.exe', 'uninstall.exe', compress_type = zipfile.ZIP_DEFLATED)
fantasy_zip.write('..\\00.RELEASE\\package.exe', 'package.exe', compress_type = zipfile.ZIP_DEFLATED)

fantasy_zip.close()
import sys
sys.exit(0)


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




