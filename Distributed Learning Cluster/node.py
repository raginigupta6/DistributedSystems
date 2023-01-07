import socket
import datetime
import threading
import json
import time
from enum import Enum
from util import *
from pprint import pprint

time_format_str = "%m/%d/%Y, %H:%M:%S"

# PORT_TO_USE = 16666
introducer = "fa22-cs425-4201.cs.illinois.edu"


def who_are_neighbors():
    vm_num = int(extract_vm_num_x())
    nb1 = (vm_num + 1 - 1) % 10
    nb2 = (vm_num + 2 - 1) % 10
    nb3 = (vm_num + 8 - 1) % 10
    nb4 = (vm_num + 9 - 1) % 10
    return [HOSTS[nb1], HOSTS[nb2], HOSTS[nb3], HOSTS[nb4]]


class PacketT(Enum):
    NONE = "NONE"
    PING = "PING"
    ACK = "ACK"
    JOIN = "JOIN"
    LEAVE = "LEAVE"


class State(Enum):
    JOINING = 1
    RUNNING = 2
    FAILED = 3
    LEFT = 4


class Packet:
    host = "host"
    port = "port"
    packet_t = "packet_t"
    body = "body"
    ID = "id"

    def __init__(self):
        pass


def return_now_str():
    return datetime.datetime.now().strftime(time_format_str)


class MemberList:
    def __init__(self, host_ip, host_id):
        self.dict = {
            host_ip: {
                "id": host_id,
                "state": State.LEFT.value,
                "timestamp": return_now_str()
            }
        }


def stringify_keys(d):
    """Convert a dict's keys to strings if they are not."""
    for key in d.keys():

        # check inner dict
        if isinstance(d[key], dict):
            value = stringify_keys(d[key])
        else:
            value = d[key]

        # convert nonstring to string if needed
        if not isinstance(key, str):
            try:
                d[str(key)] = value
            except Exception:
                try:
                    d[repr(key)] = value
                except Exception:
                    raise

            # delete old key
            del d[key]
    return d


