#!/usr/bin/env python3

import argparse
import logging
import sys

sys.path.append("../..")
from bento.client.api import ClientConnection
from bento.common.protocol import *
import bento.common.util as util


function_name= "coverbrowser"
function_code= """
import requests
import random
import json

def coverbrowser(url):
    user_agent= 'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0'
    headers= {'User-Agent': user_agent}

    cover_urls = ['https://www.google.com/', 
                'https://www.youtube.com/', 
                'https://www.umd.edu/', 
                'https://www.facebook.com/', 
                'https://www.linkedin.com/', 
                'https://www.stackoverflow.com/',  
                'https://www.github.com/', 
                'https://www.netflix.com/', 
                'https://www.yahoo.com/', 
                'https://www.amazon.com/']

    def send_cover():
        num_cover_pkts= random.randint(0, 3)
        while num_cover_pkts > 0:
            cover_url= random.choice(cover_urls)
            body= str(requests.get(cover_url, headers=headers, timeout=1).content)
            api.send(cover_url) 
            api.send(body)
            num_cover_pkts-= 1

    send_cover()
    body= str(requests.get(url, headers=headers, timeout=1).content)
    api.send(url)
    api.send(body)
    send_cover()

"""


@util.timeit
def main():
    logging.basicConfig(format='%(levelname)s:\t%(message)s',
            level=logging.DEBUG)

    parser = argparse.ArgumentParser(
            description='Fetch a website with added cover traffic')
    parser.add_argument('host', help="server's IPv4 address")
    parser.add_argument('port', type=int, help="server's port")
    parser.add_argument('url', help="URL to fetch")
    args = parser.parse_args()

    conn= ClientConnection(args.host, args.port)

    token, errmsg= conn.send_store_request(function_name, function_code)
    if errmsg is not None:
        util.fatal(f"error message from server: {errmsg}")

    logging.debug(f"got token: {token}")

    call= f"{function_name}('{args.url}')"
    session_id, errmsg= conn.send_execute_request(call, token)
    if errmsg is not None:
        util.fatal(f"error message from server: {errmsg}")

    logging.debug(f"got session_id: {session_id}")

    logging.debug("sending open request and getting output")
    conn.send_open_request(session_id)
    while True:
        from_url, session_id, err= conn.get_sessionmsg()
        if err:
            break
        data, session_id, err= conn.get_sessionmsg()

        if from_url.decode() == args.url:
            print(data.decode())


if __name__ == '__main__':
    main()
