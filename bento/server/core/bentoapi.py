"""
this file defines the bento api that is exposed to functions executed by clients.
    - want to allow functions to send data back to their clients, use the Stem library to extend their circuits, etc.
"""


import struct
import sys
import select


class StdoutData:
    HeaderLen= 5
    HeaderFmt= ">BI"

    def __init__(self, data):
        if isinstance(data, str):
            data= data.encode()
        self.data= data
    
    def serialize(self, errbyte):
        hdr= struct.pack(StdoutData.HeaderFmt, errbyte, len(self.data))
        return hdr + self.data


class StdinData:
    HeaderLen= 4
    HeaderFmt= ">I"

    def __init__(self, data):
        self.data= data
    
    def serialize(self):
        hdr= struct.pack(StdinData.HeaderFmt, len(self.data))
        return hdr + self.data


def send(data):
    """
    pack data len, append the actual data, and send to server
        - will be picked up by the dedicated exchange process for this function
    """
    if data:
        sys.stdout.buffer.write(StdoutData(data).serialize(0x00))
        sys.stdout.buffer.flush()
        return len(data)
    return 0
        

def recv():
    """
    recv data from the client through our pipe to the server 
    """
    data= sys.stdin.buffer.read(StdinData.HeaderLen)
    datalen,= struct.unpack(StdinData.HeaderFmt, data) 
    data= sys.stdin.buffer.read(datalen)
    return data


def poll():
    """
    return whether there is data in the pipe
    """
    return sys.stdin.buffer in select.select([sys.stdin.buffer], [], [], 0)[0] 
    

