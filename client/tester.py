import os
import sys
import json
import datetime
import zipfile
import pysftp
import datetime
import zipfile

if __name__ == '__main__':
  dir_path = "..\\00.RELEASE"
  os.chdir(dir_path)
  
  with open("env.json", 'r', encoding='utf-8-sig') as json_env_file:
    env_contents = json_env_file.read()
    env_dic = json.loads(env_contents)

  print(env_dic)

  cnopts = pysftp.CnOpts()
  cnopts.hostkeys = None
  filename = ""
  with pysftp.Connection(host=env_dic['myHostname'], port=2223, username=env_dic['myUsername'], password=env_dic['myPassword'], cnopts=cnopts) as sftp:
    print("Connection succesfully stablished ... ")

    # Switch to a remote directory
    #sftp.cwd('/var/www/html/2022.04.27_ftclient')
    sftp.cwd('/home/gen/workspace/DLL/DllProject/Server/downloads')

    # Obtain structure of the remote directory '/var/www/vhosts'
    directory_structure = sftp.listdir_attr()

    # Print data
    for attr in directory_structure:
      print(attr.filename, attr)

    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    sftp.get("update.zip", filename+".zip")
    zipfile.ZipFile(filename+".zip").extractall(filename)






  print(filename)
