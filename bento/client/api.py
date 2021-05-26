
"""
Api to interface with a bento server
"""

import struct
import socket
import json
import sys
import random
import string
import importlib
import os
import logging

from bento.common.protocol import *


class ClientConnection:
    """
    represents a connection with a Bento server in order to allow sending/recving
    requests/responses and session messages
    """
    
    def __init__(self, address: str, port: int):
        self.conn= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((address, port))


    def send_store_request(self, name, code):
        """
        send a synchronous store request which expects a store response or error from the server
        """
        request= StoreRequest(name, code)
        self.__send_request(request)
        response= self.__get_response()
        if response.resp_type != Types.Store:
            raise Exception("Request-Response types don't match")
        return (response.token, None) if response.success == True else (None, response.errmsg)


    def send_execute_request(self, call, token):
        """
        send a synchronous execute request which expects a execute response or error from the server
        """
        request= ExecuteRequest(call, token)
        self.__send_request(request)
        response= self.__get_response()
        if response.resp_type != Types.Execute:
            raise Exception("Request-Response types don't match")
        return (response.session_id, None) if response.success == True else (None, response.errmsg)
        

    def send_open_request(self, session_id):
        """
        send an asynchronous open request that informs the server that the client is now ready to send
        and recieve session messages
            - no response expected, any errors will be sent in subsequent session error messages
        """
        request= OpenRequest(session_id)
        self.__send_request(request)


    def send_close_request(self, session_id):
        """
        send an asynchronous close request that informs the server that the client would like to 
        stop sending and receiving session messages
            - no response expected, session messages may still be sent in the overlap between a server
              receiving a close request and sending session messages
        """
        request= CloseRequest(session_id)
        self.__send_request(request)

    
    def send_sessionmsg(self, session_id, data):
        """
        send a session message to a particular open session by providing a session_id
        """
        if len(data) == 0:
            return 0

        if isinstance(data, str):
            data= data.encode()
        msg= SessionMsg(session_id, data)
        return self.conn.send(msg.serialize())


    def get_sessionmsg(self):
        """
        get the next session message available from server
            - return if error or not
        """
        hdr= self.__recv_all(SessionMsg.HeaderLen)
        if hdr is None:
            raise Exception('failed to recv header')

        sess_type, length, err= SessionMsg.unpack_hdr(hdr)
        if err is not None:
            raise Exception(f'unpacking header failed: {err}')
        
        data= self.__recv_all(length)
        if data is None:
            raise Exception('failed to recv response data')

        if sess_type == Types.Err:
            msg= SessionMsgErr.deserialize(data)
            return msg.data, msg.session_id, True

        elif sess_type == Types.Session:
            msg= SessionMsg.deserialize(data)
            return msg.data, msg.session_id, False


    def __send_request(self, request):
        self.conn.sendall(request.serialize())


    def __get_response(self):        
        """
        attempt to receive response data from the stream
        """
        hdr= self.__recv_all(Response.HeaderLen)
        if hdr is None:
            raise Exception("failed to recv header")

        resp_type, errbyte, length, err= Response.unpack_hdr(hdr)
        if err is not None:
            raise Exception(f"unpacking header failed: {err}")

        data= self.__recv_all(length)
        if data is None:
            raise Exception("failed to recv response data")
        
        if errbyte == 0x0:
            if resp_type == Types.Execute:
                response= ExecuteResponse.deserialize(data)
            elif resp_type == Types.Store:
                response= StoreResponse.deserialize(data)
            elif resp_type == Types.Open:
                response= OpenResponse.deserialize()
            elif resp_type == Types.Close:
                response= CloseResponse.deserialize()

        else:
            response= ErrorResponse.deserialize(data, resp_type)
        
        return response
        

    def __recv_all(self, n):
        data = bytearray()
        while len(data) < n:
            packet= self.conn.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
