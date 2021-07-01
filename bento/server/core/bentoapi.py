"""
this file defines the bento api that is exposed to functions executed by clients.
    - want to allow functions to send data back to their clients, use the Stem library to extend their circuits, etc.
"""


import struct
import sys
import base64
import select


def send(data):
    """
    pack data len, append the actual data, and send to server
        - will be picked up by the dedicated exchange process for this function
    """
    if data is not None:
        datalen= struct.pack(">Q", len(data))
        sys.stdout.buffer.write(datalen) 
        if isinstance(data, str):
            data= data.encode()
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        return len(data)
    return 0
        

def recv():
    """
    recv data from the client through our pipe to the server 
    """
    bdata= sys.stdin.buffer.read(8) 
    datalen,= struct.unpack(">Q", bdata) 
    data= sys.stdin.buffer.read(datalen)
    return data


def poll():
    """
    return whether there is data in the pipe
    """
    return sys.stdin.buffer in select.select([sys.stdin.buffer], [], [], 0)[0] 
    

