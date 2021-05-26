#!/usr/bin/env python3

import argparse
import logging
import select
import socket
import struct
import zlib
from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler
import sys

sys.path.append("../..")
from bento.common.protocol import *
from bento.client.api import ClientConnection 

SOCKS_VERSION = 5
FUNCTION_FILE= "proxy.func"

DEFAULT_BENTO_ADDR = '127.0.0.1'
DEFAULT_BENTO_PORT = 8888
DEFAULT_PROXY_ADDR = '127.0.0.1'
DEFAULT_PROXY_PORT = 9011

# the command-line arguments
g_args = None

class ThreadingTCPServer(ThreadingMixIn, TCPServer):
    pass


class SocksProxy(StreamRequestHandler):

    def generate_failed_reply(self, address_type, error_number):
        return struct.pack("!BBBBIH", SOCKS_VERSION, error_number, 0, address_type, 0, 0)

    def get_available_methods(self, n):
        methods= []
        for i in range(n):
            methods.append(ord(self.connection.recv(1)))
        return methods

    def handle(self):
        logging.info('Accepting connection from %s:%s' % self.client_address)

        # greeting header
        header= self.connection.recv(2)
        version, nmethods= struct.unpack("!BB", header)

        # socks 5
        assert version == SOCKS_VERSION
        assert nmethods > 0

        # get available methods
        methods= self.get_available_methods(nmethods)

        # send welcome message
        self.connection.sendall(struct.pack("!BB", SOCKS_VERSION, 0))

        # request
        version, cmd, address_type = struct.unpack("!BBxB", self.connection.recv(4))
        assert version == SOCKS_VERSION

        if address_type == 1:  # IPv4
            address= socket.inet_ntop(socket.AF_INET,
                    self.connection.recv(4))
        elif address_type == 3:  # Domain name
            domain_length= self.connection.recv(1)[0]
            address= self.connection.recv(domain_length)
        elif address_type == 4: # IPv6
            address= socket.inet_ntop(socket.AF_INET6,
                    self.connection.recv(16))
        else:
            logging.warning('unknown address type: %x' % address_type)
            self.server.close_request(self.request)

        print('addres_type', address_type)
        port= struct.unpack('!H', self.connection.recv(2))[0]
        logging.info('Desired address and port: %s:%s' % (address, port))

        # reply
        try:
            if cmd == 1:
                """
                Connect to the Bento server
                """
                server_conn= ClientConnection(g_args.addr, g_args.port)
                bind_address = server_conn.conn.getsockname()
            else:
                """
                Only support CONNECT
                """
                self.server.close_request(self.request)

            server_addr= struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
            server_port= bind_address[1]
            reply= struct.pack("!BBBBIH", SOCKS_VERSION, 0, 0, 1, server_addr, server_port)

        except Exception as err:
            logging.error(err)
            reply= self.generate_failed_reply(address_type, 5)

        self.connection.sendall(reply)

        if reply[1] == 0 and cmd == 1:
            self.exchange(self.connection, server_conn, address, port)

        self.server.close_request(self.request)


    def exchange(self, cli, server_conn, addr, port):
        """
        Exchange data between client and Bento proxy function
        """
        function_name= "proxy"
        f= open(f"{FUNCTION_FILE}", 'r')
        function_code= f.read()

        if isinstance(addr, bytes):
            addr= addr.decode()
        token, errmsg= server_conn.send_store_request(function_name, function_code)
        if errmsg is not None:
            logging.error(f"error message from server: {errmsg}")
        else:
            logging.debug(f"got token: {token}")
            call= f"{function_name}(\'{addr}\', {port})"
            session_id, errmsg= server_conn.send_execute_request(call, token)
            if errmsg is not None:
                logging.error(f"error message from server: {errmsg}")
            else:
                logging.debug(f"got session_id: {session_id}")
                logging.debug(f"sending open request")
                server_conn.send_open_request(session_id)
                while True:
                    r, w, e= select.select([cli, server_conn.conn], [], [])

                    if cli in r:
                        logging.debug("recving client data")
                        cli_data= cli.recv(4096)
                        if server_conn.send_sessionmsg(session_id, cli_data) <= 0:
                            logging.debug('could not send data to server')
                            break
                        logging.debug("data sent to server")

                    if server_conn.conn in r:
                        logging.debug("recving server data")
                        data, session_id, err= server_conn.get_sessionmsg()
                        if err:
                            logging.debug(err)
                            break

                        if cli.send(data) <= 0:
                            logging.debug("could not send data to client")
                            break
                        logging.debug("data sent to client")
                print("done")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(
            description='Proxy requests from a web agent through bento')
    parser.add_argument('--addr', default=DEFAULT_BENTO_ADDR,
            help=f"Bento server's IPv4 address (default: {DEFAULT_BENTO_ADDR})")
    parser.add_argument('--port', type=int, default=DEFAULT_BENTO_PORT,
            help=f"Bento server's port (default: {DEFAULT_BENTO_PORT})")
    parser.add_argument('--proxy-addr', default=DEFAULT_PROXY_ADDR,
            help=f"IP address to bind proxy to (default: {DEFAULT_PROXY_ADDR})")
    parser.add_argument('--proxy-port', type=int, default=DEFAULT_PROXY_PORT,
            help=f"proxy's port (default: {DEFAULT_PROXY_PORT})")
    g_args = parser.parse_args()

    print(f"Listening on {g_args.proxy_addr}:{g_args.proxy_port}")
    print(f"Connecting to bento server at {g_args.addr}:{g_args.port}")

    with ThreadingTCPServer((g_args.proxy_addr, g_args.proxy_port), SocksProxy) as server:
        server.allow_reuse_address= True
        server.serve_forever()
