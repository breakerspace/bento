#!/usr/bin/env python3

#First all clients report to me and then I keep sending them to the load balancer poisson's process
#https://preshing.com/20111007/how-to-generate-random-timings-for-a-poisson-process/
'''usage: master_client.py <no_of_clients> '''


from time import sleep
import subprocess
import socket
import math
import random
import sys

def nextTime(rateParameter):
    return -math.log(1.0 - random.random()) / rateParameter

no_of_clients = sys.argv[1]
s = socket.socket()          
print ("Socket successfully created")
print ("I will handle client arrivals")
        
port = 12345                
          
        
s.bind(('0.0.0.0', port))         
print ("socket binded to %s" %(port) )
          
# put the socket into listening mode 
s.listen(5)      
print ("socket is listening" )           
  
  
conn ={}        

ctr = 0
while True:
    c, addr = s.accept()      
    conn[addr[0]] = c
    c.send(b'Thank you for connecting! Accepted') 
    ctr = ctr + 1
    
    if (ctr > (int(no_of_clients)-1)):
        for x in conn:
            # t = nextTime(10)
            print("sending msg: ready")
            print(conn[x])
            conn[x].send(b'Ready')
            # change sleep time
            sleep(10)
