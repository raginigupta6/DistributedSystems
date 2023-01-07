# Client
import time
import socket
import json
import sys
import threading  
import os
import re
import subprocess

HOSTS = [
    'fa22-cs425-4201.cs.illinois.edu',  # Machine-01 of IP address-
    'fa22-cs425-4202.cs.illinois.edu',  # 02
    'fa22-cs425-4203.cs.illinois.edu',  # 03
    'fa22-cs425-4204.cs.illinois.edu',  # 04
    'fa22-cs425-4205.cs.illinois.edu',  # 05
    'fa22-cs425-4206.cs.illinois.edu',  # 06
    'fa22-cs425-4207.cs.illinois.edu',  # 07
    'fa22-cs425-4208.cs.illinois.edu',  # 08
    'fa22-cs425-4209.cs.illinois.edu',  # 09
    'fa22-cs425-4210.cs.illinois.edu',  # 10
]

localhost = socket.gethostname()

def extract_vm_num():
    vm_num = localhost[13:15]
    if vm_num != "10":
        vm_num = vm_num[1]
    # print(vm_num)
    return vm_num


def construct_path_to_f():
    num = extract_vm_num()
    # print("vm"+num+".log")
    return "vm"+num+".log"


def local_grep(host, port, pattern, path_to_f):
    port_str = str(port)
    result = []
    # with open(path_to_f, 'r') as f:
    with open("%s.tmp" % host, 'w') as wf:
        line_num = 0
        grep_l = ["/bin/grep"]
        option_l = pattern.split(" ")
        option_l.append(path_to_f)
        cmd_l = grep_l + option_l
        # output = subprocess.run(grep_l+option_l)
        grep = subprocess.Popen(cmd_l, stdout=subprocess.PIPE)
        lines = list(grep.stdout)
        # print(lines)
        for l in lines:
            line_num += 1
            line = ' '.join([host, port_str, path_to_f, str(line_num), l.decode()])
            wf.write(line)
    wf.close()
    # f.close()


def run(pattern, host, port, local_path_to_f): 
    if host == localhost:
        print("Enter local grep..")
        local_grep(host, port, pattern, local_path_to_f)
        return 
    
    logs = [] 
    d    = {'pattern': pattern}  
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            data = json.dumps(d).encode()
            s.sendall(data)
            while 1:
                data = b''
                while 1:
                    _data = s.recv(4096)
                    if _data:
                        data += _data
                    else:
                        break
                if data:
                    res = json.loads(data.decode())
                    logs += res
                else:
                    break

            if logs:
                with open("%s.tmp" % host, 'w') as f:
                    for log in logs:
                        line = ' '.join([log.get("host", "#"),
                                        log.get("port", "#"),
                                        log.get("log_path", "#"),
                                        str(log.get("line_number", -1)),
                                        log.get("line", "#")])
                        f.write(line)
        except Exception as e:
            print("Encounter an error: ", e.__str__())
        # handle the client exception
        # except (OSError, socket.error) as e:
        #     print("Encounter an error: ", e.__str__())


def cleanup_tmp():
    for file in os.listdir(os.path.dirname(os.path.realpath(__file__))):
        if file.endswith('.tmp'):
            print("Cleanup old temporary file: %s" % file)
            os.remove(file)
    

def query(pattern, hosts, port, local_path_to_f):
    cleanup_tmp()
    threads = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            count_flag = False
            options = pattern.split(" ")[0]
            # print("options: " + options)
            if "c" in options:
                count_flag = True
            t_start = time.time()
            for host in hosts:
                threads.append(threading.Thread(target=run, args=(pattern, host, port, local_path_to_f)))
                threads[-1].start()
            for t in threads:                                                           
                t.join()  
            t_end = time.time() 
            running_time = t_end - t_start
            # get results from local-saved .tmp files
            d_cnt = {}
            for file in os.listdir(os.path.dirname(os.path.realpath(__file__))):
                cnt = 0
                if file.endswith('.tmp'):
                    with open(file, 'r') as f:
                        for line in f:
                            print(line, end='')
                            if count_flag:
                                cnt_str = line.split(" ")[-1]
                                # print(cnt_str)
                                cnt += int(cnt_str)
                            else:
                                cnt += 1
                    d_cnt[file.rstrip('.tmp')] = cnt

            print("\n**************************")
            total_lines = 0
            # line_count_flag = False
            # options = pattern.split(" ")[0]
            # print("options: " + options)
            for host, cnt in d_cnt.items():
                print('From host %s, %d lines matched.' % (host, cnt))
                total_lines += cnt
            print('Total lines: {} line, total time: {:.6f} secs.'.format(total_lines, running_time))
            # if not count_flag:
            #     for host, cnt in d_cnt.items():
            #         print('From host %s, %d lines matched.' % (host, cnt))
            #         total_lines += cnt
            #     print('Total lines: {} line, total time: {:.6f} secs.'.format(total_lines, running_time))
            # else:
            #     print('Total time: {:.6f} secs.'.format(running_time))

        except Exception as e:
                print('Error happens: ', e.__str__())


if __name__ == '__main__':
    if len(sys.argv) is not 2: 
        print("Number of arguments should be 1")
        exit()
    path_to_f = construct_path_to_f()
    # path_to_f = "test.txt"
    query(sys.argv[1], HOSTS, 16666, path_to_f)


