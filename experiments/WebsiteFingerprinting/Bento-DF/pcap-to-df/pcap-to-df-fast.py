import sys
import pandas as pd
import os
from os import listdir
from os.path import isfile, join
import pickle
import threading
import subprocess

def get_key(my_dict, val): 
    # print("key: " + val)
    for key, value in my_dict.items(): 
         if val == value: 
             return key 
  
    return -1

    


# Load Alexa
alexas = pd.read_csv('top-1m.csv', header=None, index_col=0, squeeze=True).to_dict()

X = []
Y = []

pcaps_by_site = sys.argv[1]
dirs = [x[0] for x in os.walk(pcaps_by_site)]
dirs = dirs[1:]


def work(working_dir):
	print("working_dir: " + str(working_dir))
	site = os.path.basename(os.path.normpath(working_dir))
	onlyfiles = [f for f in listdir(working_dir) if isfile(join(working_dir, f))]

	if get_key(alexas, site) == -1:
		return


	
	for pcapfile in onlyfiles:
		x = subprocess.run(["./better-df/pcap-to-df", working_dir + "/" + pcapfile], capture_output=True)
		flows = x.stdout.decode().split(' ')
		flows.pop()

		flows2 = []
		for f in flows:
			flows2.append(float(f))

		# input(flows)
		X.append(flows2)
		Y.append(float(get_key(alexas, site)))
		
		
			

for working_dir in dirs:
	work(working_dir)


      
print("[+] Writing to file...")
f = open('X_train.pkl','wb')
pickle.dump(X, f)
f.close()
f = open('Y_train.pkl','wb')
pickle.dump(Y, f)
f.close()
