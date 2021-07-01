#!/usr/bin/env python3

import logging
from select import EPOLLONESHOT
import socket
import time
from threading import Thread

import core.config as config
from core.config import opts

from core.handler import Handler
import core.instance_mngr as instance_mngr

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
        self.instance= None
        self.handler= Handler(conn)


    def run(self):
        while True:
            self.instance= self.handler.handle_requests()
            if self.instance:
                self.handler.handle_communication(self.instance)
            else:
                # no instance opened - client disconnect
                self._handle_disconnect()
                break


    def _clean_instance(self):
        """
        clean up the client's connection to an instance
            - the instance may continue to run while no clients are interacting with it 
        """
        if self.instance:
            logging.debug(f"({self.instance.function_id}) cleaning up instance")
            if not self.instance.clean():
                logging.debug(f"({self.instance.function_id}) function still running")
            else:
                logging.debug(f"({self.instance.function_id}) function terminated")
                instance_mngr.destroy(self.instance.function_id)
            self.instance= None


    def _handle_disconnect(self):
        """
        wait a sec before cleaning the client's instance 
        """
        logging.info(f"client disconnect: {self.address}:{self.port}")
        time.sleep(1)
        self._clean_instance()



"""
============================================================================
Entry Point
============================================================================
"""

def _pr_config():
    logging.debug("configuration: ")
    logging.debug(f"  host: {opts.host}")
    logging.debug(f"  port: {opts.port}")
    logging.debug(f"  working_dir: {opts.working_dir}")
    logging.debug(f"  functions_dir: {opts.functions_dir}")
    logging.debug(f"  instances_dir: {opts.instances_dir}")
    logging.debug(f"  function_cmd: {opts.function_cmd}")
    logging.debug("  log_level: %s" % logging.getLevelName(opts.log_level))


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
