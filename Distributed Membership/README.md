Run the script using the following command:

>> python3 node.py




This will periodically (every 1 second) continue printing the memebership list on the terminal. Node-1 is set as the introducer by default. In order to join/or leave the ring, the user has to enter the following input command:

1. join
2. leave

There are four status maintained for each of the nodes in the ring: Joining, Running, Failed and Left (voluntarily). By default, if the machine has not joined the ring it will show Left status. Time out interval is set to 2 seconds. 

Additional Files:

>>python3 node_benchmark.py 


This script is used for collecting measurements only. 


