#!/usr/bin/env python3

'''usage: python3 replica.py <IP of loadbalancer> '''

import subprocess
import socket
from time import sleep
import os
from datetime import datetime
import sys

def get_time():
        now = datetime.now() # current date and time

        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        return date_time

def scale_client():
        ip = sys.argv[1]
        file = open("client_bandwidth.txt", "w")
        os.system('killall tor')
        # Create a socket object 
        s = socket.socket()          
                
        # Define the port on which you want to connect 
        port = 12345                
                
        # connect to the server on local computer 
        s.connect((ip, port)) 
        #sleep(1)
        # receive data from the server 
        print ("server: "+s.recv(1024).decode("utf-8")  )


  
        print ("server: "+s.recv(1024).decode("utf-8")  )
        on_off = 0
        
        while True:
                currenttime = get_time()
                #check established connections on port 80
                output = subprocess.check_output("netstat -anp | grep :80 | grep ESTABLISHED | wc -l", shell=True)
                print("Established status: "+output.decode("utf-8") )
                #send my active connections to server 
                s.send(output)
                print('Sent active connections')
                print("server: "+ s.recv(1024).decode("utf-8"))
                print("server told me to:")
                cmd = int(s.recv(1024).decode("utf-8")) 
                if(cmd==0):
                        print("Dying...")
                        if(on_off!=0):
                                print(currenttime + "\t" + "0", file=file)
                                print("Dead...")
                                os.system('killall tor')
                                on_off = 0
                elif(cmd==2):
                        print(currenttime + "\t" + "Do nothing...", file=file)
                        print("Do nothing...")
                else:
                        print("Run TOR again and refresh my descriptors!")
                        if(on_off!=1):
                                print(currenttime + "\t" + "1", file=file)
                                print("Ran TOR again and refresh my descriptors!")
                                subprocess.Popen(["python3","run_tor.py"])
                                on_off = 1
                        
                sleep(1)

scale_client()
