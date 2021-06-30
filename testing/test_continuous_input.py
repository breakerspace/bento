#!/usr/bin/env python3

import argparse
import importlib
import json
import logging
import os
import sys

sys.path.append("..")
from bento.client.api import ClientConnection
from bento.common.protocol import *
import bento.common.util as util

@util.timeit
def main():
    logging.basicConfig(format='%(levelname)s:\t%(message)s',
            level=logging.DEBUG)

    parser = argparse.ArgumentParser(
            description="Simple echo server function (enter 'stop' to terminate)")
    parser.add_argument('host', help="server's IPv4 address (default: 0.0.0.0)", 
            nargs='?', default="0.0.0.0")
    parser.add_argument('port', type=int, help="server's port (default: 8888)",
            nargs='?', default=8888)
    args = parser.parse_args()

    function_name = 'continuousInput'
    function_code = util.read_file(f"functions/{function_name}")

    conn= ClientConnection(args.host, args.port)
    token, errmsg= conn.send_store_request(function_name, function_code)
    if errmsg is not None:
        util.fatal("error message from server: {errmsg}")

    logging.debug(f"got token: {token}")

    call= f"{function_name}()"
    function_id, errmsg= conn.send_execute_request(call, token)
    if errmsg is not None:
        util.fatal(f"error message from server: {errmsg}")

    logging.debug(f"got function_id: {function_id}")
    logging.debug("sending input")
    logging.debug(f"sending open request and attempting to recv output")

    conn.send_open_request(function_id)
    while True:
        data= input("enter input: ")
        conn.send_input(function_id, data)
        try:
            data, err= conn.recv_output()
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
