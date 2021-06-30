#!/usr/bin/env python3

"""
Simple test for uploading a Bento function that says hello world
- function uploaded: functions/hello
"""

import argparse
import logging
import sys

# append project root to path to source bento package modules
sys.path.append("..")
from bento.client.api import ClientConnection
from bento.common.protocol import *
import bento.common.util as util

@util.timeit
def main():
    logging.basicConfig(format='%(levelname)s:\t%(message)s',
            level=logging.DEBUG)

    parser = argparse.ArgumentParser(
            description='Upload and execute the hello function')
    parser.add_argument('host', help="server's IPv4 address (default: 0.0.0.0)", 
            nargs='?', default="0.0.0.0")
    parser.add_argument('port', type=int, help="server's port (default: 8888)",
            nargs='?', default=8888)
    args = parser.parse_args()

    function_name = 'hello'
    function_code = util.read_file(f"functions/{function_name}")
        
    # Instantiate a ClientConnection obj (will connect to Bento server)
    conn = ClientConnection(args.host, args.port)

    # Send a store request
    token, errmsg= conn.send_store_request(function_name, function_code)
    if errmsg is not None:
        util.fatal(f"Error message from server {errmsg}")

    logging.debug(f"Got token: {token}")

    # Send an execute request with our token and call 
    call= f"{function_name}()"
    function_id, errmsg= conn.send_execute_request(call, token)
    if errmsg is not None:
        util.fatal(f"Error message from server {errmsg}")

    logging.debug(f"Got function_id: {function_id}")
    logging.debug("Getting output...")

    conn.send_open_request(function_id)
    data, msg_type= conn.recv_output()
    print(data.decode())
    term_msg, msg_type= conn.recv_output()
    print(term_msg)        


if __name__ == '__main__':
    main()
