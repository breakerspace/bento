#!/usr/bin/env python3

import argparse
import logging
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
            description='Fetch the http://example.com/ webpage with cover traffic')
    parser.add_argument('host', help="server's IPv4 address (default: 0.0.0.0)", 
            nargs='?', default="0.0.0.0")
    parser.add_argument('port', type=int, help="server's port (default: 8888)",
            nargs='?', default=8888)
    args = parser.parse_args()

    function_name= "coverbrowser"
    function_code = util.read_file(f"functions/{function_name}")

    conn= ClientConnection(args.host, args.port)

    token, errmsg= conn.send_store_request(function_name, function_code)
    if errmsg is not None:
        util.fatal(f"error message from server: {errmsg}")

    logging.debug(f"got token: {token}")

    url= "http://example.com/?q=ultrasurf"
    call= f"{function_name}('{url}')"
    session_id, errmsg= conn.send_execute_request(call, token)
    if errmsg is not None:
        util.fatal(f"error message from server: {errmsg}")

    logging.debug(f"got session_id: {session_id}")

    logging.debug("sending open request and getting output")
    conn.send_open_request(session_id)
    while True:
        try:
            from_url, err= conn.recv_output()
            data, err= conn.recv_output()
            if from_url.decode() == url:
                print(data.decode())
        except Exception as e:
            print(e)
            break

if __name__ == '__main__':
    main()
