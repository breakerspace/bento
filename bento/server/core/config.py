import argparse
import logging
import os
import os.path

class Options:
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 8888
        self.working_dir = os.path.abspath(os.getcwd())
        self.functions_dir = os.path.join(self.working_dir, 'functions')
        self.instances_dir = os.path.join(self.working_dir, 'instances')
        self.function_cmd = 'python3.6'
        self.log_level = logging.DEBUG

opts = Options()

def log_level_from_str(level):
    str2level = {
        'DEBUG': logging.debug,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
        }
    return str2level[level]

def parse_cmdline():
    parser = argparse.ArgumentParser(
            description='Run a bento server')
    parser.add_argument('host', nargs='?', default=opts.host,
            help=f"server's IPv4 address (default: {opts.host})")
    parser.add_argument('port', nargs='?', type=int, default=opts.port,
            help=f"server's port (default: {opts.port})")
    parser.add_argument('-w', '--working-dir', default=opts.working_dir,
            help="working directory (default: current working directory)")
    parser.add_argument('-c', '--function-cmd', default=opts.function_cmd,
            help=f"""the command to run to execute a function (default: {opts.function_cmd}).
            For SGX execution, specify a command like 
            'graphene-sgx/pal_loader graphene-sgx/manifest'
            """)
    parser.add_argument('-l', '--log-level', default=opts.log_level,
            choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help="log level (default: %s)" % logging.getLevelName(opts.log_level))

    args = parser.parse_args()

    for name in ('host', 'port', 'function_cmd'):
        setattr(opts, name, getattr(args, name))

    # test if the user specified the working dir
    if opts.working_dir != args.working_dir:
        opts.working_dir = os.path.abspath(args.working_dir)
        opts.functions_dir = os.path.join(opts.working_dir, 'functions')
        opts.instances_dir = os.path.join(opts.working_dir, 'instances')

    # test if the user specified the log level
    if isinstance(args.log_level, str):
        opts.log_level = log_level_from_str(args.log_level)


def setup():
    os.chdir(opts.working_dir)
    os.makedirs(opts.functions_dir, exist_ok=True)
    os.makedirs(opts.instances_dir, exist_ok=True)
