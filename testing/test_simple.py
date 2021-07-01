#!/usr/bin/env python3

import importlib
import json
import logging
import os
import sys

logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.DEBUG)

sys.path.append("..")
from bento.client.api import ClientConnection
from bento.common.protocol import *
import bento.common.util as util 

@util.timeit
def __test_basic_loop(conn):
    """
    Test basic continuous output sending
    """
    code= """
def loop():
    y= 5
    while y > 0:
        api.send('y= ' + str(y))
        y-=1
    
    """
    token, errmsg= conn.send_store_request("loop", code)
    if errmsg is not None:
        logging.error(f"error message from server: {errmsg}")
    else:
        logging.debug(f"got token: {token}")
        call= f"loop()"
        function_id, errmsg= conn.send_execute_request(call, token)
        if errmsg is not None:
            logging.error(f"error message from server: {errmsg}")
        else:
            logging.debug(f"got function_id: {function_id}")
            logging.debug(f"sending open request and attempting to recv output")
            conn.send_open_request(function_id)
            while True:
                try:
                    data, err= conn.recv_output()
                    print(data)
                except Exception as e:
                    print(e)
                    break


@util.timeit
def __test_basic_input(conn):
    """
    Test sending simple input and echoing it back 
    """
    code= """
def echo():
    api.send('hello')
    data= api.recv()
    api.send('echoing response...')
    api.send(data)
    
    """
    token, errmsg= conn.send_store_request("echo", code)
    if errmsg is not None:
        logging.error(f"error message from server: {errmsg}")
    else:
        logging.debug(f"got token: {token}")
        call= f"echo()"
        function_id, errmsg= conn.send_execute_request(call, token)
        if errmsg is not None:
            logging.error(f"error message from server: {errmsg}")
        else:
            logging.debug(f"got function_id: {function_id}")
            logging.debug("sending input")
            logging.debug(f"sending open request and attempting to recv output")
            conn.send_open_request(function_id)
            conn.send_input(function_id, 'hello')
            while True:
                try:
                    data, err= conn.recv_output()
                    print(data)
                except Exception as e:
                    print(e)
                    break


@util.timeit
def __test_instance_open_close(conn):
    """
    Test opening, closing and then opening a instance while the function is still running
    """
    code= """
import time
def loop():
    y= 7
    while y > 0:
        api.send("hello" + str(y))
        time.sleep(3)
        y= y-1

    """
    token, errmsg= conn.send_store_request("loop", code)
    if errmsg is not None:
        logging.error(f"error message from server: {errmsg}")
    else:
        logging.debug(f"got token: {token}")
        call= "loop()"
        function_id, errmsg= conn.send_execute_request(call, token)
        if errmsg is not None:
            logging.error(f"error message from server: {errmsg}")
        else:
            try:
                logging.debug(f"got function_id: {function_id}")
                logging.debug(f"opening instance: {function_id}")
                conn.send_open_request(function_id)
                data, err= conn.recv_output()
                print(data)
                data, err= conn.recv_output()
                print(data)
                logging.debug(f"closing instance: {function_id}")
                conn.send_close_request(str(function_id))
                logging.debug(f"opening instance: {function_id}")
                conn.send_open_request(str(function_id))
                data, err= conn.recv_output()
                print(data)
                data, err= conn.recv_output()
                print(data)
                logging.debug(f"closing instance: {function_id}")
                conn.send_close_request(str(function_id))
            except Exception as e:
                print(e)


def __main_test_simple():
    ip= sys.argv[1]
    port= sys.argv[2]
    test_name= None
    if len(sys.argv) == 4:
        test_name= sys.argv[3]

    conn= ClientConnection(ip, int(port))
    
    # run all functions in file or specific one
    search= f'__test_{test_name}' if test_name is not None else '__test'
    current_module= sys.modules[__name__]
    for i in dir(current_module):
        if i.startswith(search):
            item= getattr(current_module, i)
            if callable(item):
                print(f"====Running test: {i}")
                item(conn)


"""
Usage: python3.6 test_simple.py localhost 8888 <testname>
    - Note: empty testname will just run all tests
    - Ex: python3.6 test_simple.py localhost 8888 basic_input
"""
__main_test_simple()