class Detector:
    def __init__(self, host_ip, port):
        self.host = host_ip
        self.port = port
        self.id = host_ip + " " + return_now_str()
        self.nbs = who_are_neighbors()
        self.memlist = MemberList(host_ip, self.id)
        self.show_mem_list()
        self.failure_ack = set()
        self.liveness_list = {}
        self.local_mem_lock = threading.Lock()
        self.timer_lock = threading.Lock()

    def exe(self):
        ping_thread = threading.Thread(target=self.ping)
        timer_thread = threading.Thread(target=self.timer)
        listen_thread = threading.Thread(target=self.listener)

        ping_thread.start()
        listen_thread.start()
        timer_thread.start()

    def show_mem_list(self):
        print("****************************************")
        print("This is membership list of VM %s: " % extract_vm_num_x())
        for _, val in self.memlist.dict.items():
            print("%s [%s] [%s]" % (val["id"], State(val["state"]), val["timestamp"]))
        print("****************************************")

    def controller(self):
        while 1:
            command = input("\nInput the command:\n\n")
            if command == "list_mem":
                self.show_mem_list()
            elif command == "join":
                self.join()
            elif command == "leave":
                self.leave()
            elif command == "list_self":
                print(self.id)
            else:
                print("Invalid input: %s" % command)

    def is_introducer(self):
        return self.host == introducer

    def listener(self):
        mem_list = self.memlist.dict
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((self.host, self.port))
            while 1:
                try:
                    # Yinfang: needs to confirm whether a left node should receive msg or not
                    if mem_list[self.host]["state"] == State.LEFT.value:
                        continue

                    data, _ = sock.recvfrom(4096)
                    if data:
                        req = json.loads(data.decode())
                        # Debug the req:
                        # print(req)
                        req_t = req.get(Packet.packet_t, "Unknown")
                        if req_t == "Unknown":
                            print("!!!!!!!!!!!!!!!!!!!!!")
                            print("Invalid request type.")
                            print("!!!!!!!!!!!!!!!!!!!!!")
                            continue
                        # print("Incoming %s request from %s; Port: %s." % (
                        # req[Packet.packet_t], req[Packet.host], req[Packet.port]))
                        origin_ip = req[Packet.host]

                        now = return_now_str()

                        self.local_mem_lock.acquire()
                        # JOIN 
                        if req_t == PacketT.JOIN.value:
                            print("Incoming JOIN packet")
                            mem_list[origin_ip] = req[Packet.body]
                            mem_list[origin_ip]["state"] = State.JOINING.value
                            mem_list[origin_ip]["timestamp"] = now
                            # Broadcast the JOIN request to all nodes as introducer
                            if self.is_introducer():
                                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                                    join_msg = {
                                        Packet.host: origin_ip,
                                        Packet.port: PORT_TO_USE,
                                        Packet.packet_t: PacketT.JOIN.value,
                                        Packet.body: mem_list[origin_ip]
                                    }
                                    for host in HOSTS:
                                        if host != origin_ip and \
                                                host != self.host:
                                            s.sendto(json.dumps(join_msg).encode(), (host, PORT_TO_USE))
                        # PING 
                        elif req_t == PacketT.PING.value:
                            body = req[Packet.body]
                            for host in body:
                                if host not in mem_list:
                                    mem_list[host] = body[host]
                                    continue
                                prev = datetime.datetime.strptime(mem_list[host]["timestamp"], time_format_str)
                                curr = datetime.datetime.strptime(body[host]["timestamp"], time_format_str)
                                # Compare the timestamp to decide whether to add the host into member list
                                if curr > prev:
                                    mem_list[host] = body[host]
                                    # Construct ACK response back
                            ack_msg = {
                                Packet.host: self.host,
                                Packet.port: PORT_TO_USE,
                                Packet.body: mem_list[self.host],
                                Packet.packet_t: PacketT.ACK.value,
                            }
                            sock.sendto(json.dumps(ack_msg).encode(), (origin_ip, PORT_TO_USE))
                        # ACK 
                        elif req_t == PacketT.ACK.value:
                            mem_list[origin_ip] = req[Packet.body]
                            if origin_ip in self.liveness_list:
                                self.timer_lock.acquire()
                                # Clean the old time list
                                del self.liveness_list[origin_ip]
                                self.timer_lock.release()
                        # LEAVE
                        elif req_t == PacketT.LEAVE.value:
                            mem_list[origin_ip]["state"] = State.LEFT.value
                            mem_list[origin_ip]["timestamp"] = now

                        else:
                            print("Invalid request type received in listener function:")
                            pprint(req)
                        self.local_mem_lock.release()

                except Exception as e:
                    print(e)

    def ping(self):
        mem_list = self.memlist.dict
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            while 1:
                try:
                    # self.show_mem_list()
                    time.sleep(1)

                    if mem_list[self.host]["state"] == State.LEFT.value:
                        continue

                    self.local_mem_lock.acquire()
                    mem_list[self.host]["timestamp"] = return_now_str()
                    mem_list[self.host]["state"] = State.RUNNING.value

                    # Send PING req to neighbours
                    for host in self.nbs:
                        # Do not send to host not in list or left nodes
                        if (host not in mem_list) or \
                                (host in mem_list) and (mem_list[host]["state"] == State.LEFT.value):
                            continue
                        ping_req = {
                            Packet.packet_t: PacketT.PING.value,
                            Packet.host: self.host,
                            Packet.port: self.port,
                            Packet.body: mem_list
                        }
                        s.sendto(json.dumps(ping_req).encode(), (host, self.port))

                        # Update the liveness_list for timer thread
                        if host in mem_list and host not in self.liveness_list:
                            self.timer_lock.acquire()
                            self.liveness_list[host] = datetime.datetime.now()
                            self.timer_lock.release()
                    self.local_mem_lock.release()
                except Exception as e:
                    print(e)

    def join(self):
        mem_list = self.memlist.dict
        if self.is_introducer():
            print("This is an introducer.")
        mem_list[self.host]["id"] = self.host + " " + return_now_str()
        mem_list[self.host]["state"] = State.RUNNING.value
        mem_list[self.host]["timestamp"] = return_now_str()
        if not self.is_introducer():
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                print("Send join request to introducer.")
                join_msg = {
                    Packet.packet_t: PacketT.JOIN.value,
                    Packet.host: self.host,
                    Packet.port: self.port,
                    Packet.body: mem_list[self.host],
                }
                s.sendto(json.dumps(stringify_keys(join_msg)).encode(), (introducer, PORT_TO_USE))

    def leave(self):
        mem_list = self.memlist.dict
        if mem_list[self.host]["state"] != State.RUNNING.value:
            print("Cannot leave in the state: %s." % mem_list[self.host]["state"])
            return
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            print("Send leave request to all the neighbours.")
            leave_msg = {
                Packet.packet_t: PacketT.LEAVE.value,
                Packet.host: self.host,
                Packet.port: self.port,
            }
            for host in self.nbs:
                s.sendto(json.dumps(leave_msg).encode(), (host, PORT_TO_USE))
            mem_list[self.host]["state"] = State.LEFT.value
        print("%s leaves." % self.host)

    def collect_live_server(self):
        mem_list = self.memlist.dict
        live_servers = set()
        for host in list(mem_list.keys()):
            if mem_list[host]['state'] == State.RUNNING.value:
                live_servers.add(host)
        # print("In collect_live_server:")
        # print(live_servers)
        return live_servers

    def timer(self):
        mem_list = self.memlist.dict
        liveness_list = self.liveness_list
        while 1:
            try:
                self.timer_lock.acquire()
                for host in list(liveness_list.keys()):
                    now = datetime.datetime.now()
                    elapse = now - liveness_list[host]
                    if elapse.seconds > 2.:
                        if (host in mem_list) and \
                                (mem_list[host]["state"] not in {State.FAILED.value, State.LEFT.value}):
                            # print("Timeout for host %s from timer." % host, elapse)
                            mem_list[host]["state"] = State.FAILED.value
                            mem_list[host]["timestamp"] = now.strftime(time_format_str)
                        del liveness_list[host]
                self.timer_lock.release()
            except Exception as e:
                print(e)

            for host in list(mem_list.keys()):
                time.sleep(0.2)
                delta = datetime.datetime.now() - datetime.datetime.strptime(mem_list[host]['timestamp'], time_format_str)
                if host not in self.failure_ack:
                    if mem_list[host]['state'] == State.FAILED.value and delta.days >= 0 \
                            and delta.seconds > 6.:
                        live_servers = self.collect_live_server()
                        # print(live_servers)
                        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                            failed_msg = {
                                'type': 'FAILED',
                                'host': host,
                                'num_server_live': len(live_servers),
                                'live_servers': list(live_servers),
                            }
                            # print("live server: ")
                            # pprint(list(live_servers))
                            s.sendto(json.dumps(failed_msg).encode(), (self.host, SDFS_PORT))
                        self.failure_ack.add(host)

# if __name__ == "__main__":
#     node = Detector(socket.gethostname(), PORT_TO_USE)
#     node.exe()
    # print(localhost)
