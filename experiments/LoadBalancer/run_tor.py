#!/usr/bin/env python3

import os
from stem.control import Controller
import stem.process
import random

control_port = random.randint(9060,9090)
socks_port = control_port-10
print("Control port: " + str(control_port))
print("Socks port: " + str(socks_port))

os.system('mkdir /tmp/datadir'+str(control_port))
os.system('rm -rf /tmp/datadir'+str(control_port) + '/*')
os.system('cp hs_ed25519_secret_key /tmp/datadir'+str(control_port))

tor_config = {'SOCKSPort': str(socks_port), 'ControlPort': str(control_port), 'DataDirectory': '/tmp/datadir'+str(control_port)}
proc = stem.process.launch_tor_with_config(config = tor_config)

print(' * Launched tor with pid: ' + str(proc.pid))

print(' * Connecting to tor')

with Controller.from_port(port=int(control_port)) as controller:
  controller.authenticate()

  # All hidden services have a directory on disk. Lets put ours in tor's data
  # directory.

  hidden_service_dir = os.path.join(controller.get_conf('DataDirectory', '/tmp'))
  # hidden_service_dir = '/usr/local/var/lib/tor/hidden_service/'
  # Create a hidden service where visitors of port 80 get redirected to local
  # port 5000 (this is where Flask runs by default).

  print(" * Creating our hidden service in %s" % hidden_service_dir)
  result = controller.create_hidden_service(hidden_service_dir, 80, target_port = 80)

  # The hostname is only available when we can read the hidden service
  # directory. This requires us to be running with the same user as tor.

  if result.hostname:
    print(" * Our service is available at %s, press ctrl+c to quit" % result.hostname)
  else:
    print(" * Unable to determine our service's hostname, probably due to being unable to read the hidden service directory")

  # Shut down the hidden service and clean it off disk. Note that you *don't*
  # want to delete the hidden service directory if you'd like to have this
  # same *.onion address in the future.
  input('Press "Enter" to shut down hs')
  print(" * Shutting down our hidden service")
  controller.remove_hidden_service(hidden_service_dir)
