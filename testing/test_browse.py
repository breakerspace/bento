#!/usr/bin/env python3

"""
Test a function that fetches the http://example.com/ webpage and pads
response.
- function uploaded: functions/browse
"""

import argparse
import logging
import sys
import zlib

sys.path.append("..")
from bento.client.api import ClientConnection
from bento.common.protocol import *
import bento.common.util as util

@util.timeit
def main():
    logging.basicConfig(format='%(levelname)s:\t%(message)s',
            level=logging.DEBUG)

    parser = argparse.ArgumentParser(
            description='Fetch the http://example.com/ webpage and pad response with dummy bytes')
    parser.add_argument('host', help="server's IPv4 address (default: 0.0.0.0)", 
            nargs='?', default="0.0.0.0")
    parser.add_argument('port', type=int, help="server's port (default: 8888)",
            nargs='?', default=8888)
    args = parser.parse_args()

    function_name = 'browse'
    function_code = util.read_file(f"functions/{function_name}")

    conn= ClientConnection(args.host, args.port)

    token, errmsg= conn.send_store_request(function_name, function_code)
    if errmsg is not None:
        util.fatal(f"Error message from server {errmsg}")

    logging.debug(f"Got token: {token}")

    url= "http://example.com/?q=ultrasurf"
    call= f"{function_name}('{url}', 5)"
    function_id, errmsg= conn.send_execute_request(call, token)
    if errmsg is not None:
       util.fatal(f"Error message from server {errmsg}")

    logging.debug(f"Got function_id: {function_id}")
    logging.debug("Getting output...")

    conn.send_open_request(function_id)
    data, err= conn.recv_output()
    print(zlib.decompress(data))


if __name__ == '__main__':
    main()
