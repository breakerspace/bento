#!/usr/bin/env python3

import argparse
import select
import sys

sys.path.append("..")
from bento.client.api import ClientConnection
from bento.common.protocol import *

def main():
    parser = argparse.ArgumentParser(
            description='Interactive interface to a Bento server')
    parser.add_argument('host', help="server's IPv4 address (default: 0.0.0.0)", 
            nargs='?', default="0.0.0.0")
    parser.add_argument('port', type=int, help="server's port (default: 8888)",
            nargs='?', default=8888)
    args = parser.parse_args()

    print("===Starting client...connecting to Bento server")
    
    try: 
        conn= ClientConnection(args.host, args.port)
    except Exception as exc:
        print(f"couldn't connect: {exc}")
        return

    menu= """
    store: send store request
    exec: send execute request
    open: send open request
    close: send close request
    send: send message to open session
    recv: get message from open session
    
    exit: quit
    """
    prompt= ">> "

    print(menu)
   
    while True:
        selection= input(prompt)

        if selection == 'store':
            function_name= input("enter name: ")
            function_code= []
            print("enter code (enter three times to submit):")
            line= input()
            line_next= input()
            while line and line_next:
                function_code.append(line)
                function_code.append(line_next)
                line= input()
                line_next= input()
           
            token, errmsg= conn.send_store_request(function_name, "\n".join(function_code))
            if errmsg is not None:
                print(f"Error: {errmsg}")
            else:
                print(f"==recved token: {token}")

        elif selection == 'exec':
            token= input("enter token: ")
            call= input("enter call: ")
            session_id, errmsg= conn.send_execute_request(call, token)
            if errmsg is not None:
                print(f"Error: {errmsg}")
            else:
                print(f"==recved session_id: {session_id}")
        
        elif selection == 'open':
            session_id= input("enter session_id: ")
            conn.send_open_request(session_id)
            print("==ok session opened")

        elif selection == 'close':
            session_id= input("enter session_id: ")
            conn.send_close_request(session_id)
            print("==ok session closed")
            
        elif selection == 'send':
            session_id= input("enter session_id: ")
            data= input("enter data: ")
            conn.send_sessionmsg(session_id, data)
            print("==sent")

        elif selection == 'recv': 
            data, session_id, err= conn.get_sessionmsg()
            if data is not None:
                if err:
                    print(f"Error: {data}")
                elif conn.conn in select.select([conn.conn], [], [], 2)[0]:
                    print(f"==recved message from session: {session_id}")
                    print(data)
                else:
                    print("no data")

        else:
            break


if __name__ == '__main__':
    main()
