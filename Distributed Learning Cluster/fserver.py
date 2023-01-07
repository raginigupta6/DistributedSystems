from pprint import pprint
from fmapper import FileMapper, DFile
import logging
from node import Detector
from util import *
import subprocess
import json
import shutil
import threading
import random
import time

# Create and configure logger
logging.basicConfig(filename="sdfs.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class FServer:
    def __init__(self, host, port):
        # init default SDFS path
        if os.path.exists(SDFS_DIR_PATH):
            # Wipes all file block/replicas it is storing before it rejoins.
            for f in os.listdir(SDFS_DIR_PATH):
                os.remove(os.path.join(SDFS_DIR_PATH, f))
        else:
            os.mkdir(SDFS_DIR_PATH)
        self.id = int(extract_vm_num_x())
        self.host = host
        self.port = port
        self.fm = FileMapper()
        self.failure_detector = Detector(socket.gethostname(), DETECTOR_PORT)
        self.failure_detector.join()

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((self.host, self.port))
            while 1:
                data, server = s.recvfrom(4096)
                if data:
                    msg = json.loads(data.decode())
                    msg_type = msg['type']
                    pprint(msg)
                    if msg_type == 'PUT':
                        self.put_handler(msg)
                    elif msg_type == 'DELETE':
                        self.delete_handler(msg)
                    elif msg_type == 'FAILED':
                        self.failure_handler(msg)

    def failure_handler(self, msg):
        server_to_fs = self.fm.server_to_fs
        file_info = self.fm.f_info
        logger.info("Receive a FAILED msg.")
        failed_server_id = int(extract_vm_num(msg['host']))
        num_live_servers = msg['num_server_live']
        live_servers = msg['live_servers']
        for f in server_to_fs[failed_server_id]:
            reps = file_info[f].replicas
            f_name = file_info[f].name
            reps.discard(failed_server_id)
            # if num_live_servers >= 4:
            # If the current server has the replica, 
            #   then we should decide whether it is responsible for re-replicate.
            if len(reps) > 0:
                if self.id == min(reps):
                    # TODO: Debug
                    repls = list(map(from_vm_num_to_host, reps))
                    candidate = random.choice(list(set(live_servers) - set(repls)))
                    # print(live_servers)
                    # print(reps)
                    # print(candidate)
                    target_host = candidate
                    # file name starts with f_name will all be replicated
                    for file_to_rep in os.listdir(SDFS_DIR_PATH):
                        if file_to_rep.startswith(f_name):
                            file_path = os.path.join(SDFS_DIR_PATH, file_to_rep)
                            # scp to the candidate server
                            if os.path.isfile(file_path):
                                dst = 'raging2' + '@' + target_host + ':' + file_path
                                subprocess.Popen(['scp', file_path, dst])
                            # Send update msg
                            can_num = int(extract_vm_num(candidate))
                            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as ss:
                                put_msg = {
                                    'type': 'PUT',
                                    'fid': f,
                                    'fname': f_name,
                                    'replicas': list({can_num} | reps),
                                    'version': self.fm.f_info[f].version,
                                }
                                for host in HOSTS:
                                    ss.sendto(json.dumps(put_msg).encode(), (host, SDFS_PORT))
        server_to_fs[failed_server_id] = set()

    def put_handler(self, msg):
        logger.info("Receive a PUT msg.")
        fid = msg['fid']
        f_name = msg['fname']
        replicas = set(msg['replicas'])
        for replica in replicas:
            self.fm.server_to_fs[replica].add(fid)
        if fid not in self.fm.f_info:
            self.fm.f_info[fid] = DFile(f_name, 0, set())

        self.fm.f_info[fid].version = msg['version']
        self.fm.f_info[fid].replicas |= replicas
        self.fm.show()

    def put_op(self, local_file_name, sdfs_file_name):
        if not file_exist(local_file_name):
            return
        # f_info = self.fm.f_info
        h_fn = hash_file_name(sdfs_file_name)
        coor = get_coordinator_num(h_fn)

        if h_fn in self.fm.f_info:
            to_replicas = self.fm.f_info[h_fn].replicas
            version = self.fm.f_info[h_fn].version + 1
        else:
            to_replicas = get_replicas(coor)
            version = 1
        print('Put file %s to %s.' % (local_file_name, sdfs_file_name))

        for vm_id in to_replicas:
            dst_path = os.path.join(SDFS_DIR_PATH, sdfs_file_name + "-" + str(version))
            target_host = from_vm_num_to_host(vm_id)
            if target_host == socket.gethostname():
                shutil.copy(local_file_name, dst_path)
            else:
                dst_str = 'raginig2@' + target_host + ':' + dst_path
                subprocess.Popen(['scp', local_file_name, dst_str])
        self.fm.insert(sdfs_file_name, to_replicas)

        # self.fm.show()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            put_msg = {
                'type': 'PUT',
                'fid': h_fn,
                'fname': sdfs_file_name,
                'coordinator': coor,
                'replicas': list(to_replicas),
                'version': self.fm.f_info[h_fn].version,
            }
            for h in HOSTS:
                s.sendto(json.dumps(put_msg).encode(), (h, SDFS_PORT))

    def get_op(self, sdfs_file_name, local_file_name):
        # print(sdfs_file_name)
        h_fn = hash_file_name(sdfs_file_name)
        coor = get_coordinator_num(h_fn)
        # print(h_fn)
        # pprint(self.fm.f_info)
        if h_fn not in self.fm.f_info:
            print('%s is not in SDFS.' % sdfs_file_name)
            return
        replicas = self.fm.f_info[h_fn].replicas
        version = self.fm.f_info[h_fn].version
        print('Going to fetch file %s to %s.' % (sdfs_file_name, local_file_name))
        src_path = os.path.join(SDFS_DIR_PATH, sdfs_file_name + "-" + str(version))
        if self.id in replicas:
            shutil.copy(src_path, local_file_name)
        else:
            target_host = from_vm_num_to_host(list(replicas)[0])
            src_str = 'yinfang3@' + target_host + ':' + src_path
            subprocess.Popen(['scp', src_str, local_file_name])
    
    def get_op_v(self, sdfs_file_name, ver, local_file_name):
        h_fn = hash_file_name(sdfs_file_name)
        coor = get_coordinator_num(h_fn)
        num_versions_to_get = int(ver)

        if h_fn not in self.fm.f_info:
            print('%s is not in SDFS.' % sdfs_file_name)
            return
        replicas = self.fm.f_info[h_fn].replicas
        version = self.fm.f_info[h_fn].version
        if num_versions_to_get > version:
            # TODO: Then get all of them.
            # print('Version of %s is smaller than the wanted.' % sdfs_file_name)
            # return
            num_versions_to_get = version
        for i in range(num_versions_to_get):
            local_file_name_v = local_file_name + "-" + str(version - i)
            src_path = os.path.join(SDFS_DIR_PATH, sdfs_file_name + "-" + str(version - i))
            if self.id in replicas:
                shutil.copy(src_path, local_file_name_v)
            else:
                target_host = from_vm_num_to_host(list(replicas)[0])
                src_str = 'raginig2@' + target_host + ':' + src_path
                subprocess.Popen(['scp', src_str, local_file_name_v])

    def delete_handler(self, msg):
        logger.info("Receive a DELETE msg.")
        fid = msg['fid']
        self.fm.delete(fid)

        sdfs_file_name = msg['fname']
        f_path = os.path.join(SDFS_DIR_PATH, sdfs_file_name)
        if file_exist(f_path):
            os.remove(f_path)

    def delete_op(self, sdfs_file_name):
        h_fn = hash_file_name(sdfs_file_name)
        coor = get_coordinator_num(h_fn)

        # Delete in the local file mapper.
        self.fm.delete(h_fn)

        # Delete in all servers' file mapper.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            delete_msg = {
                'type': 'DELETE',
                'fid': h_fn,
                'fname': sdfs_file_name,
            }
            for h in HOSTS:
                s.sendto(json.dumps(delete_msg).encode(), (h, SDFS_PORT))
        
    def store_local(self):
        for fid in self.fm.server_to_fs[self.id]: 
            self.fm.show_file_info(fid)
    
    def store_all(self):
        self.fm.show()
    
    def ls_op(self, fn):
        fid = hash_file_name(fn)
        print('%s is stored in server:' % fn)
        try:
            print(self.fm.f_info[fid].replicas)
        except KeyError as e:
            print("Try to check whether you are inputing the correct file name: %s" % str(e))

    def controller(self):
        helper = '''
        ******************************************************
        * put localfilename sdfsfilename
        * get sdfsfilename localfilename
        * delete sdfsfilename
        * ls sdfsfilename
        * store
        * get-versions sdfsfilename num-versions localfilename 
        * list_mem
        * join
        * leave
        * list_self       
        ******************************************************
        '''
        print(helper)
        while 1:
            arg = input('-->')
            args = arg.split(' ')
            if arg == 'help':
                print(helper)
            elif arg.startswith('put'):
                if len(args) != 3:
                    logger.error('Argument format error when doing a put operation: %s.' % arg)
                    print('put local_file_name sdfs_file_name')
                    continue
                self.put_op(args[1], args[2])
            elif arg.startswith('get-versions'):
                if len(args) != 4:
                    logger.error('Argument format error when doing a get-versions operation: %s.' % arg)
                    print('Argument format error when doing a get-versions operation.')
                    continue
                self.get_op_v(args[1], args[2], args[3])
            elif arg.startswith('get'):
                if len(args) != 3:
                    logger.error('Argument format error when doing a get operation: %s.' % arg)
                    print('Argument format error when doing a get operation.')
                    continue
                self.get_op(args[1], args[2])
            elif arg.startswith('delete'):
                if len(args) != 2:
                    logger.error('Argument format error when deleting a file: %s.' % arg)
                    print('Argument format error when deleting a file.')
                    continue
                self.delete_op(args[1])
            elif arg.startswith('ls'):
                if len(args) != 2:
                    logger.error('Argument format error when doing ls: %s.' % arg)
                    print('Argument format error when doing ls.')
                    continue
                self.ls_op(args[1])
            elif arg.startswith('store_all'):
                self.store_all()
            elif arg.startswith('store'):
                self.store_local()
            elif arg == 'list_mem':
                self.failure_detector.show_mem_list()
            elif arg == 'join':
                self.failure_detector.join()
            elif arg == 'leave':
                self.failure_detector.leave()
            elif arg == 'list_self':
                print(self.failure_detector.id)
            else:
                print('Invalid arguments: %s' % arg)
                logger.error('Invalid arguments: %s' % arg)

    def executor(self):
        while 1:
            time.sleep(3)
            print("Forever loop")
            for fname in os.listdir('sdfs'):
                print("Executor Running")
                if ".sh" in fname:
                    # Run the model
                    print("Trying to execute the file: %s" % fname)
                    p = subprocess.Popen(['sh', 'exes/' + fname])
                    p.wait()
                    os.remove('exes/' + fname)

    def run(self):
        self.failure_detector.exe()

        receiver_thread = threading.Thread(target=self.listen)
        controller_thread = threading.Thread(target=self.controller)
        executor_thread = threading.Thread(target=self.executor)

        receiver_thread.start()
        controller_thread.start()
        executor_thread.start()
        receiver_thread.join()
        controller_thread.join()


if __name__ == "__main__":
    # print(socket.gethostname())
    # exit()
    fs = FServer(socket.gethostname(), SDFS_PORT)
    fs.run()
