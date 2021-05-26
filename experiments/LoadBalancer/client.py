#!/usr/bin/env python3

'''usage: python3 client.py <IP address of master_client.py> '''

import time
import subprocess
import socket
from time import sleep
import os
import sys
import io
import pycurl
import stem.process
from humanize import naturalsize
from stem.util import term

filename = open('output.txt', 'w')
SOCKS_PORT = 7000
next_time = 0
start_time = 0
def progress(download_t, download_d, upload_t, upload_d):
    global next_time
    global start_time
    if start_time == 0:
        start_time = time.time()
        # print(str(start_time) + "\t" + "0" + "\t" + "0", file=filename)
    currenttime = time.time()
    duration = currenttime - start_time + 1
    if currenttime >= next_time:
        print("Total to download", download_t)
        print("Total downloaded", download_d)
        print("Total to upload", upload_t)
        print("Total uploaded", upload_d)
        download_speed = (download_d / duration) # bytes
        speed_s = naturalsize(download_speed, binary=False) # binary = True (binary suffixes ie KiB, MiB and base 2**10, else decminal suffixes kB and mB are used)
        print(str(currenttime) + "\t" + str(speed_s), file=filename)
        next_time = currenttime + 1
        
def query(url):
  """
  Uses pycurl to fetch a site using the proxy on the SOCKS_PORT.
  """

  output = io.BytesIO()

  query = pycurl.Curl()
  query.setopt(pycurl.URL, url)
  query.setopt(pycurl.PROXY, 'localhost')
  query.setopt(pycurl.PROXYPORT, SOCKS_PORT)
  query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
  query.setopt(pycurl.WRITEFUNCTION, output.write)
  query.setopt(query.NOPROGRESS, False)
  query.setopt(query.XFERINFOFUNCTION, progress)
  start_time = time.time()
  next_time = time.time() + 1
  try:
    query.perform()
    return output.getvalue()
  except pycurl.error as exc:
    return "Unable to reach %s (%s)" % (url, exc)


# This prints
# Tor's bootstrap information as it starts. Note that this likely will not
# work if you have another Tor instance running.

def print_bootstrap_lines(line):
  if "Bootstrapped " in line:
    print(term.format(line, term.Color.BLUE))

def connect_to_master():
    s = socket.socket()          
                
    # Define the port on which you want to connect 
    port = 12345                
                
    # connect to the master 
    s.connect(('174.129.56.129', port)) 
    
    # receive data from the master
    print ("server: "+s.recv(1024).decode("utf-8"))
  
    print ("server: "+s.recv(1024).decode("utf-8"))

#subprocess.Popen(["python3","bandwidth.py"])
connect_to_master()

print(term.format("Starting Tor:\n", term.Attr.BOLD))
tor_process = stem.process.launch_tor_with_config(
  config = {
    'SocksPort': str(SOCKS_PORT),
    
  },
  init_msg_handler = print_bootstrap_lines,
  )

print("DOWNLOADING...")
query("http://xpznyhql2uczf3v6lj3wqcnbjr65avqfzrrem7oif5umfnayej6oyiqd.onion/download")

tor_process.kill()  # stops tor


