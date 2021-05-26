import logging
from multiprocessing import Process, Value, Lock
import os
import shlex
import socket
import struct
import subprocess
import sys
from threading import Lock
import time
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
    a Session handles exchanging data with a function and persisting its output
    between client reconnects 
    """
    def __init__(self, session_id):
        self.is_open= Value("i", 0)
        self.is_alive= Value("i", 1)
        self.output_buff_pos= Value("i", 0)
        self.session_id= session_id
        self.output_lock= Lock()
        self.function_proc= None
        self.exchange_proc= None
        self.worker_proc= None
        self.buffout_path= f'{opts.sessions_dir}/{session_id}.out'
        self.read_handle= None


    def execute(self, exec_data):
        """
        execute the function in a defined environment and start an exchange
        process to handle its output
        """
        cmd= shlex.split(opts.function_cmd)
        cmd.append('driver.py')
        cmd.append(exec_data)
        self.function_proc= subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.exchange_proc= Process(target= exchange, args= (self,))
        self.exchange_proc.start()


    def start_worker(self, conn: socket):
        """
        start a worker for the session
        """
        self.is_open.value= 1
        self.worker_proc= Process(target= worker, args= (conn, self))
        self.worker_proc.start()

    
    def read_output(self):
        """
        read output from the output file while it exists and isn't being written to
            - return None if data couldn't be read
        """
        if self.read_handle == None:
            if os.path.exists(self.buffout_path):
                logging.info(f"({self.session_id}) read handle opened")
                self.read_handle= open(self.buffout_path, 'rb')
                self.read_handle.seek(self.output_buff_pos.value)
            else:
                return None

        datalen= self.read_handle.read(8)
        if len(datalen) == 8:
            datalen,= struct.unpack("Q", datalen)
            data= self.read_handle.read(datalen)
            self.output_buff_pos.value= self.read_handle.tell()
            logging.info(f"({self.session_id}) reading output from session")
            return data
        else: 
            return None


    def write_input(self, data: bytes):
        """
        write input to the function process pipe which will handle passing it along to the executing function
            - return whether write was successful
        """
        if self.exchange_proc.is_alive():
            datalen= struct.pack("Q", len(data))
            if self.function_proc.poll() is not None:
                logging.debug(f"({self.session_id}) function dead")
                return False
            self.function_proc.stdin.write(datalen + data)
            self.function_proc.stdin.flush()
            logging.debug(f"({self.session_id}) data written to function")
            return True
        else:
            return False

    
    def clean(self):
        """
        attempt to clean up session processes and artifacts if function has completed execution
            - return whether cleanup was successful
        """
        if self.is_alive.value == 0: 
            self.function_proc.wait()
            self.exchange_proc.join()
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
        if self.is_alive.value == 1:
            logging.info(f"({self.session_id}) killing session")
            self.exchange_proc.terminate()
            self.function_proc.kill()
        self.clean()


"""
============================================================================
Exchange & Worker process - started through the multiprocessing module 
============================================================================
"""

def exchange(session: Session):
    """
    write output from function process to buffer file 
    """
    proc_out= session.function_proc.stdout
    write_handle= open(session.buffout_path, 'wb')
    
    while True:
        bdata= proc_out.read(8) 
        if len(bdata) == 8:
            datalen,= struct.unpack("Q", bdata) 
            data= proc_out.read(datalen)
            datalen= struct.pack("Q", datalen)
            write_handle.write(datalen + data)
            write_handle.flush()
            logging.info(f"({session.session_id}) wrote output")
        else:
            if session.function_proc.poll is not None:
                # function is dead - kill exchange and print any errors from function
                logging.info(f"({session.session_id}) exchange finished")
                errors= session.function_proc.communicate()
                if errors == (b'', b''):
                    logging.debug(f"({session.session_id}) no errors")
                else:
                    logging.debug(f"({session.session_id}) errors: {errors}")
                session.is_alive.value= 0
                write_handle.close()
                break


def worker(conn: socket, session: Session):
    """
    continually read data from output file buffer of given session and send to client
    """
    while session.is_open.value == 1:
        data= session.read_output()
        if data == None: # no data available 
            if session.is_alive.value == 0:
                logging.info(f"({session.session_id}) sending termination message")
                conn.sendall(SessionMsgErr(session.session_id, b'session terminated').serialize())
                break
            time.sleep(0.01)
        else:
            conn.sendall(SessionMsg(session.session_id, data).serialize())


"""
============================================================================
Session management
============================================================================
"""

__sessions= {}
__lock= Lock()


def create():
    with __lock:
        session_id= str(uuid.uuid4())
        new_session= Session(session_id)
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


