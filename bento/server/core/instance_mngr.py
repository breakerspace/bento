import logging
from multiprocessing import Process, Value, Lock
import shlex
import subprocess
import sys
from threading import Lock
import uuid

from .config import opts

sys.path.append('..')
from common.protocol import *


"""
============================================================================
Instance management
============================================================================
"""

__instances= {}
__lock= Lock()


def create(exec_data):
    with __lock:
        function_id= str(uuid.uuid4())
        new_instance= Instance(function_id, exec_data)
        __instances[function_id]= new_instance
    return new_instance


def destroy(function_id):
    with __lock:
        if function_id in __instances:
            if not __instances[function_id].clean():
                __instances[function_id].kill()
                del __instances[function_id]


def get(function_id):
    with __lock:
        if function_id in __instances:
            return __instances[function_id]


"""
============================================================================
Function Instance Definition
============================================================================
"""

class Instance:
    """
    an Instance is an invokation of a function and holds state for its execution
    """
    def __init__(self, function_id, exec_data):
        self.function_id= function_id
        self.function_proc= None
        self.outbuff_path= f'{opts.instances_dir}/{function_id}.out'
        self.errbuff_path= f'{opts.instances_dir}/{function_id}.err'
        self.readout_handle= None
        self.readerr_handle= None
        self.writein_handle= None

        self._execute(exec_data)


    def _execute(self, exec_data):
        """
        execute the function in a defined environment and open handles to read and write data 
        """
        cmd= shlex.split(opts.function_cmd)
        cmd.append('driver.py')
        cmd.append(exec_data)

        outbuff= open(self.outbuff_path, 'wb')
        errbuff= open(self.errbuff_path, 'wb')

        self.function_proc= subprocess.Popen(cmd, stdout=outbuff, stdin=subprocess.PIPE, stderr=errbuff)
        self.writein_handle= self.function_proc.stdin
        self.readout_handle= open(self.outbuff_path, 'rb')
        self.readerr_handle= open(self.errbuff_path, 'r')

    def alive(self):
        """
        return whether the function is alive
        """
        return self.function_proc.poll() is None

    def clean(self):
        """
        attempt to clean up instance processes and artifacts if function has completed execution
            - return whether cleanup was successful
        """
        if self.function_proc.poll is not None: 
            self.function_proc.wait()
            if self.readout_handle:
                self.readout_handle.close()
            if self.readerr_handle:
                self.readerr_handle.close()
            # TODO: remove output file 
            return True
        else:
            return False

        
    def kill(self):
        """
        forcefully kill processes and cleanup
        """
        if self.function_proc.poll is None: 
            logging.info(f"({self.function_id}) killing instance")
            self.function_proc.kill()
        self.clean()

