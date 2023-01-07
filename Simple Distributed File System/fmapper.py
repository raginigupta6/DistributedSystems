from pprint import pprint
from util import *


class DFile:
    def __init__(self, _name_, _version_, _replicas_):
        self.name = _name_
        self.version = _version_
        self.replicas = _replicas_


class FileMapper:
    """This is the mapper to track the global file metadata"""
    def __init__(self):
        # ID mapper: server id -> all stored fids 
        self.server_to_fs = {i: set() for i in range(1, 11)}
        # File meta info: fid -> DFile
        self.f_info = {}  

    def show_file_info(self, fid):
        print("file name: %s,\tversion: %d,\tfid: %d" % (self.f_info[fid].name, self.f_info[fid].version, fid))

    def show(self):
        print("Server to files mapping:")
        pprint(self.server_to_fs)
        print("\nAll the files being tracked:")
        for f in self.f_info:
            print("\tfile name: %s,\tversion: %d,\tfid: %d\treplicas: " % (self.f_info[f].name, self.f_info[f].version, f))
            pprint(self.f_info[f].replicas)
        # pprint(self.f_info)

    def insert(self, f_name, servers):
        """Given a sdfs file and replicas, insert the file to all these replicas."""
        f_hv = hash_file_name(f_name)
        for server in servers:
            self.server_to_fs[server].add(f_hv)

        # If it is a newly incoming file, add it to the server's file info.
        if f_hv not in self.f_info:
            self.f_info[f_hv] = DFile(f_name, 0, set())

        # version update
        self.f_info[f_hv].version += 1
        self.f_info[f_hv].replicas |= servers

    def delete(self, f_hv):
        """Delete the file info in the mapper."""
        # f_hv = hash_file_name(f_name)
        replicas = get_replicas(get_coordinator_num(f_hv))
        for server in replicas:
            self.server_to_fs[server].discard(f_hv)

        if f_hv in self.f_info:
            del self.f_info[f_hv]
