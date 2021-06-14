#!/usr/bin/env python3

import argparse
import logging
from select import EPOLLONESHOT
import socket
import sys
import time
from threading import Thread

import core.config as config
from core.config import opts

from core.handler import Handler
import core.session_mngr as session_mngr

logging.basicConfig(format='%(levelname)s:\t%(message)s', level=opts.log_level)


class ClientThread(Thread):
    """
    interact with a client
    """
    def __init__(self, address, port, conn):
        Thread.__init__(self)
        self.address= address
        self.port= port
        self.conn= conn
        self.open_session= None
        self.handler= Handler(conn)


    def run(self):
        while True:
            self.open_session= self.handler.handle_requests()
            if self.open_session:
                self.handler.handle_session(self.open_session)
            else:
                # no session opened - client disconnect
                self._handle_disconnect()
                break


    def _clean_session(self):
        """
        clean up an open session 
        """
        if self.open_session:
            logging.debug(f"({self.open_session.session_id}) cleaning up session")
            if self.open_session.clean() == False:
                logging.debug(f"({self.open_session.session_id}) function still running")
            else:
                logging.debug(f"({self.open_session.session_id}) function terminated")
                session_mngr.destroy(self.open_session.session_id)
            self.open_session= None


    def _handle_disconnect(self):
        """
        wait a sec before cleaning the client's open sessions
        """
        logging.info(f"client disconnect: {self.address}:{self.port}, cleaning all open sessions")
        time.sleep(1)
        self._clean_session()


def _pr_config():
    logging.debug("configuration: ")
    logging.debug(f"  host: {opts.host}")
    logging.debug(f"  port: {opts.port}")
    logging.debug(f"  working_dir: {opts.working_dir}")
    logging.debug(f"  functions_dir: {opts.functions_dir}")
    logging.debug(f"  sessions_dir: {opts.sessions_dir}")
    logging.debug(f"  function_cmd: {opts.function_cmd}")
    logging.debug("  log_level: %s" % logging.getLevelName(opts.log_level))


"""
============================================================================
Entry Point
============================================================================
"""

def __main():
    config.parse_cmdline()
    config.setup()
    _pr_config()
    logging.getLogger().setLevel(opts.log_level)

    sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((opts.host, opts.port))

    try:
        sock.listen()
        logging.info(f"Listening on {opts.host}:{opts.port}")
        while True:
            conn, addr= sock.accept()
            logging.info("New connection from %s:%d" % addr)
            new_thread= ClientThread(addr[0], addr[1], conn)
            new_thread.start()

    except socket.error:
        logging.info("Closing socket...")

    finally:
        new_thread.join()
        sock.close()


if __name__ == '__main__':
    __main()
