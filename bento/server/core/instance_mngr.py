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
            __instances[function_id].clean()
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
        self.buffout_path= f'{opts.instances_dir}/{function_id}.out'
        self.read_handle= None
        self.write_handle= None

        self._execute(exec_data)


    def _execute(self, exec_data):
        """
        execute the function in a defined environment and open handles to read and write data 
        process to handle its output
        """
        cmd= shlex.split(opts.function_cmd)
        cmd.append('driver.py')
        cmd.append(exec_data)
        
        with open(self.buffout_path, 'wb') as buffer:
            self.function_proc= subprocess.Popen(cmd, stdout=buffer, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            self.write_handle= self.function_proc.stdin
            self.read_handle= open(self.buffout_path, 'rb')
    
    def clean(self):
        """
        attempt to clean up instance processes and artifacts if function has completed execution
            - return whether cleanup was successful
        """
        if self.function_proc.poll is not None: 
            self.function_proc.wait()
            if self.read_handle is not None: 
                self.read_handle.close()
            # TODO: remove output file (buffout_path)
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

