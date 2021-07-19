import base64
import json
import logging
from multiprocessing import Process
import struct
import select
import uuid

from . import instance_mngr
from . import function 
from .bentoapi import StdoutData
from common.protocol import *


class Handler():
    def __init__(self, conn):
        self.conn= conn
        

    def handle_communication(self, instance: instance_mngr.Instance):
        """
        handle instance messages until client disconnect or function terminated and no output data left
        """
        logging.debug(f"({instance.function_id}) handling communication")

        msg_queue= []

        def _handle_disconnect():
            """push read pointer back to account for unread messages"""
            pos= instance.readout_handle.tell()
            for msg in msg_queue:
                pos-= (len(msg) + StdoutData.HeaderLen)
            instance.readout_handle.seek(pos)

        inputs= [self.conn, instance.readout_handle, instance.readerr_handle]
        outputs= [self.conn]
        end_instance= False
        
        while not end_instance:
            try:
                readable, writeable, in_error= select.select(inputs, outputs, [])
            except select.error as e:
                _handle_disconnect()

            if not instance.alive():
                end_instance= True

            if self.conn in writeable:
                if msg_queue:
                    msg= msg_queue.pop(0)
                    self._send_pkt(msg)

            if self.conn in readable:
                logging.debug(f"({instance.function_id}) reading from client")
                try:
                    msg_type, data= self._recv_msg()
                except Exception as exc:
                    logging.error(exc)
                    return

                if msg_type == MsgTypes.Input:
                    # TODO: check function_id before writing to the instance
                    msg= Input.deserialize(data)
                    if instance.alive():
                        datalen= struct.pack(">I", len(msg.data))
                        instance.function_proc.stdin.write(datalen + msg.data)
                        instance.function_proc.stdin.flush()
                        logging.debug(f"({instance.function_id}) data written to function")
                
                elif msg_type == Types.Close:
                    _handle_disconnect()
                    return

                else:
                    self._send_pkt(FunctionErr(instance.function_id, "invalid msg type"))

            if instance.readout_handle in readable:
                hdr= instance.readout_handle.read(StdoutData.HeaderLen)
                if len(hdr) == StdoutData.HeaderLen:
                    end_instance= False
                    err, datalen= struct.unpack(StdoutData.HeaderFmt, hdr)
                    data= instance.readout_handle.read(datalen)
                    while len(data) < datalen:
                        data+= instance.readout_handle.read(datalen - len(data))
                    if err:
                        msg_queue.append(Error(instance.function_id, data))
                    else:
                        msg_queue.append(Output(instance.function_id, data))

            if instance.readerr_handle in readable:
                errdata= ""
                for line in instance.readerr_handle:
                    errdata+= line
                
                if errdata:
                    end_instance= False
                    logging.error(f"({instance.function_id}) Execution error:\n {errdata}")

        logging.debug(f"({instance.function_id}) function dead")
        self._send_pkt(FunctionErr(instance.function_id, "function dead"))


    def handle_requests(self) -> instance_mngr.Instance:
        """
        handle requests until a client disconnects or opens an instance
        """
        while True:
            try:
                req_type, data= self._recv_request()
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

            else:
                self._send_pkt(ErrorResponse('invalid request', req_type))


    def _handle_store_request(self, request: StoreRequest):
        """
        generate a unique id and store the funciton code and name
        """
        token= str(uuid.uuid4())
        function.create_function(token, request.name, request.code)
        self._send_pkt(StoreResponse(token))


    def _handle_execute_request(self, request: ExecuteRequest):
        """
        get the function data and start an instance
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
        get and return the instance requested
        """
        instance= instance_mngr.get(request.function_id)
        if instance is None:
            self._send_pkt(ErrorResponse(f"no instance exists with id: {request.function_id}", Types.Open))
            return None

        return instance


    def _recv_msg(self):
        """
        recv a message from client to function
        """
        hdr= self._recv_all(FunctionMessage.HeaderLen)
        if not hdr:
            raise ConnectionError("failed to recv header")
        
        msg_type, length, err= FunctionMessage.unpack_hdr(hdr)
        if err:
            raise ConnectionError(f"unpacking header failed {err}")

        data= self._recv_all(length)
        if not data:
            raise ConnectionError("failed to recv packet data")

        return msg_type, data
        

    def _recv_request(self):
        """
        recv a request from client to server
        """
        hdr= self._recv_all(Request.HeaderLen)
        if not hdr:
            raise ConnectionError("failed to recv header")
            
        req_type, length, err= Request.unpack_hdr(hdr)
        if err:
            raise ConnectionError(f"unpacking header failed {err}")

        data= self._recv_all(length)
        if not data:
            raise ConnectionError("failed to recv packet data")

        return req_type, data


    def _send_pkt(self, response: Response):
        """
        send wrapper
        """
        self.conn.sendall(response.serialize())


    def _recv_all(self, n):
        """
        recv wrapper
        """
        data = bytearray()
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

