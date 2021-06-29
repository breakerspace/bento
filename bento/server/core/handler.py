import base64
import json
import logging
from multiprocessing import Process
import struct
import select
from threading import Thread
import uuid

from . import instance_mngr
from . import function 
from common.protocol import *


class Handler():
    def __init__(self, conn):
        self.conn= conn
        

    def handle_communication(self, instance: instance_mngr.Instance):
        """
        handle instance messages until client disconnect or function terminated and no output data left
        """
        inputs= [self.conn, instance.read_handle, instance.function_proc.stderr]
        while True:
            r, w, e= select.select(inputs, [], [])

            if self.conn in r:
                """
                parse messages from client: 
                    - instance msg: send data to function
                    - close request: instance over, return
                    - invalid: send error to client
                """
                try:
                    msg_type, data= self._recv_pkt()
                except Exception as exc:
                    logging.error(exc)
                    return

                if msg_type == MsgTypes.Input:
                    if instance.function_proc.poll:
                        logging.debug(f"({instance.function_id}) function dead")
                        self._send_pkt(FunctionErr(instance.function_id, "function dead"))
                    else:
                        datalen= struct.pack("Q", len(data))
                        instance.function_proc.stdin.write(datalen + data)
                        instance.function_proc.stdin.flush()
                        logging.debug(f"({instance.function_id}) data written to function")
                
                elif msg_type == Types.Close:
                    return

                else:
                    self._send_pkt(FunctionErr(instance.function_id, "invalid msg type"))

            if instance.read_handle in r:
                """
                parse messages from function output buffer
                """
                datalen= instance.read_handle.read(8)
                if len(datalen) == 8:
                    datalen,= struct.unpack("Q", datalen)
                    data= instance.read_handle.read(datalen)
                    self._send_pkt(Output(instance.function_id, data))
                else:
                    if instance.function_proc.poll():
                        logging.debug(f"({instance.function_id}) function dead")
                        self._send_pkt(FunctionErr(instance.function_id, "function dead"))                       
                        return

            if instance.function_proc.stderr in r:
                """
                parse error data from function process
                    - instance isn't over, there could still be data in the function output buffer
                """
                errdata= ""
                for line in instance.function_proc.stderr:
                    errdata+= line
                
                if errdata == "":
                    self._send_pkt(FunctionErr(instance.function_id, "function dead"))
                    return

                logging.error(f"({instance.function_id}) error data: \n{errdata}")
                self._send_pkt(Error(instance.function_id, errdata))


    def handle_requests(self) -> instance_mngr.Instance:
        """
        handle requests until a client disconnects or opens an instance
        """
        while True:
            try:
                req_type, data= self._recv_pkt()
            except Exception as e:
                logging.error(e)
                return None                

            if req_type == Types.Store: 
                request= StoreRequest.deserialize(data)
                logging.debug("Parsing store request")
                self._handle_store_request(request)
                
            elif req_type == Types.Execute:
                request= ExecuteRequest.deserialize(data)
                logging.debug(f"Parsing execute request for token: {request.token}")
                self._handle_execute_request(request)

            elif req_type == Types.Open:
                request= OpenRequest.deserialize(data)
                logging.debug(f"Parsing open request for instance: {request.function_id}")
                instance= self._handle_open_request(request)
                if instance:
                    return instance

            elif req_type == Types.Instance:
                self._send_pkt(ErrorResponse('no instance open', req_type))
            
            else:
                self._send_pkt(ErrorResponse('invalid request', req_type))


    def _handle_store_request(self, request: StoreRequest):
        """
        generate a token, write the function info to disk, and then send the
        token back to the client
        """
        token= str(uuid.uuid4())
        function.create_function(token, request.name, request.code)
        self._send_pkt(StoreResponse(token))


    def _handle_execute_request(self, request: ExecuteRequest):
        """
        initiate a new instance and start executing the function corresponding
        to the request token
        """
        function_data= function.get_function(request.token)
        
        if function_data is not None:
            exec_data= {"call": request.call, "code": function_data['code']}
            exec_data= base64.urlsafe_b64encode(json.dumps(exec_data).encode()).decode()
            new_instance= instance_mngr.create(exec_data)
            self._send_pkt(ExecuteResponse(new_instance.function_id))
        else:
            self._send_pkt(ErrorResponse("invalid token", Types.Execute))

    
    def _handle_open_request(self, request: OpenRequest):
        """
        start a worker process to begin reading output from the function
        corresponding to the requested instance
        """
        instance= instance_mngr.get(request.function_id)
        if instance is None:
            self._send_pkt(ErrorResponse(f"no instance exists with id: {request.function_id}", Types.Open))
            return None

        return instance


    def _recv_pkt(self):
        """
        recieve a packet, parse the header, return the request type and data
        """
        hdr= self._recv_all(Request.HeaderLen)
        if hdr is None:
            raise ConnectionError("failed to recv header")
            
        req_type, length, err= Request.unpack_hdr(hdr)
        if err is not None:
            raise ConnectionError(f"unpacking header failed {err}")

        data= self._recv_all(length)
        if data is None:
            raise ConnectionError("failed to recv packet data")

        return req_type, data


    def _send_pkt(self, response: Response):
        """
        send a packet
        """
        self.conn.sendall(response.serialize())


    def _recv_all(self, n):
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

