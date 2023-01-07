# Server
import socket
import re
import sys
import json
import errno
import subprocess

host      = socket.gethostname()
port      = 16666
path_to_f = "vm1.log"

def extract_vm_num():
    vm_num = host[13:15]
    if vm_num != "10":
        vm_num = vm_num[1]
    # print(vm_num)
    return vm_num


def construct_path_to_f():
    num = extract_vm_num()
    # print("vm"+num+".log")
    return "vm"+num+".log"


def run(host, port, path_to_f):
    # print(host)
    extract_vm_num()
    port_str = str(port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(2)
    while 1:
        print("Wait for incoming connection...")
        conn, addr = s.accept()
        with conn:
            print("Incoming connection from: ", addr)
            try:
                received_data = conn.recv(1024)
                if received_data:
                    data_to_send = []
                    search_str = json.loads(received_data.decode())['pattern']
                    print("search_str: " + search_str)
                    # line_count_flag = False
                    # if "-c" in search_str:
                    #     line_count_flag = True
                    line_num = 0
                    print(path_to_f)
                    with open(path_to_f, 'r') as f:
                        try:
                            grep_l = ["/bin/grep"]
                            option_l = search_str.split(" ")
                            option_l.append(path_to_f)
                            cmd_l = grep_l + option_l
                            # output = subprocess.run(grep_l+option_l)
                            grep = subprocess.Popen(cmd_l, stdout=subprocess.PIPE)
                            lines = list(grep.stdout)
                            # print(lines)
                            for l in lines:
                                # print(l)
                                l = l.decode()
                                line_num += 1
                                data_to_send.append({
                                        'host': host,
                                        'port': port_str,
                                        'log_path': path_to_f,
                                        'line': l,
                                        'line_number': line_num,})
                        except Exception as e:
                            print(e)
                        finally: 
                            if data_to_send: 
                                try:  
                                    conn.sendall(json.dumps(data_to_send).encode())
                                except socket.error as error:
                                    if error.errno == errno.ECONNREFUSED:
                                        print("Error code when sending data: " + os.strerror(error.errno))
                                    else:
                                        raise
                        
                    f.close()
            except Exception as e:
                print("Server error: ", e.__str__())

if __name__ == "__main__":
    path_to_f = construct_path_to_f()
    run(host, port, path_to_f)

