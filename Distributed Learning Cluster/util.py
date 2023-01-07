import socket
import os


HOSTS = [
    "fa22-cs425-4201.cs.illinois.edu",  # Machine-01 of IP address-
    "fa22-cs425-4202.cs.illinois.edu",  # 02
    "fa22-cs425-4203.cs.illinois.edu",  # 03
    "fa22-cs425-4204.cs.illinois.edu",  # 04
    "fa22-cs425-4205.cs.illinois.edu",  # 05
    "fa22-cs425-4206.cs.illinois.edu",  # 06
    "fa22-cs425-4207.cs.illinois.edu",  # 07
    "fa22-cs425-4208.cs.illinois.edu",  # 08
    "fa22-cs425-4209.cs.illinois.edu",  # 09
    "fa22-cs425-4210.cs.illinois.edu",  # 10
]

DETECTOR_PORT = 20001
PORT_TO_USE = DETECTOR_PORT
SDFS_PORT = 20000
SDFS_DIR_PATH = os.path.expanduser('~/sdfs/')


def file_exist(fn):
    if os.path.exists(fn):
        return True
    else:
        print('Cannot find the file %s in the local machine.' % fn)
        return False


def extract_vm_num_x():
    localhost = socket.gethostname()
    vm_num = localhost[13:15]
    if vm_num != "10":
        vm_num = vm_num[1]
    # print(vm_num)
    return vm_num


def extract_vm_num(host):
    vm_num = host[13:15]
    if vm_num != "10":
        vm_num = vm_num[1]
    return vm_num


def from_vm_num_to_host(host_id):
    return 'fa22-cs425-42%02d.cs.illinois.edu' % host_id


def hash_file_name(f):
    return hash(f.strip().encode())


def get_coordinator_num(fn_h):
    """From node 1 to node 10"""
    return fn_h % 10 + 1


def get_replicas(co):
    """Get the file server replicas numbers - consistent hashing"""
    return set([co] + [(co + i) % 10 + 1 for i in range(0, 3)])
    # return set([1, 3])

