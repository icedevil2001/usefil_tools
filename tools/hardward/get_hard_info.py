
from email.policy import default
import psutil
import platform
from datetime import datetime
# GPU information
import GPUtil
import click 
import json 
from pathlib import Path
try:
    from rich.pretty import pprint
    from rich import print
except:
    from pprint import pprint


def get_size(bytes, suffix="B")->str:
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


def system_info()-> dict:
    """OS system information"""
    uname = platform.uname()
    return {
        "System": uname.system,
        "Node Name": uname.node,
        "Release": uname.release,
        "Version": uname.version,
        "Machine": uname.machine,
        "Processor": uname.processor,
    }

def boot_time()-> dict:
    """Boot time or uptime """
    # Boot Time
    # print("="*40, "Boot Time", "="*40)
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    return {"Boot Time": f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"}

def cpu_info()-> dict:
    """CPU information"""
    data = {}
    # number of cores
    data["Physical cores"] = psutil.cpu_count(logical=False)
    data["Total cores"] = psutil.cpu_count(logical=True)
    # CPU frequencies
    cpufreq = psutil.cpu_freq()
    data["Max Frequency"] = f"{cpufreq.max:.2f}Mhz"
    data["Min Frequency"] = f"{cpufreq.min:.2f}Mhz"
    data["Current Frequency"] = f"{cpufreq.current:.2f}Mhz"
    return data

def cpu_usage()-> dict:
    """CPU usage information"""
    data = {}
    # print("CPU Usage Per Core:")
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
        data[f"Core {i}"] =  f"{percentage}%"
    data["Total CPU Usage"] = f"{psutil.cpu_percent()}%"
    return data

def memory_info()-> dict:
    """Memory/RAM information"""
    data = {}
    svmem = psutil.virtual_memory()
    data["Total"] = get_size(svmem.total)
    data["Available"] = get_size(svmem.available)
    data["Used"] = get_size(svmem.used)
    data["Percentage"] = f"{svmem.percent}%"
    return data

def swap_memory()-> dict:
    """swap memeory information"""
    data = {}
    swap = psutil.swap_memory()
    data["Total"] = get_size(swap.total)
    data["Free"] = get_size(swap.free)
    data["Used"] = get_size(swap.used)
    data["Percentage"] = f"{swap.percent}%"
    return data

def disk_info()-> dict:
    """Disc information including mount points"""
    data = {}
    # get all disk partitions
    partitions = psutil.disk_partitions()
    # print((partitions[0]._asdict()))
    for partition in partitions:
        # print(f">>> {partition}")
        data[partition.device] = {}
        info = data[partition.device]
        info["Mountpoint"] =  partition.mountpoint
        info["File system type"] = partition.fstype
        info['opts'] = partition.opts
        info['maxfile'] = partition.maxfile
        info['maxpath'] = partition.maxpath
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            # this can be catched due to the disk 
            continue
        info["Total Size"] =  get_size(partition_usage.total)
        info["Used"] = get_size(partition_usage.used)
        info["Free"] = get_size(partition_usage.free)
        info["Percentage"] = f"{partition_usage.percent}%"
        return data

def diskio()-> dict:
    """Disc IO statistics since boot"""
    data = {}
    disk_io = psutil.disk_io_counters()
    data["Total read"] = get_size(disk_io.read_bytes)
    data["Total write"] = get_size(disk_io.write_bytes)
    return data

def natwork_info()-> dict:
    """All network information (virtual and physical)"""
    data = {}
    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        data[interface_name] = {}
        info = data[interface_name]
        for address in interface_addresses:
            if str(address.family) == 'AddressFamily.AF_INET':
                info["IP Address"] =  address.address
                info["Netmask"] =  address.netmask
                info["Broadcast IP"] = address.broadcast
            elif str(address.family) == 'AddressFamily.AF_PACKET':
                info["MAC Address"] = address.address
                info["Netmask:"] = address.netmask
                info["Broadcast MAC"] = address.broadcast
    return data 

def io_stats()-> dict:
    """IO statistics since boot"""
    data = {}
    net_io = psutil.net_io_counters()
    data["Total Bytes Sent"] =  get_size(net_io.bytes_sent)
    data["Total Bytes Received"] =  get_size(net_io.bytes_recv)
    return data

def gpu_stats()-> dict:
    """GPU stats """
    ## GPU stats ##
    data = {"GPU":{}}
    info = data['GPU']
    gpus = GPUtil.getGPUs()
    list_gpus = []
    for gpu in gpus:
        info['gpu_id'] = gpu.id
        info['gpu_uuid'] = gpu.uuid
        info['gpu_name'] = gpu.name
        # get % percentage of GPU usage of that GPU
        info['gpu_load'] = f"{gpu.load * 100}%"
        info['gpu_free_memory'] = f"{gpu.memoryFree}MB"
        info['gpu_used_memory'] = f"{gpu.memoryUsed}MB"
        info['gpu_total_memory'] = f"{gpu.memoryTotal}MB"
        info['gpu_temperature']  = f"{gpu.temperature}°C"

    return data

@click.command()
@click.option(
    '--output', '-o',
    type=click.Path(file_okay=True, dir_okay=False),
    default=None,
    help='Output file path. returns json files '

    )
def hardware_info(output: Path) -> None:
    """
    Display hardware information of the local device
    \b
    """
    data = {}
    data['System Information'] = system_info()
    data['Boot Time'] = boot_time()
    data["CPU Information"] = cpu_info()
    data['CPU Usage Per Core'] = cpu_usage()
    data['Memory Information'] = memory_info()
    data['SWAP Memory'] = swap_memory()
    data['Disk Information'] = disk_info()
    data['Disk IO'] = diskio()
    data['Network Information'] = natwork_info()
    data['IO Stat'] = io_stats()
    data['gpu_stats'] = gpu_stats()

    if output:
        output  = Path(output)
        if not output.parent.exists():
            output.parent.mkdir(parents=True)
        with open(output.with_suffix('.json'), 'w') as fh:
            json.dump(data, fh, indent=4)

    pprint(data, expand_all=True)

if __name__ == "__main__":
    hardware_info()