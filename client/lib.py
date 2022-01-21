import os
import pathlib
import psutil
import json

def lib_getwinuserhome():
	result = pathlib.Path.home()
	return result

def lib_getwindir():
	result = os.getenv('WINDIR')
	return result

def lib_virtual_memory():
    ret = psutil.virtual_memory()
    #virtual_mem_dict = dict(ttutil_virtual_memory()._asdict())
    return str(ret.percent)

def lib_cpu_usage():
    return str(psutil.cpu_percent())

def lib_net_io_counters():
    ret = psutil.net_io_counters()
    result = {
        "bytes_sent": ret.bytes_sent,
        "bytes_recv": ret.bytes_recv,
        "packets_sent":ret.packets_sent,
        "packets_recv":ret.packets_recv,
        "errin":ret.errin,
        "errout":ret.errout,
        "dropin":ret.dropin,
        "dropout":ret.dropout,
    }
    #print("SENT: "+str(sent))
    return json.dumps(result)

def lib_disk_usage():
    #return psutil.disk_usage('/')
    return str(psutil.disk_usage('/')[3])
