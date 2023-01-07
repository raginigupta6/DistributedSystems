import random
import string
import datetime
import time
import socket
import sys


from faker import Faker
faker = Faker()  ## using Faker package to generate random IP addresses for the Log files
ip_addr = faker.ipv4()



## Create a dictionary to have a sum of each type of pattern across all log files
count_dictionary={'rare_odd':0, 'rare_even':0, 'rare_regular': 0, 'somewhat_frequent':0, 'frequent':0, 'unique':0, 'common':0 }
def log_generator(name_file, Number_lines, Number_machine):
	"""
	This function will generate a log file for the machine.

	Params:
	1. name_file: Log file
	2. Number_lines: # of lines in Log file
	3. Machine #: Log file's respective machine
	"""


	with open(name_file, 'w') as file:
		for k in range(Number_lines):
			rand_number= random.uniform(0, 1)

			#  rare pattern
			if rand_number<= 0.02:
				## Pattern only found on odd number machines
				if Number_machine % 3 == 0:
					file.write(faker.ipv4()+ " "+str(datetime.datetime.utcnow())+'  https://rare_pattern_odd -- 0050,' + StringGenerater(50) + '\n')
					count_dictionary['rare_odd']= count_dictionary['rare_odd']+1
				# pattern only can be found on 02, 4, 6, 8 (even numbered machine)
				elif Number_machine % 2 == 0:
					file.write(faker.ipv4()+ " "+ str(datetime.datetime.utcnow())+'  https://rare_pattern_even -- 0050,' + StringGenerater(50) + '\n')
					count_dictionary['rare_even'] = count_dictionary['rare_even'] + 1

				else:
					file.write(faker.ipv4()+ " "+str(datetime.datetime.utcnow())+'  https://rare_regular -- 0050,' + StringGenerater(50) + '\n')
					count_dictionary['rare_regular'] = count_dictionary['rare_regular'] + 1


			# somewhat frequent
			elif rand_number <= 0.15:
				file.write(faker.ipv4()+ " "+str(datetime.datetime.utcnow())+'  https://somewhat_frequent -- 0050,' + StringGenerater(50) + '\n')
				count_dictionary['somewhat_frequent'] = count_dictionary['somewhat_frequent'] + 1


			# frequent messages
			else:
				file.write(faker.ipv4()+ " " +str(datetime.datetime.utcnow())+'  https://frequent -- 0050,' + StringGenerater(50) + '\n')
				count_dictionary['frequent'] = count_dictionary['frequent'] + 1

			# Unique message that exist on only one machine
			if Number_machine==2:
				file.write(faker.ipv4() + " " + str(
					datetime.datetime.utcnow()) + '  https://Unique -- 0050,' + StringGenerater(50) + '\n')
				count_dictionary['unique'] = count_dictionary['unique'] + 1

			## Messages Common for  All machines

			file.write(faker.ipv4() + " " + str(
				datetime.datetime.utcnow()) + '  https://Common -- 0050,' + StringGenerater(50) + '\n')
			count_dictionary['common']= count_dictionary['common']+1

	## Maintain a file with count of all types of patterns (i.e. frequent, rare, somewhat frequent, common to all, and unique or pattern for 1 machine)
	## This count can be used for Unit testing to check the integrity of distributed querier program
	with open('New_count_patterns.txt', 'w') as f2:
		for key, value in count_dictionary.items():
			f2.write(key + ': ' + str(value) + '\n')
		f2.close()


def StringGenerater(len):
	"""
	This function generates a random string of charcters (upper & lower) + digits + puncutation

	Params:
    1. Length: Random string's length
	
    returns: Randomly generated String of length len
    """
	return ''.join(random.choice(string.ascii_letters + string.digits+string.punctuation) for i in range(len))



if __name__ == '__main__':
	random.seed(2701937)
	for k in range(1, len(sys.argv)):  ## To generate all log files together for all VMs, replace sys.argv with Last Machine Number
		#print('argument:', k, 'value:', sys.argv[k])
		if k==1:
			i=sys.argv[k]
	#for i in range(1,2):
	#i=sys.argv
	# print("argument is",i)
	logfile = 'TestingLog' + str(i) + '.log'
	print("log file name is", logfile)
	log_generator(logfile, 10000, int(i))
