import logging
from multiprocessing import Process, Value, Lock
import shlex
import struct
import subprocess
import os
import sys
from threading import Lock
import uuid

from .config import opts

sys.path.append('..')
from common.protocol import *


"""
============================================================================
Session Definition
============================================================================
"""

class Session():
    """
    a Session handles executing a function and piping its data to a buffer
        NOTE: should hold relevant state (like session id)
    """
    def __init__(self, session_id, exec_data):
        self.session_id= session_id
        self.function_proc= None
        self.buffout_path= f'{opts.sessions_dir}/{session_id}.out'
        self.read_handle= None
        self.write_handle= None

        self.__execute(exec_data)


    def __execute(self, exec_data):
        """
        execute the function in a defined environment and start an exchange
        process to handle its output
        """
        cmd= shlex.split(opts.function_cmd)
        cmd.append('driver.py')
        cmd.append(exec_data)
        
        with open(self.buffout_path, 'wb') as handle:
            self.function_proc= subprocess.Popen(cmd, stdout=handle, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            self.write_handle= self.function_proc.stdin
            self.read_handle= open(self.buffout_path, 'rb')
    
    def clean(self):
        """
        attempt to clean up session processes and artifacts if function has completed execution
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
            logging.info(f"({self.session_id}) killing session")
            self.function_proc.kill()
        self.clean()


"""
============================================================================
Session management
============================================================================
"""

__sessions= {}
__lock= Lock()


def create(exec_data):
    with __lock:
        session_id= str(uuid.uuid4())
        new_session= Session(session_id, exec_data)
        __sessions[session_id]= new_session
    return new_session


def destroy(session_id):
    with __lock:
        if session_id in __sessions:
            __sessions[session_id].clean()
            del __sessions[session_id]


def get(session_id):
    with __lock:
        if session_id in __sessions:
            return __sessions[session_id]


