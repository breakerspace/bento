#!/usr/bin/env python3

import argparse
import logging
import socket
import sys
from threading import Thread

import core.config as config
from core.config import opts

from core.handler import ClientThread 

logging.basicConfig(format='%(levelname)s:\t%(message)s', level=opts.log_level)

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
    logging.debug(f"  sessions_dir: {opts.sessions_dir}")
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
