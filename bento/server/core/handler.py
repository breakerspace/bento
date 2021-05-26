import base64
import json
import logging
from multiprocessing import Process
import os
import socket
import struct
from threading import Thread
import time
import uuid

from . import session_mngr
from . import function 
from common.protocol import *


class ClientThread(Thread):
    """
    interact with client connections
    """
    def __init__(self, address, port, conn):
        Thread.__init__(self)
        self.address= address
        self.port= port
        self.conn= conn
        self.open_sessions= []


    def run(self):
        self.handle_client()


    def handle_client(self):
        """
        receive and parse packets from client
        """
        while True:

            try:
                req_type, bdata= self.__recv_pkt()
            except Exception as e:
                logging.error(e)
                self.__handle_disconnect()
                return                

            if req_type == Types.Store: 
                request= StoreRequest.deserialize(bdata)
                logging.debug("Parsing store request")
                self.handle_store_request(request)
                
            elif req_type == Types.Execute:
                request= ExecuteRequest.deserialize(bdata)
                logging.debug(f"Parsing execute request for token: {request.token}")
                self.handle_execute_request(request)

            elif req_type == Types.Open:
                request= OpenRequest.deserialize(bdata)
                logging.debug(f"Parsing open request for session: {request.session_id}")
                self.handle_open_request(request)
            
            elif req_type == Types.Close:
                request= CloseRequest.deserialize(bdata)
                logging.debug(f"Parsing close request for session: {request.session_id}")
                self.handle_close_request(request)

            elif req_type == Types.Session:
                msg= SessionMsg.deserialize(bdata)
                logging.debug(f"Parsing session message for session: {msg.session_id}")
                self.handle_sessionmsg(msg)

            else:
                self.__send_pkt(ErrorResponse('invalid request', req_type))
            
            
    def handle_store_request(self, request: StoreRequest):
        """
        generate a token, write the function info to disk, and then send the
        token back to the client
        """
        token= str(uuid.uuid4())
        function.create_function(token, request.name, request.code)
        self.__send_pkt(StoreResponse(token))


    def handle_execute_request(self, request: ExecuteRequest):
        """
        initiate a new session and start executing the function corresponding
        to the request token
        """
        function_data= function.get_function(request.token)
        
        if function_data is not None:
            exec_data= {"call": request.call, "code": function_data['code']}
            exec_data= base64.urlsafe_b64encode(json.dumps(exec_data).encode()).decode()
            new_session= session_mngr.create()
            new_session.execute(exec_data)
            self.__send_pkt(ExecuteResponse(new_session.session_id))
        else:
            self.__send_pkt(ErrorResponse("invalid token", Types.Execute))

    
    def handle_open_request(self, request: OpenRequest):
        """
        start a worker process to begin reading output from the function
        corresponding to the requested session
        """
        session= session_mngr.get(request.session_id)
        if session is None:
            self.__send_pkt(ErrorResponse(f"no session exists with id: {request.session_id}", Types.Open))
            return

        if session in self.open_sessions:
            self.__send_pkt(ErrorResponse(f"session: {session.session_id} already open", Types.Open))
            return 

        self.open_sessions.append(session)

        # start a worker to handle buffered input/out
        logging.debug(f"({session.session_id}) starting worker")
        session.start_worker(self.conn)


    def handle_close_request(self, request: CloseRequest):
        """
        clean up and remove an open session from the pool of open sessions
        """
        session= session_mngr.get(request.session_id)
        if session is None:
            self.__send_pkt(ErrorResponse(f"no session exists with id: {request.session_id}", Types.Close))
            return

        if session not in self.open_sessions:
            self.__send_pkt(ErrorResponse(f"no open session with id: {session.session_id}", Types.Close))
            return

        self.__clean_session(session)


    def handle_sessionmsg(self, msg: SessionMsg):
        """
        pass data from session message along to the function as input
        """
        session= session_mngr.get(msg.session_id)
        if session is None or not session.write_input(msg.data):
            logging.debug(f"({msg.session_id}) couldn't write to session")
            self.__send_pkt(SessionMsgErr(msg.session_id, b"session isn't alive"))


    def __handle_disconnect(self):
        """
        wait a sec before cleaning the client's open sessions
        """
        logging.info(f"client disconnect: {self.address}:{self.port}, cleaning all open sessions")
        time.sleep(1)
        for session in self.open_sessions:
            self.__clean_session(session)


    def __clean_session(self, session):
        """
        clean up an open session by terminating the worker process and attempting to further clean up if the function has finished executing
        """
        if session in self.open_sessions:
            logging.debug(f"({session.session_id}) cleaning up session")
            session.is_open.value= 0
            session.worker_proc.join()
            logging.debug(f"({session.session_id}) worker joined")

            if session.clean() == False:
                logging.debug(f"({session.session_id}) function still running")
            else:
                logging.debug(f"({session.session_id}) function terminated")
                session_mngr.destroy(session.session_id)

            self.open_sessions.remove(session)
        

    def __recv_pkt(self):
        """
        recieve a packet, parse the header, return the request type and data
        """
        hdr= self.__recv_all(Request.HeaderLen)
        if hdr is None:
            raise ConnectionError("failed to recv header")
            
        req_type, length, err= Request.unpack_hdr(hdr)
        if err is not None:
            raise ConnectionError(f"unpacking header failed {err}")

        bdata= self.__recv_all(length)
        if bdata is None:
            raise ConnectionError("failed to recv packet data")

        return req_type, bdata


    def __send_pkt(self, response: Response):
        """
        send a packet
        """
        self.conn.sendall(response.serialize())


    def __recv_all(self, n):
        """
        simple recv() wrapper
        """
        data = bytearray()
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
