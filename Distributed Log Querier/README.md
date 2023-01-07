# cs425-mp

This program is written in Python language. 

## Running the Distributed Log Querier:
On Server:
1. Run the server.py file on each server machine and keep it alive s.t. is it waiting for incoming connection from the Client Querier. E.g.
> python3 Server.py
2. The Server runs a local grep command on receiving connection from the Client and returns the output. 

On Client:
1. Run client.py and pass the argument as "-Ec" or "-c" followed by the PATTERN (this is similar to running the grep command on UNIX). E.g.
> python3 client.py "-Ec ([tT]hompson)|(sawyer).com*" 


> python3 client.py "-c www.thompson.com" 
2. The Client will return the output same as GREP command that includes the number of lines matching from each Log file of VM and total number of matching lines across all  VMs. 
3. The Client also returns the total query latency. 

For Unit Testing:
1. Run LogGen_UnitTest.py file that generates log file for each VM with frequent, rare, somewhat frequent, unique (only on one machine), and common (on all machines) patterns. The generated log file are in the format TestLog.xx.log (xx: machine number).
2. It also maintains a count file, Patterns_Count.txt that keeps count of each type of pattern to verify that Log querier returns the correct output. 
3. UnitTest.py is used for writing test cases to verify the output for frequent, rare, and somehwat_frequent patterns that were generated using LogGen_UnitTest.py.


## Authors and acknowledgment
Ragini Gupta and Yinfang Chen 

NETID: raginig2 and yinfang3 

CS 425, MP-1
