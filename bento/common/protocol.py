"""
Application Protocol
"""

import struct
import json


class Types:
    Store   = 0x0
    Execute = 0x1
    Open    = 0x2
    Close   = 0x3
    Session = 0x4
    Err     = 0x5


"""
============================================================================
Client request definitions
============================================================================
"""

class Request:
    """
    represents a request message from client -> server
    """

    """ header properties """
    HeaderLen= 5
    HeaderFmt= '>BI'

    @staticmethod
    def unpack_hdr(packed_hdr):
        if Request.HeaderLen != len(packed_hdr):
            return None, None, "header len doesn't match"

        req_type, length= struct.unpack(Request.HeaderFmt, packed_hdr)

        return req_type, length, None


    """ inherited functions """
    def serialize(self) -> bytes:
        """
        serialize the Request object into a byte buffer to send over the network
        """
        pass

    @classmethod
    def deserialize(cls, data: bytes):
        """
        deserialize a byte buffer into a Request object
        """
        pass
    

class StoreRequest(Request):
    def __init__(self, name: str, code: str):
        self.name= name
        self.code= code

    def serialize(self):
        data= json.dumps({'name': self.name, 'code': self.code})
        bdata= str(data).encode()
        header= struct.pack(Request.HeaderFmt, 
                            Types.Store, 
                            len(data))
        return header + bdata

    @classmethod
    def deserialize(cls, data):
        jdata= json.loads(data.decode())
        return cls(name= jdata.get('name'), 
                   code= jdata.get('code'))


class ExecuteRequest(Request):
    def __init__(self, call: str, token: str):
        self.call= call
        self.token= token

    def serialize(self):
        data= json.dumps({'call': self.call, 'token': self.token})
        bdata= str(data).encode()
        header= struct.pack(Request.HeaderFmt, 
                            Types.Execute, 
                            len(data))
        return header + bdata

    @classmethod
    def deserialize(cls, data):
        jdata= json.loads(data.decode())
        return cls(call= jdata.get('call'), token= jdata.get('token'))


class OpenRequest(Request):
    def __init__(self, session_id: str):
        self.session_id= session_id

    def serialize(self):
        session_id= self.session_id.encode()
        header= struct.pack(Request.HeaderFmt, Types.Open, len(session_id))
        return header + session_id
    
    @classmethod
    def deserialize(cls, data):
        return cls(session_id= data.decode())


class CloseRequest(Request):
    def __init__(self, session_id: str):
        self.session_id= session_id

    def serialize(self):
        session_id= self.session_id.encode()
        header= struct.pack(Request.HeaderFmt, Types.Close, len(session_id))
        return header + session_id 

    @classmethod
    def deserialize(cls, data):
        return cls(session_id= data.decode())


"""
============================================================================
Server response definitions
============================================================================
"""

class Response:
    """
    represents a response message from server -> client
    """
    Success, Error= range(2)

    """ header properties """
    HeaderLen= 6
    HeaderFmt= '>BBI'

    @staticmethod
    def unpack_hdr(packed_hdr):
        if Response.HeaderLen != len(packed_hdr):
            return None, None, None, "header len doesn't match"

        resp_type, error, length= struct.unpack(Response.HeaderFmt, packed_hdr)

        return resp_type, error, length, None

    def serialize(self) -> bytes:
        """
        serialize the Response object into a byte buffer to send over the network
        """
        pass

    @classmethod
    def deserialize(cls, data: bytes):
        """
        deserialize a byte buffer into a Request object
        """
        pass


class StoreResponse(Response):
    def __init__(self, token: str):
        self.token= token
        self.resp_type= Types.Store
        self.success= True

    def serialize(self):
        bdata= str(self.token).encode()
        header= struct.pack(Response.HeaderFmt, 
                            Types.Store,
                            Response.Success, 
                            len(bdata))
        return header + bdata

    @classmethod
    def deserialize(cls, data):
        return cls(token= data.decode())


class ExecuteResponse(Response):
    def __init__(self, session_id):
        self.session_id= session_id
        self.resp_type= Types.Execute
        self.success= True

    def serialize(self):
        bdata= str(self.session_id).encode()
        header= struct.pack(Response.HeaderFmt, 
                            Types.Execute,
                            Response.Success, 
                            len(bdata))
        return header + bdata

    @classmethod
    def deserialize(cls, data):
        return cls(session_id= data.decode())


class ErrorResponse(Response):
    def __init__(self, errmsg: str, resp_type: int):
        self.resp_type= resp_type
        self.errmsg= errmsg
        self.success= False

    def serialize(self):
        bdata= str(self.errmsg).encode()
        header= struct.pack(Response.HeaderFmt,
                            self.resp_type,
                            Response.Error, 
                            len(bdata))
        return header + bdata

    @classmethod
    def deserialize(cls, data, resp_type):
        return cls(errmsg= data.decode(), resp_type= resp_type)


"""
============================================================================
Open session send/recv packets 
============================================================================
"""

session_id_len= 36   

class SessionMsg():
    """
    represents a session message from either client -> server or client <- server
    """
    HeaderFmt= '>BI'
    HeaderLen= 5

    def __init__(self, session_id: str, data: bytes):
        self.session_id= session_id
        self.data= data
        self.type= Types.Session
    
    def serialize(self):
        session_id= self.session_id.encode()
        pkt_len= len(session_id) + len(self.data)
        header= struct.pack(SessionMsg.HeaderFmt, self.type, pkt_len)
        return header + session_id + self.data

    @classmethod
    def deserialize(cls, data):
        session_id= data[:session_id_len].decode()
        data= data[session_id_len:]
        return cls(session_id= session_id, data= data)

    @staticmethod
    def unpack_hdr(packed_hdr):
        if Request.HeaderLen != len(packed_hdr):
            return None, None, "header len doesn't match"

        req_type, length= struct.unpack(Request.HeaderFmt, packed_hdr)

        return req_type, length, None


class SessionMsgErr():
    """
    represents an error message in relation to a specific open session id
    """
    
    def __init__(self, session_id, data):
        self.session_id= session_id
        self.data= data
        self.type= Types.Err

    def serialize(self):
        session_id= self.session_id.encode()
        pkt_len= len(session_id) + len(self.data)
        header= struct.pack(SessionMsg.HeaderFmt, self.type, pkt_len)
        return header + session_id + self.data

    @classmethod
    def deserialize(cls, data):
        session_id= data[:session_id_len].decode()
        data= data[session_id_len:]
        return cls(session_id= session_id, data= data)
        
    