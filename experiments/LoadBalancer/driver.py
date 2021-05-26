"""
Upload and execute the loadbalancer Bento function
"""

import sys
import importlib
import os
import json
import logging
import zlib

sys.path.append("../..")

logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.DEBUG)

from bento.client.api import ClientConnection
from bento.common.protocol import *


def __driver():
        addr= sys.argv[1]
        port= int(sys.argv[2])
        function_name= "load"
        f= open(f"load_balancer.func", 'r')
        function_code= f.read()

        conn= ClientConnection(addr, port)

        token, errmsg= conn.send_store_request(function_name, function_code)
        if errmsg is not None:
            logging.error(f"Error message from server {errmsg}")
        else:
            logging.debug(f"Got token: {token}")
            call= f"{function_name}()"
            session_id, errmsg= conn.send_execute_request(call, token)
            if errmsg is not None:
                logging.error(f"Error message from server {errmsg}")
            else:
                logging.debug(f"Got session_id: {session_id}")
                logging.debug("Opening session...")
                conn.send_open_request(session_id)
                while True:
                    data, session_id, err= conn.get_sessionmsg()
                    print(data)
                    if err is not None:
                        break


__driver()
