import client
import server
import unittest
import os
import sys
import time
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




mydictionary={}

with open ('Count_Patterns.txt', 'rt') as myfile:  # Open count_patterns.txt file to read # of occurances for each pattern type
    for myline in myfile:              # For each line, read to a string,
        L=myline.split(': ')

        mydictionary[L[0]]=int(L[1].replace('\n',''))


print(mydictionary)

## Using the UnitTest package to write test cases to check if the count for each type of pattern maintened in the Count_Patterns.txt file is same as # of matching patterns computed by the distributed log querier. 

class UnitTest(unittest.TestCase):
    def test_frequent_pattern_count(self):
        '''
        Test case to verify the number of frequent patterns. 
        '''
        s="-c " + "https://frequent"
        Count_matching_lines=client.query(s, HOSTS,54329,"test.txt")
        print(Count_matching_lines)
        self.assertEqual(Count_matching_lines,mydictionary['frequent'])
    def test_infrequent_pattern_Odd_machine_count(self):

        '''
        Test case to verify the number of rare/infrequent pattern on Odd number of machines
        '''
        s = "-c " + "https://rare_pattern_odd"
        Count_matching_lines = client.query(s, HOSTS, 54329, "test.txt")
        print(Count_matching_lines)
        self.assertEqual(Count_matching_lines, mydictionary['rare_odd'])

    def test_infrequent_pattern_Even_machine_count(self):

        '''
        Test case to verify the number of rare/infrequent patterns from even number of machines
        '''
        s="-c "+"https://rare_pattern_even"
        Count_matching_lines = client.query(s, HOSTS, 54329, "test.txt")
        print(Count_matching_lines)
        self.assertEqual(Count_matching_lines, mydictionary['rare_even'])

    def test_somewhat_frequent_count(self):
        '''
        Test case to verify the count of somewhat_frequent patterns from all machines.
        '''

        s = "-c " + "https://somewhat_frequent"
        Count_matching_lines = client.query(s, HOSTS, 54329, "test.txt")
        print(Count_matching_lines)
        self.assertEqual(Count_matching_lines, mydictionary['somewhat_frequent'])
## The Test cases output will be pass or fail and printed out to the user

def main():

    suite = unittest.TestLoader().loadTestsFromTestCase(UnitTest)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    main()
